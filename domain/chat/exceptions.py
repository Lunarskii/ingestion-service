from exceptions.base import ApplicationError


class RAGError(ApplicationError):
    message = "Не удалось обработать запрос к чату"
    error_code = "rag_error"
