from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
)

from api.v1.dependencies import (
    chat_service_dependency,
    chat_session_repository_dependency,
    chat_message_repository_dependency,
)
from domain.chat.service import ChatService
from domain.chat.repositories import (
    ChatSessionRepository,
    ChatMessageRepository,
)
from domain.chat.schemas import (
    ChatRequest,
    ChatResponse,
    ChatSessionDTO,
    ChatMessageDTO,
)


router = APIRouter(prefix="/chat")


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
    repository: Annotated[ChatMessageRepository, Depends(chat_message_repository_dependency)],
) -> list[ChatMessageDTO]:
    return await repository.chat_history(session_id)


@router.get("/")
async def sessions_list(
    workspace_id: str,
    repository: Annotated[ChatSessionRepository, Depends(chat_session_repository_dependency)],
) -> list[ChatSessionDTO]:
    return await repository.get_n(workspace_id=workspace_id)
