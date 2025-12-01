from unittest.mock import MagicMock
import random

from fastapi import status
from fastapi.testclient import TestClient
from httpx import Response
import pytest

from tests.generators import ValueGenerator
from tests.mock_utils import assert_called_once_with
from app.domain.chat.schemas import (
    RAGRequest,
    RAGResponse,
    ChatSession,
    ChatRole,
    ChatMessage,
    ChatMessageSource,
)
from app.domain.chat.dependencies import (
    rag_service_dependency,
    chat_service_dependency,
)


class TestChatAPI:
    @pytest.fixture
    def chat_api_url(self) -> str:
        return "/v1/chat"

    def test_chats_returns_list(
        self,
        chat_api_url: str,
        test_api_client: TestClient,
        mock_chat_service: MagicMock,
        workspace_id: str = ValueGenerator.uuid(),
        expected_status_code: int = status.HTTP_200_OK,
    ):
        test_api_client.app.dependency_overrides[chat_service_dependency] = (
            lambda: mock_chat_service
        )

        sessions: list[ChatSession] = [
            ChatSession(workspace_id=workspace_id)
            for _ in range(ValueGenerator.integer(2))
        ]
        mock_chat_service.get_sessions.return_value = sessions

        response: Response = test_api_client.get(
            chat_api_url,
            params={"workspace_id": workspace_id},
        )

        assert response.status_code == expected_status_code
        assert response.json() == [
            session.model_dump(by_alias=True) for session in sessions
        ]

        assert_called_once_with(
            mock_chat_service.get_sessions,
            workspace_id=workspace_id,
        )

    @pytest.mark.parametrize(
        "rag_request, rag_response",
        [
            (
                RAGRequest(
                    question=ValueGenerator.text(),
                    workspace_id=ValueGenerator.uuid(),
                    top_k=ValueGenerator.integer(),
                ),
                RAGResponse(
                    answer=ValueGenerator.text(),
                    sources=[],
                    session_id=ValueGenerator.uuid(),
                ),
            ),
        ],
    )
    def test_ask_returns_response(
        self,
        chat_api_url: str,
        test_api_client: TestClient,
        mock_rag_service: MagicMock,
        rag_request: RAGRequest,
        rag_response: RAGResponse,
        expected_status_code: int = status.HTTP_200_OK,
    ):
        test_api_client.app.dependency_overrides[rag_service_dependency] = (
            lambda: mock_rag_service
        )

        mock_rag_service.ask.return_value = rag_response

        response: Response = test_api_client.post(
            f"{chat_api_url}/ask",
            json=rag_request.model_dump(),
        )

        assert response.status_code == expected_status_code
        assert response.json() == rag_response.model_dump(by_alias=True)

        assert_called_once_with(
            mock_rag_service.ask,
            request=rag_request,
        )

    def test_chat_history_returns_list(
        self,
        chat_api_url: str,
        test_api_client: TestClient,
        mock_chat_service: MagicMock,
        session_id: str = ValueGenerator.uuid(),
        expected_status_code: int = status.HTTP_200_OK,
    ):
        test_api_client.app.dependency_overrides[chat_service_dependency] = (
            lambda: mock_chat_service
        )

        messages: list[ChatMessage] = [
            ChatMessage(
                id=ValueGenerator.uuid(),
                session_id=session_id,
                role=random.choice((ChatRole.user, ChatRole.assistant)),
                content=ValueGenerator.text(),
                sources=[
                    ChatMessageSource(
                        source_id=ValueGenerator.uuid(),
                        document_name=ValueGenerator.text(),
                        page_start=ValueGenerator.integer(),
                        page_end=ValueGenerator.integer(),
                        snippet=ValueGenerator.text(),
                    )
                    for _ in range(ValueGenerator.integer(2))
                ],
            )
        ]
        mock_chat_service.get_messages.return_value = messages

        response: Response = test_api_client.get(
            f"{chat_api_url}/{session_id}/messages",
            params={"session_id": session_id},
        )

        assert response.status_code == expected_status_code
        assert response.json() == [
            message.model_dump(by_alias=True) for message in messages
        ]

        assert_called_once_with(
            mock_chat_service.get_messages,
            session_id=session_id,
        )
