from app.exceptions.base import ApplicationError


class ExtractionError(ApplicationError):
    message = "Не удалось извлечь текст из документа"
    error_code = "text_extraction_error"
