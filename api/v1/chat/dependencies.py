from typing import Annotated

from fastapi import Depends

from api.v1.dependencies import (
    vector_store_dependency,
    embedding_model_dependency,
)
from domain.chat.service import RAGService
from domain.embedding import EmbeddingModel
from services import VectorStore


async def rag_service_dependency(
    vector_store: Annotated[VectorStore, Depends(vector_store_dependency)],
    embedding_model: Annotated[EmbeddingModel, Depends(embedding_model_dependency)],
) -> RAGService:
    """
    Создаёт и возвращает экземпляр сервиса :class:`RAGService`.
    """

    return RAGService(
        vector_store=vector_store,
        embedding_model=embedding_model,
    )
