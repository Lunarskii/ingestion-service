from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
)

from api.v1.dependencies import chat_service_dependency
from domain.chat.service import ChatService
from domain.chat.schemas import (
    ChatRequest,
    ChatResponse,
    ChatSessionDTO,
    ChatMessageDTO,
)


router = APIRouter(prefix="/chat")


@router.get("")
async def chats(
    workspace_id: str,
    service: Annotated[ChatService, Depends(chat_service_dependency)],
) -> list[ChatSessionDTO]:
    return await service.chats(workspace_id)


@router.post("/ask")
async def ask_llm(
    question: ChatRequest,
    service: Annotated[ChatService, Depends(chat_service_dependency)],
) -> ChatResponse:
    """
    Принимает вопрос пользователя и ID рабочего пространства, находит релевантные документы в векторном
    хранилище и генерирует ответ на основе найденного контекста.
    """

    return await service.ask(question)


@router.get("/{session_id}/messages")
async def chat_history(
    session_id: str,
    service: Annotated[ChatService, Depends(chat_service_dependency)],
) -> list[ChatMessageDTO]:
    return await service.messages(session_id)
