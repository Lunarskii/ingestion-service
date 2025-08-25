from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from domain.chat.repositories import (
    ChatSessionRepository,
    ChatMessageRepository,
    ChatMessageSourceRepository,
)
from domain.database.dependencies import scoped_session_dependency
from domain.database.uow import (
    UnitOfWork,
    UnitOfWorkFactory,
)


async def chat_uow_dependency(
    session: Annotated[AsyncSession, Depends(scoped_session_dependency)],
) -> UnitOfWork:
    async with UnitOfWorkFactory.get_uow(
        session,
        ChatSessionRepository,
        ChatMessageRepository,
        ChatMessageSourceRepository,
    ) as uow:
        yield uow
