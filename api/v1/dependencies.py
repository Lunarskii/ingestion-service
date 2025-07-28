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
    Валидирует загружаемый файл по расширению и размеру.

    :param file: Загружаемый файл из запроса multipart/form-data.
    :type file: UploadFile
    :param settings: Ограничения на типы и максимальный размер файла.
    :type settings: DocumentRestrictionSettings
    :return: Полные байты файла, считанные чанками.
    :rtype: bytes
    :raises UnsupportedFileTypeError: Если расширение файла не входит в разрешенный список.
    :raises FileTooLargeError: Если размер файла превышает максимально допустимый.
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
    """
    DI-зависимость для RawStorage.

    :param raw_storage: Экземпляр RawStorage, полученный из get_raw_storage().
    :type raw_storage: RawStorage
    :return: Тот же переданный экземпляр RawStorage.
    :rtype: RawStorage
    """

    return raw_storage


async def vector_store_dependency(
    vector_store: Annotated[VectorStore, Depends(lambda: fh_dependencies.get_vector_store())],
) -> VectorStore:
    """
    DI-зависимость для VectorStore.

    :param vector_store: Экземпляр VectorStore, полученный из get_vector_store().
    :type vector_store: VectorStore
    :return: Тот же переданный экземпляр VectorStore.
    :rtype: VectorStore
    """

    return vector_store


async def metadata_repository_dependency(
    metadata_repository: Annotated[MetadataRepository, Depends(lambda: fh_dependencies.get_metadata_repository())],
) -> MetadataRepository:
    """
    DI-зависимость для MetadataRepository.

    :param metadata_repository: Экземпляр MetadataRepository, полученный из get_metadata_repository().
    :type metadata_repository: MetadataRepository
    :return: Тот же переданный экземпляр MetadataRepository.
    :rtype: MetadataRepository
    """

    return metadata_repository


async def document_processor_dependency(
    document_processor: Annotated[DocumentProcessor, Depends(lambda: fh_dependencies.get_document_processor())],
) -> DocumentProcessor:
    """
    DI-зависимость для DocumentProcessor.

    :param document_processor: Экземпляр DocumentProcessor, полученный из get_document_processor().
    :type document_processor: DocumentProcessor
    :return: Тот же переданный экземпляр DocumentProcessor.
    :rtype: DocumentProcessor
    """

    return document_processor


async def chat_service_dependency(
    chat_service: Annotated[ChatService, Depends(lambda: chat_dependencies.get_chat_service())],
):
    """
    DI-зависимость для ChatService.

    :param chat_service: Экземпляр ChatService, полученный из get_chat_service().
    :type chat_service: ChatService
    :return: Тот же переданный экземпляр ChatService.
    :rtype: ChatService
    """

    return chat_service
