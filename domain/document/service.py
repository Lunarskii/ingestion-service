from datetime import datetime
from typing import Any

import langdetect
from langchain.text_splitter import TextSplitter
from sentence_transformers import SentenceTransformer

from domain.schemas import (
    VectorMetadata,
    Vector,
)
from domain.extraction import (
    extract as extract_from_document,
    Page,
    ExtractedInfo,
)
from domain.document.schemas import (
    File,
    DocumentStatus,
    DocumentMeta,
)
from services import (
    RawStorage,
    VectorStore,
    MetadataRepository,
)
from config import logger


class DocumentService:
    """
    Сервис, управляющий полным циклом обработки загруженных документов.
    """

    def __init__(
        self,
        raw_storage: RawStorage,
        vector_store: VectorStore,
        metadata_repository: MetadataRepository,
        embedding_model: SentenceTransformer,
        text_splitter: TextSplitter,
    ):
        """
        :param raw_storage: Экземпляр сервиса для сохранения сырых файлов.
        :type raw_storage: RawStorage
        :param vector_store: Экземпляр сервиса векторного хранилища.
        :type vector_store: VectorStore
        :param metadata_repository: Экземпляр репозитория метаданных.
        :type metadata_repository: MetadataRepository
        :param embedding_model: Модель для работы с эмбеддингами.
        :type embedding_model: SentenceTransformer
        :param text_splitter: Инструмент для разбиения текста на чанки.
        :type text_splitter: TextSplitter
        """

        self.raw_storage = raw_storage
        self.vector_store = vector_store
        self.metadata_repository = metadata_repository
        self.embedding_model = embedding_model
        self.text_splitter = text_splitter

    def process(
        self,
        file: File,
        document_id: str,
        workspace_id: str,
    ) -> None:
        """
        Выполняет полный цикл обработки загруженного документа.

        Метаданные документа сохраняются, если они присутствуют в результате извлечения.
        В случае любой ошибки на этапе обработки в поле метаданных будет записано
        ``status=DocumentStatus.failed`` и текст ошибки в ``error_message``.
        Метод гарантирует попытку сохранить метаданные в любом случае (успех/ошибка обработки).

        Пайплайн:
            1. Сохранение исходного файла в ``RawStorage``.
            2. Извлечение текста и метаданных с помощью ``TextExtractor``.
            3. Определение языка документа (по тексту первой страницы).
            4. Разбиение текста на чанки с помощью ``TextSplitter``.
            5. Генерация эмбеддингов для каждого чанка.
            6. Загрузка векторов в ``VectorStore``.
            7. Сохранение метаданных в ``MetadataRepository``.

        :param file: Объект файла, содержащий байты и метаданные (:class:`File`).
        :type file: File
        :param document_id: Идентификатор документа (используется для ключей/путей хранения).
        :type document_id: str
        :param workspace_id: Идентификатор рабочего пространства (workspace).
        :type workspace_id: str
        """

        context_logger = logger.bind(document_id=document_id, workspace_id=workspace_id)

        metadata_kwargs: dict[str, Any] = {
            "document_id": document_id,
            "workspace_id": workspace_id,
            "document_name": file.name,
            "media_type": file.type,
            "raw_storage_path": f"{workspace_id}/{document_id}{file.extension}",
            "file_size_bytes": file.size,
            "ingested_at": datetime.now(),
            "status": DocumentStatus.success,
        }

        try:
            context_logger.info(
                "Сохранение необработанного документа",
                raw_storage_path=metadata_kwargs["raw_storage_path"],
            )
            self.raw_storage.save(file.content, metadata_kwargs["raw_storage_path"])

            context_logger.info(
                "Извлечение текста и метаданных из документа",
                media_type=metadata_kwargs["media_type"],
                file_size_bytes=file.size,
            )
            document_info: ExtractedInfo = extract_from_document(file)
            metadata_kwargs.update(
                document_info.model_dump(
                    include={
                        "document_page_count",
                        "author",
                        "creation_date",
                    }
                )
            )

            context_logger.info("Определение основного языка документа")
            if document_info.pages:
                metadata_kwargs["detected_language"] = langdetect.detect(
                    document_info.pages[0].text
                )

            context_logger.info("Разбиение текста на чанки")
            chunks: list[Page] = self._split_text(document_info.pages)

            context_logger.info("Создание эмбеддингов для каждого чанка, векторизация")
            vectors: list[Vector] = self._vectorize_chunks(
                chunks, document_id, workspace_id, file.name
            )

            context_logger.info("Сохранение векторов")
            self.vector_store.upsert(vectors)
        except Exception as e:
            error_message: str = str(e)
            context_logger.error(
                "Не удалось обработать документ", error_message=error_message
            )
            metadata_kwargs["error_message"] = error_message
            metadata_kwargs["status"] = DocumentStatus.failed

        try:
            context_logger.info("Сохранение метаданных документа")
            self.metadata_repository.save(DocumentMeta(**metadata_kwargs))
        except Exception as e:
            context_logger.error(
                "Не удалось сохранить метаданные документа", error_message=str(e)
            )

    def _split_text(self, pages: list[Page]) -> list[Page]:
        chunks: list[Page] = []
        for page in pages:
            page_chunks: list[str] = self.text_splitter.split_text(page.text)
            for chunk in page_chunks:
                chunks.append(Page(num=page.num, text=chunk))
        return chunks

    def _vectorize_chunks(
        self,
        chunks: list[Page],
        document_id: str,
        workspace_id: str,
        document_name: str,
    ) -> list[Vector]:
        embeddings = self.embedding_model.encode(
            [chunk.text for chunk in chunks], show_progress_bar=False
        )
        return [
            Vector(
                id=f"{document_id}-{i}",
                values=embedding.tolist(),
                metadata=VectorMetadata(
                    document_id=document_id,
                    workspace_id=workspace_id,
                    document_name=document_name,
                    document_page=chunk.num,
                    text=chunk.text,
                ),
            )
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
        ]
