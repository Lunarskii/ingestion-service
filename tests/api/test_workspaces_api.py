from unittest.mock import (
    MagicMock,
    AsyncMock,
)

from fastapi.testclient import TestClient
from fastapi import status
from httpx import Response
import pytest

from tests.conftest import ValueGenerator
from tests.mock_utils import assert_called_once_with
from api.main import app
from api.v1.dependencies import (
    workspace_service_dependency,
    raw_storage_dependency,
    vector_store_dependency,
    metadata_repository_dependency,
)
from domain.workspace.schemas import WorkspaceDTO


class TestWorkspacesAPI:
    @pytest.fixture
    def workspaces_api_url(self) -> str:
        return "/v1/workspaces"

    def test_workspaces_returns_list(
        self,
        mock_workspace_service: MagicMock,
        workspaces_api_url: str,
        expected_status_code: int = status.HTTP_200_OK,
    ):
        app.dependency_overrides.clear() # noqa
        app.dependency_overrides[workspace_service_dependency] = lambda: mock_workspace_service # noqa
        client = TestClient(app)

        list_workspaces: list[WorkspaceDTO] = [
            WorkspaceDTO(name=ValueGenerator.text())
            for _ in range(ValueGenerator.integer(2))
        ]
        mock_workspace_service.workspaces.return_value = list_workspaces
        response: Response = client.get(workspaces_api_url)

        assert response.status_code == expected_status_code
        assert response.json() == [workspace.model_dump() for workspace in list_workspaces]

        assert_called_once_with(mock_workspace_service.workspaces)

    def test_create_workspace_returns_response(
        self,
        mock_workspace_service: MagicMock,
        workspaces_api_url: str,
        expected_status_code: int = status.HTTP_201_CREATED,
    ):
        app.dependency_overrides.clear() # noqa
        app.dependency_overrides[workspace_service_dependency] = lambda: mock_workspace_service # noqa
        client = TestClient(app)

        workspace: WorkspaceDTO = WorkspaceDTO(name=ValueGenerator.text())
        mock_workspace_service.create.return_value = workspace
        response: Response = client.post(
            workspaces_api_url,
            params={"name": workspace.name},
        )

        assert response.status_code == expected_status_code
        assert response.json() == workspace.model_dump()

        assert_called_once_with(
            mock_workspace_service.create,
            name=workspace.name,
        )

    def test_delete_workspace_success(
        self,
        mock_workspace_service: MagicMock,
        mock_raw_storage: MagicMock,
        mock_vector_store: MagicMock,
        mock_metadata_repository: MagicMock,
        workspaces_api_url: str,
        workspace_id: str = ValueGenerator.uuid(),
        expected_status_code: int = status.HTTP_204_NO_CONTENT,
    ):
        app.dependency_overrides.clear() # noqa
        mock_workspace_service.delete = AsyncMock(return_value=None)
        app.dependency_overrides[workspace_service_dependency] = lambda: mock_workspace_service # noqa
        app.dependency_overrides[raw_storage_dependency] = lambda: mock_raw_storage # noqa
        app.dependency_overrides[vector_store_dependency] = lambda: mock_vector_store # noqa
        app.dependency_overrides[metadata_repository_dependency] = lambda: mock_metadata_repository # noqa
        client = TestClient(app)

        response: Response = client.delete(f"{workspaces_api_url}/{workspace_id}")

        assert response.status_code == expected_status_code

        assert_called_once_with(
            mock_workspace_service.delete,
            workspace_id=workspace_id,
            raw_storage=mock_raw_storage,
            vector_store=mock_vector_store,
            metadata_repository=mock_metadata_repository,
        )
