from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from fastapi import status
from httpx import Response
import pytest

from tests.conftest import ValueGenerator
from tests.mock_utils import assert_called_once_with
from api.main import app
from api.v1.dependencies import (
    chat_session_service_dependency,
    chat_message_service_dependency,
    rag_service_dependency,
)
from domain.chat.schemas import (
    ChatRequest,
    ChatResponse,
    ChatSessionDTO,
    ChatRole,
    ChatMessageDTO,
)


class TestChatAPI:
    @pytest.fixture
    def chat_api_url(self) -> str:
        return "/v1/chat"

    def test_chats_returns_list(
        self,
        mock_chat_session_service: MagicMock,
        chat_api_url: str,
        workspace_id: str = ValueGenerator.uuid(),
        expected_status_code: int = status.HTTP_200_OK,
    ):
        app.dependency_overrides.clear()  # noqa
        app.dependency_overrides[chat_session_service_dependency] = (  # noqa
            lambda: mock_chat_session_service
        )
        client = TestClient(app)

        list_sessions: list[ChatSessionDTO] = [
            ChatSessionDTO(workspace_id=workspace_id)
            for _ in range(ValueGenerator.integer(2))
        ]
        mock_chat_session_service.sessions.return_value = list_sessions
        response: Response = client.get(
            chat_api_url,
            params={"workspace_id": workspace_id},
        )

        assert response.status_code == expected_status_code
        assert response.json() == [session.model_dump() for session in list_sessions]

        assert_called_once_with(
            mock_chat_session_service.sessions,
            workspace_id=workspace_id,
        )

    @pytest.mark.parametrize(
        "chat_request, chat_response",
        [
            (
                ChatRequest(
                    question=ValueGenerator.text(),
                    workspace_id=ValueGenerator.uuid(),
                    top_k=ValueGenerator.integer(),
                ),
                ChatResponse(
                    answer=ValueGenerator.text(),
                    sources=[],
                    session_id=ValueGenerator.uuid(),
                ),
            ),
        ],
    )
    def test_ask_returns_response(
        self,
        mock_rag_service: MagicMock,
        chat_api_url: str,
        chat_request: ChatRequest,
        chat_response: ChatResponse,
        expected_status_code: int = status.HTTP_200_OK,
    ):
        app.dependency_overrides.clear()  # noqa
        app.dependency_overrides[rag_service_dependency] = lambda: mock_rag_service  # noqa
        client = TestClient(app)

        mock_rag_service.ask.return_value = chat_response
        response: Response = client.post(
            f"{chat_api_url}/ask",
            json=chat_request.model_dump(),
        )

        assert response.status_code == expected_status_code
        assert response.json() == chat_response.model_dump()

        assert_called_once_with(
            mock_rag_service.ask,
            request=chat_request,
        )

    def test_chat_history_returns_list(
        self,
        mock_chat_message_service: MagicMock,
        chat_api_url: str,
        session_id: str = ValueGenerator.uuid(),
        expected_status_code: int = status.HTTP_200_OK,
    ):
        app.dependency_overrides.clear()  # noqa
        app.dependency_overrides[chat_message_service_dependency] = (
            lambda: mock_chat_message_service
        )  # noqa
        client = TestClient(app)

        list_messages: list[ChatMessageDTO] = [
            ChatMessageDTO(
                session_id=session_id, role=ChatRole.user, content=ValueGenerator.text()
            )
            for _ in range(ValueGenerator.integer(2))
        ]
        mock_chat_message_service.messages.return_value = list_messages
        response: Response = client.get(
            f"{chat_api_url}/{session_id}/messages",
            params={"session_id": session_id},
        )

        assert response.status_code == expected_status_code
        assert response.json() == [message.model_dump() for message in list_messages]

        assert_called_once_with(
            mock_chat_message_service.messages,
            session_id=session_id,
        )
