from typing import Annotated
from pathlib import Path

from fastapi import (
    Depends,
    UploadFile,
)
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter

from api.v1.exc import (
    UnsupportedFileTypeError,
    FileTooLargeError,
)
from domain.fhandler.service import DocumentProcessor
from domain.chat.service import ChatService
from services import (
    RawStorage,
    VectorStore,
    MetadataRepository,
)
from stubs import (
    FileRawStorage,
    JSONVectorStore,
    SQLiteMetadataRepository,
)
from config import (
    StorageSettings,
    DocumentRestrictionSettings,
    EmbeddingSettings,
    TextSplitterSettings,
    storage_settings,
    document_restriction_settings,
    embedding_settings,
    text_splitter_settings,
)


async def validate_upload_file(
    file: UploadFile,
    settings: Annotated[DocumentRestrictionSettings, Depends(lambda: document_restriction_settings)],
) -> bytes:
    """
    Валидация расширения и размера загружаемого файла.
    Читает файл чанками. Если размер файла превышает допустимый - выбрасывает исключение.
    """

    ext: str = Path(file.filename or "").suffix.lower()
    if ext not in settings.allowed_extensions:
        raise UnsupportedFileTypeError(
            message=f"Неподдерживаемый формат {ext!r}. Поддерживаются: {settings.allowed_extensions}"
        )

    max_upload_bytes: int = settings.max_upload_mb * 1024 * 1024
    size: int = 0
    chunks: list[bytes] = []
    chunk_size: int = 1024 * 1024

    while chunk := await file.read(chunk_size):
        size += len(chunk)
        if size > max_upload_bytes:
            raise FileTooLargeError(
                message=f"Размер файла превышает максимально допустимый размер {settings.max_upload_mb}MB"
            )
        chunks.append(chunk)

    return b"".join(chunks)


def raw_storage_dependency(
    settings: Annotated[StorageSettings, Depends(lambda: storage_settings)],
) -> RawStorage:
    if settings.raw_storage_path:
        return FileRawStorage()
    raise ValueError("Переменная окружения 'RAW_STORAGE_PATH' не установлена или установлена неверно.")


def vector_store_dependency(
    settings: Annotated[StorageSettings, Depends(lambda: storage_settings)],
) -> VectorStore:
    if settings.index_path:
        return JSONVectorStore()
    raise ValueError("Переменная окружения 'INDEX_PATH' не установлена или установлена неверно.")


def metadata_repository_dependency(
    settings: Annotated[StorageSettings, Depends(lambda: storage_settings)],
) -> MetadataRepository:
    if settings.sqlite_url:
        return SQLiteMetadataRepository()
    raise ValueError("Переменная окружения 'SQLITE_URL' не установлена или установлена неверно.")


def embedding_model_dependency(
    settings: Annotated[EmbeddingSettings, Depends(lambda: embedding_settings)],
) -> SentenceTransformer:
    if settings.model_name:
        return SentenceTransformer(
            model_name_or_path=settings.model_name,
            device=settings.device,
            cache_folder=settings.cache_folder,
            token=settings.token,
        )
    raise ValueError("Переменная окружения 'EMBEDDING_MODEL_NAME' не установлена или установлена неверно.")


def text_splitter_dependency(
    settings: Annotated[TextSplitterSettings, Depends(lambda: text_splitter_settings)],
) -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )


def document_processor_dependency(
    raw_storage: Annotated[RawStorage, Depends(raw_storage_dependency)],
    vector_store: Annotated[VectorStore, Depends(vector_store_dependency)],
    metadata_repository: Annotated[MetadataRepository, Depends(metadata_repository_dependency)],
    embedding_model: Annotated[SentenceTransformer, Depends(embedding_model_dependency)],
    text_splitter: Annotated[RecursiveCharacterTextSplitter, Depends(text_splitter_dependency)],
):
    return DocumentProcessor(raw_storage, vector_store, metadata_repository, embedding_model, text_splitter)


def chat_service_dependency(
    vector_store: Annotated[VectorStore, Depends(vector_store_dependency)],
    embedding_model: Annotated[SentenceTransformer, Depends(embedding_model_dependency)],
):
    return ChatService(vector_store, embedding_model)
