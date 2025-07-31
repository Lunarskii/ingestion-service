from asyncio import current_task
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
    async_scoped_session,
)

from config import database_settings


def get_async_engine(**kwargs: Any) -> AsyncEngine:
    return create_async_engine(
        url=database_settings.url,
        echo=database_settings.echo,
        echo_pool=database_settings.echo_pool,
        pool_pre_ping=database_settings.pool_pre_ping,
        **kwargs,
    )


def get_async_session_factory(
    engine: AsyncEngine,
    **kwargs: Any,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=engine,
        autoflush=database_settings.auto_flush,
        autocommit=database_settings.auto_commit,
        expire_on_commit=database_settings.expire_on_commit,
        **kwargs,
    )


async_engine: AsyncEngine = get_async_engine()
async_session_factory: async_sessionmaker[AsyncSession] = get_async_session_factory(async_engine)


def get_async_scoped_session():
    return async_scoped_session(
        session_factory=async_session_factory,
        scopefunc=current_task,
    )
