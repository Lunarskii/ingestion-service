from datetime import datetime
from enum import Enum
from typing import Annotated
import uuid

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
)


class ChatRequest(BaseModel):
    """
    Схема запроса к RAGService.

    :param question: Текст вопроса пользователя.
    :type question: str
    :param workspace_id: Идентификатор рабочего пространства.
    :type workspace_id: str
    :param session_id: Идентификатор сессии.
    :type session_id: str | None
    :param top_k: Количество релевантных источников (фрагментов) для поиска в RAG.
    :type top_k: int
    """

    question: str
    workspace_id: str
    session_id: str | None = None
    top_k: int = 3


class Source(BaseModel):
    """
    Схема источника (фрагмента документа).

    :param source_id: Идентификатор источника (документа).
    :type source_id: str
    :param document_name: Имя документа.
    :type document_name: str
    :param document_page: Страница в документе, на которой находится фрагмент.
    :type document_page: int
    :param snippet: Фрагмент.
    :type snippet: str
    """

    source_id: str
    document_name: str
    document_page: int
    snippet: str


class ChatResponse(BaseModel):
    """
    Схема ответа от ChatService.

    :param answer: Сгенерированный ответ на вопрос.
    :type answer: str
    :param sources: Список источников (фрагментов), на которых основан ответ.
    :type sources: list[Source]
    :param session_id: Идентификатор сессии.
    :type session_id: str
    """

    answer: str
    sources: list[Source]
    session_id: str


class ChatSessionDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Annotated[str, Field(default_factory=lambda: str(uuid.uuid4()))]  # type: ignore
    workspace_id: str
    created_at: Annotated[datetime, Field(default_factory=datetime.now)]

    @field_serializer("created_at")
    def datetime_to_str(self, value: datetime) -> str | None:
        """
        Сериализация datetime в строку формата YYYY-MM-DD HH:MM:SS.
        """

        if value is None:
            return value
        return datetime.strftime(value, "%Y-%m-%d %H:%M:%S")


class ChatRole(str, Enum):
    user = "user"
    assistant = "assistant"


class ChatMessageDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Annotated[str, Field(default_factory=lambda: str(uuid.uuid4()))]  # type: ignore
    session_id: str
    role: ChatRole
    content: str
    created_at: Annotated[datetime, Field(default_factory=datetime.now)]

    @field_serializer("created_at")
    def datetime_to_str(self, value: datetime) -> str | None:
        """
        Сериализация datetime в строку формата YYYY-MM-DD HH:MM:SS.
        """

        if value is None:
            return value
        return datetime.strftime(value, "%Y-%m-%d %H:%M:%S")
