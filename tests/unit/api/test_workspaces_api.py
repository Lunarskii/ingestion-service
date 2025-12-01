from unittest.mock import MagicMock

from fastapi import status
from fastapi.testclient import TestClient
from httpx import Response
import pytest

from tests.generators import ValueGenerator
from tests.mock_utils import assert_called_once_with
from app.domain.workspace.schemas import Workspace
from app.domain.workspace.dependencies import workspace_service_dependency


class TestWorkspacesAPI:
    @pytest.fixture
    def workspaces_api_url(self) -> str:
        return "/v1/workspaces"

    def test_workspaces_returns_list(
        self,
        workspaces_api_url: str,
        test_api_client: TestClient,
        mock_workspace_service: MagicMock,
        expected_status_code: int = status.HTTP_200_OK,
    ):
        test_api_client.app.dependency_overrides[workspace_service_dependency] = (
            lambda: mock_workspace_service
        )

        workspaces: list[Workspace] = [
            Workspace(
                id=ValueGenerator.uuid(),
                name=ValueGenerator.text(),
            )
            for _ in range(ValueGenerator.integer(2))
        ]
        mock_workspace_service.get_workspaces.return_value = workspaces

        response: Response = test_api_client.get(workspaces_api_url)

        assert response.status_code == expected_status_code
        assert response.json() == [
            workspace.model_dump(by_alias=True) for workspace in workspaces
        ]

        assert_called_once_with(mock_workspace_service.get_workspaces)

    def test_create_workspace_returns_response(
        self,
        workspaces_api_url: str,
        test_api_client: TestClient,
        mock_workspace_service: MagicMock,
        expected_status_code: int = status.HTTP_201_CREATED,
    ):
        test_api_client.app.dependency_overrides[workspace_service_dependency] = (
            lambda: mock_workspace_service
        )

        workspace = Workspace(
            id=ValueGenerator.uuid(),
            name=ValueGenerator.text(),
        )
        mock_workspace_service.create_workspace.return_value = workspace

        response: Response = test_api_client.post(
            workspaces_api_url,
            params={"name": workspace.name},
        )

        assert response.status_code == expected_status_code
        assert response.json() == workspace.model_dump(by_alias=True)

        assert_called_once_with(
            mock_workspace_service.create_workspace,
            name=workspace.name,
        )

    def test_delete_workspace_success(
        self,
        workspaces_api_url: str,
        test_api_client: TestClient,
        mock_workspace_service: MagicMock,
        workspace_id: str = ValueGenerator.uuid(),
        expected_status_code: int = status.HTTP_204_NO_CONTENT,
    ):
        test_api_client.app.dependency_overrides[workspace_service_dependency] = (
            lambda: mock_workspace_service
        )

        mock_workspace_service.delete_workspace.return_value = None

        response: Response = test_api_client.delete(
            f"{workspaces_api_url}/{workspace_id}"
        )

        assert response.status_code == expected_status_code

        assert_called_once_with(
            mock_workspace_service.delete_workspace,
            workspace_id=workspace_id,
        )
