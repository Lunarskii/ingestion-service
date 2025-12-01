from datetime import datetime
from uuid import (
    UUID,
    uuid4,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)
import sqlalchemy as sa

from app.utils.datetime import universal_time


class IDMixin:
    """
    Mixin для целочисленного первичного ключа.

    :ivar id: Целочисленный первичный ключ.
    """

    __abstract__ = True

    id: Mapped[int] = mapped_column(
        sa.Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False,
        sort_order=-100,
    )


class UUIDMixin:
    """
    Mixin для UUID-первичного ключа.

    :ivar id: UUID-первичный ключ.
    """

    __abstract__ = True

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        nullable=False,
        default=lambda: str(uuid4()),
        sort_order=-100,
    )


class CreatedAtMixin:
    """
    Mixin, добавляющий поле ``created_at`` с временем создания записи.

    :ivar created_at: Время создания записи. По умолчанию используется ``universal_time``.
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
