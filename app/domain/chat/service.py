from typing import (
    Callable,
    AsyncContextManager,
)
import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.chat.prompt_builder import PromptBuilder
from app.domain.chat.schemas import (
    RAGRequest,
    RAGResponse,
    ChatSession,
    ChatSessionDTO,
    ChatMessage,
    ChatMessageDTO,
    ChatRole,
    RetrievalSource,
    RetrievalChunk,
    RetrievalSourceDTO,
    RetrievalChunkDTO,
)
from app.domain.chat.repositories import (
    ChatSessionRepository,
    ChatMessageRepository,
    RetrievalChunkRepository,
    RetrievalSourceRepository,
)
from app.domain.chat.exceptions import RAGError
from app.domain.database.dependencies import async_scoped_session_ctx
from app.workflows.chat import search_sources, rerank
from app.interfaces import (
    VectorStorage,
    LLMClient,
    EmbeddingModel,
)
from app.defaults import defaults
from app.core import logger


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

    async def ask(
        self,
        request: RAGRequest,
        *,
        embedding_model: EmbeddingModel = defaults.embedding_model,
        llm_client: LLMClient = defaults.llm_client,
        vector_storage: VectorStorage = defaults.vector_storage,
        session_ctx: Callable[[], AsyncContextManager["AsyncSession"]] = async_scoped_session_ctx,
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
        :param embedding_model: Embedding модель.
        :param llm_client: Клиент для работы с LLM.
        :param vector_storage: Векторное хранилище.
        :param session_ctx: Асинхронный контекстный менеджер, возвращающий сессию AsyncSession.
                            Функция не коммитит изменения, поэтому ваш асинхронный контекстный
                            менеджер должен содержать commit() и rollback() обработку, если
                            требуется.

        :return: Ответ в виде :class:`RAGResponse`, содержащий текст ответа, источники и session_id.
        :raises RAGError: При любых ошибках внутри RAG-пайплайна.
        """

        if not request.session_id:
            async with session_ctx() as session:
                repo = ChatSessionRepository(session)
                chat_session: ChatSessionDTO = await repo.create(
                    workspace_id=request.workspace_id,
                )
            request.session_id = chat_session.id

        context_logger = logger.bind(
            workspace_id=request.workspace_id,
            session_id=request.session_id,
        )

        try:
            context_logger.info("Векторизация вопроса")
            embedding: list[float] = embedding_model.encode(request.question)

            context_logger.info("Формирование списка источников")
            sources: list[RetrievalSource] = await search_sources(
                question=request.question,
                embedding=embedding,
                workspace_id=request.workspace_id,
                top_k="all",  # TODO временно
                vector_storage=vector_storage,
                session_ctx=session_ctx,
            )

            # context_logger.info("Реранжирование источников")
            # sources = rerank(
            #     question=request.question,
            #     sources=sources,
            #     top_k=None,
            # )

            chunks: list[RetrievalChunk] = []

            for source in sources:
                for chunk in source.chunks:
                    if len(chunks) < 100:
                        chunks.append(chunk)
                    else:
                        break

            with open("chunks.json", "w", encoding="utf-8") as f:
                f.write(json.dumps([chunk.model_dump() for chunk in chunks]))

            answer = ""

            # context_logger.info("Формирование контекста для LLM")
            # builder = PromptBuilder(8192)
            # prompts: list[str] = builder.build(
            #     question=request.question,
            #     context=[
            #         chunk.text
            #         for source in sources
            #         for chunk in source.chunks
            #         if chunk.text is not None
            #     ],
            # )
            #
            # # TODO temp debug
            # sources_total: int = 0
            # for source in sources:
            #     sources_total += len(source.chunks)
            # context_logger.info(f"Получено {sources_total} источников, составлено {len(prompts)} промптов")
            #
            # context_logger.info(f"Получение ответа от LLM")
            # while len(prompts) >= 2:
            #     answers: list[str] = list(map(llm_client.generate, prompts))
            #     prompts = builder.build(
            #         question=request.question,
            #         context=answers,
            #     )
            # if not prompts:
            #     raise RAGError("Нет релевантных источников для ответа")
            # answer: str = llm_client.generate(prompts[0])
        except Exception as e:
            context_logger.error(RAGError.message, error_message=str(e))
            raise RAGError()

        async with session_ctx() as session:
            context_logger.info("Сохранение сообщений в базе данных")
            repo = ChatMessageRepository(session)
            await repo.create(
                session_id=request.session_id,
                role=ChatRole.user,
                content=request.question,
            )
            assistant_message: ChatMessageDTO = await repo.create(
                session_id=request.session_id,
                role=ChatRole.assistant,
                content=answer,
            )

            context_logger.info("Сохранение источников ответа в базе данных")
            retrieval_source_repo = RetrievalSourceRepository(session)
            retrieval_chunk_repo = RetrievalChunkRepository(session)
            for source in sources:
                retrieval_source: RetrievalSourceDTO = await retrieval_source_repo.create(
                    source_id=source.source_id,
                    message_id=assistant_message.id,
                    title=source.title,
                )
                for chunk in source.chunks:
                    await retrieval_chunk_repo.create(
                        retrieval_source_id=retrieval_source.id,
                        chunk_id=chunk.chunk_id,
                        page_start=chunk.page_start,
                        page_end=chunk.page_end,
                        retrieval_score=chunk.retrieval_score,
                        reranked_score=chunk.reranked_score,
                        combined_score=chunk.combined_score,
                    )

        return RAGResponse(
            answer=answer,
            sources=sources,
            session_id=request.session_id,
        )

    # async def _generate_prompt(
    #     self,
    #     session_id: str,
    #     question: str,
    #     sources: list[ChatMessageSource],
    #     *,
    #     session_ctx: Callable[[], AsyncContextManager["AsyncSession"]] = async_scoped_session_ctx,
    # ) -> str:
    #     """
    #     Составляет текст промпта для LLM на основе найденных фрагментов и истории чата.
    #
    #     Описание
    #     --------
    #     - Получает последние сообщения из репозитория сообщений ``ChatMessageRepository``.
    #     - Собирает текстовые сниппеты найденных источников и историю сообщений.
    #     - Склеивает их в итоговый промпт, который предназначен для передачи в LLM.
    #
    #     :param session_id: Идентификатор текущей сессии.
    #     :param question: Текст вопроса.
    #     :param sources: Список источников.
    #     :param session_ctx: Асинхронный контекстный менеджер, возвращающий сессию AsyncSession.
    #                         Функция не коммитит изменения, поэтому ваш асинхронный контекстный
    #                         менеджер должен содержать commit() и rollback() обработку, если
    #                         требуется.
    #
    #     :return: Промпт.
    #     """
    #
    #     source_context: str = "\n".join([source.snippet for source in sources])
    #     async with session_ctx() as session:
    #         repo = ChatMessageRepository(session)
    #         recent_messages: list[
    #             ChatMessageDTO
    #         ] = await repo.get_recent_messages(
    #             session_id=session_id,
    #             limit=settings.chat.chat_history_memory_limit,
    #         )
    #     message_context: str = "\n".join(
    #         [message.content for message in recent_messages]
    #     )
    #     context: str = "\n".join([source_context, message_context])
    #
    #     return "\n".join(
    #         [
    #             "Основываясь на следующем контексте, ответь на вопрос.",
    #             "---",
    #             "Вопрос:",
    #             question,
    #             "---",
    #             "Контекст:",
    #             context,
    #         ],
    #     )


class ChatService:
    """
    Сервис-обёртка для логики работы с чат-сессиями и сообщениями.
    """

    async def get_sessions(
        self,
        workspace_id: str,
        *,
        session_ctx: Callable[[], AsyncContextManager["AsyncSession"]] = async_scoped_session_ctx,
    ) -> list[ChatSession]:
        """
        Возвращает список чат-сессий для заданного рабочего пространства.

        :param workspace_id: Идентификатор рабочего пространства.
        :param session_ctx: Асинхронный контекстный менеджер, возвращающий сессию AsyncSession.
                            Функция не коммитит изменения, поэтому ваш асинхронный контекстный
                            менеджер должен содержать commit() и rollback() обработку, если
                            требуется.
        """

        async with session_ctx() as session:
            repo = ChatSessionRepository(session)
            sessions: list[ChatSessionDTO] = await repo.get_n(
                workspace_id=workspace_id,
            )
        return [self._map_session(session) for session in sessions]

    async def get_messages(
        self,
        session_id: str,
        *,
        session_ctx: Callable[[], AsyncContextManager["AsyncSession"]] = async_scoped_session_ctx,
    ) -> list[ChatMessage]:
        """
        Возвращает историю сообщений + вложенные источники указанной чат-сессии в хронологическом порядке.

        :param session_id: Идентификатор чат-сессии.
        :param session_ctx: Асинхронный контекстный менеджер, возвращающий сессию AsyncSession.
                            Функция не коммитит изменения, поэтому ваш асинхронный контекстный
                            менеджер должен содержать commit() и rollback() обработку, если
                            требуется.
        """

        async with session_ctx() as session:
            chat_message_repo = ChatMessageRepository(session)
            messages: list[ChatMessageDTO] = await chat_message_repo.get_messages(
                session_id=session_id,
            )

            retrieval_source_repo = RetrievalSourceRepository(session)
            retrieval_chunk_repo = RetrievalChunkRepository(session)

            async def get_chunks_by_source_id(source_id: int) -> list[RetrievalChunk]:
                retrieval_chunks: list[RetrievalChunkDTO] = await retrieval_chunk_repo.get_n(
                    retrieval_source_id=source_id,
                )
                return [
                    RetrievalChunk(
                        chunk_id=retrieval_chunk.chunk_id,
                        page_start=retrieval_chunk.page_start,
                        page_end=retrieval_chunk.page_end,
                        retrieval_score=retrieval_chunk.retrieval_score,
                        reranked_score=retrieval_chunk.reranked_score,
                        combined_score=retrieval_chunk.combined_score,
                    )
                    for retrieval_chunk in retrieval_chunks
                ]

            async def get_sources_by_message_id(message_id: str) -> list[RetrievalSource]:
                retrieval_sources: list[RetrievalSourceDTO] = await retrieval_source_repo.get_n(
                    message_id=message_id,
                )
                return [
                    RetrievalSource(
                        source_id=retrieval_source.source_id,
                        title=retrieval_source.title,
                        chunks=await get_chunks_by_source_id(retrieval_source.id),
                    )
                    for retrieval_source in retrieval_sources
                ]

            return [
                ChatMessage(
                    id=message.id,
                    session_id=message.session_id,
                    role=message.role,
                    content=message.content,
                    sources=await get_sources_by_message_id(message.id),
                    created_at=message.created_at,
                )
                for message in messages
            ]

    @staticmethod
    def _map_session(dto: ChatSessionDTO) -> ChatSession:
        return ChatSession(
            id=dto.id,
            workspace_id=dto.workspace_id,
            created_at=dto.created_at,
        )

    # @staticmethod
    # def _map_message(
    #     dto: ChatMessageDTO,
    #     sources: list[ChatMessageSourceDTO],
    # ) -> ChatMessage:
    #     return ChatMessage(
    #         id=dto.id,
    #         session_id=dto.session_id,
    #         role=dto.role,
    #         content=dto.content,
    #         sources=[
    #             ChatMessageSource(
    #                 source_id=source.source_id,
    #                 document_name=source.document_name,
    #                 page_start=source.page_start,
    #                 page_end=source.page_end,
    #                 snippet=source.snippet,
    #             )
    #             for source in sources
    #         ],
    #         created_at=dto.created_at,
    #     )
