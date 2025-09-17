from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    BackgroundTasks,
    status,
)
from starlette.status import HTTP_204_NO_CONTENT

from app.api.v1.dependencies import (
    raw_storage_dependency,
    vector_store_dependency,
)
from app.domain.workspace.dependencies import workspace_uow_dependency
from app.domain.workspace.repositories import WorkspaceRepository
from app.domain.workspace.schemas import WorkspaceDTO
from app.domain.database.uow import UnitOfWork
from app.services import (
    RawStorage,
    VectorStore,
)


router = APIRouter(prefix="/workspaces")


@router.get("", status_code=status.HTTP_200_OK)
async def workspaces(
    uow: Annotated[UnitOfWork, Depends(workspace_uow_dependency)],
) -> list[WorkspaceDTO]:
    """
    Возвращает список всех рабочих пространств.
    """

    workspace_repo = uow.get_repository(WorkspaceRepository)
    return await workspace_repo.get_n()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_workspace(
    name: str,
    uow: Annotated[UnitOfWork, Depends(workspace_uow_dependency)],
) -> WorkspaceDTO:
    """
    Создаёт новое рабочее пространство с заданным именем.
    """

    workspace_repo = uow.get_repository(WorkspaceRepository)
    return await workspace_repo.create(name=name)


@router.delete("/{workspace_id}", status_code=HTTP_204_NO_CONTENT)
async def delete_workspace(
    bg_tasks: BackgroundTasks,
    workspace_id: str,
    uow: Annotated[UnitOfWork, Depends(workspace_uow_dependency)],
    raw_storage: Annotated[RawStorage, Depends(raw_storage_dependency)],
    vector_store: Annotated[VectorStore, Depends(vector_store_dependency)],
) -> None:
    """
    Запускает фоновую задачу по удалению рабочего пространства и всех связанных данных.
    """

    workspace_repo = uow.get_repository(WorkspaceRepository)
    await workspace_repo.delete(workspace_id)

    bg_tasks.add_task(
        raw_storage.delete,
        path=f"{workspace_id}/",
    )
    bg_tasks.add_task(
        vector_store.delete,
        workspace_id=workspace_id,
    )
