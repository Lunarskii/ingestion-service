from unittest.mock import MagicMock
from typing import Any
import uuid

from fastapi.testclient import TestClient
from fastapi import (
    status,
    Response,
)
import pytest

from api.main import app
from api.v1.dependencies import (
    document_processor_dependency,
    chat_service_dependency,
)
from domain.fhandler.service import DocumentProcessor
from domain.chat.service import ChatService
from domain.chat.schemas import ChatResponse


mock_processor = MagicMock(spec=DocumentProcessor)
mock_chat_service = MagicMock(spec=ChatService)


app.dependency_overrides[document_processor_dependency] = lambda: mock_processor
app.dependency_overrides[chat_service_dependency] = lambda: mock_chat_service
client = TestClient(app)


class TestDocumentsAPI:
    def test_upload_file_success(self):
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

    def test_upload_file_restricted_type(self):
        ...

    def test_upload_file_too_large(self):
        ...


class TestChatAPI:
    @pytest.mark.parametrize(
        "payload, chat_response, expected_status_code",
        [
            (
                {"question": "Hello, world!", "workspace_id": "test-workspace", "top_k": 1},
                ChatResponse(
                    answer="fake llm answer",
                    sources=[],
                ),
                status.HTTP_200_OK,
            ),
        ],
    )
    def test_ask_returns_response(
        self,
        payload: dict[str, Any],
        chat_response: ChatResponse,
        expected_status_code: int,
    ):
        mock_chat_service.ask.return_value = chat_response
        response: Response = client.post("/v1/chat/ask", json=payload)

        assert response.status_code == expected_status_code
        assert response.json() == chat_response.model_dump()

        mock_chat_service.ask.assert_called_once()
        args = mock_chat_service.ask.call_args.args
        assert args[0].question == payload["question"]
