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
    """
    DAO (ORM) модель, представляющая рабочее пространство (workspace).

    :ivar id: Идентификатор рабочего пространства.
    :vartype id: UUID
    :ivar name: Человеко-читаемое уникальное имя пространства.
    :vartype name: str
    :ivar created_at: Время создания рабочего пространства.
    :vartype created_at: datetime
    """

    __tablename__ = "workspaces"

    name: Mapped[str] = mapped_column(unique=True)

    sessions: Mapped[list["ChatSessionDAO"]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
