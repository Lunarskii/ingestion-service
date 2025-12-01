from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
)

from app.domain.workspace.schemas import Workspace
from app.domain.workspace.service import WorkspaceService
from app.domain.workspace.dependencies import workspace_service_dependency
from app import status


router = APIRouter(prefix="/workspaces")


@router.get("", status_code=status.HTTP_200_OK)
async def workspaces(
    service: Annotated[WorkspaceService, Depends(workspace_service_dependency)],
) -> list[Workspace]:
    """
    Возвращает список всех рабочих пространств.
    """

    return await service.get_workspaces()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_workspace(
    name: str,
    service: Annotated[WorkspaceService, Depends(workspace_service_dependency)],
) -> Workspace:
    """
    Создаёт новое рабочее пространство с заданным именем.
    """

    return await service.create_workspace(name)


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: str,
    service: Annotated[WorkspaceService, Depends(workspace_service_dependency)],
) -> None:
    """
    Удаляет рабочее пространство и все связанные с ним данные.
    """

    await service.delete_workspace(workspace_id)
