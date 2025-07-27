from typing import Annotated
from pathlib import Path

from fastapi import (
    Depends,
    UploadFile,
)

from api.v1.exc import (
    UnsupportedFileTypeError,
    FileTooLargeError,
)
from domain.fhandler.service import DocumentProcessor
import domain.fhandler.dependencies as fh_dependencies
from domain.chat.service import ChatService
import domain.chat.dependencies as chat_dependencies
from services import (
    RawStorage,
    VectorStore,
    MetadataRepository,
)
from config import (
    DocumentRestrictionSettings,
    document_restriction_settings,
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
            f"Неподдерживаемый формат {ext!r}. Поддерживаются: {settings.allowed_extensions}"
        )

    max_upload_bytes: int = settings.max_upload_mb * 1024 * 1024
    size: int = 0
    chunks: list[bytes] = []
    chunk_size: int = 1024 * 1024

    while chunk := await file.read(chunk_size):
        size += len(chunk)
        if size > max_upload_bytes:
            raise FileTooLargeError(f"Размер файла превышает максимально допустимый размер {settings.max_upload_mb}MB")
        chunks.append(chunk)

    return b"".join(chunks)


async def raw_storage_dependency(
    raw_storage: Annotated[RawStorage, Depends(lambda: fh_dependencies.get_raw_storage())],
) -> RawStorage:
    return raw_storage


async def vector_store_dependency(
    vector_store: Annotated[VectorStore, Depends(lambda: fh_dependencies.get_vector_store())],
) -> VectorStore:
    return vector_store


async def metadata_repository_dependency(
    metadata_repository: Annotated[MetadataRepository, Depends(lambda: fh_dependencies.get_metadata_repository())],
) -> MetadataRepository:
    return metadata_repository


async def document_processor_dependency(
    document_processor: Annotated[DocumentProcessor, Depends(lambda: fh_dependencies.get_document_processor())],
) -> DocumentProcessor:
    return document_processor


async def chat_service_dependency(
    chat_service: Annotated[ChatService, Depends(lambda: chat_dependencies.get_chat_service())],
):
    return chat_service
