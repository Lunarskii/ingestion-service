from typing import (
    TYPE_CHECKING,
    Coroutine,
)
from functools import partial
import asyncio

from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter

from stubs import (
    FileRawStorage,
    JSONVectorStore,
    SQLiteMetadataRepository,
)
from infrastructure.storage.minio import MinIORawStorage
from config import settings


if TYPE_CHECKING:
    from fastapi import FastAPI


async def on_startup_event_handler(app: "FastAPI") -> None:
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
            bucket_name=settings.minio.bucket,
            access_key=settings.minio.access_key,
            secret_key=settings.minio.secret_key,
            session_token=settings.minio.session_token,
            secure=settings.minio.secure,
            region=settings.minio.region,
        )
    else:
        raw_storage_coro = __init_object(FileRawStorage)

    tasks: list[Coroutine] = [
        raw_storage_coro,
        __init_object(JSONVectorStore),
        __init_object(SQLiteMetadataRepository),
        __init_object(
            SentenceTransformer,
            model_name_or_path=settings.embedding_model.model_name,
            device=settings.embedding_model.device,
            cache_folder=settings.embedding_model.cache_folder,
            token=settings.embedding_model.token,
        ),
        __init_object(
            RecursiveCharacterTextSplitter,
            chunk_size=settings.text_splitter.chunk_size,
            chunk_overlap=settings.text_splitter.chunk_overlap,
        ),
    ]

    raw_storage, vector_store, metadata_repository, embedding_model, text_splitter = await asyncio.gather(*tasks)

    app.state.raw_storage = raw_storage
    app.state.vector_store = vector_store
    app.state.metadata_repository = metadata_repository
    app.state.embedding_model = embedding_model
    app.state.text_splitter = text_splitter


def setup_event_handlers(app: "FastAPI") -> None:
    app.add_event_handler("startup", lambda: asyncio.create_task(on_startup_event_handler(app)))
