from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    BackgroundTasks,
    status,
)
from starlette.status import HTTP_204_NO_CONTENT

from api.v1.dependencies import (
    workspace_service_dependency,
    raw_storage_dependency,
    vector_store_dependency,
    metadata_repository_dependency,
)
from domain.workspace.service import WorkspaceService
from domain.workspace.schemas import WorkspaceDTO
from services import (
    RawStorage,
    VectorStore,
    MetadataRepository,
)


router = APIRouter(prefix="/workspaces")


@router.get("", status_code=status.HTTP_200_OK)
async def workspaces(
    service: Annotated[WorkspaceService, Depends(workspace_service_dependency)],
) -> list[WorkspaceDTO]:
    """
    Возвращает список всех рабочих пространств.
    """

    return await service.workspaces()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_workspace(
    name: str,
    service: Annotated[WorkspaceService, Depends(workspace_service_dependency)],
) -> WorkspaceDTO:
    """
    Создаёт новое рабочее пространство с заданным именем.
    """

    return await service.create(name=name)


@router.delete("/{workspace_id}", status_code=HTTP_204_NO_CONTENT)
async def delete_workspace(
    bg_tasks: BackgroundTasks,
    workspace_id: str,
    service: Annotated[WorkspaceService, Depends(workspace_service_dependency)],
    raw_storage: Annotated[RawStorage, Depends(raw_storage_dependency)],
    vector_store: Annotated[VectorStore, Depends(vector_store_dependency)],
    metadata_repository: Annotated[
        MetadataRepository, Depends(metadata_repository_dependency)
    ],
) -> None:
    """
    Запускает фоновую задачу по удалению рабочего пространства и всех связанных данных.
    """

    bg_tasks.add_task(
        service.delete,
        workspace_id=workspace_id,
        raw_storage=raw_storage,
        vector_store=vector_store,
        metadata_repository=metadata_repository,
    )
