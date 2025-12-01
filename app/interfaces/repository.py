from typing import (
    TYPE_CHECKING,
    Protocol,
    Any,
)


if TYPE_CHECKING:
    from pydantic import BaseModel


class Repository(Protocol):
    """
    Универсальный интерфейс репозитория для CRUD-операций над моделями.

    Конкретные реализации могут работать с:
        - базой данных (SQL, NoSQL);
        - внешним API;
        - in-memory структурами данных (например, для тестов).
    """

    async def create(self, **kwargs) -> "BaseModel":
        """
        Создаёт и сохраняет новый объект.

        :param kwargs: Аргументы, необходимые для создания объекта.

        :return: Созданный объект.
        """

        ...

    async def get(self, key: Any) -> "BaseModel":
        """
        Получает объект по ключу (например, по ID).

        :param key: Уникальный идентификатор объекта.

        :return: Объект модели.
        """

        ...

    async def get_n(
        self,
        limit: int | None = None,
        offset: int | None = None,
        **kwargs,
    ) -> list["BaseModel"]:
        """
        Возвращает список объектов с возможностью пагинации и фильтрации.

        :param limit: Максимальное количество объектов (опционально).
        :param offset: Смещение для пагинации (опционально).
        :param kwargs: Дополнительные параметры фильтрации.

        :return: Список объектов.
        """

        ...

    async def update(self, key: Any, **kwargs) -> "BaseModel":
        """
        Обновляет существующий объект по ключу.

        :param key: Уникальный идентификатор объекта.
        :param kwargs: Поля и их новые значения.

        :return: Обновлённый объект.
        """

        ...

    async def delete(self, key: Any) -> None:
        """
        Удаляет объект по ключу.

        :param key: Уникальный идентификатор объекта.
        """

        ...

    async def exists(self, key: Any) -> bool:
        """
        Проверяет существование объекта по ключу.

        :param key: Уникальный идентификатор объекта.

        :return: True, если объект существует, иначе False.
        """

        ...
