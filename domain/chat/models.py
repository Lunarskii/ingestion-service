from uuid import UUID
from typing import TYPE_CHECKING

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
import sqlalchemy as sa

from domain.database.models import BaseDAO
from domain.database.mixins import (
    IDMixin,
    UUIDMixin,
    CreatedAtMixin,
)
from domain.chat.schemas import ChatRole


if TYPE_CHECKING:
    from domain.workspace.models import WorkspaceDAO


class ChatSessionDAO(BaseDAO, UUIDMixin, CreatedAtMixin):
    """
    DAO (ORM) модель, представляющая сессию чата.

    :ivar id: Идентификатор сессии.
    :vartype id: UUID
    :ivar workspace_id: Внешний ключ рабочего пространства, которому принадлежит сессия.
    :vartype workspace_id: UUID
    :ivar created_at: Время создания сессии.
    :vartype created_at: datetime
    """

    __tablename__ = "chat_sessions"

    workspace_id: Mapped[UUID] = mapped_column(
        sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
    )
    workspace: Mapped["WorkspaceDAO"] = relationship(back_populates="sessions")

    messages: Mapped[list["ChatMessageDAO"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )


class ChatMessageDAO(BaseDAO, UUIDMixin, CreatedAtMixin):
    """
    DAO (ORM) модель, представляющая сообщение внутри чат-сессии.

    :ivar id: Идентификатор сообщения.
    :vartype id: UUID
    :ivar session_id: Внешний ключ чат-сессии.
    :vartype session_id: UUID
    :ivar role: Роль автора сообщения (enum ``ChatRole``).
    :vartype role: ChatRole
    :ivar content: Текст сообщения.
    :vartype content: str
    :ivar created_at: Время создания сообщения.
    :vartype created_at: datetime
    """

    __tablename__ = "chat_messages"

    session_id: Mapped[UUID] = mapped_column(
        sa.ForeignKey("chat_sessions.id", ondelete="CASCADE"),
    )
    session: Mapped["ChatSessionDAO"] = relationship(back_populates="messages")

    role: Mapped[ChatRole] = mapped_column(
        sa.Enum(
            ChatRole,
            name="chat_role",
            native_enum=False,
        ),
    )
    content: Mapped[str]

    sources: Mapped[list["ChatMessageSourceDAO"]] = relationship(
        back_populates="message",
        cascade="all, delete-orphan",
    )


class ChatMessageSourceDAO(BaseDAO, IDMixin):
    """
    DAO (ORM) модель, представляющая источник сообщения.

    Используется для сообщений от LLM.

    :ivar id: Идентификатор записи источника в базе данных.
    :vartype id: int
    :ivar source_id: Идентификатор источника (фрагмента документа).
    :vartype source_id: UUID
    :ivar message_id: Идентификатор сообщения, которому принадлежит источник.
    :vartype message_id: UUID
    :ivar document_name: Имя документа.
    :vartype document_name: str
    :ivar page_start: Страница, на которой находится начало источника (фрагмента документа).
    :vartype page_start: int
    :ivar page_end: Страница, на которой находится конец источника (фрагмента документа).
    :vartype page_end: int
    :ivar snippet: Текстовый фрагмент документа.
    :vartype snippet: str
    """

    __tablename__ = "chat_message_sources"

    source_id: Mapped[UUID]

    message_id: Mapped[UUID] = mapped_column(
        sa.ForeignKey("chat_messages.id", ondelete="CASCADE"),
    )
    message: Mapped["ChatMessageDAO"] = relationship(back_populates="sources")

    document_name: Mapped[str]
    page_start: Mapped[int]
    page_end: Mapped[int]
    snippet: Mapped[str]
