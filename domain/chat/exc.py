from exceptions.base import ApplicationError


class RAGError(ApplicationError):
    message = "Не удалось обработать запрос к чату"
    error_code = "chat_error"


class ChatSessionError(ApplicationError):
    message = "Ошибка при работе с чат-сессиями"
    error_code = "chat_session_error"


class ChatSessionCreationError(ChatSessionError):
    message = "Не удалось создать новую чат-сессию"
    error_code = "chat_session_creation_error"


class ChatSessionRetrivalError(ChatSessionError):
    message = "Не удалось получить чат-сессию"
    error_code = "chat_session_retrieval_error"


class ChatMessageError(ApplicationError):
    message = "Ошибка при работе с сообщениями в чат-сессии"
    error_code = "chat_message_error"


class ChatMessageCreationError(ChatMessageError):
    message = "Не удалось создать новое сообщение в чат-сессии"
    error_code = "chat_message_creation_error"


class ChatMessageRetrievalError(ChatMessageError):
    message = "Не удалось получить сообщение из чат-сессии"
    error_code = "chat_message_retrieval_error"
