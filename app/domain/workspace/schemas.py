from app.schemas import (
    BaseDTO,
    UUIDMixin,
    CreatedAtMixin,
)


class WorkspaceDTO(BaseDTO, UUIDMixin, CreatedAtMixin):
    """
    DTO (Data Transfer Object) для представления рабочего пространства.

    :ivar id: Идентификатор пространства (UUID в строковом виде).
    :vartype id: str
    :ivar name: Уникальное имя рабочего пространства.
    :vartype name: str
    :ivar created_at: Время создания пространства.
    :vartype created_at: datetime
    """

    name: str
