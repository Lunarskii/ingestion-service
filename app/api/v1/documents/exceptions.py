from fastapi import status

from app.exceptions.base import ApplicationError


class UnsupportedFileTypeError(ApplicationError):
    message = "Неподдерживаемый формат файла"
    error_code = "unsupported_media_type"
    status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE


class FileTooLargeError(ApplicationError):
    message = "Размер файла слишком велик"
    error_code = "file_too_large"
    status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE


class DocumentNotFoundError(ApplicationError):
    message = "Файл не найден"
    error_code = "file_not_found"
    status_code = status.HTTP_404_NOT_FOUND
