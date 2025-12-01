from tests.generators import ValueGenerator
from app.types import Vector
from app.infrastructure.vectorstore_qdrant import QdrantVectorStorage


class TestQdrantVectorStore:
    def test_upsert_correct(
        self,
        qdrant: QdrantVectorStorage,
    ):
        vector: Vector = ValueGenerator.vector()

        qdrant.upsert([vector])
        vector_search: Vector = qdrant.search(
            embedding=vector.values,
            top_k=1,
            workspace_id=vector.payload.workspace_id,
        )[0]
        assert vector_search.payload == vector.payload
        qdrant.delete(
            workspace_id=vector.payload.workspace_id,
            document_id=vector.payload.document_id,
        )

    def test_delete_correct(
        self,
        qdrant: QdrantVectorStorage,
    ):
        vector: Vector = ValueGenerator.vector()

        def exists() -> bool:
            return qdrant.search(
                embedding=vector.values,
                top_k=1,
                workspace_id=vector.payload.workspace_id,
            ) != []

        assert not exists()
        qdrant.upsert([vector])
        assert exists()
        qdrant.delete(
            workspace_id=vector.payload.workspace_id,
            document_id=vector.payload.document_id,
        )
        assert not exists()

    def test_delete_by_workspace_correct(
        self,
        qdrant: QdrantVectorStorage,
    ):
        vector1: Vector = ValueGenerator.vector()
        vector2: Vector = ValueGenerator.vector()
        vector2.payload.workspace_id = vector1.payload.workspace_id

        def exists(values) -> bool:
            return qdrant.search(
                embedding=values,
                top_k=1,
                workspace_id=vector1.payload.workspace_id,
            ) != []

        assert not exists(vector1.values)
        assert not exists(vector2.values)
        qdrant.upsert([vector1, vector2])
        assert exists(vector1.values)
        assert exists(vector2.values)
        qdrant.delete_by_workspace(vector1.payload.workspace_id)
        assert not exists(vector1.values)
        assert not exists(vector2.values)
