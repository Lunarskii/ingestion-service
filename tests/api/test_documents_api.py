from unittest.mock import (
    MagicMock,
    AsyncMock,
    create_autospec,
)
from typing import Any

from fastapi.testclient import TestClient
from fastapi import status
from httpx import (
    Response,
    HTTPError,
)
import pytest

from tests.conftest import ValueGenerator
from tests.mock_utils import assert_called_once_with
from api.main import app
from api.v1.dependencies import (
    document_service_dependency,
    raw_storage_dependency,
)
from api.v1.documents.dependencies import validate_upload_file
from api.v1.documents.exceptions import (
    UnsupportedFileTypeError,
    FileTooLargeError,
    DocumentNotFoundError,
)
from domain.document.schemas import (
    DocumentDTO,
    Document,
    DocumentStatus,
)
from domain.document.repositories import DocumentRepository
from domain.document.dependencies import document_uow_dependency


mock_document_repo = create_autospec(DocumentRepository, instance=True)


def _get_repo_side_effect(repo_type):
    if repo_type is DocumentRepository:
        return mock_document_repo
    raise KeyError(f"Неожиданный тип репозитория: {repo_type!r}")


class TestDocumentsAPI:
    @pytest.fixture
    def documents_api_url(self) -> str:
        return "/v1/documents"

    def test_documents_returns_list(
        self,
        mock_uow: MagicMock,
        documents_api_url: str,
        workspace_id: str = ValueGenerator.uuid(),
        expected_status_code: int = status.HTTP_200_OK,
    ):
        app.dependency_overrides.clear()  # noqa
        mock_uow.get_repository.side_effect = _get_repo_side_effect
        app.dependency_overrides[document_uow_dependency] = lambda: mock_uow  # noqa
        client = TestClient(app)

        documents: list[DocumentDTO] = [
            DocumentDTO(
                workspace_id=workspace_id,
                name=ValueGenerator.text(),
                media_type=ValueGenerator.text(),
                raw_storage_path=f"{ValueGenerator.path()}.pdf",
                size_bytes=ValueGenerator.integer(),
                status=DocumentStatus.success,
            )
            for _ in range(ValueGenerator.integer(2))
        ]
        mock_document_repo.get_n.return_value = documents
        response: Response = client.get(
            documents_api_url,
            params={"workspace_id": workspace_id},
        )

        assert response.status_code == expected_status_code
        assert response.json() == [
            Document(**document.model_dump()).model_dump(by_alias=True)
            for document in documents
        ]

        assert_called_once_with(
            mock_document_repo.get_n,
            workspace_id=workspace_id,
        )

    def test_upload_file_success(
        self,
        mock_document_service: MagicMock,
        mock_file_scheme: MagicMock,
        tmp_document: Any,
        documents_api_url: str,
        workspace_id: str = ValueGenerator.uuid(),
        expected_status_code: int = status.HTTP_202_ACCEPTED,
    ):
        mock_document_service.process = AsyncMock(return_value=None)
        app.dependency_overrides.clear()  # noqa
        app.dependency_overrides[document_service_dependency] = (
            lambda: mock_document_service
        )  # noqa
        app.dependency_overrides[validate_upload_file] = lambda: mock_file_scheme  # noqa
        client = TestClient(app)

        file_bytes, _, _ = tmp_document()
        response: Response = client.post(
            f"{documents_api_url}/upload",
            files={"file": ("test.pdf", file_bytes, "application/pdf")},
            params={"workspace_id": workspace_id},
        )

        assert response.status_code == expected_status_code
        json_response = response.json()
        assert "document_id" in json_response

        assert_called_once_with(
            mock_document_service.process,
            file=mock_file_scheme,
            document_id=json_response.get("document_id"),
            workspace_id=workspace_id,
        )

    def test_upload_file_restricted_type(
        self,
        documents_api_url: str,
        workspace_id: str = ValueGenerator.uuid(),
        expected_status_code: int = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
    ):
        app.dependency_overrides.clear()  # noqa
        client = TestClient(app)

        response: Response = client.post(
            f"{documents_api_url}/upload",
            files={"file": ("test.pdf", b"some dummy file content", "application/pdf")},
            params={"workspace_id": workspace_id},
        )

        assert response.status_code == expected_status_code
        assert response.json().get("code") == UnsupportedFileTypeError.error_code
        with pytest.raises(HTTPError):
            response.raise_for_status()

    def test_upload_file_too_large(
        self,
        tmp_document: Any,
        documents_api_url: str,
        workspace_id: str = ValueGenerator.uuid(),
        expected_status_code: int = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
    ):
        app.dependency_overrides.clear()  # noqa
        client = TestClient(app)

        file_bytes, path, file_extension = tmp_document(30_000_000)
        response: Response = client.post(
            f"{documents_api_url}/upload",
            files={"file": ("test.pdf", file_bytes, "application/pdf")},
            params={"workspace_id": workspace_id},
        )

        assert response.status_code == expected_status_code
        assert response.json().get("code") == FileTooLargeError.error_code
        with pytest.raises(HTTPError):
            response.raise_for_status()

    def test_download_file_not_found(
        self,
        mock_uow: MagicMock,
        mock_raw_storage: MagicMock,
        documents_api_url: str,
        document_id: str = ValueGenerator.uuid(),
        expected_status_code: int = status.HTTP_404_NOT_FOUND,
    ):
        app.dependency_overrides.clear()  # noqa
        mock_uow.get_repository.side_effect = _get_repo_side_effect
        app.dependency_overrides[document_uow_dependency] = lambda: mock_uow  # noqa
        app.dependency_overrides[raw_storage_dependency] = lambda: mock_raw_storage  # noqa
        client = TestClient(app)

        mock_document_repo.get = AsyncMock(side_effect=Exception("database get error"))
        response: Response = client.get(f"{documents_api_url}/{document_id}/download")

        assert response.status_code == expected_status_code
        assert response.json().get("code") == DocumentNotFoundError.error_code
        with pytest.raises(HTTPError):
            response.raise_for_status()

        mock_document_repo.get.assert_called_once_with(document_id)

    def test_download_file_success(
        self,
        mock_uow: MagicMock,
        mock_raw_storage: MagicMock,
        documents_api_url: str,
        document_id=ValueGenerator.uuid(),
        expected_status_code: int = status.HTTP_200_OK,
    ):
        app.dependency_overrides.clear()  # noqa
        mock_uow.get_repository.side_effect = _get_repo_side_effect
        app.dependency_overrides[document_uow_dependency] = lambda: mock_uow  # noqa
        app.dependency_overrides[raw_storage_dependency] = lambda: mock_raw_storage  # noqa
        client = TestClient(app)

        file_bytes = b"some dummy file content"
        document = DocumentDTO(
            id=document_id,
            workspace_id=ValueGenerator.uuid(),
            name="test.pdf",
            media_type="application/pdf",
            raw_storage_path="some/path/test.pdf",
            size_bytes=len(file_bytes),
            status=DocumentStatus.success,
        )
        mock_document_repo.get = AsyncMock(return_value=document)
        mock_raw_storage.get.return_value = file_bytes
        response: Response = client.get(f"{documents_api_url}/{document_id}/download")

        assert response.status_code == expected_status_code
        assert response.content == file_bytes
        content_disposition = response.headers.get("content-disposition", "")
        assert "filename" in content_disposition
        assert response.headers.get("content-length") == str(document.size_bytes)

        mock_document_repo.get.assert_called_once_with(document_id)

        assert_called_once_with(
            mock_raw_storage.get,
            path=document.raw_storage_path,
        )
