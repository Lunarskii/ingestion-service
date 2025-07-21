from io import BytesIO
from datetime import datetime
from typing import Any

from langdetect import detect
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

from domain.schemas import (
    Vector,
    DocumentMeta,
    DocumentStatus,
)
from domain.handlers import (
    TextExtractor,
    ExtractorFactory,
    ExtractedInfo,
)
from domain.utils import get_file_extension
from services.interfaces import (
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
    ):
        self.raw_storage = raw_storage
        self.vector_store = vector_store
        self.metadata_repository = metadata_repository
        self.sentence_transformer = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

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

        context_logger.info("Начало обработки документа")

        ingested_at: datetime = datetime.now()
        file = BytesIO(file_bytes)
        file_extension: str = get_file_extension(file_bytes)
        file_size_bytes: int = len(file_bytes)
        document_type: str = file_extension.lstrip(".").upper()
        raw_storage_path: str = f"{document_id}{file_extension}"
        if workspace_id:
            raw_storage_path = f"{workspace_id}/{raw_storage_path}"

        metadata_kwargs: dict[str, Any] = {
            "document_id": document_id,
            "workspace_id": workspace_id,
            "document_type": document_type,
            "raw_storage_path": raw_storage_path,
            "file_size_bytes": file_size_bytes,
            "ingested_at": ingested_at,
            "status": DocumentStatus.success,
        }
        document_info: ExtractedInfo | None = None
        language: str | None = None
        try:
            context_logger.info("Сохранение необработанного документа", raw_storage_path=raw_storage_path)
            self.raw_storage.save(file_bytes, raw_storage_path)

            context_logger.info("Извлечение текста и метаданных из документа")
            extractor: TextExtractor = ExtractorFactory().get_extractor(file_extension)
            document_info: ExtractedInfo = extractor.extract(file)

            context_logger.info("Определение основного языка документа")
            language: str = detect(document_info.text)

            context_logger.info("Разбиение текста на чанки")
            chunks: list[str] = self.text_splitter.split_text(document_info.text)

            context_logger.info("Создание эмбеддингов для каждого чанка, векторизация")
            vectors: list[Vector] = self._vectorize_chunks(chunks, document_id)

            context_logger.info("Сохранение векторов")
            self.vector_store.upsert(vectors)
        except Exception as e:
            metadata_kwargs["status"] = DocumentStatus.failed
            error_message: str = (
                document_info.error_message if document_info and document_info.error_message else str(e)
            )
            context_logger.error("Ошибка обработки документа", error_message=error_message)
            metadata_kwargs["error_message"] = error_message

        if document_info:
            metadata_kwargs["document_text"] = document_info.text
            metadata_kwargs["error_message"] = document_info.error_message
            metadata_kwargs["document_page_count"] = document_info.document_page_count
            metadata_kwargs["author"] = document_info.author
            metadata_kwargs["creation_date"] = document_info.creation_date
        if language:
            metadata_kwargs["detected_language"] = language

        context_logger.info("Сохранение метаданных документа")
        self.metadata_repository.save(DocumentMeta(**metadata_kwargs))

    def _vectorize_chunks(self, chunks: list[str], document_id: str) -> list[Vector]:
        embeddings = self.sentence_transformer.encode(chunks, show_progress_bar=False)
        return [
            Vector(
                id=f"{document_id}-{i}",
                values=embedding.tolist(),  # noqa
                metadata={
                    "document_id": document_id,
                    "chunk_id": i,
                    "text": chunk,
                },
            )
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
        ]
