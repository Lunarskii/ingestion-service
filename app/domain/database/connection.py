from asyncio import current_task
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
    async_scoped_session,
)

from app.config import settings


def get_async_engine(**kwargs: Any) -> AsyncEngine:
    """
    Создаёт и возвращает асинхронный SQLAlchemy ``AsyncEngine``.

    Параметры URL и флаги логирования берутся из ``settings.db``. Любые переданные через ``kwargs``
    параметры имеют приоритет и будут добавлены к конфигурации движка.

    :param kwargs: Дополнительные аргументы для ``create_async_engine``.
    :type kwargs: dict[str, Any]
    :return: Экземпляр ``AsyncEngine``, сконфигурированный через ``config.settings``.
    :rtype: AsyncEngine
    """

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
    """
    Создаёт фабрику асинхронных сессий (``async_sessionmaker``) для переданного движка.

    Конфигурация ``autoflush``, ``autocommit`` и ``expire_on_commit`` берётся из ``settings.db``.
    Любые переданные через ``kwargs`` параметры имеют приоритет и будут добавлены к конфигурации фабрики сессии.

    :param engine: Экземпляр ``AsyncEngine``, к которому будут привязаны сессии.
    :type engine: AsyncEngine
    :param kwargs: Дополнительные аргументы для ``async_sessionmaker``.
    :type kwargs: dict[str, Any]
    :return: Сконфигурированная фабрика сессий ``async_sessionmaker[AsyncSession]``.
    :rtype: async_sessionmaker[AsyncSession]
    """

    return async_sessionmaker(
        bind=engine,
        autoflush=settings.db.auto_flush,
        autocommit=settings.db.auto_commit,
        expire_on_commit=settings.db.expire_on_commit,
        **kwargs,
    )


async_engine: AsyncEngine = get_async_engine()
async_session_factory: async_sessionmaker[AsyncSession] = get_async_session_factory(
    async_engine
)


def get_async_scoped_session() -> async_scoped_session[AsyncSession]:
    """
    Возвращает scoped (контекстно-зависимую) фабрику сессий для асинхронного контекста.

    Использует ``current_task`` в качестве ``scopefunc``, чтобы обеспечить одну сессию
    на асинхронную задачу.

    :returns: Обёртка ``async_scoped_session``, использующая ``current_task`` как функцию области видимости.
    :rtype: async_scoped_session
    """

    return async_scoped_session(
        session_factory=async_session_factory,
        scopefunc=current_task,
    )
