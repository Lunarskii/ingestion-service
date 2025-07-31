from enum import Enum
from typing import (
    Any,
    Self,
)
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
import sqlalchemy as sa


class BaseModel(AsyncAttrs, DeclarativeBase):
    __abstract__ = True
    type_annotation_map = {
        int: sa.BigInteger,
        Enum: sa.Enum(Enum, native_enum=False),
        UUID: sa.Uuid(as_uuid=False),
    }
    metadata = sa.MetaData(
        naming_convention={
            "ix": "%(column_0_label)s_idx",
            "uq": "%(table_name)s_%(column_0_name)s_key",
            "ck": "%(table_name)s_%(constraint_name)s_check",
            "fk": "%(table_name)s_%(column_0_name)s_%(referred_table_name)s_fkey",
            "pk": "%(table_name)s_pkey",
        }
    )

    def update(self, **data: Any) -> Self:
        for key, value in data.items():
            setattr(self, key, value)
        return self


class BaseDAO(BaseModel):
    __abstract__ = True
