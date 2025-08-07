from typing import TYPE_CHECKING

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from domain.database.models import BaseDAO
from domain.database.mixins import (
    UUIDMixin,
    CreatedAtMixin,
)


if TYPE_CHECKING:
    from domain.chat.models import ChatSessionDAO


class WorkspaceDAO(BaseDAO, UUIDMixin, CreatedAtMixin):
    __tablename__ = "workspaces"

    name: Mapped[str] = mapped_column(nullable=False, unique=True)

    sessions: Mapped[list["ChatSessionDAO"]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
