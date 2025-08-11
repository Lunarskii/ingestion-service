from sentence_transformers import SentenceTransformer

from domain.chat.schemas import (
    ChatRequest,
    ChatResponse,
    Source,
    ChatMessageDTO,
    ChatRole,
    ChatSessionDTO,
)
from domain.chat.repositories import (
    ChatSessionRepository,
    ChatMessageRepository,
)
from domain.chat.exc import (
    RAGError,
    ChatSessionCreationError,
    ChatSessionRetrivalError,
    ChatMessageCreationError,
    ChatMessageRetrievalError,
)
from domain.schemas import Vector
from stubs import llm_stub
from services import VectorStore
from config import logger


class ChatSessionService:
    def __init__(
        self,
        repository: ChatSessionRepository,
    ):
        self.repository = repository

    async def create(self, workspace_id: str):
        try:
            session = ChatSessionDTO(workspace_id=workspace_id)
            session = await self.repository.create(**session.model_dump())
        except Exception as e:
            logger.error(
                ChatSessionCreationError.message,
                workspace_id=workspace_id,
                error_message=str(e),
            )
            raise ChatSessionCreationError()
        else:
            return session

    async def sessions(self, workspace_id: str) -> list[ChatSessionDTO]:
        try:
            sessions: list[ChatSessionDTO] = await self.repository.get_n(workspace_id=workspace_id)
        except Exception as e:
            error_message: str = "Не удалось получить список чат-сессий"
            logger.error(
                error_message,
                workspace_id=workspace_id,
                error_message=str(e),
            )
            raise ChatSessionRetrivalError(error_message)
        else:
            return sessions


class ChatMessageService:
    def __init__(
        self,
        repository: ChatMessageRepository,
    ):
        self.repository = repository

    async def create(
        self,
        workspace_id: str,
        session_id: str,
        role: ChatRole,
        content: str,
    ) -> ChatMessageDTO:
        try:
            message = ChatMessageDTO(
                session_id=session_id,
                role=role,
                content=content,
            )
            message = await self.repository.create(**message.model_dump())
        except Exception as e:
            logger.error(
                ChatMessageCreationError.message,
                workspace_id=workspace_id,
                session_id=session_id,
                error_message=str(e),
            )
            raise ChatMessageCreationError()
        else:
            return message

    async def messages(self, session_id: str) -> list[ChatMessageDTO]:
        try:
            messages: list[ChatMessageDTO] = await self.repository.chat_history(session_id=session_id)
        except Exception as e:
            error_message: str = "Не удалось получить список сообщений из чат-сессии"
            logger.error(
                error_message,
                session_id=session_id,
                error_message=str(e),
            )
            raise ChatMessageRetrievalError(error_message)
        else:
            return messages

    async def recent_messages(self, session_id: str, n: int) -> list[ChatMessageDTO]:
        try:
            messages: list[ChatMessageDTO] = await self.repository.fetch_recent_messages(
                session_id=session_id,
                n=n,
            )
        except Exception as e:
            error_message: str = "Не удалось получить список последних n сообщений из чат-сессии"
            logger.error(
                error_message,
                session_id=session_id,
                n=n,
                error_message=str(e),
            )
            raise ChatMessageRetrievalError(error_message)
        else:
            return messages


# TODO обновить доку
class RAGService:
    """
    Управляет RAG-логикой для ответов на вопросы.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_model: SentenceTransformer,
        session_service: ChatSessionService,
        message_service: ChatMessageService,
    ):
        self.vector_store = vector_store
        self.embedding_model = embedding_model
        self.session_service = session_service
        self.message_service = message_service

    async def ask(self, request: ChatRequest) -> ChatResponse:
        """
        Обрабатывает запрос в чат с помощью RAG-логики.
            1. Векторизует вопрос.
            2. Формирует список источников.
            3. Формирует промпт для LLM, используя источники для контекста и вопрос.
            4. Генерирует ответ, используя LLM.
            5. Формирует ответ.
        """

        if not request.session_id:
            session = await self.session_service.create(request.workspace_id)
            request.session_id = session.id

        context_logger = logger.bind(workspace_id=request.workspace_id, session_id=request.session_id)

        try:
            context_logger.info("Векторизация вопроса")
            question_vector: list[float] = self.embedding_model.encode(request.question).tolist()

            context_logger.info("Формирование списка источников")
            sources: list[Source] = self._generate_sources(
                vector=question_vector,
                top_k=request.top_k,
                workspace_id=request.workspace_id,
            )

            context_logger.info("Формирование контекста для LLM")
            prompt: str = await self._generate_prompt(
                session_id=request.session_id,
                question=request.question,
                sources=sources,
            )

            context_logger.info("Получение ответа от LLM")
            answer: str = llm_stub.generate(prompt)
        except Exception as e:
            context_logger.error(RAGError.message, error_message=str(e))
            raise RAGError()

        context_logger.info("Сохранение сообщений в базе данных")
        await self.message_service.create(
            workspace_id=request.workspace_id,
            session_id=request.session_id,
            role=ChatRole.user,
            content=request.question,
        )
        await self.message_service.create(
            workspace_id=request.workspace_id,
            session_id=request.session_id,
            role=ChatRole.assistant,
            content=answer,
        )

        return ChatResponse(
            answer=answer,
            sources=sources,
            session_id=request.session_id,
        )

    def _generate_sources(self, vector: list[float], top_k: int, workspace_id: str) -> list[Source]:
        retrieved_vectors: list[Vector] = self.vector_store.search(
            vector=vector,
            top_k=top_k,
            workspace_id=workspace_id,
        )
        return [
            Source(
                source_id=vector.metadata.document_id,
                document_name=vector.metadata.document_name,
                document_page=vector.metadata.document_page,
                snippet=vector.metadata.text,
            )
            for vector in retrieved_vectors
        ]

    async def _generate_prompt(
        self,
        session_id: str,
        question: str,
        sources: list[Source] | None = None,
    ) -> str:
        source_context: str = "\n".join([source.snippet for source in sources])
        recent_messages: list[ChatMessageDTO] = await self.message_service.recent_messages(
            session_id=session_id,
            n=4,
        )  # TODO мб нужно как-то вынести n
        message_context: str = "\n".join([message.content for message in recent_messages])

        return "\n".join(
            [
                "Основываясь на следующем контексте, ответь на вопрос.",
                "---",
                "Контекст:",
                "\n".join([source_context, message_context]),
                "---",
                "Вопрос:",
                question,
            ],
        )
