from abc import ABC, abstractmethod
from typing import TypeVar, Dict, Type

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from domain.database.repositories import BaseAlchemyRepository
from domain.database.exceptions import handle_sqlalchemy_error


T = TypeVar('T', bound=BaseAlchemyRepository)


class IUnitOfWork(ABC):
    """Интерфейс для Unit of Work паттерна"""
    
    @abstractmethod
    async def commit(self) -> None:
        """Сохраняет все изменения"""
        pass
    
    @abstractmethod
    async def rollback(self) -> None:
        """Откатывает все изменения"""
        pass
    
    @abstractmethod
    def get_repository(self, repo_type: Type[T]) -> T:
        """Получает репозиторий по типу"""
        pass
    
    @abstractmethod
    def register_repository(self, repo_type: Type[T]) -> T:
        """Регистрирует новый репозиторий"""
        pass
    
    @abstractmethod
    async def __aenter__(self):
        """Async context manager entry"""
        pass
    
    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        pass


class UnitOfWork(IUnitOfWork):
    """
    Универсальный Unit of Work паттерн для управления транзакциями и репозиториями.
    
    Этот класс инкапсулирует работу с базой данных и предоставляет
    единую точку для управления транзакциями. Может работать с любыми репозиториями.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self._repositories: Dict[Type[BaseAlchemyRepository], BaseAlchemyRepository] = {}
    
    def get_repository(self, repo_type: Type[T]) -> T:
        """
        Получает репозиторий по типу. Если репозиторий еще не создан,
        создает его автоматически.
        
        :param repo_type: Тип репозитория
        :return: Экземпляр репозитория
        """
        if repo_type not in self._repositories:
            # Создаем репозиторий по требованию
            self._repositories[repo_type] = repo_type(self.session)
        
        return self._repositories[repo_type]
    
    def register_repository(self, repo_type: Type[T]) -> T:
        """
        Регистрирует новый репозиторий в Unit of Work.
        
        Этот метод позволяет явно зарегистрировать репозиторий,
        даже если он еще не был запрошен через get_repository.
        
        :param repo_type: Тип репозитория для регистрации
        :return: Экземпляр репозитория
        """
        if repo_type not in self._repositories:
            self._repositories[repo_type] = repo_type(self.session)
        
        return self._repositories[repo_type]
    
    async def commit(self) -> None:
        """Сохраняет все изменения в базе данных"""
        try:
            await self.session.commit()
        except SQLAlchemyError as e:
            # Преобразуем SQLAlchemy исключения в наши доменные исключения
            raise handle_sqlalchemy_error(e)
    
    async def rollback(self) -> None:
        """Откатывает все изменения"""
        await self.session.rollback()
    
    async def close(self) -> None:
        """Закрывает сессию"""
        await self.session.close()
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if exc_type is not None:
            # Если произошла ошибка, откатываем транзакцию
            await self.rollback()
        else:
            # Если все хорошо, коммитим изменения
            await self.commit()
        
        # Закрываем сессию
        await self.close()


# Фабрика для создания Unit of Work с предустановленными репозиториями
class UnitOfWorkFactory:
    """
    Фабрика для создания Unit of Work с предустановленными репозиториями.
    
    Это удобно для случаев, когда нужно быстро получить доступ к часто используемым репозиториям.
    """
    
    @staticmethod
    def create_with_repositories(session: AsyncSession, *repo_types: Type[BaseAlchemyRepository]):
        """
        Создает Unit of Work с предустановленными репозиториями.
        
        :param session: Сессия базы данных
        :param repo_types: Типы репозиториев для предустановки
        :return: Unit of Work с готовыми репозиториями
        """
        uow = UnitOfWork(session)
        
        # Предустанавливаем репозитории
        for repo_type in repo_types:
            uow.register_repository(repo_type)
        
        return uow


# Пример использования фабрики для конкретных доменов
def create_chat_unit_of_work(session: AsyncSession):
    """
    Создает Unit of Work для работы с чатом.
    
    Это удобная функция для быстрого доступа к репозиториям чата.
    """
    from domain.chat.repositories import (
        ChatSessionRepository,
        ChatMessageRepository,
        ChatMessageSourceRepository,
    )
    
    return UnitOfWorkFactory.create_with_repositories(
        session,
        ChatSessionRepository,
        ChatMessageRepository,
        ChatMessageSourceRepository,
    )


def create_workspace_unit_of_work(session: AsyncSession):
    """
    Создает Unit of Work для работы с рабочими пространствами.
    
    Это удобная функция для быстрого доступа к репозиториям workspace.
    """
    # Здесь нужно будет добавить импорты workspace репозиториев
    # from domain.workspace.repositories import WorkspaceRepository, etc.
    
    # Пока возвращаем базовый Unit of Work
    return UnitOfWork(session)


def create_document_unit_of_work(session: AsyncSession):
    """
    Создает Unit of Work для работы с документами.
    """
    # Здесь нужно будет добавить импорты document репозиториев
    return UnitOfWork(session)


def create_extraction_unit_of_work(session: AsyncSession):
    """
    Создает Unit of Work для работы с извлечением данных.
    """
    # Здесь нужно будет добавить импорты extraction репозиториев
    return UnitOfWork(session)
