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
    ChatError,
    ChatSessionCreationError,
    ChatMessageCreationError,
)
from domain.schemas import Vector
from stubs import llm_stub
from services import VectorStore
from services.exc import VectorStoreDocumentsNotFound
from config import logger


# TODO обновить доку
class ChatService:
    """
    Управляет RAG-логикой для ответов на вопросы.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_model: SentenceTransformer,
        chat_session_repository: ChatSessionRepository,
        chat_message_repository: ChatMessageRepository,
    ):
        self.vector_store = vector_store
        self.embedding_model = embedding_model
        self.chat_session_repository = chat_session_repository
        self.chat_message_repository = chat_message_repository

    async def ask(self, request: ChatRequest) -> ChatResponse:
        """
        Обрабатывает запрос в чат с помощью RAG-логики.
            1. Векторизует вопрос.
            2. Запрашивает в хранилище векторов соответствующие вектора с фильтром по 'workspace_id'.
            3. Формирует контекст для LLM.
            4. Генерирует ответ, используя LLM.
            5. Формирует ответ.
        """

        if not request.session_id:
            session = await self.create_session(request.workspace_id)
            request.session_id = session.id

        context_logger = logger.bind(workspace_id=request.workspace_id, session_id=request.session_id)

        try:
            context_logger.info("Векторизация вопроса")
            question_vector: list[float] = self.embedding_model.encode(request.question).tolist()

            context_logger.info("Поиск top_k чанков в VectorStore", top_k=request.top_k)
            retrieved_vectors: list[Vector] = self.vector_store.search(
                vector=question_vector,
                top_k=request.top_k,
                workspace_id=request.workspace_id,
            )

            sources: list[Source] = [
                Source(
                    source_id=vector.metadata.document_id,
                    document_name=vector.metadata.document_name,
                    document_page=vector.metadata.document_page,
                    snippet=vector.metadata.text,
                )
                for vector in retrieved_vectors
            ]

            context_logger.info("Формирование контекста для LLM")
            prompt: str = await self.generate_prompt(
                session_id=request.session_id,
                question=request.question,
                sources=sources,
            )

            context_logger.info("Получение ответа от LLM")
            answer: str = llm_stub.generate(prompt)

            context_logger.info("Сохранение сообщений в базе данных")
            await self.create_message(
                workspace_id=request.workspace_id,
                session_id=request.session_id,
                role=ChatRole.user,
                content=request.question,
            )
            await self.create_message(
                workspace_id=request.workspace_id,
                session_id=request.session_id,
                role=ChatRole.assistant,
                content=answer,
            )
        except VectorStoreDocumentsNotFound as e:
            context_logger.error(ChatError.message, error_message=e.message)
            raise VectorStoreDocumentsNotFound(e.message)
        except Exception as e:
            context_logger.error(ChatError.message, error_message=str(e))
            raise ChatError()
        else:
            return ChatResponse(
                answer=answer,
                sources=sources,
                session_id=request.session_id,
            )

    async def generate_prompt(
        self,
        session_id: str,
        question: str,
        sources: list[Source] | None = None,
    ) -> str:
        source_context: str = "\n".join([source.snippet for source in sources])
        recent_messages: list[ChatMessageDTO] = await self.chat_message_repository.fetch_recent_messages(
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

    async def create_session(self, workspace_id: str) -> ChatSessionDTO:
        try:
            session = ChatSessionDTO(workspace_id=workspace_id)
            session = await self.chat_session_repository.create(**session.model_dump())
        except Exception as e:
            logger.error(
                ChatSessionCreationError.message,
                workspace_id=workspace_id,
                error_message=str(e),
            )
            raise ChatSessionCreationError()
        else:
            return session

    async def create_message(
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
            message = await self.chat_message_repository.create(**message.model_dump())
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

    async def chats(self, workspace_id: str) -> list[ChatSessionDTO]:
        return await self.chat_session_repository.get_n(workspace_id=workspace_id)

    async def messages(self, session_id: str) -> list[ChatMessageDTO]:
        return await self.chat_message_repository.chat_history(session_id=session_id)
