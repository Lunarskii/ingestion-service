from abc import ABC
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.database.models import BaseDAO
from schemas.base import BaseDTO


class BaseAlchemyRepository[M: BaseDAO, S: BaseDTO](ABC):
    """
    Базовый асинхронный репозиторий для работы с SQLAlchemy моделями.

    Параметры типа
    --------------
    M : BaseDAO
        SQLAlchemy ORM модель (класс), с которой репозиторий работает.
    S : BaseModel
        Pydantic-схема/модель, используемая для валидации/сериализации результатов.

    :ivar session: Асинхронная SQLAlchemy сессия, передаваемая в конструктор.
    :vartype session: AsyncSession
    :ivar model_type: Класс ORM модели (устанавливается в конкретных реализациях).
    :vartype model_type: type[M]
    :ivar schema_type: Класс Pydantic-схемы (устанавливается в конкретных реализациях).
    :vartype schema_type: type[S]
    """

    session: AsyncSession
    model_type: type[M]
    schema_type: type[S]

    def __init__(self, session: AsyncSession):
        """
        :param session: Асинхронная SQLAlchemy сессия ``AsyncSession``.
        :type session: AsyncSession
        """

        self.session = session

    async def create(self, **data: Any) -> S:
        """
        Создаёт новую запись в базе данных и возвращает её в виде pydantic-схемы.

        :param data: Набор keyword аргументов для инициализации ORM-модели.
        :type data: dict[str, Any]
        :return: Созданная запись, преобразованная через ``schema_type.model_validate``.
        :rtype: S
        """

        instance = self.model_type(**data)
        self.session.add(instance)
        await self.session.commit()
        return self.schema_type.model_validate(instance)

    async def get(self, id: int | str) -> S | None:
        """
        Возвращает запись по её первичному ключу.

        :param id: Значение первичного ключа.
        :type id: int | str
        :return: Pydantic-схема найденного объекта или ``None``, если запись не найдена.
        :rtype: S | None
        """

        instance = await self.session.get(self.model_type, id)
        if instance is None:
            return None
        return self.schema_type.model_validate(instance)

    async def get_n(self, n: int | None = None, **data: Any) -> list[S]:
        """
        Возвращает список записей, отфильтрованных по переданным критериям.

        :param n: Максимальное число возвращаемых записей. ``None`` означает отсутствие лимита.
        :type n: int | None
        :param data: Критерии фильтрации.
        :type data: dict[str, Any]
        :return: Список pydantic-схем соответствующих записей.
        :rtype: list[S]
        """

        stmt = select(self.model_type).filter_by(**data).limit(n)
        instances = await self.session.scalars(stmt)
        return list(map(self.schema_type.model_validate, instances))

    async def update(self, id: int | str, **data: Any) -> S | None:
        """
        Обновляет существующую запись заданными полями и возвращает её.

        :param id: Значение первичного ключа записи для обновления.
        :type id: int | str
        :param data: Поля и значения для обновления.
        :type data: dict
        :return: Обновлённая запись в виде pydantic-схемы или ``None``, если запись не найдена.
        :rtype: S | None
        """

        instance = await self.session.get(self.model_type, id)
        if instance is None:
            return None
        instance.update(**data)
        await self.session.commit()
        return self.schema_type.model_validate(instance)

    async def delete(self, id: int | str) -> S | None:
        """
        Удаляет запись по первичному ключу и возвращает её представление.

        :param id: Значение первичного ключа удаляемой записи.
        :type id: int | str
        :return: Pydantic-схема удалённого объекта или ``None``, если запись не найдена.
        :rtype: S | None
        """

        instance = await self.session.get(self.model_type, id)
        if instance is None:
            return None
        await self.session.delete(instance)
        await self.session.commit()
        return self.schema_type.model_validate(instance)
