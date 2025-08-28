from unittest.mock import (
    MagicMock,
    create_autospec,
    call,
)

from fastapi.testclient import TestClient
from fastapi import status
from httpx import Response
import pytest

from tests.conftest import ValueGenerator
from tests.mock_utils import assert_called_once_with
from api.main import app
from api.v1.dependencies import rag_service_dependency
from domain.chat.dependencies import chat_uow_dependency
from domain.chat.schemas import (
    RAGRequest,
    RAGResponse,
    ChatSessionDTO,
    ChatSession,
    ChatRole,
    ChatMessageDTO,
    ChatMessage,
    ChatMessageSourceDTO,
    ChatMessageSource,
)
from domain.chat.repositories import (
    ChatSessionRepository,
    ChatMessageRepository,
    ChatMessageSourceRepository,
)


mock_chat_session_repo = create_autospec(ChatSessionRepository, instance=True)
mock_chat_message_repo = create_autospec(ChatMessageRepository, instance=True)
mock_chat_message_source_repo = create_autospec(ChatMessageSourceRepository, instance=True)


def _get_repo_side_effect(repo_type):
    if repo_type is ChatSessionRepository:
        return mock_chat_session_repo
    if repo_type is ChatMessageRepository:
        return mock_chat_message_repo
    if repo_type is ChatMessageSourceRepository:
        return mock_chat_message_source_repo
    raise KeyError(f"Неожиданный тип репозитория: {repo_type!r}")


class TestChatAPI:
    @pytest.fixture
    def chat_api_url(self) -> str:
        return "/v1/chat"

    def test_chats_returns_list(
        self,
        mock_uow: MagicMock,
        chat_api_url: str,
        workspace_id: str = ValueGenerator.uuid(),
        expected_status_code: int = status.HTTP_200_OK,
    ):
        app.dependency_overrides.clear()  # noqa
        mock_uow.get_repository.side_effect = _get_repo_side_effect
        app.dependency_overrides[chat_uow_dependency] = lambda: mock_uow  # noqa
        client = TestClient(app)

        sessions: list[ChatSessionDTO] = [
            ChatSessionDTO(workspace_id=workspace_id)
            for _ in range(ValueGenerator.integer(2))
        ]
        mock_chat_session_repo.get_n.return_value = sessions
        response: Response = client.get(
            chat_api_url,
            params={"workspace_id": workspace_id},
        )

        assert response.status_code == expected_status_code
        assert response.json() == [
            ChatSession(**session.model_dump()).model_dump(by_alias=True)
            for session in sessions
        ]

        assert_called_once_with(
            mock_chat_session_repo.get_n,
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
        mock_rag_service: MagicMock,
        mock_uow: MagicMock,
        chat_api_url: str,
        rag_request: RAGRequest,
        rag_response: RAGResponse,
        expected_status_code: int = status.HTTP_200_OK,
    ):
        app.dependency_overrides.clear()  # noqa
        app.dependency_overrides[rag_service_dependency] = lambda: mock_rag_service  # noqa
        app.dependency_overrides[chat_uow_dependency] = lambda: mock_uow  # noqa
        client = TestClient(app)

        mock_rag_service.ask.return_value = rag_response
        response: Response = client.post(
            f"{chat_api_url}/ask",
            json=rag_request.model_dump(),
        )

        assert response.status_code == expected_status_code
        assert response.json() == rag_response.model_dump(by_alias=True)

        assert_called_once_with(
            mock_rag_service.ask,
            request=rag_request,
            uow=mock_uow,
        )

    def test_chat_history_returns_list(
        self,
        mock_uow: MagicMock,
        chat_api_url: str,
        session_id: str = ValueGenerator.uuid(),
        expected_status_code: int = status.HTTP_200_OK,
    ):
        app.dependency_overrides.clear()  # noqa
        mock_uow.get_repository.side_effect = _get_repo_side_effect
        app.dependency_overrides[chat_uow_dependency] = lambda: mock_uow  # noqa
        client = TestClient(app)

        messages: list[ChatMessageDTO] = [
            ChatMessageDTO(
                session_id=session_id,
                role=ChatRole.user,
                content=ValueGenerator.text(),
            )
            for _ in range(ValueGenerator.integer(2))
        ]
        sources: list[ChatMessageSourceDTO] = [
            ChatMessageSourceDTO(
                source_id=ValueGenerator.uuid(),
                message_id=ValueGenerator.uuid(),
                document_name=ValueGenerator.text(),
                page_start=ValueGenerator.integer(),
                page_end=ValueGenerator.integer(),
                snippet=ValueGenerator.text(),
            )
            for _ in range(ValueGenerator.integer(2))
        ]
        mock_chat_message_repo.get_messages.return_value = messages
        mock_chat_message_source_repo.get_n.return_value = sources
        response: Response = client.get(
            f"{chat_api_url}/{session_id}/messages",
            params={"session_id": session_id},
        )

        assert response.status_code == expected_status_code
        assert response.json() == [
            ChatMessage(
                id=message.id,
                session_id=message.session_id,
                role=message.role,
                content=message.content,
                sources=[
                    ChatMessageSource(
                        source_id=source.source_id,
                        document_name=source.document_name,
                        page_start=source.page_start,
                        page_end=source.page_end,
                        snippet=source.snippet,
                    )
                    for source in sources
                ],
                created_at=message.created_at,
            ).model_dump(by_alias=True)
            for message in messages
        ]

        assert_called_once_with(
            mock_chat_message_repo.get_messages,
            session_id=session_id,
        )
        mock_chat_message_source_repo.get_n.assert_has_calls(
            [
                call(message_id=message.id)
                for message in messages
            ],
        )
