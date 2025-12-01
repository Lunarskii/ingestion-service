from app.exceptions.base import ApplicationError
from app import status


class DocumentNotFoundError(ApplicationError):
    message = "Файл не найден"
    error_code = "file_not_found"
    status_code = status.HTTP_404_NOT_FOUND


class ValidationError(ApplicationError):
    message = "Ошибка при валидации документа"
    error_code = "validation_error"
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class UnsupportedMediaTypeError(ValidationError):
    message = "Неподдерживаемый формат файла"
    error_code = "unsupported_media_type"
    status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE


class FileTooLargeError(ValidationError):
    message = "Размер файла слишком велик"
    error_code = "file_too_large"
    status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE


class DuplicateDocumentError(ValidationError):
    message = "Документ является дубликатом"
    error_code = "duplicate_document_error"


class EmptyTextError(ValidationError):
    message = "Документ не содержит текста"
    error_code = "empty_text"
