from typing import (
    Any,
    Awaitable,
    Callable,
)

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    QueryResponse,
)

from services import VectorStore
from domain.embedding.schemas import (
    Vector,
    VectorMetadata,
)


class QdrantVectorStore(VectorStore):
    def __init__(
        self,
        collection_name: str,
        vector_size: int,
        distance: str = Distance.COSINE,
        location: str | None = None,
        url: str | None = None,
        port: int | None = 6333,
        grpc_port: int | None = 6334,
        prefer_grpc: bool = False,
        https: bool | None = None,
        api_key: str | None = None,
        prefix: str | None = None,
        timeout: int | None = None,
        host: str | None = None,
        path: str | None = None,
        force_disable_check_same_thread: bool = False,
        grpc_options: dict[str, Any] | None = None,
        auth_token_provider: Callable[[], str] | Callable[[], Awaitable[str]] | None = None,
        cloud_inference: bool = False,
        local_inference_batch_size: int | None = None,
        check_compatibility: bool = True,
        **kwargs: Any,
    ):
        self.client = QdrantClient(
            location=location,
            url=url,
            port=port,
            grpc_port=grpc_port,
            prefer_grpc=prefer_grpc,
            https=https,
            api_key=api_key,
            prefix=prefix,
            timeout=timeout,
            host=host,
            path=path,
            force_disable_check_same_thread=force_disable_check_same_thread,
            grpc_options=grpc_options,
            auth_token_provider=auth_token_provider,
            cloud_inference=cloud_inference,
            local_inference_batch_size=local_inference_batch_size,
            check_compatibility=check_compatibility,
            **kwargs,
        )

        self.collection_name = collection_name
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance,
                ),
            )

    def upsert(self, vectors: list[Vector]) -> None:
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=vector.id,
                    vector=vector.values,
                    payload=vector.metadata.model_dump(),
                )
                for vector in vectors
            ],
        )

    def search(
        self,
        vector: list[float],
        top_k: int,  # TODO мб переименовать в limit или ...
        workspace_id: str,
    ) -> list[Vector]:
        response: QueryResponse = self.client.query_points(
            collection_name=self.collection_name,
            query=vector,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="workspace_id",
                        match=MatchValue(value=workspace_id),
                    ),
                ],
            ),
            with_payload=True,
            limit=top_k,
        )
        return [
            Vector(
                id=point.id,
                values=point.vector,
                metadata=VectorMetadata(**point.payload),
            )
            for point in response.points
        ]

    def delete(self, workspace_id: str, document_id: str | None = None) -> None:
        must_conditions: list[FieldCondition] = [
            FieldCondition(
                key="workspace_id",
                match=MatchValue(value=workspace_id),
            ),
        ]

        if document_id:
            must_conditions.append(
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id),
                ),
            )

        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(must=must_conditions),
        )
