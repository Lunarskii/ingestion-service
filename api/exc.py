from fastapi import status

from exceptions.http import HTTPApplicationError


class UnsupportedFileTypeError(HTTPApplicationError):
    message = "Неподдерживаемый формат файла"
    error_code = "unsupported_media_type"
    status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE


class FileTooLargeError(HTTPApplicationError):
    message = "Размер файла слишком велик"
    error_code = "file_too_large"
    status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
