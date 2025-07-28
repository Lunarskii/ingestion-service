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
    """
    Создаёт и кэширует единый экземпляр ChatService.

    :param vector_store: Реализация VectorStore для поиска векторов.
    :type vector_store: VectorStore
    :param embedding_model: Модель для создания векторов из текста.
    :type embedding_model: SentenceTransformer
    :return: Готовый экземпляр ChatService.
    :rtype: ChatService
    """

    return ChatService(
        vector_store=vector_store,
        embedding_model=embedding_model,
    )
