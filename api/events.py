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
from config import (
    embedding_settings,
    text_splitter_settings,
)


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

    tasks: list[Coroutine] = [
        __init_object(FileRawStorage),
        __init_object(JSONVectorStore),
        __init_object(SQLiteMetadataRepository),
        __init_object(
            SentenceTransformer,
            model_name_or_path=embedding_settings.model_name,
            device=embedding_settings.device,
            cache_folder=embedding_settings.cache_folder,
            token=embedding_settings.token,
        ),
        __init_object(
            RecursiveCharacterTextSplitter,
            chunk_size=text_splitter_settings.chunk_size,
            chunk_overlap=text_splitter_settings.chunk_overlap,
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
