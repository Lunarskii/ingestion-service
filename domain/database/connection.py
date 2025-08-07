from asyncio import current_task
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
    async_scoped_session,
)

from config import settings


def get_async_engine(**kwargs: Any) -> AsyncEngine:
    return create_async_engine(
        url=settings.db.url,
        echo=settings.db.echo,
        echo_pool=settings.db.echo_pool,
        pool_pre_ping=settings.db.pool_pre_ping,
        **kwargs,
    )


def get_async_session_factory(
    engine: AsyncEngine,
    **kwargs: Any,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=engine,
        autoflush=settings.db.auto_flush,
        autocommit=settings.db.auto_commit,
        expire_on_commit=settings.db.expire_on_commit,
        **kwargs,
    )


async_engine: AsyncEngine = get_async_engine()
async_session_factory: async_sessionmaker[AsyncSession] = get_async_session_factory(async_engine)


def get_async_scoped_session():
    return async_scoped_session(
        session_factory=async_session_factory,
        scopefunc=current_task,
    )
