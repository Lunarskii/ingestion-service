from unittest.mock import (
    MagicMock,
    call,
)
import random

import pytest

from tests.generators import ValueGenerator
from tests.mock_utils import assert_called_once_with
from app.domain.chat.service import ChatService
from app.domain.chat.schemas import (
    ChatSession,
    ChatSessionDTO,
    ChatMessage,
    ChatMessageDTO,
    ChatMessageSource,
    ChatMessageSourceDTO,
    ChatRole,
)


class TestChatService:
    @pytest.mark.asyncio
    async def test_get_sessions_returns_list(
        self,
        mock_chat_session_repo: MagicMock,
        mock_chat_message_repo: MagicMock,
        mock_chat_message_source_repo: MagicMock,
        workspace_id: str = ValueGenerator.uuid(),
    ):
        sessions: list[ChatSessionDTO] = [
            ChatSessionDTO(
                id=ValueGenerator.uuid(),
                workspace_id=workspace_id,
            )
            for _ in range(ValueGenerator.integer(2))
        ]
        mock_chat_session_repo.get_n.return_value = sessions

        chat_service = ChatService(
            chat_session_repo=mock_chat_session_repo,
            chat_message_repo=mock_chat_message_repo,
            chat_message_source_repo=mock_chat_message_source_repo,
        )
        result: list[ChatSession] = await chat_service.get_sessions(workspace_id)

        assert result == [
            ChatSession(
                id=dto.id,
                workspace_id=dto.workspace_id,
                created_at=dto.created_at,
            )
            for dto in sessions
        ]

        assert_called_once_with(
            mock_chat_session_repo.get_n,
            workspace_id=workspace_id,
        )

    @pytest.mark.asyncio
    async def test_get_messages_returns_list(
        self,
        mock_chat_session_repo: MagicMock,
        mock_chat_message_repo: MagicMock,
        mock_chat_message_source_repo: MagicMock,
        session_id: str = ValueGenerator.uuid(),
    ):
        messages: list[ChatMessageDTO] = [
            ChatMessageDTO(
                id=ValueGenerator.uuid(),
                session_id=session_id,
                role=random.choice((ChatRole.user, ChatRole.assistant)),
                content=ValueGenerator.text(),
            )
            for _ in range(ValueGenerator.integer(2))
        ]
        mock_chat_message_repo.get_messages.return_value = messages

        sources_mapping: dict[str, list[ChatMessageSourceDTO]] = {
            message.id: [
                ChatMessageSourceDTO(
                    source_id=ValueGenerator.uuid(),
                    message_id=message.id,
                    document_name=ValueGenerator.text(),
                    page_start=ValueGenerator.integer(),
                    page_end=ValueGenerator.integer(),
                    snippet=ValueGenerator.text(),
                )
                for _ in range(ValueGenerator.integer(1))
            ]
            for message in messages
        }

        def source_repo_get_n_side_effect(
            message_id, *args, **kwargs
        ) -> list[ChatMessageSourceDTO]:
            return sources_mapping.get(message_id)

        mock_chat_message_source_repo.get_n.side_effect = source_repo_get_n_side_effect

        chat_service = ChatService(
            chat_session_repo=mock_chat_session_repo,
            chat_message_repo=mock_chat_message_repo,
            chat_message_source_repo=mock_chat_message_source_repo,
        )
        result: list[ChatMessage] = await chat_service.get_messages(session_id)

        assert result == [
            ChatMessage(
                id=message.id,
                session_id=message.session_id,
                role=message.role,
                content=message.content,
                sources=[
                    ChatMessageSource(
                        source_id=source.source_id,
                        message_id=source.message_id,
                        document_name=source.document_name,
                        page_start=source.page_start,
                        page_end=source.page_end,
                        snippet=source.snippet,
                    )
                    for source in source_repo_get_n_side_effect(message.id)
                ],
                created_at=message.created_at,
            )
            for message in messages
        ]

        assert_called_once_with(
            mock_chat_message_repo.get_messages,
            session_id=session_id,
        )

        mock_chat_message_source_repo.get_n.assert_has_calls(
            [call(message_id=message.id) for message in messages],
        )
