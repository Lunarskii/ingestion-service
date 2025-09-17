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

from app.services import VectorStore
from app.domain.embedding import (
    Vector,
    VectorMetadata,
)


class QdrantVectorStore(VectorStore):
    """
    Реализация интерфейса :class:`VectorStore` на базе векторного хранилища Qdrant.
    """

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
        auth_token_provider: Callable[[], str]
        | Callable[[], Awaitable[str]]
        | None = None,
        cloud_inference: bool = False,
        local_inference_batch_size: int | None = None,
        check_compatibility: bool = True,
        **kwargs: Any,
    ):
        """
        :param collection_name: Имя коллекции.
        :type collection_name: str
        :param vector_size: Размерность векторов (число измерений).
        :type vector_size: int
        :param distance: Функция расстояния (см. :class:`Distance`).
        :type distance: str
        :param location: Локация (для облачных развёртываний).
        :type location: str | None
        :param url: URL сервера Qdrant, опционально.
        :type url: str | None
        :param port: HTTP-порт (по умолчанию 6333).
        :type port: int | None
        :param grpc_port: gRPC-порт (по умолчанию 6334).
        :type grpc_port: int | None
        :param prefer_grpc: Предпочитать gRPC соединение, если доступно.
        :type prefer_grpc: bool
        :param https: Использовать HTTPS (если применимо).
        :type https: bool | None
        :param api_key: API-ключ для доступа (если требуется).
        :type api_key: str | None
        :param prefix: Префикс URL (если используется).
        :type prefix: str | None
        :param timeout: Таймаут запросов (секунды), опционально.
        :type timeout: int | None
        :param host: Хост (альтернативный способ указания адреса).
        :type host: str | None
        :param path: Путь (альтернативный способ указания адреса).
        :type path: str | None
        :param force_disable_check_same_thread: Флаг для клиента Qdrant.
        :type force_disable_check_same_thread: bool
        :param grpc_options: Опции для gRPC (словарь), опционально.
        :type grpc_options: dict[str, Any] | None
        :param auth_token_provider: Callable, возвращающий токен (может быть асинхронным).
        :type auth_token_provider: Callable[[], str] | Callable[[], Awaitable[str]] | None
        :param cloud_inference: Включить облачные опции инференса, если применимо.
        :type cloud_inference: bool
        :param local_inference_batch_size: Размер батча для локального инференса.
        :type local_inference_batch_size: int | None
        :param check_compatibility: Проверять ли совместимость версии клиента/сервера.
        :type check_compatibility: bool
        :param kwargs: Дополнительные параметры, которые будут переданы в :class:`QdrantClient`.
        :type kwargs: Any
        """

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
        """
        Добавляет или обновляет список векторов в коллекции.

        :param vectors: Список векторов для индексации.
        :type vectors: list[Vector]
        :raises Exception: Пробрасывает исключения QdrantClient в случае ошибок выполнения.
        """

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
        embedding: list[float],
        top_k: int,  # TODO мб переименовать в limit или ...
        workspace_id: str,
    ) -> list[Vector]:
        """
        Выполняет поиск ближайших векторов по переданному эмбеддингу.

        :param embedding: Вектор-запрос для поиска похожих чанков.
        :type embedding: list[float]
        :param top_k: Максимальное число возвращаемых результатов.
        :type top_k: int
        :param workspace_id: Значение фильтра workspace_id (используется в payload).
        :type workspace_id: str
        :return: Список найденных векторов в виде :class:`Vector`.
        :rtype: list[Vector]
        :raises Exception: Пробрасывает исключения QdrantClient в случае ошибок выполнения.
        """

        response: QueryResponse = self.client.query_points(
            collection_name=self.collection_name,
            query=embedding,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="workspace_id",
                        match=MatchValue(value=workspace_id),
                    ),
                ],
            ),
            with_vectors=True,
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
        """
        Удаляет точки из коллекции по фильтру.

        :param workspace_id: Значение workspace_id для фильтрации удаления.
        :type workspace_id: str
        :param document_id: При указании - дополнительно фильтрует по document_id.
        :type document_id: str | None
        :raises Exception: Пробрасывает исключения QdrantClient в случае ошибок выполнения.
        """

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
