import pytest

from tests.conftest import ValueGenerator
from app.domain import Vector
from app.infrastructure import QdrantVectorStore
from config import settings


@pytest.fixture
def qdrant():
    return QdrantVectorStore(
        url=settings.qdrant.url,
        collection_name=settings.qdrant.collection,
        host=settings.qdrant.host,
        port=settings.qdrant.port,
        grpc_port=settings.qdrant.grpc_port,
        api_key=settings.qdrant.api_key,
        https=settings.qdrant.use_https,
        prefer_grpc=settings.qdrant.prefer_grpc,
        timeout=settings.qdrant.timeout,
        vector_size=settings.qdrant.vector_size,
        distance=settings.qdrant.distance,
    )


class TestQdrantVectorStore:
    def test_upsert_correct(
        self,
        qdrant: QdrantVectorStore,
    ):
        vector: Vector = ValueGenerator.vector()
        qdrant.upsert([vector])
        vector_search: Vector = qdrant.search(
            embedding=vector.values,
            top_k=1,
            workspace_id=vector.metadata.workspace_id,
        )[0]
        assert vector_search.metadata == vector.metadata
        qdrant.delete(
            workspace_id=vector.metadata.workspace_id,
            document_id=vector.metadata.document_id,
        )
