from typing import Annotated
from datetime import datetime
import uuid

from pydantic import (
    Field,
    field_serializer,
)

from app.utils.datetime import (
    universal_time,
    serialize_datetime_to_str,
)


class IDMixin:
    id: int | None = None


class UUIDMixin:
    """
    Mixin, добавляющий уникальный идентификатор (UUID).

    :ivar id: Уникальный идентификатор в формате UUID4, автоматически генерируется при создании экземпляра.
    :vartype id: str
    """

    id: Annotated[str, Field(default_factory=lambda: str(uuid.uuid4()))]  # type: ignore


class CreatedAtMixin:
    """
    Mixin, добавляющий поле даты и времени создания.

    :ivar created_at: Метка времени создания объекта, по умолчанию - текущее
                      UTC-время (наивный datetime без tzinfo).
    :vartype created_at: datetime
    """

    created_at: Annotated[datetime, Field(default_factory=universal_time)]

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str | None:
        return serialize_datetime_to_str(value)


class UpdatedAtMixin:
    """
    Mixin, добавляющий поле даты и времени последнего обновления.

    :ivar updated_at: Метка времени последнего изменения объекта, по умолчанию - текущее
                      UTC-время (наивный datetime без tzinfo).
    :typevar updated_at: datetime
    """

    updated_at: Annotated[datetime, Field(default_factory=universal_time)]

    @field_serializer("updated_at")
    def serialize_updated_at(self, value: datetime) -> str | None:
        return serialize_datetime_to_str(value)


class TimestampMixin(CreatedAtMixin, UpdatedAtMixin):
    """
    Комбинированный mixin, включающий ``created_at`` и ``updated_at`` поля.

    Наследует поведение ``CreatedAtMixin`` и ``UpdatedAtMixin``.
    """

    ...
