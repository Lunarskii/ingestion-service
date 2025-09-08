from typing import Any
import typing
import types
import sys

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select

from domain.database.models import BaseDAO
from domain.database.exceptions import (
    DatabaseError,
    EntityNotFoundError,
    ValidationError,
)
from services import Repository
from schemas import BaseDTO
from config import logger


def _resolve_type_arg(arg: Any, cls: Any) -> type | None:
    """
    Попытаться привести аргумент типа к реальному классу:
        - если arg - ForwardRef или строка => eval в пространстве имён модуля cls
        - если arg - type => вернуть его
        - иначе вернуть None
    """

    if isinstance(arg, typing.ForwardRef):
        arg = arg.__forward_arg__

    if isinstance(arg, str):
        _module: types.ModuleType = sys.modules.get(cls.__module__)
        _globals: dict = getattr(_module, "__dict__", {}) if _module else {}

        if arg in _globals:
            return _globals[arg]

        try:
            return eval(arg, _globals)
        except Exception:
            return None

    if isinstance(arg, type):
        return arg


class AlchemyRepository[M: BaseDAO, S: BaseDTO](Repository):
    """
    Асинхронный репозиторий для работы с SQLAlchemy ORM моделями.

    Generic типы:
    --------------
        - M : BaseDAO - SQLAlchemy ORM модель (класс), с которой репозиторий работает.
        - S : BaseDTO - DTO-схема/модель, используемая для валидации/сериализации результатов.

    :ivar session: Асинхронная SQLAlchemy сессия, передаваемая в конструктор.
    :vartype session: AsyncSession
    :ivar model_type: Класс ORM модели (устанавливается в конкретных реализациях).
    :vartype model_type: type[M]
    :ivar schema_type: Класс Pydantic-схемы (устанавливается в конкретных реализациях).
    :vartype schema_type: type[S]
    """

    model_type: type[M] | None = None
    schema_type: type[S] | None = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if (
            getattr(cls, "model_type", None) is not None
            and getattr(cls, "schema_type", None) is not None
        ):
            return

        for base in getattr(cls, "__orig_bases__", ()):
            origin = typing.get_origin(base) or base
            if origin is AlchemyRepository:
                args = typing.get_args(base)
                if len(args) >= 2:
                    cls.model_type = _resolve_type_arg(args[0], cls)
                    cls.schema_type = _resolve_type_arg(args[1], cls)
                break

        if cls.model_type is None or not isinstance(cls.model_type, type):
            raise TypeError(
                f"Не удалось найти model_type для {cls.__name__}. "
                f"Укажите явно атрибут model_type или параметризуйте класс"
            )
        if cls.schema_type is None or not isinstance(cls.schema_type, type):
            raise TypeError(
                f"Не удалось найти schema_type для {cls.__name__}. "
                f"Укажите явно атрибут schema_type или параметризуйте класс."
            )

    def __init__(self, session: AsyncSession):
        """
        :param session: Асинхронная SQLAlchemy сессия ``AsyncSession``.
        :type session: AsyncSession
        """

        self.session = session
        self._context_logger = logger.bind(
            model_type=self.model_type.__name__,
            schema_type=self.schema_type.__name__,
            entity_type=self.model_type.__tablename__,
        )

    async def _get_instance(self, id: Any) -> M:
        """
        Внутренний метод для получения ORM модели по первичному ключу (ID).

        :param id: ID записи
        :return: ORM модель
        :raises: EntityNotFoundError если запись не найдена
        """

        try:
            instance = await self.session.get(self.model_type, id)
            if instance is None:
                self._context_logger.warning(EntityNotFoundError.message)
                raise EntityNotFoundError()
            return instance
        except SQLAlchemyError as e:
            self._context_logger.error(
                DatabaseError.message,
                error_message=str(e),
            )
            raise DatabaseError()

    async def create(self, **kwargs) -> S:
        """
        Создаёт новую запись в базе данных и возвращает её в виде DTO-схемы.

        :param kwargs: Набор keyword аргументов для инициализации ORM-модели.
        :type kwargs: Any
        :return: Созданная запись, преобразованная через ``schema_type.model_validate``.
        :rtype: S
        """

        try:
            instance = self.model_type(**kwargs)
            self.session.add(instance)
            await self.session.flush()
            return self.schema_type.model_validate(instance)
        except SQLAlchemyError as e:
            self._context_logger.error(
                DatabaseError.message,
                error_message=str(e),
            )
            raise DatabaseError()

    async def get(self, id: Any) -> S:
        """
        Возвращает запись по её первичному ключу (ID).

        :param id: ID записи.
        :type id: Any
        :return: DTO-схему найденной записи.
        :rtype: S
        :raises: EntityNotFoundError если запись не найдена.
        """

        instance = await self._get_instance(id)
        return self.schema_type.model_validate(instance)

    async def get_n(
        self,
        limit: int | None = None,
        offset: int | None = None,
        **kwargs,
    ) -> list[S]:
        """
        Возвращает список записей, отфильтрованных по переданным критериям.

        :param limit: Максимальное число возвращаемых записей. ``None`` означает отсутствие лимита.
        :type limit: int | None
        :param offset: Смещение от начала. ``None`` означает отсутствие сдвига.
        :type offset: int
        :param kwargs: Критерии фильтрации.
        :type kwargs: Any
        :return: Список DTO-схем соответствующих записей.
        :rtype: list[S]
        """

        try:
            stmt = (
                select(self.model_type).filter_by(**kwargs).limit(limit).offset(offset)
            )
            instances = await self.session.scalars(stmt)
            return list(map(self.schema_type.model_validate, instances))
        except SQLAlchemyError as e:
            self._context_logger.error(
                DatabaseError.message,
                error_message=str(e),
            )
            raise DatabaseError()

    async def update(self, id: Any, **kwargs) -> S:
        """
        Обновляет существующую запись заданными полями и возвращает её.

        :param id: ID записи для обновления.
        :type id: Any
        :param kwargs: Поля и значения для обновления.
        :type kwargs: Any
        :return: DTO-схему обновленной записи.
        :rtype: S
        :raises: EntityNotFoundError если запись не найдена.
        """

        try:
            instance = await self._get_instance(id)

            for key, value in kwargs.items():
                if not hasattr(instance, key):
                    self._context_logger.error(
                        ValidationError.message,
                        field=key,
                    )
                    raise ValidationError()
                setattr(instance, key, value)

            await self.session.flush()
            return self.schema_type.model_validate(instance)
        except SQLAlchemyError as e:
            self._context_logger.error(
                DatabaseError.message,
                error_message=str(e),
            )
            raise DatabaseError()

    async def delete(self, id: Any) -> None:
        """
        Удаляет запись по первичному ключу (ID).

        :param id: ID удаляемой записи.
        :type id: Any
        :raises: EntityNotFoundError если запись не найдена
        """

        try:
            instance = await self._get_instance(id)
            await self.session.delete(instance)
            await self.session.flush()
        except SQLAlchemyError as e:
            self._context_logger.error(
                DatabaseError.message,
                error_message=str(e),
            )
            raise DatabaseError()

    async def exists(self, id: Any) -> bool:
        """
        Проверяет существование записи по первичному ключу (ID).

        :param id: ID записи.
        :return: True если запись существует, False иначе.
        :rtype: bool
        """

        try:
            instance = await self.session.get(self.model_type, id)
            return instance is not None
        except SQLAlchemyError as e:
            self._context_logger.error(
                DatabaseError.message,
                error_message=str(e),
            )
            raise DatabaseError()

    async def count(self) -> int:
        """
        Возвращает общее количество записей.

        :return: Количество записей
        :rtype: int
        """

        try:
            stmt = select(self.model_type.id)
            result = await self.session.execute(stmt)
            return len(result.scalars().all())
        except SQLAlchemyError as e:
            self._context_logger.error(
                DatabaseError.message,
                error_message=str(e),
            )
            raise DatabaseError()
