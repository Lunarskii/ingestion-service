from unittest.mock import MagicMock
import uuid

from fastapi.testclient import TestClient

from api.main import app
from api.dependencies import document_processor_dependency
from domain.process import DocumentProcessor


mock_processor = MagicMock(spec=DocumentProcessor)


def get_mock_processor_override():
    return mock_processor


app.dependency_overrides[document_processor_dependency] = get_mock_processor_override
client = TestClient(app)


def test_upload_document_success():
    mock_processor.process.reset_mock()

    with open("tests/resources/1mb.docx", "rb") as file:
        file_bytes: bytes = file.read()
    filename: str = "test.pdf"
    workspace_id: str = str(uuid.uuid4())
    files: dict = {"file": (filename, file_bytes, "application/pdf")}
    params: dict = {"workspace_id": workspace_id}

    response = client.post("/v1/documents/upload", files=files, params=params)

    assert response.status_code == 202
    json_response = response.json()
    assert "document_id" in json_response

    mock_processor.process.assert_called_once()
    call_args = mock_processor.process.call_args.kwargs
    assert call_args["document_id"] == json_response["document_id"]
    assert call_args["workspace_id"] == workspace_id
    assert call_args["file_bytes"] == file_bytes
