from domain.workspace.repositories import WorkspaceRepository
from domain.workspace.schemas import WorkspaceDTO
from domain.workspace.exc import WorkspaceAlreadyExistsError


class WorkspaceService:
    def __init__(
        self,
        workspace_repository: WorkspaceRepository,
    ):
        self.repository = workspace_repository

    async def create(self, name: str) -> WorkspaceDTO:
        if await self.repository.get_by_name(name):
            raise WorkspaceAlreadyExistsError()
        workspace = WorkspaceDTO(name=name)
        return await self.repository.create(**workspace.model_dump())

    async def delete(self, workspace_id: str) -> None:
        await self.repository.delete(workspace_id)
        # TODO удалить связанные документы через RawStorage
        # TODO удалить связанные вектора документов через VectorStore
        # TODO удалить связанные метаданные документов через MetadataRepository

    async def workspaces(self) -> list[WorkspaceDTO]:
        return await self.repository.get_n()
