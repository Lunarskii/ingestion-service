from unittest.mock import (
    MagicMock,
    AsyncMock,
    create_autospec,
)

from fastapi.testclient import TestClient
from fastapi import status
from httpx import Response
import pytest

from tests.conftest import ValueGenerator
from tests.mock_utils import assert_called_once_with
from api.main import app
from api.v1.dependencies import (
    raw_storage_dependency,
    vector_store_dependency,
)
from domain.workspace.schemas import WorkspaceDTO
from domain.workspace.repositories import WorkspaceRepository
from domain.workspace.dependencies import workspace_uow_dependency


mock_workspace_repo = create_autospec(WorkspaceRepository, instance=True)


def _get_repo_side_effect(repo_type):
    if repo_type is WorkspaceRepository:
        return mock_workspace_repo
    raise KeyError(f"Неожиданный тип репозитория: {repo_type!r}")


class TestWorkspacesAPI:
    @pytest.fixture
    def workspaces_api_url(self) -> str:
        return "/v1/workspaces"

    def test_workspaces_returns_list(
        self,
        mock_uow: MagicMock,
        workspaces_api_url: str,
        expected_status_code: int = status.HTTP_200_OK,
    ):
        app.dependency_overrides.clear()  # noqa
        mock_uow.get_repository.side_effect = _get_repo_side_effect
        app.dependency_overrides[workspace_uow_dependency] = lambda: mock_uow  # noqa
        client = TestClient(app)

        workspaces: list[WorkspaceDTO] = [
            WorkspaceDTO(name=ValueGenerator.text())
            for _ in range(ValueGenerator.integer(2))
        ]
        mock_workspace_repo.get_n.return_value = workspaces
        response: Response = client.get(workspaces_api_url)

        assert response.status_code == expected_status_code
        assert response.json() == [
            workspace.model_dump(by_alias=True) for workspace in workspaces
        ]

        assert_called_once_with(mock_workspace_repo.get_n)

    def test_create_workspace_returns_response(
        self,
        mock_uow: MagicMock,
        workspaces_api_url: str,
        expected_status_code: int = status.HTTP_201_CREATED,
    ):
        app.dependency_overrides.clear()  # noqa
        mock_uow.get_repository.side_effect = _get_repo_side_effect
        app.dependency_overrides[workspace_uow_dependency] = lambda: mock_uow  # noqa
        client = TestClient(app)

        workspace = WorkspaceDTO(name=ValueGenerator.text())
        mock_workspace_repo.create.return_value = workspace
        response: Response = client.post(
            workspaces_api_url,
            params={"name": workspace.name},
        )

        assert response.status_code == expected_status_code
        assert response.json() == workspace.model_dump(by_alias=True)

        assert_called_once_with(
            mock_workspace_repo.create,
            name=workspace.name,
        )

    def test_delete_workspace_success(
        self,
        mock_uow: MagicMock,
        mock_raw_storage: MagicMock,
        mock_vector_store: MagicMock,
        workspaces_api_url: str,
        workspace_id: str = ValueGenerator.uuid(),
        expected_status_code: int = status.HTTP_204_NO_CONTENT,
    ):
        app.dependency_overrides.clear()  # noqa
        mock_uow.get_repository.side_effect = _get_repo_side_effect
        app.dependency_overrides[workspace_uow_dependency] = lambda: mock_uow  # noqa
        app.dependency_overrides[raw_storage_dependency] = lambda: mock_raw_storage  # noqa
        app.dependency_overrides[vector_store_dependency] = lambda: mock_vector_store  # noqa
        client = TestClient(app)

        mock_workspace_repo.delete = AsyncMock(return_value=None)
        mock_raw_storage.delete = AsyncMock(return_value=None)
        mock_vector_store.delete = AsyncMock(return_value=None)
        response: Response = client.delete(f"{workspaces_api_url}/{workspace_id}")

        assert response.status_code == expected_status_code

        mock_workspace_repo.delete.assert_called_once_with(workspace_id)

        assert_called_once_with(
            mock_raw_storage.delete,
            path=f"{workspace_id}/",
        )

        assert_called_once_with(
            mock_vector_store.delete,
            workspace_id=workspace_id,
        )
