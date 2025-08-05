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
from domain.schemas import Vector
from stubs import llm_stub
from services import VectorStore
from services.exc import VectorStoreDocumentsNotFound
from config import logger


# TODO что будет, если куда либо придет недействительный session_id?
# TODO написать исключение ChatSessionError


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
            try:
                session = await self._create_new_chat_session(request.workspace_id)
            except Exception as e:
                logger.error(
                    "Не удалось создать новую сессию чата",
                    workspace_id=request.workspace_id,
                    error_message=str(e),
                )
                return None
            else:
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

            user_message = ChatMessageDTO(
                session_id=request.session_id,
                role=ChatRole.user,
                content=request.question,
            )
            assistant_message = ChatMessageDTO(
                session_id=request.session_id,
                role=ChatRole.assistant,
                content=answer,
            )

            context_logger.info("Сохранение сообщений в базе данных")
            await self.chat_message_repository.create(**user_message.model_dump())
            await self.chat_message_repository.create(**assistant_message.model_dump())
        except VectorStoreDocumentsNotFound as e:
            context_logger.error("Не удалось обработать запрос к чату", error_message=e.message)
            raise VectorStoreDocumentsNotFound(e.message)
        except Exception as e:
            context_logger.error("Не удалось обработать запрос к чату", error_message=str(e))
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

    async def _create_new_chat_session(self, workspace_id: str) -> ChatSessionDTO:
        session = ChatSessionDTO(workspace_id=workspace_id)
        return await self.chat_session_repository.create(**session.model_dump())
