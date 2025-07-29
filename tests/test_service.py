from unittest.mock import MagicMock

import pytest

from domain.fhandler.service import DocumentProcessor
from domain.chat.service import ChatService
from domain.chat.schemas import (
    ChatRequest,
    ChatResponse,
)
from domain.schemas import (
    Vector,
    DocumentMeta,
)
from services.exc import VectorStoreDocumentsNotFound
from stubs import JSONVectorStore
from tests.conftest import assert_any_exception


class TestDocumentProcessor:
    class DummyEmbeddingModel:
        def __init__(self, vector: list[float]):
            self._vector = vector

        # TODO сделать overload для возврата и [_Vector()] и _Vector()
        def encode(self, sentences, **kwargs):
            class _Vector:
                def __init__(self, values):
                    self._values = values

                def tolist(self) -> list:
                    return self._values

            return [_Vector(self._vector)]

    class DummyTextSplitter:
        def __init__(self, chunks: list[str]):
            self.chunks = chunks

        def split_text(self, text: str):
            return self.chunks

    def test_process_success(
        self,
        mock_raw_storage: MagicMock,
        mock_vector_store: MagicMock,
        mock_metadata_repository: MagicMock,
        random_document_id: str,
        random_workspace_id: str,
        tmp_document,
    ):
        path, file_extension = tmp_document()
        with open(path, "rb") as file:
            file_bytes: bytes = file.read()

        vectors: list[float] = [0.1, 0.5, 1.0]
        embedding_model = self.DummyEmbeddingModel(vectors)

        chunks: list[str] = ["abcdef"]
        text_splitter = self.DummyTextSplitter(chunks)

        document_processor = DocumentProcessor(
            raw_storage=mock_raw_storage,  # noqa
            vector_store=mock_vector_store,  # noqa
            metadata_repository=mock_metadata_repository,  # noqa
            embedding_model=embedding_model,  # noqa
            text_splitter=text_splitter,  # noqa
        )
        document_processor.process(
            file_bytes=file_bytes,
            document_id=random_document_id,
            workspace_id=random_workspace_id,
        )

        mock_raw_storage.save.assert_called_once_with(
            file_bytes, f"{random_workspace_id}/{random_document_id}{file_extension}"
        )

        mock_vector_store.upsert.assert_called_once_with(
            [
                Vector(
                    id=f"{random_document_id}-0",
                    values=vectors,
                    metadata={
                        "document_id": random_document_id,
                        "workspace_id": random_workspace_id,
                        "chunk_index": 0,
                        "text": chunks[0],
                    },
                )
            ]
        )
        args, _ = mock_vector_store.upsert.call_args
        assert len(args[0]) > 0
        assert isinstance(args[0], list) and all(
            isinstance(vector, Vector) for vector in args[0]
        )
        assert args[0][0].metadata["document_id"] == random_document_id

        mock_metadata_repository.save.assert_called_once()
        args, _ = mock_metadata_repository.save.call_args
        assert isinstance(args[0], DocumentMeta)
        assert args[0].document_id == random_document_id

    def test_restricted_file_type(self): ...


class TestChatService:
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
                        {
                            "document_id": "doc1",
                            "chunk_id": "chunk-1",
                            "snippet": "snippet1",
                        },
                        {
                            "document_id": "doc2",
                            "chunk_id": "chunk-2",
                            "snippet": "snippet2",
                        },
                        {
                            "document_id": "doc3",
                            "chunk_id": "chunk-3",
                            "snippet": "snippet3",
                        },
                        {
                            "document_id": "doc4",
                            "chunk_id": "chunk-4",
                            "snippet": "snippet4",
                        },
                        {
                            "document_id": "doc5",
                            "chunk_id": "chunk-5",
                            "snippet": "snippet5",
                        },
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
                        {
                            "document_id": "unknown",
                            "chunk_id": "chunk-1",
                            "snippet": "",
                        },
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
        dummy_vector_store = self.DummyVectorStore()
        dummy_vector_store.search.return_value = retrieved_vectors
        dummy_embedding_model = self.DummyEmbeddingModel(embedding)
        mocker.patch("stubs.llm_stub.generate", return_value=llm_answer)
        service = ChatService(
            vector_store=dummy_vector_store, embedding_model=dummy_embedding_model
        )  # noqa
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
            (
                ChatRequest(question="test", workspace_id="test-workspace", top_k=3),
                [0.1, 0.11, 0.12, 0.13, 0.14],
            ),
        ],
    )
    def test_ask_raises_for_empty_workspace(self, chat_request, embedding):
        vector_store = JSONVectorStore()
        dummy_embedding_model = self.DummyEmbeddingModel(embedding)
        service = ChatService(
            vector_store=vector_store, embedding_model=dummy_embedding_model
        )  # noqa
        with pytest.raises(VectorStoreDocumentsNotFound) as exc:
            service.ask(chat_request)
        assert_any_exception(VectorStoreDocumentsNotFound, exc)
