from abc import (
    ABC,
    abstractmethod,
)
from typing import (
    TypeVar,
    Self,
)

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from domain.database.repositories import AlchemyRepository
from domain.database.exceptions import DatabaseError
from config import logger


T = TypeVar("T", bound=AlchemyRepository)


class IUnitOfWork(ABC):
    """Интерфейс для Unit of Work паттерна"""

    @abstractmethod
    async def commit(self) -> None:
        """Сохраняет все изменения"""
        ...

    @abstractmethod
    async def rollback(self) -> None:
        """Откатывает все изменения"""
        ...

    @abstractmethod
    def get_repository(self, repo_type: type[T]) -> T:
        """Получает репозиторий по типу"""
        ...

    @abstractmethod
    def register_repository(self, repo_type: type[T]) -> T:
        """Регистрирует новый репозиторий"""
        ...

    @abstractmethod
    async def __aenter__(self):
        """Вход в асинхронный контекстный менеджер"""
        ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Выход из асинхронного контекстного менеджера"""
        ...


class UnitOfWork(IUnitOfWork):
    """
    Универсальный Unit of Work паттерн для управления транзакциями и репозиториями.

    Этот класс инкапсулирует работу с базой данных и предоставляет
    единую точку для управления транзакциями. Может работать с любыми ``AlchemyRepository``.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self._repositories: dict[type[AlchemyRepository], AlchemyRepository] = {}
        self._context_logger = logger

    def get_repository(self, repo_type: type[T]) -> T:
        """
        Получает репозиторий по типу. Если репозиторий еще не создан,
        создает его автоматически.

        :param repo_type: Тип репозитория.
        :return: Экземпляр репозитория.
        """

        if repo_type not in self._repositories:
            self._repositories[repo_type] = repo_type(self.session)

        return self._repositories[repo_type]

    def register_repository(self, repo_type: type[T]) -> T:
        """
        Регистрирует новый репозиторий в Unit of Work.

        Этот метод позволяет явно зарегистрировать репозиторий,
        даже если он еще не был запрошен через get_repository.

        :param repo_type: Тип репозитория для регистрации.
        :return: Экземпляр репозитория.
        """

        if repo_type not in self._repositories:
            self._repositories[repo_type] = repo_type(self.session)

        return self._repositories[repo_type]

    async def commit(self) -> None:
        """Сохраняет все изменения в базе данных"""

        try:
            await self.session.commit()
        except SQLAlchemyError as e:
            self._context_logger.error(
                DatabaseError.message,
                error_message=str(e),
            )
            raise DatabaseError()

    async def rollback(self) -> None:
        """Откатывает все изменения в базе данных"""

        try:
            await self.session.rollback()
        except SQLAlchemyError as e:
            self._context_logger.error(
                DatabaseError.message,
                error_message=str(e),
            )
            raise DatabaseError()

    async def close(self) -> None:
        """Закрывает сессию базы данных"""

        try:
            await self.session.close()
        except SQLAlchemyError as e:
            self._context_logger.error(
                DatabaseError.message,
                error_message=str(e),
            )
            raise DatabaseError()

    async def __aenter__(self) -> Self:
        """
        Открывает транзакцию в базе данных.

        :return: Этот же экземпляр UnitOfWork.
        :rtype: UnitOfWork
        """

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Закрывает транзакцию в базе данных.

        Откатывает все изменения, если произошла какая-то ошибка, иначе
        сохраняет.
        """

        try:
            if exc_type is not None:
                await self.rollback()
            else:
                await self.commit()
        except SQLAlchemyError as e:
            self._context_logger.error(
                DatabaseError.message,
                error_message=str(e),
            )
            raise DatabaseError()
        finally:
            await self.close()


class UnitOfWorkFactory:
    """
    Фабрика для создания Unit of Work с предустановленными репозиториями.

    Это удобно для случаев, когда нужно быстро получить доступ к часто используемым репозиториям.
    """

    @staticmethod
    def get_uow(
        session: AsyncSession,
        *repo_types: type[AlchemyRepository],
    ) -> UnitOfWork:
        """
        Создает Unit of Work с предустановленными репозиториями.

        :param session: Сессия базы данных.
        :type session: AsyncSession
        :param repo_types: Типы репозиториев для предустановки.
        :type repo_types: type[AlchemyRepository]
        :return: UnitOfWork с готовыми репозиториями.
        :rtype: UnitOfWork
        """

        uow = UnitOfWork(session)

        for repo_type in repo_types:
            uow.register_repository(repo_type)

        return uow
