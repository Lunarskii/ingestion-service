from typing import (
    Any,
    Awaitable,
    Callable,
    Literal,
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
from qdrant_client.http.exceptions import ApiException

from app.interfaces import VectorStorage
from app.types import (
    VectorPayload,
    Vector,
    ScoredVector,
)
from app.core import logger
from app.utils.sequence import chunked


class QdrantVectorStorage(VectorStorage):
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
        grpc_port: int = 6334,
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
        :param vector_size: Размерность векторов (число измерений).
        :param distance: Функция расстояния (см. :class:`Distance`).
        :param location: Локация (для облачных развёртываний).
        :param url: URL сервера Qdrant, опционально.
        :param port: HTTP-порт (по умолчанию 6333).
        :param grpc_port: gRPC-порт (по умолчанию 6334).
        :param prefer_grpc: Предпочитать gRPC соединение, если доступно.
        :param https: Использовать HTTPS (если применимо).
        :param api_key: API-ключ для доступа (если требуется).
        :param prefix: Префикс URL (если используется).
        :param timeout: Таймаут запросов (секунды), опционально.
        :param host: Хост (альтернативный способ указания адреса).
        :param path: Путь (альтернативный способ указания адреса).
        :param force_disable_check_same_thread: Флаг для клиента Qdrant.
        :param grpc_options: Опции для gRPC (словарь), опционально.
        :param auth_token_provider: Callable, возвращающий токен (может быть асинхронным).
        :param cloud_inference: Включить облачные опции инференса, если применимо.
        :param local_inference_batch_size: Размер батча для локального инференса.
        :param check_compatibility: Проверять ли совместимость версии клиента/сервера.
        :param kwargs: Дополнительные параметры, которые будут переданы в :class:`QdrantClient`.
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

        self._logger = logger.bind(
            url=url,
            host=host,
            path=path,
            port=port,
            grpc_port=grpc_port,
            collection_name=collection_name,
        )

        if not self.client.collection_exists(self.collection_name):
            try:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=distance,
                    ),
                )
            except ApiException as e:
                self._logger.warning(
                    f"Произошла ошибка при создании коллекции: возможно, коллекция '{collection_name}' уже создана",
                    error_message=str(e),
                )

    def upsert(
        self,
        vectors: list[Vector],
        *,
        batch_size: int = 500,
    ) -> None:
        """
        Добавляет или обновляет список векторов в коллекции.

        :param vectors: Список векторов для индексации.
        :param batch_size: Количество точек, вставляемых за один раз.

        :raises ApiException: Пробрасывает исключения QdrantClient в случае ошибок выполнения.
        """

        points: list[PointStruct] = [
            PointStruct(
                id=vector.id,
                vector=vector.values,
                payload=vector.payload.model_dump(),
            )
            for vector in vectors
        ]
        try:
            for chunk in chunked(points, batch_size):
                self.client.upsert(self.collection_name, chunk)
        except ApiException as e:
            self._logger.error(
                "Произошла ошибка при обновлении или вставке новой точки в коллекцию",
                error_message=str(e),
            )
            raise

    # TODO
    """
    1. Вместе с векторами должен возвращаться score (счет по схожести) - DONE
    2. Попробовать убрать сохранение текста в точках векторного хранилища, вместо этого дать айдишку на нужные данные в хранилище, например SilverStorage
    """
    def search(
        self,
        embedding: list[float],
        top_k: int | Literal["all"],
        workspace_id: str,
        *,
        score_threshold: float | None = 0.35,
    ) -> list[ScoredVector]:
        """
        Выполняет поиск ближайших векторов по переданному эмбеддингу.

        :param embedding: Вектор-запрос для поиска похожих чанков.
        :param top_k: Максимальное число возвращаемых результатов.
        :param workspace_id: Значение фильтра workspace_id (используется в payload).
        :param score_threshold: Минимальный порог оценки для результата. Если он задан,
                                менее похожие результаты не будут возвращены. Оценка
                                возвращаемого результата может быть выше или меньше
                                порогового значения в зависимости от используемой
                                функции расстояния. Например, для косинусного
                                сходства будут возвращены только более высокие оценки.

        :return: Список найденных векторов.
        :raises ApiException: Пробрасывает исключения QdrantClient в случае ошибок выполнения.
        """

        try:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="workspace_id",
                        match=MatchValue(value=workspace_id),
                    ),
                ],
            )

            if isinstance(top_k, int):
                response: QueryResponse = self.client.query_points(
                    collection_name=self.collection_name,
                    query=embedding,
                    query_filter=query_filter,
                    with_vectors=True,
                    with_payload=True,
                    limit=top_k,
                    score_threshold=score_threshold,
                )
                return [
                    ScoredVector(
                        id=point.id,
                        values=point.vector,
                        payload=VectorPayload(**point.payload),
                        score=point.score,
                    )
                    for point in response.points
                ]

            vectors: list[ScoredVector] = []
            top_k = 500
            offset: int = 0

            while True:
                response: QueryResponse = self.client.query_points(
                    collection_name=self.collection_name,
                    query=embedding,
                    query_filter=query_filter,
                    with_vectors=True,
                    with_payload=True,
                    limit=top_k,
                    offset=offset,
                    score_threshold=score_threshold,
                )
                for point in response.points:
                    vectors.append(
                        ScoredVector(
                            id=point.id,
                            values=point.vector,
                            payload=VectorPayload(**point.payload),
                            score=point.score,
                        ),
                    )
                if len(response.points) < top_k:
                    break
                offset += top_k

            return vectors
        except ApiException as e:
            self._logger.error(
                "Произошла ошибка при поиске подходящих точек в коллекции",
                workspace_id=workspace_id,
                top_k=top_k,
                error_message=str(e)
            )
            raise

    def delete(self, workspace_id: str, document_id: str) -> None:
        """
        Удаляет точки из коллекции по фильтру.

        :param workspace_id: Идентификатор рабочего пространства для фильтрации точек.
        :param document_id: Идентификатор документа для фильтрации точек.

        :raises ApiException: Пробрасывает исключения QdrantClient в случае ошибок выполнения.
        """

        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="workspace_id",
                            match=MatchValue(value=workspace_id),
                        ),
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id),
                        ),
                    ],
                ),
            )
        except ApiException as e:
            self._logger.error(
                "Произошла ошибка при удалении точек из коллекции",
                workspace_id=workspace_id,
                document_id=document_id,
                error_message=str(e),
            )

    def delete_by_workspace(self, workspace_id: str) -> None:
        """
        Удаляет точки из коллекции по фильтру.

        :param workspace_id: Идентификатор рабочего пространства для фильтрации точек.

        :raises ApiException: Пробрасывает исключения QdrantClient в случае ошибок выполнения.
        """

        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="workspace_id",
                            match=MatchValue(value=workspace_id),
                        ),
                    ],
                ),
            )
        except ApiException as e:
            self._logger.error(
                "Произошла ошибка при удалении точек из коллекции",
                workspace_id=workspace_id,
                error_message=str(e),
            )
