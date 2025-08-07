from exceptions.base import ApplicationError


class ChatError(ApplicationError):
    message = "Не удалось обработать запрос к чату"
    error_code = "chat_error"


class ChatSessionCreationError(ChatError):
    message = "Не удалось создать новую чат-сессию"
    error_code = "chat_session_creation_error"


class ChatMessageCreationError(ChatError):
    message = "Не удалось создать новое сообщение в чат-сессии"
    error_code = "chat_message_creation_error"
