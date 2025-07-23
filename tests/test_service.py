from unittest.mock import MagicMock
import uuid

import pytest
from sentence_transformers import SentenceTransformer

from domain.fhandler.service import DocumentProcessor
from domain.chat.service import ChatService
from domain.chat.schemas import (
    ChatRequest,
    Source,
    ChatResponse,
)
from domain.schemas import (
    Vector,
    DocumentMeta,
)
from services import (
    RawStorage,
    VectorStore,
    MetadataRepository,
)
from services.exc import VectorStoreDocumentsNotFound
from stubs import JSONVectorStore
from tests.conftest import assert_any_exception


@pytest.fixture
def mock_raw_storage(mocker):
    return mocker.MagicMock(spec=RawStorage)


@pytest.fixture
def mock_vector_store(mocker):
    return mocker.MagicMock(spec=VectorStore)


@pytest.fixture
def mock_metadata_repository(mocker):
    return mocker.MagicMock(spec=MetadataRepository)


@pytest.fixture
def document_processor(
    mock_raw_storage: MagicMock,
    mock_vector_store: MagicMock,
    mock_metadata_repository: MagicMock,
) -> DocumentProcessor:
    return DocumentProcessor(
        raw_storage=mock_raw_storage,  # noqa
        vector_store=mock_vector_store,  # noqa
        metadata_repository=mock_metadata_repository,  # noqa
    )


@pytest.fixture
def mock_embedding_model(mocker):
    return mocker.MagicMock(spec=SentenceTransformer)


@pytest.fixture
def chat_service(
    mock_vector_store: MagicMock,
    mock_embedding_model: MagicMock,
) -> ChatService:
    return ChatService(
        vector_store=mock_vector_store,  # noqa
        embedding_model=mock_embedding_model,  # noqa
    )


class TestDocumentProcessor:
    @pytest.mark.parametrize(
        "path, file_extension",
        [
            ("tests/resources/1mb.docx", ".docx"),
            ("tests/resources/1mb.pdf", ".pdf"),
        ],
    )
    def test_process_success(
        self,
        document_processor: DocumentProcessor,
        mock_raw_storage: MagicMock,
        mock_vector_store: MagicMock,
        mock_metadata_repository: MagicMock,
        path: str,
        file_extension: str,
    ):
        with open(path, "rb") as file:
            file_bytes: bytes = file.read()
        document_id: str = str(uuid.uuid4())
        workspace_id: str = str(uuid.uuid4())

        document_processor.process(
            file_bytes=file_bytes,
            document_id=document_id,
            workspace_id=workspace_id,
        )

        mock_raw_storage.save.assert_called_once_with(
            file_bytes, f"{workspace_id}/{document_id}{file_extension}"
        )

        mock_vector_store.upsert.assert_called_once()
        args, _ = mock_vector_store.upsert.call_args
        assert len(args[0]) > 0
        assert isinstance(args[0], list) and all(
            isinstance(vector, Vector) for vector in args[0]
        )
        assert args[0][0].metadata["document_id"] == document_id

        mock_metadata_repository.save.assert_called_once()
        args, _ = mock_metadata_repository.save.call_args
        assert isinstance(args[0], DocumentMeta)
        assert args[0].document_id == document_id

    def test_restricted_file_type(self):
        ...


class DummyEmbeddingModel:
    def __init__(self, vector: list[float]):
        self._vector = vector

    def encode(self, sentences, **kwargs):
        class _Vector:
            def __init__(self, values):
                self._values = values

            def tolist(self) -> list:
                return self._values

        return _Vector(self._vector)


class DummyVectorStore:
    def __init__(self):
        self.search = MagicMock()


class TestChatService:
    @pytest.mark.parametrize(
        "chat_request, retrieved_vectors, embedding, llm_answer, expected_response",
        [
            (
                ChatRequest(question="Hello, world!", workspace_id="test_ws", top_k=5),
                [
                    Vector(
                        id="chunk-1",
                        values=[0.1, 0.11, 0.12, 0.13, 0.14],
                        metadata={"document_id": "doc1", "text": "snippet1"},
                    ),
                    Vector(
                        id="chunk-2",
                        values=[0.2, 0.21, 0.22, 0.23, 0.24],
                        metadata={"document_id": "doc2", "text": "snippet2"},
                    ),
                    Vector(
                        id="chunk-3",
                        values=[0.3, 0.31, 0.32, 0.33, 0.34],
                        metadata={"document_id": "doc3", "text": "snippet3"},
                    ),
                    Vector(
                        id="chunk-4",
                        values=[0.4, 0.41, 0.42, 0.43, 0.44],
                        metadata={"document_id": "doc4", "text": "snippet4"},
                    ),
                    Vector(
                        id="chunk-5",
                        values=[0.5, 0.51, 0.52, 0.53, 0.54],
                        metadata={"document_id": "doc5", "text": "snippet5"},
                    ),
                ],
                [0.1, 0.5, 1.0],
                "fake llm answer",
                ChatResponse(
                    answer="fake llm answer",
                    sources=[
                        {"document_id": "doc1", "chunk_id": "chunk-1", "snippet": "snippet1"},
                        {"document_id": "doc2", "chunk_id": "chunk-2", "snippet": "snippet2"},
                        {"document_id": "doc3", "chunk_id": "chunk-3", "snippet": "snippet3"},
                        {"document_id": "doc4", "chunk_id": "chunk-4", "snippet": "snippet4"},
                        {"document_id": "doc5", "chunk_id": "chunk-5", "snippet": "snippet5"},
                    ],
                ),
            ),
            (
                ChatRequest(question="Hello, world!", workspace_id="test_ws", top_k=5),
                [
                    Vector(id="chunk-1", values=[0], metadata={}),
                ],
                [0.1, 0.5, 1.0],
                "fake llm answer",
                ChatResponse(
                    answer="fake llm answer",
                    sources=[
                        {"document_id": "unknown", "chunk_id": "chunk-1", "snippet": ""},
                    ],
                ),
            ),
        ],
    )
    def test_ask_returns_correct_response(
        self,
        mocker,
        chat_request: ChatRequest,
        retrieved_vectors: list[Vector],
        embedding: list[float],
        llm_answer: str,
        expected_response: ChatResponse,
    ):
        dummy_vector_store = DummyVectorStore()
        dummy_vector_store.search.return_value = retrieved_vectors
        dummy_embedding_model = DummyEmbeddingModel(embedding)
        mocker.patch("stubs.llm_stub.generate", return_value=llm_answer)
        service = ChatService(vector_store=dummy_vector_store, embedding_model=dummy_embedding_model)  # noqa
        response = service.ask(chat_request)

        assert isinstance(response, ChatResponse)
        assert response == expected_response

        vector_store_args, vector_store_kwargs = dummy_vector_store.search.call_args
        assert isinstance(vector_store_kwargs["vector"], Vector)
        assert vector_store_kwargs["vector"].values == embedding
        assert vector_store_kwargs["top_k"] == chat_request.top_k
        assert vector_store_kwargs["workspace_id"] == chat_request.workspace_id

    @pytest.mark.parametrize(
        "chat_request, embedding",
        [
            (ChatRequest(question="test", workspace_id="test-workspace", top_k=3),
            [0.1, 0.11, 0.12, 0.13, 0.14]),
        ],
    )
    def test_ask_raises_for_empty_workspace(self, chat_request, embedding):
        vector_store = JSONVectorStore()
        dummy_embedding_model = DummyEmbeddingModel(embedding)
        service = ChatService(vector_store=vector_store, embedding_model=dummy_embedding_model) # noqa
        with pytest.raises(VectorStoreDocumentsNotFound) as exc:
            service.ask(chat_request)
        assert_any_exception(VectorStoreDocumentsNotFound, exc)
