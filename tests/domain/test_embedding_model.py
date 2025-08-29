import pytest
import numpy

from tests.conftest import ValueGenerator
from domain.embedding import (
    EmbeddingModel,
    Vector,
    VectorMetadata,
)
from config import settings


@pytest.fixture
def embedding_model() -> EmbeddingModel:
    return EmbeddingModel(
        model_name_or_path=settings.embedding.model_name,
        device=settings.embedding.device,
        cache_folder=settings.embedding.cache_folder,
        token=settings.embedding.token,
        max_concurrency=settings.embedding.max_concurrency,
    )


class TestEmbeddingModel:
    @pytest.mark.asyncio
    async def test_encode_returns_list_float(
        self,
        embedding_model: EmbeddingModel,
    ):
        embedding: list[float] = await embedding_model.encode("some string")
        assert isinstance(embedding, list)
        assert len(embedding) > 0
        for value in embedding:
            assert isinstance(value, float)

    @pytest.mark.asyncio
    async def test_encode_returns_ndarray(
        self,
        embedding_model: EmbeddingModel,
    ):
        embeddings: numpy.ndarray = await embedding_model.encode(
            ["some string", "some string", "some string"]
        )
        assert isinstance(embeddings, numpy.ndarray)
        assert len(embeddings) > 0
        for embedding in embeddings:
            assert isinstance(embedding, numpy.ndarray)
            assert hasattr(embedding, "tolist")
            for value in embedding.tolist():
                assert isinstance(value, float)

    @pytest.mark.asyncio
    async def test_encode_returns_vectors(
        self,
        embedding_model: EmbeddingModel,
    ):
        n_vectors: int = 3
        metadata: list[VectorMetadata] = [
            VectorMetadata(
                document_id=ValueGenerator.uuid(),
                workspace_id=ValueGenerator.uuid(),
                document_name=ValueGenerator.text(),
                page_start=ValueGenerator.integer(),
                page_end=ValueGenerator.integer(),
                text=ValueGenerator.text(),
            )
            for _ in range(n_vectors)
        ]

        vectors: list[Vector] = await embedding_model.encode(
            sentences=["some string" for _ in range(n_vectors)],
            metadata=metadata,
        )
        assert isinstance(vectors, list)
        assert len(vectors) == n_vectors
        for vector in vectors:
            assert isinstance(vector, Vector)
            for value in vector.values:
                assert isinstance(value, float)
            assert isinstance(vector.metadata, VectorMetadata)
