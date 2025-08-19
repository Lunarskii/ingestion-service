from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    status,
)

from api.v1.dependencies import (
    chat_session_service_dependency,
    chat_message_service_dependency,
    rag_service_dependency,
)
from domain.chat.service import (
    ChatSessionService,
    ChatMessageService,
    RAGService,
)
from domain.chat.schemas import (
    ChatRequest,
    ChatResponse,
    ChatSessionDTO,
    ChatMessageDTO,
)


router = APIRouter(prefix="/chat")


@router.get("", status_code=status.HTTP_200_OK)
async def chats(
    workspace_id: str,
    service: Annotated[ChatSessionService, Depends(chat_session_service_dependency)],
) -> list[ChatSessionDTO]:
    """
    Возвращает список чат-сессий для заданного рабочего пространства.
    """

    return await service.sessions(workspace_id)


@router.post("/ask", status_code=status.HTTP_200_OK)
async def ask_llm(
    question: ChatRequest,
    service: Annotated[RAGService, Depends(rag_service_dependency)],
) -> ChatResponse:
    """
    Принимает вопрос пользователя, выполняет RAG-процесс и возвращает ответ с источниками.
    """

    return await service.ask(question)


# TODO добавить в path ("session_id") required==True
@router.get("/{session_id}/messages", status_code=status.HTTP_200_OK)
async def chat_history(
    session_id: str,
    service: Annotated[ChatMessageService, Depends(chat_message_service_dependency)],
) -> list[ChatMessageDTO]:
    """
    Возвращает историю сообщений указанной чат-сессии в хронологическом порядке.
    """

    return await service.messages(session_id)
