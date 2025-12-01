from app.domain.chat.service import (
    RAGService,
    ChatService,
)


async def rag_service_dependency() -> RAGService:
    """
    Создаёт и возвращает экземпляр сервиса :class:`RAGService`.
    """

    return RAGService()


async def chat_service_dependency() -> ChatService:
    return ChatService()
