from sentence_transformers import SentenceTransformer

from domain.chat.schemas import (
    ChatRequest,
    ChatResponse,
    Source,
    ChatMessageDTO,
    ChatRole,
    ChatSessionDTO,
    ChatMessageSourceDTO,
)
from domain.chat.repositories import (
    ChatSessionRepository,
    ChatMessageRepository,
    ChatMessageSourceRepository,
)
from domain.chat.exceptions import (
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
    """
    Сервис для управления чат-сессиями.
    """

    def __init__(
        self,
        repository: ChatSessionRepository,
    ):
        """
        :param repository: Экземпляр репозитория для работы с чат-сессиями.
        :type repository: ChatSessionRepository
        """

        self.repository = repository

    async def create(self, workspace_id: str) -> ChatSessionDTO:
        """
        Создаёт новую чат-сессию для указанного рабочего пространства.

        :param workspace_id: Идентификатор рабочего пространства.
        :type workspace_id: str
        :return: Созданная сессия в виде DTO.
        :rtype: ChatSessionDTO
        :raises ChatSessionCreationError: В случае ошибки при создании сессии.
        """

        try:
            session = ChatSessionDTO(workspace_id=workspace_id)
            session = await self.repository.create(**session.model_raw_dump())
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
        """
        Возвращает список чат-сессий для указанного рабочего пространства.

        :param workspace_id: Идентификатор рабочего пространства.
        :type workspace_id: str
        :return: Список DTO сессий.
        :rtype: list[ChatSessionDTO]
        :raises ChatSessionRetrivalError: Если произошла ошибка при получении списка.
        """

        try:
            sessions: list[ChatSessionDTO] = await self.repository.get_n(
                workspace_id=workspace_id
            )
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
    """
    Сервис для управления сообщениями внутри чат-сессий.
    """

    def __init__(
        self,
        repository: ChatMessageRepository,
    ):
        """
        :param repository: Экземпляр репозитория для работы с сообщениями.
        :type repository: ChatMessageRepository
        """

        self.repository = repository

    async def create(
        self,
        session_id: str,
        role: ChatRole,
        content: str,
    ) -> ChatMessageDTO:
        """
        Создаёт новое сообщение в заданной сессии и возвращает его DTO.

        :param session_id: Идентификатор чат-сессии.
        :type session_id: str
        :param role: Роль автора сообщения.
        :type role: ChatRole
        :param content: Текст сообщения.
        :type content: str
        :returns: Созданное сообщение в виде DTO.
        :rtype: ChatMessageDTO
        :raises ChatMessageCreationError: В случае ошибки при создании сообщения.
        """

        try:
            message = ChatMessageDTO(
                session_id=session_id,
                role=role,
                content=content,
            )
            message = await self.repository.create(**message.model_raw_dump())
        except Exception as e:
            logger.error(
                ChatMessageCreationError.message,
                session_id=session_id,
                error_message=str(e),
            )
            raise ChatMessageCreationError()
        else:
            return message

    async def messages(self, session_id: str) -> list[ChatMessageDTO]:
        """
        Возвращает полную историю сообщений для указанной чат-сессии.

        :param session_id: Идентификатор чат-сессии.
        :type session_id: str
        :return: Список сообщений в хронологическом порядке в виде списка DTO.
        :rtype: list[ChatMessageDTO]
        :raises ChatMessageRetrievalError: Если произошла ошибка при получении списка сообщений.
        """

        try:
            messages: list[ChatMessageDTO] = await self.repository.chat_history(
                session_id=session_id
            )
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
        """
        Возвращает последние ``n`` сообщений для указанной сессии.

        :param session_id: Идентификатор чат-сессии.
        :type session_id: str
        :param n: Количество сообщений для выборки.
        :type n: int
        :return: Список последних сообщений (в порядке от новых к старым) в виде списка DTO.
        :rtype: list[ChatMessageDTO]
        :raises ChatMessageRetrievalError: Если произошла ошибка при получении списка сообщений.
        """

        try:
            messages: list[
                ChatMessageDTO
            ] = await self.repository.fetch_recent_messages(
                session_id=session_id,
                n=n,
            )
        except Exception as e:
            error_message: str = (
                "Не удалось получить список последних n сообщений из чат-сессии"
            )
            logger.error(
                error_message,
                session_id=session_id,
                n=n,
                error_message=str(e),
            )
            raise ChatMessageRetrievalError(error_message)
        else:
            return messages


class ChatMessageSourceService:
    def __init__(
        self,
        repository: ChatMessageSourceRepository,
    ):
        self.repository = repository

    async def sources(self, message_id: str) -> list[ChatMessageSourceDTO]:
        try:
            sources: list[ChatMessageSourceDTO] = await self.repository.get_n(message_id=message_id)
        except Exception as e:
            ...
        else:
            return sources


class RAGService:
    """
    Сервис, реализующий RAG-подход (Retrieval-Augmented Generation) для ответа на вопросы
    с использованием векторного поиска и LLM.

    Основные шаги по обработке запроса:
        1. Векторизация вопроса с помощью `embedding_model`.
        2. Получение релевантных источников из `vector_store`.
        3. Формирование промпта с контекстом (источники + последние сообщения).
        4. Получение ответа от LLM и сохранение сообщений в базе данных.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_model: SentenceTransformer,
        session_service: ChatSessionService,
        message_service: ChatMessageService,
    ):
        """
        :param vector_store: Сервис векторного поиска/хранения.
        :type vector_store: VectorStore
        :param embedding_model: Модель для кодирования входных вопросов в векторы.
        :type embedding_model: SentenceTransformer
        :param session_service: Сервис управления чат-сессиями.
        :type session_service: ChatSessionService
        :param message_service: Сервис управления сообщениями чата.
        :type message_service: ChatMessageService
        """

        self.vector_store = vector_store
        self.embedding_model = embedding_model
        self.session_service = session_service
        self.message_service = message_service

    async def ask(self, request: ChatRequest) -> ChatResponse:
        """
        Обрабатывает входящий запрос и возвращает сгенерированный ответ и список источников.

        Пайплайн:
            1. Создание/получение чат-сессии (если ``session_id`` отсутствует).
            2. Векторизация вопроса.
            3. Поиск релевантных документов (источников).
            4. Формирование промпта и получение ответа от LLM.
            5. Сохранение ``user/assistant`` сообщений в БД.
            6. Формирование ответа.

        :param request: Схема запроса.
        :type request: ChatRequest
        :return: Ответ в виде :class:`ChatResponse`, содержащий текст ответа, источники и session_id.
        :rtype: ChatResponse
        :raises RAGError: При любых ошибках внутри RAG-пайплайна.
        """

        if not request.session_id:
            session = await self.session_service.create(request.workspace_id)
            request.session_id = session.id

        context_logger = logger.bind(
            workspace_id=request.workspace_id, session_id=request.session_id
        )

        try:
            context_logger.info("Векторизация вопроса")
            question_vector: list[float] = self.embedding_model.encode(
                request.question
            ).tolist()

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
            session_id=request.session_id,
            role=ChatRole.user,
            content=request.question,
        )
        await self.message_service.create(
            session_id=request.session_id,
            role=ChatRole.assistant,
            content=answer,
        )

        return ChatResponse(
            answer=answer,
            sources=sources,
            session_id=request.session_id,
        )

    def _generate_sources(
        self, vector: list[float], top_k: int, workspace_id: str
    ) -> list[Source]:
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
        recent_messages: list[
            ChatMessageDTO
        ] = await self.message_service.recent_messages(
            session_id=session_id,
            n=4,
        )  # TODO мб нужно как-то вынести n
        message_context: str = "\n".join(
            [message.content for message in recent_messages]
        )

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
