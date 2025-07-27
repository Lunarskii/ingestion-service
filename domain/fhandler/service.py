from io import BytesIO
from datetime import datetime
from typing import Any

import langdetect
from langchain.text_splitter import TextSplitter
from sentence_transformers import SentenceTransformer

from domain.schemas import (
    Vector,
    DocumentMeta,
    DocumentStatus,
)
from domain.fhandler.extractor import (
    TextExtractor,
    ExtractedInfo,
)
from domain.fhandler.factory import ExtractorFactory
from domain.fhandler.utils import get_file_extension
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
    :ivar vector_store: Сервис для индексации векторов.
    :type vector_store: VectorStore
    :ivar metadata_repository: Сервис для хранения метаданных.
    :type metadata_repository: MetadataRepository
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
        file_bytes: bytes,
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

        :param file_bytes: Документ в байтах.
        :type file_bytes: bytes
        :param document_id: ID документа.
        :type document_id: str
        :param workspace_id: ...
        :type workspace_id: str
        """

        context_logger = logger.bind(document_id=document_id, workspace_id=workspace_id)

        ingested_at: datetime = datetime.now()
        file = BytesIO(file_bytes)
        file_extension: str = get_file_extension(file_bytes)
        file_size_bytes: int = len(file_bytes)
        document_type: str = file_extension.lstrip(".").upper()
        raw_storage_path: str = f"{workspace_id}/{document_id}{file_extension}"
        metadata_kwargs: dict[str, Any] = {
            "document_id": document_id,
            "workspace_id": workspace_id,
            "document_type": document_type,
            "raw_storage_path": raw_storage_path,
            "file_size_bytes": file_size_bytes,
            "ingested_at": ingested_at,
            "status": DocumentStatus.success,
        }

        try:
            context_logger.info(
                "Сохранение необработанного документа",
                raw_storage_path=raw_storage_path,
            )
            self.raw_storage.save(file_bytes, raw_storage_path)

            context_logger.info(
                "Извлечение текста и метаданных из документа",
                document_type=document_type,
                file_size_bytes=file_size_bytes,
            )
            extractor: TextExtractor = ExtractorFactory().get_extractor(file_extension)
            document_info: ExtractedInfo = extractor.extract(file)
            metadata_kwargs.update(document_info.model_dump(include={"document_page_count", "author", "creation_date"}))

            context_logger.info("Определение основного языка документа")
            metadata_kwargs["detected_language"] = langdetect.detect(document_info.text)

            context_logger.info("Разбиение текста на чанки")
            chunks: list[str] = self.text_splitter.split_text(document_info.text)

            context_logger.info("Создание эмбеддингов для каждого чанка, векторизация")
            vectors: list[Vector] = self._vectorize_chunks(chunks, document_id, workspace_id)

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

    def _vectorize_chunks(self, chunks: list[str], document_id: str, workspace_id: str) -> list[Vector]:
        embeddings = self.embedding_model.encode(chunks, show_progress_bar=False)
        return [
            Vector(
                id=f"{document_id}-{i}",
                values=embedding.tolist(),  # noqa
                metadata={
                    "document_id": document_id,
                    "workspace_id": workspace_id,
                    "chunk_index": i,
                    "text": chunk,
                },
            )
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
        ]
