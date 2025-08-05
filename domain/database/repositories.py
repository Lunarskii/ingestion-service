from abc import ABC
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from domain.database.models import BaseDAO


class BaseAlchemyRepository[M: BaseDAO, S: BaseModel](ABC):
    session: AsyncSession
    model_type: type[M]
    schema_type: type[S]

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **data: Any) -> S:
        instance = self.model_type(**data)
        self.session.add(instance)
        await self.session.commit()
        return self.schema_type.model_validate(instance)

    async def get(self, id: int) -> S | None:
        instance = await self.session.get(self.model_type, id)
        if instance is None:
            return None
        return self.schema_type.model_validate(instance)

    async def get_n(self, n: int | None = None, **data: Any):
        stmt = select(self.model_type).filter_by(**data).limit(n)
        instances = await self.session.scalars(stmt)
        return list(map(self.schema_type.model_validate, instances))

    async def update(self, id: int, **data: Any) -> S | None:
        instance = await self.session.get(self.model_type, id)
        if instance is None:
            return None
        instance.update(**data)
        await self.session.commit()
        return self.schema_type.model_validate(instance)

    async def delete(self, id: int) -> S | None:
        instance = await self.session.get(self.model_type, id)
        if instance is None:
            return None
        await self.session.delete(instance)
        await self.session.commit()
        return self.schema_type.model_validate(instance)
