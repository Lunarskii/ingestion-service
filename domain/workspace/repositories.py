from sqlalchemy import select

from domain.database.repositories import BaseAlchemyRepository
from domain.workspace.models import WorkspaceDAO
from domain.workspace.schemas import WorkspaceDTO


class WorkspaceRepository(BaseAlchemyRepository[WorkspaceDAO, WorkspaceDTO]):
    """
    Репозиторий для работы с сущностями ``WorkspaceDAO``.

    Наследует :class:`BaseAlchemyRepository` и задаёт конкретные типы модели и схемы:

    :ivar model_type: ORM-модель рабочего пространства.
    :vartype model_type: type[WorkspaceDAO]
    :ivar schema_type: Pydantic-схема для сериализации/валидации workspace.
    :vartype schema_type: type[WorkspaceDTO]
    """

    model_type = WorkspaceDAO
    schema_type = WorkspaceDTO

    async def get_by_name(self, name: str) -> WorkspaceDTO | None:
        """
        Возвращает рабочее пространство по его уникальному имени.

        Выполняет запрос к БД, выбирая первую запись с совпадающим значением поля ``name``.

        :param name: Имя рабочего пространства для поиска.
        :type name: str
        :return: DTO рабочего пространства или ``None``, если запись не найдена.
        :rtype: WorkspaceDTO | None
        """

        stmt = select(self.model_type).where(self.model_type.name == name)
        instance = await self.session.scalar(stmt)
        if instance is None:
            return None
        return self.schema_type.model_validate(instance)
