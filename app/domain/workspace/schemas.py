from typing import Annotated

from pydantic import Field

from app.schemas import (
    BaseSchema,
    BaseDTO,
    UUIDMixin,
    CreatedAtMixin,
)


class Workspace(BaseSchema, CreatedAtMixin):
    """
    Схема представления рабочего пространства.

    :ivar id: Идентификатор пространства (UUID в строковом виде).
    :ivar name: Уникальное имя рабочего пространства.
    :ivar created_at: Время создания пространства.
    """

    id: Annotated[
        str,
        Field(serialization_alias="workspace_id"),
    ]
    name: str

    @classmethod
    def from_dto(cls, dto: "WorkspaceDTO") -> "Workspace":
        return Workspace(
            id=dto.id,
            name=dto.name,
            created_at=dto.created_at,
        )


class WorkspaceDTO(BaseDTO, UUIDMixin, CreatedAtMixin):
    """
    DTO (Data Transfer Object) для представления рабочего пространства.

    :ivar id: Идентификатор пространства (UUID в строковом виде).
    :ivar name: Уникальное имя рабочего пространства.
    :ivar created_at: Время создания пространства.
    """

    name: str
