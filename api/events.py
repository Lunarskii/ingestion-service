from typing import (
    TYPE_CHECKING,
    Coroutine,
)
from functools import partial
import asyncio

from domain.embedding import EmbeddingModel
from domain.text_splitter import TextSplitter
from infrastructure.storage_minio import MinIORawStorage
from infrastructure.vectorstore_qdrant import QdrantVectorStore
from stubs import (
    FileRawStorage,
    JSONVectorStore,
)
from config import settings
from utils.singleton import singleton_registry


if TYPE_CHECKING:
    from fastapi import FastAPI


async def on_startup_event_handler(app: "FastAPI") -> None:
    """
    Инициализирует внешние сервисы и сохраняет их в ``app.state``.

    Инициализация выполняется параллельно через ``asyncio.to_thread`` + ``asyncio.gather``
    для избежания блокировки основного ивент-лупа.

    :param app: Экземпляр FastAPI, в котором будут установлены состояния.
    :type app: FastAPI
    """

    def __init_object(cls, *args, **kwargs) -> Coroutine:
        return asyncio.to_thread(
            partial(
                cls,
                *args,
                **kwargs,
            )
        )

    if settings.minio.is_configured:
        raw_storage_coro = __init_object(
            MinIORawStorage,
            endpoint=settings.minio.endpoint,
            bucket_name=settings.minio.bucket_raw,
            access_key=settings.minio.access_key,
            secret_key=settings.minio.secret_key,
            session_token=settings.minio.session_token,
            secure=settings.minio.secure,
            region=settings.minio.region,
        )
    else:
        raw_storage_coro = __init_object(FileRawStorage)

    if settings.qdrant.is_configured:
        vector_store_coro = __init_object(
            QdrantVectorStore,
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
    else:
        vector_store_coro = __init_object(JSONVectorStore)

    tasks: list[Coroutine] = [
        raw_storage_coro,
        vector_store_coro,
        __init_object(
            EmbeddingModel,
            model_name_or_path=settings.embedding.model_name,
            device=settings.embedding.device,
            cache_folder=settings.embedding.cache_folder,
            token=settings.embedding.token,
            max_concurrency=settings.embedding.max_concurrency,
        ),
        __init_object(
            TextSplitter,
            chunk_size=settings.text_splitter.chunk_size,
            chunk_overlap=settings.text_splitter.chunk_overlap,
        ),
    ]

    (
        raw_storage,
        vector_store,
        embedding_model,
        text_splitter,
    ) = await asyncio.gather(*tasks)

    app.state.raw_storage = raw_storage  # type: ignore[attr-defined]
    app.state.vector_store = vector_store  # type: ignore[attr-defined]
    app.state.embedding_model = embedding_model  # type: ignore[attr-defined]
    app.state.text_splitter = text_splitter  # type: ignore[attr-defined]


async def on_shutdown_event_handler(app: "FastAPI") -> None:
    await singleton_registry.close_all()


def setup_event_handlers(app: "FastAPI") -> None:
    """
    Регистрирует обработчики событий приложения.
    """

    app.add_event_handler("startup", partial(on_startup_event_handler, app))
    app.add_event_handler("shutdown", partial(on_shutdown_event_handler, app))
