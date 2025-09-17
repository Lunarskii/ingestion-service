from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.database.connection import get_async_scoped_session


async def async_scoped_session_dependency() -> AsyncSession:
    """
    Зависимость для FastAPI / любых DI-контекстов, предоставляющая scoped AsyncSession.

    При исключении типа `SQLAlchemyError` откатывает транзакцию и повторно бросает ошибку.
    Всегда гарантирует закрытие сессии.

    :returns: Асинхронная сессия SQLAlchemy ``AsyncSession``.
    :rtype: AsyncSession
    """

    session = get_async_scoped_session()
    try:
        yield session
    except SQLAlchemyError as e:
        await session.rollback()
        raise e
    finally:
        await session.close()
