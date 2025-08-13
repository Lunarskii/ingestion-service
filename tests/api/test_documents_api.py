from unittest.mock import (
    MagicMock,
    AsyncMock,
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
    metadata_repository_dependency,
    raw_storage_dependency,
    validate_upload_file,
)
from api.v1.exc import (
    UnsupportedFileTypeError,
    FileTooLargeError,
    DocumentNotFoundError,
)
from domain.document.schemas import (
    DocumentMeta,
    DocumentStatus,
)


class TestDocumentsAPI:
    @pytest.fixture
    def documents_api_url(self) -> str:
        return "/v1/documents"

    def test_documents_returns_list(
        self,
        mock_metadata_repository: MagicMock,
        documents_api_url: str,
        workspace_id: str = ValueGenerator.uuid(),
        expected_status_code: int = status.HTTP_200_OK,
    ):
        app.dependency_overrides.clear()  # noqa
        app.dependency_overrides[metadata_repository_dependency] = (
            lambda: mock_metadata_repository
        )  # noqa
        client = TestClient(app)

        list_metadata: list[DocumentMeta] = [
            DocumentMeta(
                document_id=ValueGenerator.uuid(),
                workspace_id=workspace_id,
                document_name=ValueGenerator.text(),
                media_type=ValueGenerator.text(),
                raw_storage_path=f"{ValueGenerator.path()}.pdf",
                file_size_bytes=ValueGenerator.integer(),
                status=DocumentStatus.success,
            )
            for _ in range(ValueGenerator.integer(2))
        ]
        mock_metadata_repository.get.return_value = list_metadata
        response: Response = client.get(
            documents_api_url,
            params={"workspace_id": workspace_id},
        )

        assert response.status_code == expected_status_code
        assert response.json() == [metadata.model_dump() for metadata in list_metadata]

        assert_called_once_with(
            mock_metadata_repository.get,
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
        mock_metadata_repository: MagicMock,
        mock_raw_storage: MagicMock,
        documents_api_url: str,
        document_id: str = ValueGenerator.uuid(),
        expected_status_code: int = status.HTTP_404_NOT_FOUND,
    ):
        app.dependency_overrides.clear()  # noqa
        app.dependency_overrides[metadata_repository_dependency] = (
            lambda: mock_metadata_repository
        )  # noqa
        app.dependency_overrides[raw_storage_dependency] = lambda: mock_raw_storage  # noqa
        client = TestClient(app)

        mock_metadata_repository.get.return_value = []
        response: Response = client.get(f"{documents_api_url}/{document_id}/download")

        assert response.status_code == expected_status_code
        assert response.json().get("code") == DocumentNotFoundError.error_code
        with pytest.raises(HTTPError):
            response.raise_for_status()

        assert_called_once_with(
            mock_metadata_repository.get,
            document_id=document_id,
        )

    def test_download_file_success(
        self,
        mock_metadata_repository: MagicMock,
        mock_raw_storage: MagicMock,
        documents_api_url: str,
        document_id=ValueGenerator.uuid(),
        expected_status_code: int = status.HTTP_200_OK,
    ):
        app.dependency_overrides.clear()  # noqa
        app.dependency_overrides[metadata_repository_dependency] = (
            lambda: mock_metadata_repository
        )  # noqa
        app.dependency_overrides[raw_storage_dependency] = lambda: mock_raw_storage  # noqa
        client = TestClient(app)

        file_bytes = b"some dummy file content"
        metadata = DocumentMeta(
            document_id=document_id,
            workspace_id=ValueGenerator.uuid(),
            document_name="test.pdf",
            media_type="application/pdf",
            raw_storage_path="some/path/test.pdf",
            file_size_bytes=len(file_bytes),
            status=DocumentStatus.success,
        )
        mock_metadata_repository.get.return_value = [metadata]
        mock_raw_storage.get.return_value = file_bytes
        response: Response = client.get(f"{documents_api_url}/{document_id}/download")

        assert response.status_code == expected_status_code
        assert response.content == file_bytes
        content_disposition = response.headers.get("content-disposition", "")
        assert "filename" in content_disposition
        assert response.headers.get("content-length") == str(metadata.file_size_bytes)

        assert_called_once_with(
            mock_metadata_repository.get,
            document_id=document_id,
        )
        assert_called_once_with(
            mock_raw_storage.get,
            path=metadata.raw_storage_path,
        )
