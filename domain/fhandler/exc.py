from exceptions.base import ApplicationError


class ExtractError(ApplicationError):
    message = "Не удалось извлечь текст из документа"
    error_code = "extract_error"
