import uuid
from enum import Enum
from typing import (
    Annotated,
    Optional,
)

from pydantic import Field

from app.schemas import (
    BaseSchema,
    BaseDTO,
)
from app.schemas import (
    IDMixin,
    UUIDMixin,
    CreatedAtMixin,
)


class ChatRole(str, Enum):
    """
    Перечисление ролей участников чата.

    :cvar user: Пользователь.
    :cvar assistant: Ассистент/LLM
    """

    user = "user"
    assistant = "assistant"


class RetrievalChunk(BaseSchema):
    chunk_id: str = Field(..., description="Идентификатор чанка в хранилище обработанных документов")
    page_start: int = Field(..., description="Страница, на которой находится начало фрагмента документа")
    page_end: int = Field(..., description="Страница, на которой находится конец фрагмента документа")
    retrieval_score: float = Field(..., description="Релевантность")
    reranked_score: Optional[float] = Field(default=None, description="Релевантность")
    combined_score: Optional[float] = Field(default=None, description="Релевантность")
    text: Optional[str] = Field(default=None, description="Текст") # TODO временное решение, убрать после


class RetrievalChunkDTO(BaseDTO, IDMixin, CreatedAtMixin):
    retrieval_source_id: int = Field(..., description="...")
    chunk_id: str = Field(..., description="Идентификатор чанка в хранилище обработанных документов")
    page_start: int = Field(..., description="Страница, на которой находится начало фрагмента документа")
    page_end: int = Field(..., description="Страница, на которой находится конец фрагмента документа")
    retrieval_score: float = Field(..., description="Релевантность")
    reranked_score: Optional[float] = Field(default=None, description="Релевантность")
    combined_score: Optional[float] = Field(default=None, description="Релевантность")


class RetrievalSource(BaseSchema, CreatedAtMixin):
    """
    Схема полученного источника для ответа LLM.

    Заметки:
        - В данный момент источником (source_id) может выступать только документ (document_id),
          поэтому source_id = document_id.
    """

    source_id: str = Field(..., description="Идентификатор источника")
    title: Optional[str] = Field(default=None, description="Заголовок документа/страницы, если есть")
    source_type: Optional[str] = Field(default=None, description="Тип источника (краулер, веб и др.)")
    chunks: list[RetrievalChunk] = Field(..., description="Полученные чанки документа")


class RetrievalSourceDTO(BaseDTO, IDMixin, CreatedAtMixin):
    source_id: str = Field(..., description="Идентификатор источника")
    message_id: str = Field(..., description="Идентификатор сообщения")
    title: Optional[str] = Field(default=None, description="Заголовок документа/страницы, если есть")
    source_type: Optional[str] = Field(default=None, description="Тип источника (краулер, веб и др.)")


class ChatMessage(BaseSchema, CreatedAtMixin):
    """
    Схема представления сообщения чат-сессии.

    :ivar id: Идентификатор сообщения (UUID в строковом виде).
    :ivar session_id: Идентификатор чат-сессии, к которой относится сообщение.
    :ivar role: Роль автора (:class:`ChatRole`).
    :ivar content: Текст сообщения.
    :ivar sources: Список источников, связанных с сообщением (если имеются).
    :ivar created_at: Время создания сообщения.
    """

    id: Annotated[
        str,
        Field(
            serialization_alias="message_id",
            default_factory=lambda: str(uuid.uuid4()),  # type: ignore
        ),
    ]
    session_id: str
    role: ChatRole
    content: str
    sources: list[RetrievalSource] = []


class ChatSession(BaseSchema, CreatedAtMixin):
    """
    Схема представления чат-сессии.

    :ivar id: Идентификатор сессии (UUID в строковом виде).
    :ivar workspace_id: Идентификатор рабочего пространства, к которому относится сессия.
    :ivar created_at: Время создания сессии.
    """

    id: Annotated[
        str,
        Field(
            serialization_alias="session_id",
            default_factory=lambda: str(uuid.uuid4()),  # type: ignore
        ),
    ]
    workspace_id: str


class RAGRequest(BaseSchema):
    """
    Схема запроса к RAGService.

    :ivar question: Текст вопроса пользователя.
    :ivar workspace_id: Идентификатор рабочего пространства.
    :ivar session_id: Идентификатор сессии.
    :ivar top_k: Количество релевантных источников (фрагментов) для поиска в RAG.
    """

    question: str
    workspace_id: str
    session_id: str | None = None
    top_k: int = 3


class RAGResponse(BaseSchema):
    """
    Схема ответа от RAGService.

    :ivar answer: Сгенерированный ответ на вопрос.
    :ivar sources: Список источников (фрагментов), на которых основан ответ.
    :ivar session_id: Идентификатор сессии.
    """

    answer: str
    sources: list[RetrievalSource]
    session_id: str


class ChatSessionDTO(BaseDTO, UUIDMixin, CreatedAtMixin):
    """
    DTO (Data Transfer Object) для представления чат-сессии.

    :ivar id: Идентификатор сессии (UUID в строковом виде).
    :ivar workspace_id: Идентификатор рабочего пространства, к которому относится сессия.
    :ivar created_at: Время создания сессии.
    """

    workspace_id: str


class ChatMessageDTO(BaseDTO, UUIDMixin, CreatedAtMixin):
    """
    DTO (Data Transfer Object) для представления сообщения чата.

    :ivar id: Идентификатор сообщения (UUID в строковом виде).
    :ivar session_id: Идентификатор чат-сессии, к которой относится сообщение.
    :ivar role: Роль автора (:class:`ChatRole`).
    :ivar content: Текст сообщения.
    :ivar created_at: Время создания сообщения.
    """

    session_id: str
    role: ChatRole
    content: str
