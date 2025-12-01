from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
)

from app.domain.chat.service import (
    RAGService,
    ChatService,
)
from app.domain.chat.schemas import (
    ChatMessage,
    ChatSession,
    RAGRequest,
    RAGResponse,
)
from app.domain.chat.dependencies import (
    rag_service_dependency,
    chat_service_dependency,
)
from app import status


router = APIRouter(prefix="/chat")


@router.get("", status_code=status.HTTP_200_OK)
async def chats(
    workspace_id: str,
    service: Annotated[ChatService, Depends(chat_service_dependency)],
) -> list[ChatSession]:
    """
    Возвращает список чат-сессий для заданного рабочего пространства.
    """

    return await service.get_sessions(workspace_id)


@router.post("/ask", status_code=status.HTTP_200_OK)
async def ask(
    request: RAGRequest,
    service: Annotated[RAGService, Depends(rag_service_dependency)],
) -> RAGResponse:
    """
    Принимает вопрос пользователя, выполняет RAG-процесс и возвращает ответ с источниками.
    """

    return await service.ask(request)


@router.get("/{session_id}/messages", status_code=status.HTTP_200_OK)
async def chat_history(
    session_id: str,
    service: Annotated[ChatService, Depends(chat_service_dependency)],
) -> list[ChatMessage]:
    """
    Возвращает историю сообщений указанной чат-сессии в хронологическом порядке.
    """

    return await service.get_messages(session_id)
