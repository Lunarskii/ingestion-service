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
)


router = APIRouter(prefix="/chat")


@router.post("/ask")
async def ask_llm(
    question: ChatRequest,
    chat_service: Annotated[ChatService, Depends(chat_service_dependency)],
) -> ChatResponse:
    """
    Принимает вопрос пользователя и ID рабочего пространства, находит релевантные документы в векторном
    хранилище и генерирует ответ на основе найденного контекста.
    """

    return chat_service.ask(question)
