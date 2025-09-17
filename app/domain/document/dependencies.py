from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.document.repositories import DocumentRepository
from app.domain.database.dependencies import async_scoped_session_dependency
from app.domain.database.uow import (
    UnitOfWork,
    UnitOfWorkFactory,
)


async def document_uow_dependency(
    session: Annotated[AsyncSession, Depends(async_scoped_session_dependency)],
) -> UnitOfWork:
    """
    Возвращает UnitOfWork с предзарегистрированными репозиториями:
        * ``DocumentRepository``
    """

    async with UnitOfWorkFactory.get_uow(
        session,
        DocumentRepository,
    ) as uow:
        yield uow
