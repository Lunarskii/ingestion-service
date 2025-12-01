from app.domain.workspace.service import WorkspaceService


async def workspace_service_dependency() -> WorkspaceService:
    return WorkspaceService()
