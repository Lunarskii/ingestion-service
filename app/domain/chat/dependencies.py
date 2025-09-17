from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.chat.repositories import (
    ChatSessionRepository,
    ChatMessageRepository,
    ChatMessageSourceRepository,
)
from app.domain.database.dependencies import async_scoped_session_dependency
from app.domain.database.uow import (
    UnitOfWork,
    UnitOfWorkFactory,
)


async def chat_uow_dependency(
    session: Annotated[AsyncSession, Depends(async_scoped_session_dependency)],
) -> UnitOfWork:
    """
    Возвращает UnitOfWork с предзарегистрированными репозиториями:
        * ``ChatSessionRepository``
        * ``ChatMessageRepository``
        * ``ChatMessageSourceRepository``
    """

    async with UnitOfWorkFactory.get_uow(
        session,
        ChatSessionRepository,
        ChatMessageRepository,
        ChatMessageSourceRepository,
    ) as uow:
        yield uow
