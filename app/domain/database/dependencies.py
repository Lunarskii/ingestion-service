from typing import TYPE_CHECKING
from contextlib import asynccontextmanager

from sqlalchemy.exc import SQLAlchemyError

from app.domain.database.connection import get_async_scoped_session
from app.domain.database.exceptions import DatabaseError
from app.core import logger


if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def async_scoped_session_dependency() -> "AsyncSession":
    """
    Зависимость для FastAPI / любых DI-контекстов, предоставляющая scoped AsyncSession.

    При исключении типа `SQLAlchemyError` откатывает транзакцию и повторно бросает ошибку.
    Всегда гарантирует закрытие сессии.

    :return: Асинхронная сессия SQLAlchemy ``AsyncSession``.
    """

    session = get_async_scoped_session()
    try:
        yield session
        await session.commit()
    except SQLAlchemyError as e:
        logger.error(
            DatabaseError.message,
            error_message=str(e),
        )
        await session.rollback()
    finally:
        await session.close()


@asynccontextmanager
async def async_scoped_session_ctx() -> "AsyncSession":
    """
    Зависимость для использования через ``with``, предоставляющая scoped AsyncSession.

    При исключении типа `SQLAlchemyError` откатывает транзакцию и повторно бросает ошибку.
    Всегда гарантирует закрытие сессии.

    :return: Асинхронная сессия SQLAlchemy ``AsyncSession``.
    """

    session = get_async_scoped_session()
    try:
        yield session
        await session.commit()
    except SQLAlchemyError as e:
        logger.error(
            DatabaseError.message,
            error_message=str(e),
        )
        await session.rollback()
    finally:
        await session.close()
