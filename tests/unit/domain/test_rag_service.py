from unittest.mock import (
    MagicMock,
    call,
)

import pytest

from tests.generators import ValueGenerator
from tests.mock_utils import assert_called_once_with
from app.domain.chat.service import RAGService
from app.domain.chat.schemas import (
    RAGRequest,
    RAGResponse,
    ChatMessageSource,
    ChatSessionDTO,
    ChatRole,
    ChatMessageDTO,
)
from app.domain.chat.exceptions import RAGError
from app.types import VectorPayload, Vector


class TestRAGService:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "rag_request",
        [
            RAGRequest(
                question=ValueGenerator.text(),
                workspace_id=ValueGenerator.uuid(),
                session_id=ValueGenerator.uuid(),
                top_k=ValueGenerator.integer(),
            ),
            RAGRequest(
                question=ValueGenerator.text(),
                workspace_id=ValueGenerator.uuid(),
                session_id=None,
                top_k=ValueGenerator.integer(),
            ),
        ],
    )
    async def test_ask_returns_response(
        self,
        mock_vector_store: MagicMock,
        mock_llm_client: MagicMock,
        mock_embedding_model: MagicMock,
        mock_chat_session_repo: MagicMock,
        mock_chat_message_repo: MagicMock,
        mock_chat_message_source_repo: MagicMock,
        rag_request: RAGRequest,
    ):
        workspace_id: str = rag_request.workspace_id

        if rag_request.session_id:
            chat_session = ChatSessionDTO(
                id=rag_request.session_id,
                workspace_id=workspace_id,
            )
        else:
            chat_session = ChatSessionDTO(workspace_id=workspace_id)
        mock_chat_session_repo.create.return_value = chat_session

        embedding: list[float] = ValueGenerator.float_vector()
        mock_embedding_model.encode.return_value = embedding

        vectors: list[Vector] = [
            Vector(
                id=f"{ValueGenerator.uuid()}-{ValueGenerator.integer()}",
                values=embedding,
                payload=VectorPayload(
                    document_id=ValueGenerator.uuid(),
                    workspace_id=workspace_id,
                    document_name=ValueGenerator.text(),
                    page_start=ValueGenerator.integer(),
                    page_end=ValueGenerator.integer(),
                    text=ValueGenerator.text(),
                ),
            )
        ]
        mock_vector_store.search.return_value = vectors

        messages: list[ChatMessageDTO] = [
            ChatMessageDTO(
                session_id=chat_session.id,
                role=ChatRole.user,
                content=ValueGenerator.text(),
            )
            for _ in range(ValueGenerator.integer(2))
        ]
        mock_chat_message_repo.get_recent_messages.return_value = messages

        llm_answer: str = ValueGenerator.text()
        mock_llm_client.generate.return_value = llm_answer

        expected_ask_response = RAGResponse(
            answer=llm_answer,
            sources=[
                ChatMessageSource(
                    source_id=v.payload.document_id,
                    document_name=v.payload.document_name,
                    page_start=v.payload.page_start,
                    page_end=v.payload.page_end,
                    snippet=v.payload.text,
                )
                for v in vectors
            ],
            session_id=chat_session.id,
        )

        rag_service = RAGService(
            vector_store=mock_vector_store,  # noqa
            llm_client=mock_llm_client,  # noqa
            embedding_model=mock_embedding_model,  # noqa
            chat_session_repo=mock_chat_session_repo,  # noqa
            chat_message_repo=mock_chat_message_repo,  # noqa
            chat_message_source_repo=mock_chat_message_source_repo,  # noqa
        )
        ask_response: RAGResponse = await rag_service.ask(rag_request.model_copy())

        assert ask_response == expected_ask_response

        if rag_request.session_id:
            mock_chat_session_repo.create.assert_not_called()
        else:
            assert_called_once_with(
                mock_chat_session_repo.create,
                workspace_id=workspace_id,
            )

        assert_called_once_with(
            mock_embedding_model.encode,
            sentences=rag_request.question,
        )

        assert_called_once_with(
            mock_vector_store.search,
            embedding=embedding,
            top_k=rag_request.top_k,
            workspace_id=workspace_id,
        )

        assert_called_once_with(
            mock_chat_message_repo.get_recent_messages,
            session_id=chat_session.id,
            limit=4,
        )

        mock_chat_message_repo.create.assert_has_calls(
            [
                call(
                    session_id=chat_session.id,
                    role=ChatRole.user,
                    content=rag_request.question,
                ),
                call(
                    session_id=chat_session.id,
                    role=ChatRole.assistant,
                    content=llm_answer,
                ),
            ],
        )

        # mock_chat_message_source_repo.create.assert_has_calls(
        #     [
        #         call(
        #             source_id=source.source_id,
        #             message_id=None,
        #             document_name=source.document_name,
        #             page_start=source.page_start,
        #             page_end=source.page_end,
        #             snippet=source.snippet,
        #         )
        #         for source in expected_ask_response.sources
        #     ]
        # )

    @pytest.mark.asyncio
    async def test_ask_raises_rag_error(
        self,
        mock_vector_store: MagicMock,
        mock_llm_client: MagicMock,
        mock_embedding_model: MagicMock,
        mock_chat_session_repo: MagicMock,
        mock_chat_message_repo: MagicMock,
        mock_chat_message_source_repo: MagicMock,
    ):
        rag_request = RAGRequest(
            question=ValueGenerator.text(),
            workspace_id=ValueGenerator.uuid(),
            session_id=ValueGenerator.uuid(),
            top_k=ValueGenerator.integer(),
        )

        mock_embedding_model.encode = MagicMock(side_effect=Exception("rag error"))

        rag_service = RAGService(
            vector_store=mock_vector_store,  # noqa
            llm_client=mock_llm_client,  # noqa
            embedding_model=mock_embedding_model,  # noqa
            chat_session_repo=mock_chat_session_repo,  # noqa
            chat_message_repo=mock_chat_message_repo,  # noqa
            chat_message_source_repo=mock_chat_message_source_repo,  # noqa
        )

        with pytest.raises(RAGError):
            await rag_service.ask(rag_request)
