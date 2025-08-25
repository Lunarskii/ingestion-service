from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from domain.document.repositories import DocumentRepository
from domain.database.dependencies import scoped_session_dependency
from domain.database.uow import (
    UnitOfWork,
    UnitOfWorkFactory,
)


async def document_uow_dependency(
    session: Annotated[AsyncSession, Depends(scoped_session_dependency)],
) -> UnitOfWork:
    async with UnitOfWorkFactory.get_uow(
        session,
        DocumentRepository,
    ) as uow:
        yield uow
