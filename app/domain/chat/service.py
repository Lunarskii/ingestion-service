from app.domain.embedding.base import EmbeddingModel
from app.domain.chat.schemas import (
    RAGRequest,
    RAGResponse,
    ChatMessageSource,
    ChatMessageDTO,
    ChatRole,
    ChatSessionDTO,
)
from app.domain.chat.repositories import (
    ChatSessionRepository,
    ChatMessageRepository,
    ChatMessageSourceRepository,
)
from app.domain.chat.exceptions import RAGError
from app.domain.database.uow import UnitOfWork
from app.domain.embedding.schemas import Vector
from app.stubs import llm_stub
from app.services import VectorStore
from config import logger


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
        embedding_model: EmbeddingModel,
    ):
        """
        :param vector_store: Сервис векторного поиска/хранения.
        :type vector_store: VectorStore
        :param embedding_model: Модель для кодирования входных вопросов в векторы.
        :type embedding_model: SentenceTransformer
        """

        self.vector_store = vector_store
        self.embedding_model = embedding_model

    async def ask(
        self,
        request: RAGRequest,
        uow: UnitOfWork,
    ) -> RAGResponse:
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
        :type request: RAGRequest
        :param uow: UnitOfWork - менеджер транзакции и фабрика репозиториев.
        :type uow: UnitOfWork
        :return: Ответ в виде :class:`RAGResponse`, содержащий текст ответа, источники и session_id.
        :rtype: RAGResponse
        :raises RAGError: При любых ошибках внутри RAG-пайплайна.
        """

        if not request.session_id:
            chat_sessions_repo = uow.get_repository(ChatSessionRepository)
            session: ChatSessionDTO = await chat_sessions_repo.create(
                workspace_id=request.workspace_id,
            )
            request.session_id = session.id

        context_logger = logger.bind(
            workspace_id=request.workspace_id,
            session_id=request.session_id,
        )

        try:
            context_logger.info("Векторизация вопроса")
            embedding: list[float] = self.embedding_model.encode(
                sentences=request.question,
            )

            context_logger.info("Формирование списка источников")
            sources: list[ChatMessageSource] = self._generate_sources(
                embedding=embedding,
                top_k=request.top_k,
                workspace_id=request.workspace_id,
            )

            context_logger.info("Формирование контекста для LLM")
            prompt: str = await self._generate_prompt(
                uow=uow,
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
        chat_message_repo = uow.get_repository(ChatMessageRepository)
        await chat_message_repo.create(
            session_id=request.session_id,
            role=ChatRole.user,
            content=request.question,
        )
        assistant_message: ChatMessageDTO = await chat_message_repo.create(
            session_id=request.session_id,
            role=ChatRole.assistant,
            content=answer,
        )

        context_logger.info("Сохранение источников ответа в базе данных")
        chat_message_source_repo = uow.get_repository(ChatMessageSourceRepository)
        for source in sources:
            await chat_message_source_repo.create(
                source_id=source.source_id,
                message_id=assistant_message.id,
                document_name=source.document_name,
                page_start=source.page_start,
                page_end=source.page_end,
                snippet=source.snippet,
            )

        return RAGResponse(
            answer=answer,
            sources=sources,
            session_id=request.session_id,
        )

    def _generate_sources(
        self,
        embedding: list[float],
        top_k: int,
        workspace_id: str,
    ) -> list[ChatMessageSource]:
        """
        Преобразует результаты поиска в список источников.

        :param embedding: Вектор запроса.
        :type embedding: list[float]
        :param top_k: Максимальное количество возвращаемых источников.
        :type top_k: int
        :param workspace_id: Идентификатор рабочего пространства.
        :type workspace_id: str
        :return: Список источников.
        :rtype: list[ChatMessageSource]
        """

        retrieved_vectors: list[Vector] = self.vector_store.search(
            embedding=embedding,
            top_k=top_k,
            workspace_id=workspace_id,
        )
        return [
            ChatMessageSource(
                source_id=vector.metadata.document_id,
                document_name=vector.metadata.document_name,
                page_start=vector.metadata.page_start,
                page_end=vector.metadata.page_end,
                snippet=vector.metadata.text,
            )
            for vector in retrieved_vectors
        ]

    async def _generate_prompt(
        self,
        uow: UnitOfWork,
        session_id: str,
        question: str,
        sources: list[ChatMessageSource] | None = None,
    ) -> str:
        """
        Составляет текст промпта для LLM на основе найденных фрагментов и истории чата.

        Описание
        --------
        * Получает последние сообщения из репозитория сообщений ``ChatMessageRepository``.
        * Собирает текстовые сниппеты найденных источников и историю сообщений.
        * Склеивает их в итоговый промпт, который предназначен для передачи в LLM.

        :param uow: UnitOfWork для доступа к репозиторию сообщений.
        :type uow: UnitOfWork
        :param session_id: Идентификатор текущей сессии.
        :type session_id: str
        :param question: Текст вопроса.
        :type question: str
        :param sources: Список источников.
        :type sources: list[ChatMessageSource] | None
        :return: Текст промпта.
        :rtype: str

        :note:
            Текущее ограничение количества сообщений из истории сообщений задано хардкодом (`limit=4`).
            Можно вынести в параметр конфигурации при необходимости.
        """

        source_context: str = "\n".join([source.snippet for source in sources])
        chat_message_repo: ChatMessageRepository = uow.get_repository(
            ChatMessageRepository
        )
        recent_messages: list[
            ChatMessageDTO
        ] = await chat_message_repo.get_recent_messages(
            session_id=session_id,
            limit=4,
        )  # TODO мб нужно как-то вынести limit (n)
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
