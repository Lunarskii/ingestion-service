from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    status,
)
from starlette.status import HTTP_204_NO_CONTENT

from api.v1.dependencies import workspace_service_dependency
from domain.workspace.service import WorkspaceService
from domain.workspace.schemas import WorkspaceDTO


router = APIRouter(prefix="/workspaces")


@router.get("", status_code=status.HTTP_200_OK)
async def workspaces(
    service: Annotated[WorkspaceService, Depends(workspace_service_dependency)],
) -> list[WorkspaceDTO]:
    return await service.workspaces()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_workspace(
    name: str,
    service: Annotated[WorkspaceService, Depends(workspace_service_dependency)],
) -> None:
    await service.create(name=name)


@router.delete("/{workspace_id}", status_code=HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: str,
    service: Annotated[WorkspaceService, Depends(workspace_service_dependency)],
) -> None:
    await service.delete(workspace_id=workspace_id)
