from unittest.mock import (
    MagicMock,
    AsyncMock,
    create_autospec,
    call,
)

import pytest

from tests.conftest import ValueGenerator
from tests.mock_utils import assert_called_once_with
from domain.chat.service import (
    ChatSessionService,
    ChatMessageService,
    RAGService,
)
from domain.chat.schemas import (
    ChatRequest,
    Source,
    ChatResponse,
    ChatSessionDTO,
    ChatRole,
    ChatMessageDTO,
)
from domain.chat.exceptions import (
    ChatSessionCreationError,
    ChatSessionRetrivalError,
    ChatMessageCreationError,
    ChatMessageRetrievalError,
    RAGError,
)
from domain.schemas import (
    VectorMetadata,
    Vector,
)
from stubs import llm_stub


class TestChatSessionService:
    @pytest.mark.asyncio
    async def test_create_returns_new_session(
        self,
        mock_chat_session_repository: MagicMock,
        workspace_id: str = ValueGenerator.uuid(),
    ):
        expected_schema = ChatSessionDTO(workspace_id=workspace_id)

        mock_chat_session_repository.create = AsyncMock(return_value=expected_schema)
        chat_session_service = ChatSessionService(
            repository=mock_chat_session_repository
        )

        schema: ChatSessionDTO = await chat_session_service.create(
            workspace_id=workspace_id
        )
        assert schema == expected_schema

        assert_called_once_with(
            mock_chat_session_repository.create,
            workspace_id=workspace_id,
        )

    @pytest.mark.asyncio
    async def test_create_raises_for_database_error(
        self,
        mock_chat_session_repository: MagicMock,
        workspace_id: str = ValueGenerator.uuid(),
    ):
        mock_chat_session_repository.create = AsyncMock(
            side_effect=Exception("database error")
        )
        chat_session_service = ChatSessionService(
            repository=mock_chat_session_repository
        )

        with pytest.raises(ChatSessionCreationError):
            await chat_session_service.create(workspace_id=workspace_id)

        assert_called_once_with(
            mock_chat_session_repository.create,
            workspace_id=workspace_id,
        )

    @pytest.mark.asyncio
    async def test_sessions_returns_list(
        self,
        mock_chat_session_repository: MagicMock,
        workspace_id: str = ValueGenerator.uuid(),
    ):
        expected_schemas: list[ChatSessionDTO] = [
            ChatSessionDTO(workspace_id=workspace_id)
            for _ in range(ValueGenerator.integer(2))
        ]

        mock_chat_session_repository.get_n = AsyncMock(return_value=expected_schemas)
        chat_session_service = ChatSessionService(
            repository=mock_chat_session_repository
        )

        schemas: list[ChatSessionDTO] = await chat_session_service.sessions(
            workspace_id=workspace_id
        )
        assert schemas == expected_schemas

        assert_called_once_with(
            mock_chat_session_repository.get_n,
            workspace_id=workspace_id,
        )

    @pytest.mark.asyncio
    async def test_sessions_raises_for_database_error(
        self,
        mock_chat_session_repository: MagicMock,
        workspace_id: str = ValueGenerator.uuid(),
    ):
        mock_chat_session_repository.get_n = AsyncMock(
            side_effect=Exception("database error")
        )
        chat_session_service = ChatSessionService(
            repository=mock_chat_session_repository
        )

        with pytest.raises(ChatSessionRetrivalError):
            await chat_session_service.sessions(workspace_id=workspace_id)

        assert_called_once_with(
            mock_chat_session_repository.get_n,
            workspace_id=workspace_id,
        )


class TestChatMessageService:
    @pytest.mark.asyncio
    async def test_create_returns_new_message(
        self,
        mock_chat_message_repository: MagicMock,
        session_id: str = ValueGenerator.uuid(),
        role: ChatRole = ChatRole.user,
        content: str = ValueGenerator.text(),
    ):
        expected_schema = ChatMessageDTO(
            session_id=session_id,
            role=role,
            content=content,
        )

        mock_chat_message_repository.create = AsyncMock(return_value=expected_schema)
        chat_message_service = ChatMessageService(
            repository=mock_chat_message_repository
        )

        schema: ChatMessageDTO = await chat_message_service.create(
            session_id=session_id,
            role=role,
            content=content,
        )
        assert schema == expected_schema

        assert_called_once_with(
            mock_chat_message_repository.create,
            session_id=session_id,
            role=role,
            content=content,
        )

    @pytest.mark.asyncio
    async def test_create_raises_for_database_error(
        self,
        mock_chat_message_repository: MagicMock,
        session_id: str = ValueGenerator.uuid(),
        role: ChatRole = ChatRole.user,
        content: str = ValueGenerator.text(),
    ):
        mock_chat_message_repository.create = AsyncMock(
            side_effect=Exception("database error")
        )
        chat_message_service = ChatMessageService(
            repository=mock_chat_message_repository
        )

        with pytest.raises(ChatMessageCreationError):
            await chat_message_service.create(
                session_id=session_id,
                role=role,
                content=content,
            )

        assert_called_once_with(
            mock_chat_message_repository.create,
            session_id=session_id,
            role=role,
            content=content,
        )

    @pytest.mark.asyncio
    async def test_messages_returns_list(
        self,
        mock_chat_message_repository: MagicMock,
        session_id: str = ValueGenerator.uuid(),
    ):
        expected_schemas: list[ChatMessageDTO] = [
            ChatMessageDTO(
                session_id=session_id,
                role=ChatRole.user,
                content=ValueGenerator.text(),
            )
            for _ in range(ValueGenerator.integer(2))
        ]

        mock_chat_message_repository.chat_history = AsyncMock(
            return_value=expected_schemas
        )
        chat_message_service = ChatMessageService(
            repository=mock_chat_message_repository
        )

        schemas: list[ChatMessageDTO] = await chat_message_service.messages(
            session_id=session_id
        )
        assert schemas == expected_schemas

        assert_called_once_with(
            mock_chat_message_repository.chat_history, session_id=session_id
        )

    @pytest.mark.asyncio
    async def test_messages_raises_for_database_error(
        self,
        mock_chat_message_repository: MagicMock,
        session_id: str = ValueGenerator.uuid(),
    ):
        mock_chat_message_repository.chat_history = AsyncMock(
            side_effect=Exception("database error")
        )
        chat_message_service = ChatMessageService(
            repository=mock_chat_message_repository
        )

        with pytest.raises(ChatMessageRetrievalError):
            await chat_message_service.messages(session_id=session_id)

        assert_called_once_with(
            mock_chat_message_repository.chat_history, session_id=session_id
        )

    @pytest.mark.asyncio
    async def test_recent_messages_returns_list(
        self,
        mock_chat_message_repository: MagicMock,
        session_id: str = ValueGenerator.uuid(),
        n: int = ValueGenerator.integer(),
    ):
        expected_schemas: list[ChatMessageDTO] = [
            ChatMessageDTO(
                session_id=session_id,
                role=ChatRole.user,
                content=ValueGenerator.text(),
            )
            for _ in range(ValueGenerator.integer(2))
        ]

        mock_chat_message_repository.fetch_recent_messages = AsyncMock(
            return_value=expected_schemas
        )
        chat_message_service = ChatMessageService(
            repository=mock_chat_message_repository
        )

        schemas: list[ChatMessageDTO] = await chat_message_service.recent_messages(
            session_id=session_id,
            n=n,
        )
        assert schemas == expected_schemas

        assert_called_once_with(
            mock_chat_message_repository.fetch_recent_messages,
            session_id=session_id,
            n=n,
        )

    @pytest.mark.asyncio
    async def test_recent_messages_raises_for_database_error(
        self,
        mock_chat_message_repository: MagicMock,
        session_id: str = ValueGenerator.uuid(),
        n: int = ValueGenerator.integer(),
    ):
        mock_chat_message_repository.fetch_recent_messages = AsyncMock(
            side_effect=Exception("database error")
        )
        chat_message_service = ChatMessageService(
            repository=mock_chat_message_repository
        )

        with pytest.raises(ChatMessageRetrievalError):
            await chat_message_service.recent_messages(
                session_id=session_id,
                n=n,
            )

        assert_called_once_with(
            mock_chat_message_repository.fetch_recent_messages,
            session_id=session_id,
            n=n,
        )


class TestRAGService:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "chat_request",
        [
            ChatRequest(
                question=ValueGenerator.text(),
                workspace_id=ValueGenerator.uuid(),
                session_id=ValueGenerator.uuid(),
                top_k=ValueGenerator.integer(),
            ),
            ChatRequest(
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
        mock_vector_store: MagicMock,
        mock_embedding_model: MagicMock,
        mock_chat_session_service: MagicMock,
        mock_chat_message_service: MagicMock,
        chat_request: ChatRequest,
    ):
        workspace_id: str = chat_request.workspace_id
        if chat_request.session_id:
            session = ChatSessionDTO(
                id=chat_request.session_id, workspace_id=workspace_id
            )
        else:
            session = ChatSessionDTO(workspace_id=workspace_id)
        vector: list[float] = ValueGenerator.float_vector()
        vectors: list[Vector] = [
            Vector(
                id=f"{ValueGenerator.uuid()}-{ValueGenerator.integer()}",
                values=vector,
                metadata=VectorMetadata(
                    document_id=ValueGenerator.uuid(),
                    workspace_id=workspace_id,
                    document_name=ValueGenerator.text(),
                    document_page=ValueGenerator.integer(),
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
        expected_ask_response = ChatResponse(
            answer=llm_answer,
            sources=[
                Source(
                    source_id=v.metadata.document_id,
                    document_name=v.metadata.document_name,
                    document_page=v.metadata.document_page,
                    snippet=v.metadata.text,
                )
                for v in vectors
            ],
            session_id=session.id,
        )

        mock_chat_session_service.create.return_value = session
        mock_vector = MagicMock()
        mock_vector.tolist.return_value = vector
        mock_embedding_model.encode.return_value = mock_vector
        mock_vector_store.search.return_value = vectors
        mock_chat_message_service.recent_messages.return_value = messages
        mock_llm_generate_function = create_autospec(
            llm_stub.generate, return_value=llm_answer, spec_set=True
        )
        monkeypatch.setattr(
            "domain.chat.service.llm_stub.generate", mock_llm_generate_function
        )

        rag_service = RAGService(
            vector_store=mock_vector_store,  # noqa
            embedding_model=mock_embedding_model,  # noqa
            session_service=mock_chat_session_service,  # noqa
            message_service=mock_chat_message_service,  # noqa
        )
        ask_response: ChatResponse = await rag_service.ask(
            request=chat_request.model_copy()
        )

        assert ask_response == expected_ask_response

        if chat_request.session_id:
            mock_chat_session_service.create.assert_not_called()
        else:
            assert_called_once_with(
                mock_chat_session_service.create,
                workspace_id=workspace_id,
            )

        assert_called_once_with(
            mock_embedding_model.encode,
            sentences=chat_request.question,
        )

        assert_called_once_with(
            mock_vector_store.search,
            vector=vector,
            top_k=chat_request.top_k,
            workspace_id=workspace_id,
        )

        assert_called_once_with(
            mock_chat_message_service.recent_messages,
            session_id=session.id,
            n=4,
        )

        mock_chat_message_service.create.assert_has_calls(
            [
                call(
                    session_id=session.id,
                    role=ChatRole.user,
                    content=chat_request.question,
                ),
                call(
                    session_id=session.id, role=ChatRole.assistant, content=llm_answer
                ),
            ]
        )

    @pytest.mark.asyncio
    async def test_ask_raises_rag_error(
        self,
        mock_vector_store: MagicMock,
        mock_embedding_model: MagicMock,
        mock_chat_session_service: MagicMock,
        mock_chat_message_service: MagicMock,
    ):
        chat_request = ChatRequest(
            question=ValueGenerator.text(),
            workspace_id=ValueGenerator.uuid(),
            session_id=ValueGenerator.uuid(),
            top_k=ValueGenerator.integer(),
        )

        mock_embedding_model.encode = MagicMock(side_effect=Exception("rag error"))

        rag_service = RAGService(
            vector_store=mock_vector_store,  # noqa
            embedding_model=mock_embedding_model,  # noqa
            session_service=mock_chat_session_service,  # noqa
            message_service=mock_chat_message_service,  # noqa
        )

        with pytest.raises(RAGError):
            await rag_service.ask(request=chat_request)
