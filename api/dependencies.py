from typing import Annotated
from pathlib import Path

from fastapi import (
    Depends,
    UploadFile,
)

from api.exc import (
    UnsupportedFileTypeError,
    FileTooLargeError,
)
from services.interfaces import (
    RawStorage,
    VectorStore,
    MetadataRepository,
)
from stubs import (
    FileRawStorage,
    JSONVectorStore,
    SQLiteMetadataRepository,
)
from domain.process import DocumentProcessor
from config import (
    StorageSettings,
    DocumentSettings,
    storage_settings,
    document_settings,
)


async def validate_upload_file(
    file: UploadFile,
    settings: Annotated[DocumentSettings, Depends(lambda: document_settings)]
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


def raw_storage_dependency(settings: Annotated[StorageSettings, Depends(lambda: storage_settings)]) -> RawStorage:
    if settings.raw_storage_path:
        return FileRawStorage()
    raise ValueError("Переменная окружения 'RAW_STORAGE_PATH' не установлена или установлена неверно.")


def vector_store_dependency(settings: Annotated[StorageSettings, Depends(lambda: storage_settings)]) -> VectorStore:
    if settings.index_path:
        return JSONVectorStore()
    raise ValueError("Переменная окружения 'INDEX_PATH' не установлена или установлена неверно.")


def metadata_repository_dependency(settings: Annotated[StorageSettings, Depends(lambda: storage_settings)]) -> MetadataRepository:
    if settings.sqlite_url:
        return SQLiteMetadataRepository()
    raise ValueError("Переменная окружения 'SQLITE_URL' не установлена или установлена неверно.")


def document_processor_dependency(
    raw_storage: Annotated[RawStorage, Depends(raw_storage_dependency)],
    vector_store: Annotated[VectorStore, Depends(vector_store_dependency)],
    metadata_repository: Annotated[MetadataRepository, Depends(metadata_repository_dependency)],
):
    return DocumentProcessor(raw_storage, vector_store, metadata_repository)
