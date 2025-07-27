from functools import lru_cache

from sentence_transformers import SentenceTransformer

from domain.chat.service import ChatService
from domain.fhandler.dependencies import (
    get_vector_store,
    get_embedding_model,
)
from services import VectorStore


@lru_cache
def get_chat_service(
    vector_store: VectorStore = get_vector_store(),
    embedding_model: SentenceTransformer = get_embedding_model(),
) -> ChatService:
    return ChatService(
        vector_store=vector_store,
        embedding_model=embedding_model,
    )
