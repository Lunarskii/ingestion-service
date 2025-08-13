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

    :cvar __tablename__: Название таблицы в базе данных.
    :vartype __tablename__: str
    :ivar name: Человеко-читаемое уникальное имя пространства.
    :vartype name: str
    :ivar sessions: Список связанных чат-сессий (relationship).
    :vartype sessions: list[ChatSessionDAO]
    """

    __tablename__ = "workspaces"

    name: Mapped[str] = mapped_column(nullable=False, unique=True)

    sessions: Mapped[list["ChatSessionDAO"]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
