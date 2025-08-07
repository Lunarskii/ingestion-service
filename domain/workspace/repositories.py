from sqlalchemy import select

from domain.database.repositories import BaseAlchemyRepository
from domain.workspace.models import WorkspaceDAO
from domain.workspace.schemas import WorkspaceDTO


class WorkspaceRepository(BaseAlchemyRepository[WorkspaceDAO, WorkspaceDTO]):
    model_type = WorkspaceDAO
    schema_type = WorkspaceDTO

    async def get_by_name(self, name: str) -> WorkspaceDTO | None:
        stmt = (
            select(self.model_type)
            .where(self.model_type.name == name)
        )
        instance = await self.session.scalar(stmt)
        if instance is None:
            return None
        return self.schema_type.model_validate(instance)
