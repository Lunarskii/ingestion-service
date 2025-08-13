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
    UUIDMixin,
    CreatedAtMixin,
)
from domain.chat.schemas import ChatRole


if TYPE_CHECKING:
    from domain.workspace.models import WorkspaceDAO


class ChatSessionDAO(BaseDAO, UUIDMixin, CreatedAtMixin):
    """
    DAO (ORM) модель, представляющая сессию чата.

    :cvar __tablename__: Название таблицы в базе данных.
    :vartype __tablename__: str
    :ivar workspace_id: Внешний ключ рабочего пространства, которому принадлежит сессия.
    :vartype workspace_id: UUID
    :ivar workspace: Объект рабочего пространства (relationship).
    :vartype workspace: WorkspaceDAO
    :ivar messages: Список связанных сообщений (relationship).
    :vartype messages: list[ChatMessageDAO]
    """

    __tablename__ = "chat_sessions"

    workspace_id: Mapped[UUID] = mapped_column(
        sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    workspace: Mapped["WorkspaceDAO"] = relationship(back_populates="sessions")

    messages: Mapped[list["ChatMessageDAO"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )


class ChatMessageDAO(BaseDAO, UUIDMixin, CreatedAtMixin):
    """
    DAO (ORM) модель, представляющая сообщение внутри чат-сессии.

    :cvar __tablename__: Название таблицы в базе данных.
    :vartype __tablename__: str
    :ivar session_id: Внешний ключ чат-сессии.
    :vartype session_id: UUID
    :ivar session: Объект сессии (relationship).
    :vartype session: ChatSessionDAO
    :ivar role: Роль автора сообщения (enum ``ChatRole``).
    :vartype role: ChatRole
    :ivar content: Текст сообщения.
    :vartype content: str
    """

    __tablename__ = "chat_messages"

    session_id: Mapped[UUID] = mapped_column(
        sa.ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    session: Mapped["ChatSessionDAO"] = relationship(back_populates="messages")

    role: Mapped[ChatRole] = mapped_column(
        sa.Enum(
            ChatRole,
            name="chat_role",
            native_enum=True,
            create_type=True,
        ),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(nullable=False)
