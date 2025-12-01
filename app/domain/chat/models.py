from uuid import UUID
from typing import TYPE_CHECKING

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
import sqlalchemy as sa

from app.domain.database.models import BaseDAO
from app.domain.database.mixins import (
    IDMixin,
    UUIDMixin,
    CreatedAtMixin,
)
from app.domain.chat.schemas import ChatRole


if TYPE_CHECKING:
    from app.domain.workspace.models import WorkspaceDAO


class ChatSessionDAO(BaseDAO, UUIDMixin, CreatedAtMixin):
    """
    DAO (ORM) модель, представляющая сессию чата.

    :ivar id: Идентификатор сессии.
    :ivar workspace_id: Внешний ключ рабочего пространства, которому принадлежит сессия.
    :ivar created_at: Время создания сессии.
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
    :ivar session_id: Внешний ключ чат-сессии.
    :ivar role: Роль автора сообщения (enum ``ChatRole``).
    :ivar content: Текст сообщения.
    :ivar created_at: Время создания сообщения.
    """

    __tablename__ = "chat_messages"

    session_id: Mapped[UUID] = mapped_column(
        sa.ForeignKey("chat_sessions.id", ondelete="CASCADE"),
    )
    role: Mapped[ChatRole] = mapped_column(
        sa.Enum(
            ChatRole,
            name="chat_role",
            native_enum=False,
        ),
    )
    content: Mapped[str]

    session: Mapped["ChatSessionDAO"] = relationship(back_populates="messages")
    sources: Mapped[list["RetrievalSourceDAO"]] = relationship(
        back_populates="message",
        cascade="all, delete-orphan",
    )


class RetrievalSourceDAO(BaseDAO, IDMixin, CreatedAtMixin):
    __tablename__ = "retrieval_sources"

    source_id: Mapped[UUID]
    message_id: Mapped[UUID] = mapped_column(
        sa.ForeignKey(
            "chat_messages.id",
            ondelete="CASCADE",
        ),
    )
    title: Mapped[str] = mapped_column(nullable=True)
    source_type: Mapped[str] = mapped_column(nullable=True)

    message: Mapped["ChatMessageDAO"] = relationship(back_populates="sources")
    chunks: Mapped[list["RetrievalChunkDAO"]] = relationship(
        back_populates="retrieval_source",
        cascade="all, delete-orphan",
    )


class RetrievalChunkDAO(BaseDAO, IDMixin, CreatedAtMixin):
    __tablename__ = "retrieval_chunks"

    # TODO сделать unique_id из retrieval_source_id + chunk_id
    retrieval_source_id: Mapped[int] = mapped_column(
        sa.ForeignKey(
            "retrieval_sources.id",
            ondelete="CASCADE",
        ),
    )
    chunk_id: Mapped[str]
    page_start: Mapped[int]
    page_end: Mapped[int]
    retrieval_score: Mapped[float]
    reranked_score: Mapped[float] = mapped_column(nullable=True)
    combined_score: Mapped[float] = mapped_column(nullable=True)

    retrieval_source: Mapped["RetrievalSourceDAO"] = relationship(
        back_populates="chunks",
    )
