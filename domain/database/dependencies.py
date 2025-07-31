from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from domain.database.connection import get_async_scoped_session


async def scoped_session_dependency() -> AsyncSession:
    session = get_async_scoped_session()
    try:
        yield session
    except SQLAlchemyError as e:
        await session.rollback()
        raise e
    finally:
        await session.close()
