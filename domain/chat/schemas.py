from enum import Enum

from schemas.base import (
    BaseSchema,
    BaseDTO,
)
from schemas.mixins import (
    UUIDMixin,
    CreatedAtMixin,
)


class ChatRequest(BaseSchema):
    """
    Схема запроса к RAGService.

    :ivar question: Текст вопроса пользователя.
    :vartype question: str
    :ivar workspace_id: Идентификатор рабочего пространства.
    :vartype workspace_id: str
    :ivar session_id: Идентификатор сессии.
    :vartype session_id: str | None
    :ivar top_k: Количество релевантных источников (фрагментов) для поиска в RAG.
    :vartype top_k: int
    """

    question: str
    workspace_id: str
    session_id: str | None = None
    top_k: int = 3


class Source(BaseSchema):
    """
    Схема источника (фрагмента документа).

    :ivar source_id: Идентификатор источника (документа).
    :vartype source_id: str
    :ivar document_name: Имя документа.
    :vartype document_name: str
    :ivar document_page: Страница в документе, на которой находится фрагмент.
    :vartype document_page: int
    :ivar snippet: Фрагмент.
    :vartype snippet: str
    """

    source_id: str
    document_name: str
    document_page: int
    snippet: str


class ChatResponse(BaseSchema):
    """
    Схема ответа от ChatService.

    :ivar answer: Сгенерированный ответ на вопрос.
    :vartype answer: str
    :ivar sources: Список источников (фрагментов), на которых основан ответ.
    :vartype sources: list[Source]
    :ivar session_id: Идентификатор сессии.
    :vartype session_id: str
    """

    answer: str
    sources: list[Source]
    session_id: str


class ChatSessionDTO(BaseDTO, UUIDMixin, CreatedAtMixin):
    """
    DTO (Data Transfer Object) для представления чат-сессии.

    :ivar id: Идентификатор сессии (UUID в строковом виде).
    :vartype id: str
    :ivar workspace_id: Идентификатор рабочего пространства, к которому относится сессия.
    :vartype workspace_id: str
    :ivar created_at: Время создания сессии.
    :vartype created_at: datetime
    """

    workspace_id: str


class ChatRole(str, Enum):
    """
    Перечисление ролей участников чата.

    :cvar user: Пользователь.
    :vartype user: str
    :cvar assistant: Ассистент/LLM
    :vartype assistant: str
    """

    user = "user"
    assistant = "assistant"


class ChatMessageDTO(BaseDTO, UUIDMixin, CreatedAtMixin):
    """
    DTO (Data Transfer Object) для представления сообщения чата.

    :ivar id: Идентификатор сообщения (UUID в строковом виде).
    :vartype id: str
    :ivar session_id: Идентификатор чат-сессии, к которой относится сообщение.
    :vartype session_id: str
    :ivar role: Роль автора (:class:`ChatRole`).
    :vartype role: ChatRole
    :ivar content: Текст сообщения.
    :vartype content: str
    :ivar created_at: Время создания сообщения.
    :vartype created_at: datetime
    """

    session_id: str
    role: ChatRole
    content: str
