from unittest.mock import MagicMock
from typing import Any

from fastapi import status
from fastapi.testclient import TestClient
from httpx import Response
import pytest

from tests.generators import (
    DocumentGenerator,
    ValueGenerator,
)
from tests.mock_utils import assert_called_once_with
from app.domain.document.schemas import Document
from app.domain.document.dependencies import document_service_dependency


class TestDocumentsAPI:
    @pytest.fixture
    def documents_api_url(self) -> str:
        return "/v1/documents"

    def test_documents_returns_list(
        self,
        documents_api_url: str,
        test_api_client: TestClient,
        mock_document_service: MagicMock,
        workspace_id: str = ValueGenerator.uuid(),
        expected_status_code: int = status.HTTP_200_OK,
    ):
        test_api_client.app.dependency_overrides[document_service_dependency] = (
            lambda: mock_document_service
        )

        documents: list[Document] = [DocumentGenerator.document(1)]
        mock_document_service.get_documents.return_value = documents

        response: Response = test_api_client.get(
            documents_api_url,
            params={"workspace_id": workspace_id},
        )

        assert response.status_code == expected_status_code
        assert response.json() == [
            document.model_dump(by_alias=True) for document in documents
        ]

        assert_called_once_with(
            mock_document_service.get_documents,
            workspace_id=workspace_id,
        )

    def test_upload_file_success(
        self,
        documents_api_url: str,
        test_api_client: TestClient,
        mock_document_service: MagicMock,
        tmp_document: Any,
        workspace_id: str = ValueGenerator.uuid(),
        expected_status_code: int = status.HTTP_202_ACCEPTED,
    ):
        test_api_client.app.dependency_overrides[document_service_dependency] = (
            lambda: mock_document_service
        )

        document: Document = DocumentGenerator.document()
        mock_document_service.save_document.return_value = document

        file, _ = tmp_document()

        response: Response = test_api_client.post(
            f"{documents_api_url}/upload",
            files={"file": (file.name, file.content, "application/pdf")},
            params={"workspace_id": workspace_id},
        )

        assert response.status_code == expected_status_code
        assert response.json() == {"document_id": document.id}

        assert_called_once_with(
            mock_document_service.save_document,
            file=file,
            workspace_id=workspace_id,
        )

    def test_download_file_success(
        self,
        documents_api_url: str,
        test_api_client: TestClient,
        mock_document_service: MagicMock,
        tmp_document: Any,
        document_id=ValueGenerator.uuid(),
        expected_status_code: int = status.HTTP_200_OK,
    ):
        test_api_client.app.dependency_overrides[document_service_dependency] = (
            lambda: mock_document_service
        )

        file, _ = tmp_document()
        mock_document_service.get_document_file.return_value = file

        response: Response = test_api_client.get(
            f"{documents_api_url}/{document_id}/download"
        )

        assert response.status_code == expected_status_code
        assert response.content == file.content
        content_disposition = response.headers.get("content-disposition", "")
        assert "filename" in content_disposition
        assert response.headers.get("content-length") == str(file.size)

        assert_called_once_with(
            mock_document_service.get_document_file,
            document_id=document_id,
        )
