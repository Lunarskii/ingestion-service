from unittest.mock import (
    MagicMock,
    create_autospec,
    call,
)

import pytest

from tests.conftest import ValueGenerator
from tests.mock_utils import assert_called_once_with
from domain.chat.service import RAGService
from domain.chat.schemas import (
    RAGRequest,
    ChatMessageSource,
    RAGResponse,
    ChatSessionDTO,
    ChatRole,
    ChatMessageDTO,
)
from domain.chat.exceptions import RAGError
from domain.chat.repositories import (
    ChatSessionRepository,
    ChatMessageRepository,
    ChatMessageSourceRepository,
)
from domain.embedding import (
    VectorMetadata,
    Vector,
)
from stubs import llm_stub


mock_chat_session_repo = create_autospec(ChatSessionRepository, instance=True)
mock_chat_message_repo = create_autospec(ChatMessageRepository, instance=True)
mock_chat_message_source_repo = create_autospec(
    ChatMessageSourceRepository, instance=True
)


def _get_repo_side_effect(repo_type):
    if repo_type is ChatSessionRepository:
        return mock_chat_session_repo
    if repo_type is ChatMessageRepository:
        return mock_chat_message_repo
    if repo_type is ChatMessageSourceRepository:
        return mock_chat_message_source_repo
    raise KeyError(f"Неожиданный тип репозитория: {repo_type!r}")


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
        monkeypatch,
        mock_uow: MagicMock,
        mock_vector_store: MagicMock,
        mock_embedding_model: MagicMock,
        rag_request: RAGRequest,
    ):
        mock_chat_session_repo.reset_mock()
        mock_chat_message_repo.reset_mock()
        mock_chat_message_source_repo.reset_mock()

        workspace_id: str = rag_request.workspace_id
        if rag_request.session_id:
            session = ChatSessionDTO(
                id=rag_request.session_id,
                workspace_id=workspace_id,
            )
        else:
            session = ChatSessionDTO(workspace_id=workspace_id)
        embedding: list[float] = ValueGenerator.float_vector()
        vectors: list[Vector] = [
            Vector(
                id=f"{ValueGenerator.uuid()}-{ValueGenerator.integer()}",
                values=embedding,
                metadata=VectorMetadata(
                    document_id=ValueGenerator.uuid(),
                    workspace_id=workspace_id,
                    document_name=ValueGenerator.text(),
                    page_start=ValueGenerator.integer(),
                    page_end=ValueGenerator.integer(),
                    text=ValueGenerator.text(),
                ),
            )
        ]
        messages: list[ChatMessageDTO] = [
            ChatMessageDTO(
                session_id=session.id,
                role=ChatRole.user,
                content=ValueGenerator.text(),
            )
            for _ in range(ValueGenerator.integer(2))
        ]
        llm_answer: str = ValueGenerator.text()
        expected_ask_response = RAGResponse(
            answer=llm_answer,
            sources=[
                ChatMessageSource(
                    source_id=v.metadata.document_id,
                    document_name=v.metadata.document_name,
                    page_start=v.metadata.page_start,
                    page_end=v.metadata.page_end,
                    snippet=v.metadata.text,
                )
                for v in vectors
            ],
            session_id=session.id,
        )

        mock_uow.get_repository.side_effect = _get_repo_side_effect
        mock_chat_session_repo.create.return_value = session
        mock_embedding_model.encode.return_value = embedding
        mock_vector_store.search.return_value = vectors
        mock_chat_message_repo.get_recent_messages.return_value = messages
        mock_llm_generate_function = create_autospec(
            llm_stub.generate,
            return_value=llm_answer,
            spec_set=True,
        )
        monkeypatch.setattr(
            "domain.chat.service.llm_stub.generate",
            mock_llm_generate_function,
        )

        rag_service = RAGService(
            vector_store=mock_vector_store,  # noqa
            embedding_model=mock_embedding_model,  # noqa
        )
        ask_response: RAGResponse = await rag_service.ask(
            request=rag_request.model_copy(),
            uow=mock_uow,
        )

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
            session_id=session.id,
            limit=4,
        )

        mock_chat_message_repo.create.assert_has_calls(
            [
                call(
                    session_id=session.id,
                    role=ChatRole.user,
                    content=rag_request.question,
                ),
                call(
                    session_id=session.id,
                    role=ChatRole.assistant,
                    content=llm_answer,
                ),
            ]
        )

        # mock_chat_message_source_repo.create.assert_has_calls(
        #     [
        #         call(
        #             source_id=source.source_id,
        #             message_id=
        #         ),
        #         for source in expected_ask_response.sources
        #     ]
        # )

    @pytest.mark.asyncio
    async def test_ask_raises_rag_error(
        self,
        mock_uow: MagicMock,
        mock_vector_store: MagicMock,
        mock_embedding_model: MagicMock,
    ):
        chat_request = RAGRequest(
            question=ValueGenerator.text(),
            workspace_id=ValueGenerator.uuid(),
            session_id=ValueGenerator.uuid(),
            top_k=ValueGenerator.integer(),
        )

        mock_embedding_model.encode = MagicMock(side_effect=Exception("rag error"))

        rag_service = RAGService(
            vector_store=mock_vector_store,  # noqa
            embedding_model=mock_embedding_model,  # noqa
        )

        with pytest.raises(RAGError):
            await rag_service.ask(
                request=chat_request,
                uow=mock_uow,
            )
