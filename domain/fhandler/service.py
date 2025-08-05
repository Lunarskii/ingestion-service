from datetime import datetime
from typing import Any

import langdetect
from langchain.text_splitter import TextSplitter
from sentence_transformers import SentenceTransformer

from domain.schemas import (
    VectorMetadata,
    Vector,
    DocumentMeta,
    DocumentStatus,
)
from domain.extraction.base import (
    TextExtractor,
    ExtractedInfo,
)
from domain.extraction.factory import ExtractorFactory
from domain.fhandler.schemas import File
from services import (
    RawStorage,
    VectorStore,
    MetadataRepository,
)
from config import logger


class DocumentProcessor:
    """
    Управляет всем процессом обработки документов.

    :ivar raw_storage: Сервис для сохранения сырых файлов.
    :type raw_storage: RawStorage
    :ivar vector_store: Сервис векторного хранилища.
    :type vector_store: VectorStore
    :ivar metadata_repository: Сервис репозитория метаданных.
    :type metadata_repository: MetadataRepository
    :ivar embedding_model: Модель для эмбеддингов.
    :type embedding_model: SentenceTransformer
    :ivar text_splitter: Разделитель текста на чанки.
    :type text_splitter: TextSplitter
    """

    def __init__(
        self,
        raw_storage: RawStorage,
        vector_store: VectorStore,
        metadata_repository: MetadataRepository,
        embedding_model: SentenceTransformer,
        text_splitter: TextSplitter,
    ):
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
        Выполняет полный цикл обработки загруженного документа:
            1. Сохраняет исходный документ.
            2. Извлекает текст и метаданные из документа в зависимости от его типа.
            3. Определяет язык.
            4. Разбивает текст на чанки.
            5. Создает эмбеддинги для каждого чанка.
            6. Загружает векторы в хранилище векторов.
            7. Сохраняет метаданные документа.

        :param file: Полные байты файла и метаданные файла.
        :type file: File
        :param document_id: ID документа.
        :type document_id: str
        :param workspace_id: Идентификатор рабочего пространства.
        :type workspace_id: str
        """

        context_logger = logger.bind(document_id=document_id, workspace_id=workspace_id)

        metadata_kwargs: dict[str, Any] = {
            "document_id": document_id,
            "workspace_id": workspace_id,
            "document_type": file.extension.lstrip(".").upper(),
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
                document_type=metadata_kwargs["document_type"],
                file_size_bytes=file.size,
            )
            extractor: TextExtractor = ExtractorFactory().get_extractor(file.extension)
            document_info: ExtractedInfo = extractor.extract(file.file)
            metadata_kwargs.update(document_info.model_dump(include={"document_page_count", "author", "creation_date"}))

            context_logger.info("Определение основного языка документа")
            metadata_kwargs["detected_language"] = langdetect.detect(document_info.text)

            context_logger.info("Разбиение текста на чанки")
            chunks: list[str] = self.text_splitter.split_text(document_info.text)

            context_logger.info("Создание эмбеддингов для каждого чанка, векторизация")
            vectors: list[Vector] = self._vectorize_chunks(chunks, document_id, workspace_id, file.name)

            context_logger.info("Сохранение векторов")
            self.vector_store.upsert(vectors)
        except Exception as e:
            error_message: str = str(e)
            context_logger.error("Не удалось обработать документ", error_message=error_message)
            metadata_kwargs["error_message"] = error_message
            metadata_kwargs["status"] = DocumentStatus.failed

        try:
            context_logger.info("Сохранение метаданных документа")
            self.metadata_repository.save(DocumentMeta(**metadata_kwargs))
        except Exception as e:
            context_logger.error("Не удалось сохранить метаданные документа", error_message=str(e))

    def _vectorize_chunks(
        self,
        chunks: list[str],
        document_id: str,
        workspace_id: str,
        document_name: str,
    ) -> list[Vector]:
        embeddings = self.embedding_model.encode(chunks, show_progress_bar=False)
        return [
            Vector(
                id=f"{document_id}-{i}",
                values=embedding.tolist(),  # noqa
                metadata=VectorMetadata(
                    document_id=document_id,
                    workspace_id=workspace_id,
                    document_name=document_name,
                    chunk_index=i,
                    text=chunk,
                ),
            )
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
        ]
