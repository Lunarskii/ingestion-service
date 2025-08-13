from datetime import (
    datetime,
    UTC,
)
from uuid import UUID

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)


def local_time() -> datetime:
    """
    Возвращает текущее локальное время.

    :returns: Текущая локальная дата и время (без явного указания временной зоны).
    :rtype: datetime
    """

    return datetime.now()


def universal_time() -> datetime:
    """
    Возвращает текущую UTC-временную метку без информации о временной зоне.

    :returns: Текущее UTC-время с обнулённой tzinfo (naive datetime).
    :rtype: datetime
    """

    return datetime.now(UTC).replace(tzinfo=None)


class IDMixin:
    """
    Mixin для целочисленного первичного ключа.

    :ivar id: Целочисленный первичный ключ.
    :type id: int
    """

    __abstract__ = True

    id: Mapped[int] = mapped_column(
        primary_key=True,
        nullable=False,
        sort_order=-100,
    )


class UUIDMixin:
    """
    Mixin для UUID-первичного ключа.

    :ivar id: UUID-первичный ключ.
    :type id: UUID
    """

    __abstract__ = True

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        nullable=False,
        sort_order=-100,
    )


class CreatedAtMixin:
    """
    Mixin, добавляющий поле ``created_at`` с временем создания записи.

    :ivar created_at: Время создания записи. По умолчанию используется ``universal_time``.
    :type created_at: datetime
    """

    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(
        default=universal_time,
        sort_order=100,
    )


class UpdatedAtMixin:
    """
    Mixin, добавляющий поле ``updated_at`` с временем последнего обновления записи.

    :ivar updated_at: Время последнего обновления записи. По умолчанию используется ``universal_time``
        и автоматически обновляется при изменении записи.
    :type updated_at: datetime
    """

    __abstract__ = True

    updated_at: Mapped[datetime] = mapped_column(
        default=universal_time,
        onupdate=universal_time,
        sort_order=101,
    )


class TimestampMixin(CreatedAtMixin, UpdatedAtMixin):
    """
    Комбинированный mixin, включающий ``created_at`` и ``updated_at`` поля.

    Наследует поведение ``CreatedAtMixin`` и ``UpdatedAtMixin``.
    """

    __abstract__ = True
