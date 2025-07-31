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
    return datetime.now()


def universal_time() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class IDMixin:
    __abstract__ = True

    id: Mapped[int] = mapped_column(
        primary_key=True,
        nullable=False,
        sort_order=-100,
    )


class UUIDMixin:
    __abstract__ = True

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        nullable=False,
        sort_order=-100,
    )


class CreatedAtMixin:
    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(
        default=universal_time,
        sort_order=100,
    )


class UpdatedAtMixin:
    __abstract__ = True

    updated_at: Mapped[datetime] = mapped_column(
        default=universal_time,
        onupdate=universal_time,
        sort_order=101,
    )


class TimestampMixin(CreatedAtMixin, UpdatedAtMixin):
    __abstract__ = True
