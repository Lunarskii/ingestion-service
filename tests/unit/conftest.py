from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_rag_service(mocker) -> MagicMock:
    from app.domain.chat.service import RAGService
    return mocker.create_autospec(RAGService, instance=True)


@pytest.fixture
def mock_chat_service(mocker) -> MagicMock:
    from app.domain.chat.service import ChatService
    return mocker.create_autospec(ChatService, instance=True)


@pytest.fixture
def mock_async_db_session(mocker) -> MagicMock:
    from sqlalchemy.ext.asyncio import AsyncSession
    return mocker.create_autospec(AsyncSession, instance=True)


@pytest.fixture
def mock_raw_storage(mocker) -> MagicMock:
    from app.interfaces import RawStorage
    return mocker.create_autospec(RawStorage, instance=True)


@pytest.fixture
def mock_silver_storage(mocker) -> MagicMock:
    from app.interfaces import RawStorage
    return mocker.create_autospec(RawStorage, instance=True)


@pytest.fixture
def mock_vector_store(mocker) -> MagicMock:
    from app.interfaces import VectorStorage
    return mocker.create_autospec(VectorStorage, instance=True)


@pytest.fixture
def mock_llm_client(mocker) -> MagicMock:
    from app.interfaces import LLMClient
    return mocker.create_autospec(LLMClient, instance=True)


@pytest.fixture
def mock_embedding_model(mocker) -> MagicMock:
    from app.domain.embedding import EmbeddingModel
    return mocker.create_autospec(EmbeddingModel, instance=True)


@pytest.fixture
def mock_text_splitter(mocker) -> MagicMock:
    from app.domain.text_splitter import TextSplitter
    return mocker.create_autospec(TextSplitter, instance=True)


@pytest.fixture
def mock_document_service(mocker) -> MagicMock:
    from app.domain.document.service import DocumentService
    return mocker.create_autospec(DocumentService, instance=True)


@pytest.fixture
def mock_document_repo(mocker) -> MagicMock:
    from app.domain.document.repositories import DocumentRepository
    return mocker.create_autospec(DocumentRepository, instance=True)


@pytest.fixture
def mock_file_scheme(mocker) -> MagicMock:
    from app.domain.document.schemas import File
    return mocker.create_autospec(File, instance=True)


@pytest.fixture
def mock_chat_session_repo(mocker) -> MagicMock:
    from app.domain.chat.repositories import ChatSessionRepository
    return mocker.create_autospec(ChatSessionRepository, instance=True)


@pytest.fixture
def mock_chat_message_repo(mocker) -> MagicMock:
    from app.domain.chat.repositories import ChatMessageRepository
    return mocker.create_autospec(ChatMessageRepository, instance=True)


@pytest.fixture
def mock_chat_message_source_repo(mocker) -> MagicMock:
    from app.domain.chat.repositories import ChatMessageSourceRepository
    return mocker.create_autospec(ChatMessageSourceRepository, instance=True)


@pytest.fixture
def mock_workspace_service(mocker) -> MagicMock:
    from app.domain.workspace.service import WorkspaceService
    return mocker.create_autospec(WorkspaceService, instance=True)


@pytest.fixture
def mock_workspace_repo(mocker) -> MagicMock:
    from app.domain.workspace.repositories import WorkspaceRepository
    return mocker.create_autospec(WorkspaceRepository, instance=True)


@pytest.fixture
def mock_classifier(mocker) -> MagicMock:
    from app.domain.classifier.rules import Classifier
    return mocker.create_autospec(Classifier, instance=True)


@pytest.fixture
def mock_topic_repo(mocker) -> MagicMock:
    from app.domain.classifier.repositories import TopicRepository
    return mocker.create_autospec(TopicRepository, instance=True)


@pytest.fixture
def mock_document_topic_repo(mocker) -> MagicMock:
    from app.domain.classifier.repositories import DocumentTopicRepository
    return mocker.create_autospec(DocumentTopicRepository, instance=True)


@pytest.fixture
def mock_keycloak_client(mocker) -> MagicMock:
    from app.domain.security.service import KeycloakClient
    return mocker.create_autospec(KeycloakClient, instance=True)
