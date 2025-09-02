from fastapi import Request

from domain.embedding import EmbeddingModel
from domain.text_splitter import TextSplitter
from services import (
    RawStorage,
    VectorStore,
)


async def raw_storage_dependency(request: Request) -> RawStorage:
    """
    Возвращает настроенное хранилище сырых файлов из состояния приложения.
    """

    return request.app.state.raw_storage


async def vector_store_dependency(request: Request) -> VectorStore:
    """
    Возвращает настроенное векторное хранилище из состояния приложения.
    """

    return request.app.state.vector_store


async def embedding_model_dependency(request: Request) -> EmbeddingModel:
    """
    Возвращает настроенную модель эмбеддингов из состояния приложения.
    """

    return request.app.state.embedding_model


async def text_splitter_dependency(request: Request) -> TextSplitter:
    """
    Возвращает настроенный текстовый разделитель из состояния приложения.
    """

    return request.app.state.text_splitter
