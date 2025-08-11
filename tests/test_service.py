from unittest.mock import MagicMock

import pytest

from tests.conftest import (
    assert_any_exception,
    ValueGenerator,
)
from tests.dummies import (
    DummyEmbeddingModel,
    DummyTextSplitter,
)
from tests.mock_utils import (
    call_args,
    assert_called_once_with,
)
from domain.document.service import DocumentService
from domain.chat.service import RAGService
from domain.chat.schemas import (
    ChatRequest,
    ChatResponse,
)
from domain.schemas import (
    Vector,
)
from domain.document.schemas import DocumentMeta
from services.exc import VectorStoreDocumentsNotFound
from stubs import JSONVectorStore


class TestDocumentProcessor:
    def test_process_success(
        self,
        mock_raw_storage: MagicMock,
        mock_vector_store: MagicMock,
        mock_metadata_repository: MagicMock,
        document_id: str,
        workspace_id: str,
        tmp_document,
    ):
        path, file_extension = tmp_document()
        with open(path, "rb") as file:
            file_bytes: bytes = file.read()

        vectors: list[float] = ValueGenerator.float_vector()
        embedding_model = DummyEmbeddingModel(vectors)

        chunks: list[str] = ValueGenerator.chunks(1)
        text_splitter = DummyTextSplitter(chunks)

        document_processor = DocumentService(
            raw_storage=mock_raw_storage,  # noqa
            vector_store=mock_vector_store,  # noqa
            metadata_repository=mock_metadata_repository,  # noqa
            embedding_model=embedding_model,  # noqa
            text_splitter=text_splitter,  # noqa
        )
        document_processor.process(
            file_bytes=file_bytes,
            document_id=document_id,
            workspace_id=workspace_id,
        )

        assert_called_once_with(
            mock_raw_storage.save,
            file_bytes=file_bytes,
            path=f"{workspace_id}/{document_id}{file_extension}",
        )

        assert_called_once_with(
            mock_vector_store.upsert,
            vectors=[
                Vector(
                    id=f"{document_id}-0",
                    values=vectors,
                    metadata={
                        "document_id": document_id,
                        "workspace_id": workspace_id,
                        "chunk_index": 0,
                        "text": chunks[0],
                    },
                )
            ],
        )

        mock_metadata_repository.save.assert_called_once()
        args = call_args(mock_metadata_repository.save)
        assert isinstance(args["meta"], DocumentMeta)
        assert args["meta"].document_id == document_id

    def test_restricted_file_type(self): ...


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
                [Vector(id="chunk-1", values=[0], metadata={})],
                [0.1, 0.5, 1.0],
                "fake llm answer",
                ChatResponse(
                    answer="fake llm answer",
                    sources=[
                        {
                            "document_id": "",
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
        mock_vector_store: MagicMock,
        chat_request: ChatRequest,
        retrieved_vectors: list[Vector],
        embedding: list[float],
        llm_answer: str,
        expected_response: ChatResponse,
    ):
        mock_vector_store.search.return_value = retrieved_vectors
        dummy_embedding_model = DummyEmbeddingModel(embedding)
        mocker.patch("stubs.llm_stub.generate", return_value=llm_answer)
        service = RAGService(
            vector_store=mock_vector_store,  # noqa
            embedding_model=dummy_embedding_model,  # noqa
        )
        response = service.ask(chat_request)

        mock_vector_store.search.assert_called_once()
        args = call_args(mock_vector_store.search)
        assert isinstance(args["vector"], Vector)
        assert args["vector"].values == embedding
        assert args["top_k"] == chat_request.top_k
        assert args["workspace_id"] == chat_request.workspace_id

        assert isinstance(response, ChatResponse)
        assert response == expected_response

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
        dummy_embedding_model = DummyEmbeddingModel(embedding)
        service = RAGService(vector_store=vector_store, embedding_model=dummy_embedding_model)  # noqa
        with pytest.raises(VectorStoreDocumentsNotFound) as exc:
            service.ask(chat_request)
        assert_any_exception(VectorStoreDocumentsNotFound, exc)
