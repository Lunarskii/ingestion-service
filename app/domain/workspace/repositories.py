from sqlalchemy import select

from app.adapters.sqlalchemy_repository import AlchemyRepository
from app.domain.workspace.models import WorkspaceDAO
from app.domain.workspace.schemas import WorkspaceDTO


class WorkspaceRepository(AlchemyRepository[WorkspaceDAO, WorkspaceDTO]):
    """
    Репозиторий для работы с пространствами.
    """

    model_type = WorkspaceDAO
    schema_type = WorkspaceDTO

    async def get_by_name(self, name: str) -> WorkspaceDTO | None:
        """
        Возвращает рабочее пространство по его уникальному имени.
        Выполняет запрос к БД, выбирая запись с совпадающим значением поля ``name``.

        :param name: Имя рабочего пространства для поиска.

        :return: DTO-схема рабочего пространства или ``None``, если запись не найдена.
        """

        stmt = select(self.model_type).where(self.model_type.name == name)
        instance = await self.session.scalar(stmt)
        if instance is None:
            return None
        return self.schema_type.model_validate(instance)
