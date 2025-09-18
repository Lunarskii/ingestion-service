from typing import Annotated

from fastapi import (
    UploadFile,
    Depends,
)

from app.api.v1.dependencies import raw_storage_dependency
from app.api.v1.documents.exceptions import (
    UnsupportedFileTypeError,
    FileTooLargeError,
)
from config import (
    Settings,
    settings as _settings,
)
from app.domain.document.service import DocumentService
from app.domain.document.schemas import File
from app.services import RawStorage
from app.utils.file import get_file_extension


async def validate_upload_file(
    file: UploadFile,
    settings: Annotated[Settings, Depends(lambda: _settings)],
) -> File:
    """
    Валидирует загружаемый файл по расширению и размеру.

    :param file: Загружаемый файл из запроса multipart/form-data.
    :type file: UploadFile
    :param settings: Ограничения на типы и максимальный размер файла.
    :type settings: DocumentRestrictionSettings
    :return: Полные байты файла и метаданные файла.
    :rtype: File
    :raises UnsupportedFileTypeError: Если расширение файла не входит в разрешенный список.
    :raises FileTooLargeError: Если размер файла превышает максимально допустимый.
    """

    ext: str = get_file_extension(await file.read(8192))
    if ext not in settings.document_restriction.allowed_extensions:
        raise UnsupportedFileTypeError(
            f"Неподдерживаемый формат {ext!r}. Поддерживаются: {settings.document_restriction.allowed_extensions}"
        )
    await file.seek(0)

    if file.size > (settings.document_restriction.max_upload_mb * 1024 * 1024):
        raise FileTooLargeError(
            f"Размер файла превышает максимально допустимый размер {settings.document_restriction.max_upload_mb}MB"
        )

    return File(
        content=await file.read(),
        name=file.filename,
        size=file.size,
        extension=ext,
        headers=file.headers,
    )


async def document_service_dependency(
    raw_storage: Annotated[RawStorage, Depends(raw_storage_dependency)],
) -> DocumentService:
    """
    Создаёт и возвращает экземпляр сервиса :class:`DocumentService`.
    """

    return DocumentService(raw_storage)
