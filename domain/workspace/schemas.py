from datetime import datetime
from typing import Annotated
import uuid

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
)


class WorkspaceDTO(BaseModel):
    """
    DTO (Data Transfer Object) для представления рабочего пространства.

    :ivar id: Идентификатор пространства (UUID в строковом виде).
    :vartype id: str
    :ivar name: Уникальное имя рабочего пространства.
    :vartype name: str
    :ivar created_at: Время создания пространства.
    :vartype created_at: datetime
    """

    model_config = ConfigDict(from_attributes=True)

    id: Annotated[str, Field(default_factory=lambda: str(uuid.uuid4()))]  # type: ignore
    name: str
    created_at: Annotated[datetime, Field(default_factory=datetime.now)]

    @field_serializer("created_at")
    def datetime_to_str(self, value: datetime) -> str | None:
        """
        Сериализация datetime в строку формата YYYY-MM-DD HH:MM:SS.
        """

        if value is None:
            return value
        return datetime.strftime(value, "%Y-%m-%d %H:%M:%S")
