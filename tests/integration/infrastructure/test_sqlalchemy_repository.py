import asyncio

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)
from sqlalchemy.exc import SQLAlchemyError

from app.adapters.sqlalchemy_repository import AlchemyRepository
from app.domain.database.models import BaseDAO
from app.domain.database.mixins import IDMixin
from app.domain.database.exceptions import (
    DatabaseError,
    EntityNotFoundError,
    ValidationError,
)
from app.schemas import BaseDTO


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def async_engine() -> AsyncEngine:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(BaseDAO.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(async_engine: AsyncEngine) -> AsyncSession:
    async_session_maker = async_sessionmaker(
        bind=async_engine,
        expire_on_commit=False,
    )
    async with async_session_maker() as session:
        yield session


class UserDAO(BaseDAO, IDMixin):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(nullable=False)


class UserDTO(BaseDTO):
    id: int
    name: str


class UserRepository(AlchemyRepository[UserDAO, UserDTO]):
    pass


class DummyDAO:
    __tablename__ = "dummy_table"

    def __init__(self, **kwargs):
        raise SQLAlchemyError("database_error")


class DummyDTO:
    def __init__(self): ...


class DummyRepository(AlchemyRepository[DummyDAO, DummyDTO]):
    pass


class TestAlchemyRepository:
    @pytest.mark.asyncio
    async def test_create_and_get(
        self,
        async_session: AsyncSession,
    ):
        repo = UserRepository(async_session)
        user: UserDTO = await repo.create(name="Alice")

        assert isinstance(user, UserDTO)
        assert user.name == "Alice"
        assert await repo.get(user.id) == user

    @pytest.mark.asyncio
    async def test_get_n_and_count(
        self,
        async_session: AsyncSession,
    ):
        repo = UserRepository(async_session)
        await repo.create(name="Bob")
        await repo.create(name="Charlie")

        users: list[UserDTO] = await repo.get_n()
        assert all(isinstance(i, UserDTO) for i in users)
        assert len(users) == 2
        assert await repo.count() == 2

    @pytest.mark.asyncio
    async def test_update(
        self,
        async_session: AsyncSession,
    ):
        repo = UserRepository(async_session)
        user: UserDTO = await repo.create(name="David")

        updated_user = await repo.update(user.id, name="Dave")
        assert updated_user.id == user.id
        assert updated_user.name == "Dave"

        get_updated_user = await repo.get(user.id)
        assert get_updated_user.id == user.id
        assert get_updated_user.name == "Dave"

    @pytest.mark.asyncio
    async def test_exists_and_delete(
        self,
        async_session: AsyncSession,
    ):
        repo = UserRepository(async_session)
        user: UserDTO = await repo.create(name="Eve")

        assert await repo.exists(user.id)
        await repo.delete(user.id)
        await repo.session.commit()
        assert not await repo.exists(user.id)

    @pytest.mark.asyncio
    async def test_create_raises_for_database_error(
        self,
        async_session: AsyncSession,
    ):
        repo = DummyRepository(async_session)

        with pytest.raises(DatabaseError):
            await repo.create(field="value")

    @pytest.mark.asyncio
    async def test_get_not_found(
        self,
        async_session: AsyncSession,
    ):
        repo = UserRepository(async_session)

        with pytest.raises(EntityNotFoundError):
            await repo.get(999)

    @pytest.mark.asyncio
    async def test_get_n_raises_for_database_error(
        self,
        async_session: AsyncSession,
    ):
        repo = DummyRepository(async_session)

        with pytest.raises(DatabaseError):
            await repo.get_n()

    @pytest.mark.asyncio
    async def test_update_not_found(
        self,
        async_session: AsyncSession,
    ):
        repo = UserRepository(async_session)

        with pytest.raises(EntityNotFoundError):
            await repo.update(999, field="value")

    @pytest.mark.asyncio
    async def test_update_attribute_error(
        self,
        async_session: AsyncSession,
    ):
        repo = UserRepository(async_session)
        user: UserDTO = await repo.create(name="Alice")

        with pytest.raises(ValidationError):
            await repo.update(user.id, field="value")

    @pytest.mark.asyncio
    async def test_update_raises_for_database_error(
        self,
        async_session: AsyncSession,
    ):
        repo = DummyRepository(async_session)

        with pytest.raises(DatabaseError):
            await repo.update(999, field="value")

    @pytest.mark.asyncio
    async def test_delete_not_found(
        self,
        async_session: AsyncSession,
    ):
        repo = UserRepository(async_session)

        with pytest.raises(EntityNotFoundError):
            await repo.delete(999)

    @pytest.mark.asyncio
    async def test_delete_raises_for_database_error(
        self,
        async_session: AsyncSession,
    ):
        repo = DummyRepository(async_session)

        with pytest.raises(DatabaseError):
            await repo.delete(999)

    @pytest.mark.asyncio
    async def test_exists_raises_for_database_error(
        self,
        async_session: AsyncSession,
    ):
        repo = DummyRepository(async_session)

        with pytest.raises(DatabaseError):
            await repo.exists(999)
