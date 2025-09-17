from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.workspace.repositories import WorkspaceRepository
from app.domain.database.dependencies import async_scoped_session_dependency
from app.domain.database.uow import (
    UnitOfWork,
    UnitOfWorkFactory,
)


async def workspace_uow_dependency(
    session: Annotated[AsyncSession, Depends(async_scoped_session_dependency)],
) -> UnitOfWork:
    """
    Возвращает UnitOfWork с предзарегистрированными репозиториями:
        * ``WorkspaceRepository``
    """

    async with UnitOfWorkFactory.get_uow(
        session,
        WorkspaceRepository,
    ) as uow:
        yield uow
