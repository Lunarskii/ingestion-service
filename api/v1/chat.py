from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    status,
)

from api.v1.dependencies import rag_service_dependency
from domain.chat.dependencies import chat_uow_dependency
from domain.chat.service import RAGService
from domain.chat.repositories import (
    ChatSessionRepository,
    ChatMessageRepository,
    ChatMessageSourceRepository,
)
from domain.chat.schemas import (
    ChatMessageSource,
    ChatMessage,
    ChatSession,
    RAGRequest,
    RAGResponse,
    ChatSessionDTO,
    ChatMessageDTO,
    ChatMessageSourceDTO,
)
from domain.database.uow import UnitOfWork


router = APIRouter(prefix="/chat")


@router.get("", status_code=status.HTTP_200_OK)
async def chats(
    workspace_id: str,
    uow: Annotated[UnitOfWork, Depends(chat_uow_dependency)],
) -> list[ChatSession]:
    """
    Возвращает список чат-сессий для заданного рабочего пространства.
    """

    chat_session_repo = uow.get_repository(ChatSessionRepository)
    sessions: list[ChatSessionDTO] = await chat_session_repo.get_n(workspace_id=workspace_id)
    return [
        ChatSession(
            id=session.id,
            workspace_id=session.workspace_id,
            created_at=session.created_at,
        )
        for session in sessions
    ]


@router.post("/ask", status_code=status.HTTP_200_OK)
async def ask(
    request: RAGRequest,
    service: Annotated[RAGService, Depends(rag_service_dependency)],
    uow: Annotated[UnitOfWork, Depends(chat_uow_dependency)],
) -> RAGResponse:
    """
    Принимает вопрос пользователя, выполняет RAG-процесс и возвращает ответ с источниками.
    """

    return await service.ask(request, uow)


@router.get("/{session_id}/messages", status_code=status.HTTP_200_OK)
async def chat_history(
    session_id: str,
    uow: Annotated[UnitOfWork, Depends(chat_uow_dependency)],
) -> list[ChatMessage]:
    """
    Возвращает историю сообщений указанной чат-сессии в хронологическом порядке.
    """

    messages: list[ChatMessage] = []

    chat_message_repo = uow.get_repository(ChatMessageRepository)
    chat_message_source_repo = uow.get_repository(ChatMessageSourceRepository)

    messages_dto: list[ChatMessageDTO] = await chat_message_repo.get_messages(session_id)
    for message in messages_dto:
        sources: list[ChatMessageSourceDTO] = await chat_message_source_repo.get_n(message_id=message.id)
        messages.append(
            ChatMessage(
                id=message.id,
                session_id=message.session_id,
                role=message.role,
                content=message.content,
                sources=[
                    ChatMessageSource(
                        source_id=source.source_id,
                        document_name=source.document_name,
                        page_start=source.page_start,
                        page_end=source.page_end,
                        snippet=source.snippet,
                    )
                    for source in sources
                ],
                created_at=message.created_at,
            ),
        )

    return messages
