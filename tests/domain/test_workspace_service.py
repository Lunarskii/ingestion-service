from unittest.mock import (
    MagicMock,
    AsyncMock,
)

import pytest

from tests.conftest import ValueGenerator
from tests.mock_utils import assert_called_once_with
from domain.workspace.service import WorkspaceService
from domain.workspace.schemas import WorkspaceDTO
from domain.workspace.exc import (
    WorkspaceCreationError,
    WorkspaceRetrievalError,
    WorkspaceDeletionError,
    WorkspaceAlreadyExistsError,
)


class TestWorkspaceService:
    @pytest.mark.asyncio
    async def test_create_returns_new_workspace(
        self,
        mock_workspace_repository: MagicMock,
        name: str = ValueGenerator.text(),
    ):
        expected_schema = WorkspaceDTO(name=name)

        mock_workspace_repository.get_by_name = AsyncMock(return_value=None)
        mock_workspace_repository.create = AsyncMock(return_value=expected_schema)
        workspace_service = WorkspaceService(repository=mock_workspace_repository)

        schema: WorkspaceDTO = await workspace_service.create(name=name)
        assert schema == expected_schema

        assert_called_once_with(
            mock_workspace_repository.create,
            name=name,
        )

    @pytest.mark.asyncio
    async def test_create_workspace_already_exists_error(
        self,
        mock_workspace_repository: MagicMock,
        name: str = ValueGenerator.text(),
    ):
        mock_workspace_repository.get_by_name.return_value = WorkspaceDTO(name=name)
        workspace_service = WorkspaceService(repository=mock_workspace_repository)

        with pytest.raises(WorkspaceAlreadyExistsError):
            await workspace_service.create(name=name)

        assert_called_once_with(
            mock_workspace_repository.get_by_name,
            name=name,
        )

        mock_workspace_repository.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_raises_for_database_error(
        self,
        mock_workspace_repository: MagicMock,
        name: str = ValueGenerator.text(),
    ):
        # case1
        mock_workspace_repository.get_by_name = AsyncMock(
            side_effect=Exception("database error")
        )
        workspace_service = WorkspaceService(repository=mock_workspace_repository)

        with pytest.raises(WorkspaceRetrievalError):
            await workspace_service.create(name=name)

        # case2
        mock_workspace_repository.get_by_name = AsyncMock(return_value=None)
        mock_workspace_repository.create = AsyncMock(
            side_effect=Exception("database error")
        )
        workspace_service = WorkspaceService(repository=mock_workspace_repository)

        with pytest.raises(WorkspaceCreationError):
            await workspace_service.create(name=name)

    @pytest.mark.asyncio
    async def test_delete_success(
        self,
        mock_workspace_repository: MagicMock,
        mock_raw_storage: MagicMock,
        mock_vector_store: MagicMock,
        mock_metadata_repository: MagicMock,
        workspace_id: str = ValueGenerator.uuid(),
    ):
        mock_workspace_repository.delete.return_value = None
        mock_raw_storage.delete.return_value = None
        mock_vector_store.delete.return_value = None
        mock_metadata_repository.delete.return_value = None
        workspace_service = WorkspaceService(repository=mock_workspace_repository)

        await workspace_service.delete(
            workspace_id=workspace_id,
            raw_storage=mock_raw_storage,  # noqa
            vector_store=mock_vector_store,  # noqa
            metadata_repository=mock_metadata_repository,  # noqa
        )

        assert_called_once_with(
            mock_workspace_repository.delete,
            id=workspace_id,
        )

        assert_called_once_with(
            mock_raw_storage.delete,
            path=f"{workspace_id}/",
        )

        assert_called_once_with(
            mock_vector_store.delete,
            workspace_id=workspace_id,
        )

        assert_called_once_with(
            mock_metadata_repository.delete,
            workspace_id=workspace_id,
        )

    @pytest.mark.asyncio
    async def test_delete_raises(
        self,
        mock_workspace_repository: MagicMock,
        mock_raw_storage: MagicMock,
        mock_vector_store: MagicMock,
        mock_metadata_repository: MagicMock,
        workspace_id: str = ValueGenerator.uuid(),
    ):
        mock_workspace_repository.delete = AsyncMock(
            side_effect=Exception("database error")
        )
        workspace_service = WorkspaceService(repository=mock_workspace_repository)

        with pytest.raises(WorkspaceDeletionError):
            await workspace_service.delete(
                workspace_id=workspace_id,
                raw_storage=mock_raw_storage,  # noqa
                vector_store=mock_vector_store,  # noqa
                metadata_repository=mock_metadata_repository,  # noqa
            )

    @pytest.mark.asyncio
    async def test_workspaces_returns_list(
        self,
        mock_workspace_repository: MagicMock,
    ):
        expected_schemas: list[WorkspaceDTO] = [
            WorkspaceDTO(
                name=ValueGenerator.text(),
            )
            for _ in range(ValueGenerator.integer(2))
        ]

        mock_workspace_repository.get_n = AsyncMock(return_value=expected_schemas)
        workspace_service = WorkspaceService(repository=mock_workspace_repository)

        schemas: list[WorkspaceDTO] = await workspace_service.workspaces()
        assert schemas == expected_schemas

        assert_called_once_with(mock_workspace_repository.get_n)

    @pytest.mark.asyncio
    async def test_workspaces_raises_for_database_error(
        self,
        mock_workspace_repository: MagicMock,
    ):
        mock_workspace_repository.get_n = AsyncMock(
            side_effect=Exception("database error")
        )
        workspace_service = WorkspaceService(repository=mock_workspace_repository)

        with pytest.raises(WorkspaceRetrievalError):
            await workspace_service.workspaces()

        assert_called_once_with(mock_workspace_repository.get_n)
