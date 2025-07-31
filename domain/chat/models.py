from enum import Enum

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


class ChatSessionDAO(BaseDAO, UUIDMixin, CreatedAtMixin):
    __tablename__ = "chat_sessions"

    workspace_id: Mapped[str] = mapped_column(nullable=False)

    messages: Mapped[list["ChatMessageDAO"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )


class ChatRole(str, Enum):
    user = "user"
    assistant = "assistant"


class ChatMessageDAO(BaseDAO, UUIDMixin, CreatedAtMixin):
    __tablename__ = "chat_messages"

    session_id: Mapped[int] = mapped_column(
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
