from typing import Annotated
from datetime import (
    datetime,
    UTC,
)
import uuid

from pydantic import (
    Field,
    field_serializer,
)


def local_time() -> datetime:
    """
    Возвращает текущее локальное время.

    :return: Текущая локальная дата и время (без явного указания временной зоны).
    :rtype: datetime
    """

    return datetime.now()


def universal_time() -> datetime:
    """
    Возвращает текущую UTC-временную метку без информации о временной зоне.

    :return: Текущее UTC-время с обнулённой tzinfo (naive datetime).
    :rtype: datetime
    """

    return datetime.now(UTC).replace(tzinfo=None)


def datetime_to_str(value: datetime) -> str | None:
    """
    Сериализация datetime в строку формата YYYY-MM-DD HH:MM:SS.
    """

    if value is None:
        return value
    return datetime.strftime(value, "%Y-%m-%d %H:%M:%S")


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
        return datetime_to_str(value)


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
        return datetime_to_str(value)


class TimestampMixin(CreatedAtMixin, UpdatedAtMixin):
    """
    Комбинированный mixin, включающий ``created_at`` и ``updated_at`` поля.

    Наследует поведение ``CreatedAtMixin`` и ``UpdatedAtMixin``.
    """
    ...
