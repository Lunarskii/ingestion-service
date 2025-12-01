from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    AsyncContextManager,
)
from io import BytesIO
from functools import wraps
import inspect
import time

import langdetect

from app.domain.document.repositories import (
    DocumentRepository,
    DocumentEventRepository,
)
from app.domain.document.schemas import (
    DocumentStatus,
    DocumentStage,
)
from app.domain.document.exceptions import EmptyTextError
from app.domain.extraction.extractors import DocumentExtractor
from app.domain.extraction.utils import pages_to_text
from app.domain.extraction.exceptions import ExtractionError
from app.domain.classifier.repositories import (
    TopicRepository,
    DocumentTopicRepository,
)
from app.domain.database.dependencies import async_scoped_session_ctx
from app.domain.database.exceptions import EntityNotFoundError
from app.utils.datetime import (
    reset_timezone,
    universal_time,
)
from app.defaults import defaults
from app.core import logger
from app.types import (
    VectorPayload,
    Vector,
    Document,
)


if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from loguru import Logger

    from app.domain.document.schemas import (
        DocumentDTO,
        DocumentEventDTO,
    )
    from app.domain.classifier.rules import Classifier
    from app.domain.classifier.schemas import (
        ClassificationResult,
        TopicDTO,
    )
    from app.domain.extraction.schemas import ExtractionResult
    from app.interfaces import (
        EmbeddingModel,
        FileStorage,
        TextSplitter,
        VectorStorage,
    )
    from app.types import DocumentChunk


# TODO вынести в утилиты
def get_param_value(func: Callable[..., Any], args: tuple, kwargs: dict, param_name: str) -> Any:
    signature = inspect.signature(func)

    try:
        bound = signature.bind_partial(*args, **kwargs)
    except TypeError:
        return kwargs.get(param_name)

    if param_name in bound.arguments:
        return bound.arguments[param_name]

    param = signature.parameters.get(param_name)
    if param is None:
        return None
    if param.default is not inspect._empty:  # noqa
        return param.default

    return None


def document_pipeline(stage: DocumentStage):
    def decorator(func) -> Callable:
        signature = inspect.signature(func)
        params = list(signature.parameters.items())

        logger_in_param: bool = False
        for name, param in params:
            if name == "_logger":
                logger_in_param = True
                break

        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            document_id: str = get_param_value(func, args, kwargs, "document_id")
            if not document_id:
                error_message: str = "Для использования @document_pipeline требуется объявленный параметр 'document_id' в функции"
                logger.error(error_message)
                raise RuntimeError(error_message)

            document: "DocumentDTO" = await get_document_meta(document_id)

            _logger = logger.bind(
                trace_id=document.trace_id,
                workspace_id=document.workspace_id,
                document_id=document_id,
                stage=stage,
                status=document.status,
            )

            if logger_in_param and "_logger" not in kwargs and (len(args) + len(kwargs) < len(params)):
                kwargs["_logger"] = _logger

            await create_document_event(
                document_id=document_id,
                trace_id=document.trace_id,
                stage=stage,
                status=DocumentStatus.processing,
                started_at=universal_time(),
            )
            started_at_mono: float = time.monotonic()
            try:
                _logger.info(f"Запуск рабочего процесса {func.__qualname__}")
                result = await func(*args, **kwargs)
                duration_ms: int = int((time.monotonic() - started_at_mono) * 1000)
                _logger.info(
                    f"Рабочий процесс {func.__qualname__} завершен успешно",
                    duration_ms=duration_ms,
                )
            except Exception as e:
                duration_ms: int = int((time.monotonic() - started_at_mono) * 1000)
                _logger.error(
                    f"Не удалось выполнить рабочий процесс {func.__qualname__}",
                    duration_ms=duration_ms,
                    error_message=str(e),
                )
                await update_document_meta(
                    document_id,
                    error_message=str(e),
                )
                await update_document_event(
                    document_id=document_id,
                    stage=stage,
                    status=DocumentStatus.failed,
                    finished_at=universal_time(),
                    duration_ms=duration_ms,
                    error_message=str(e),
                )
                raise
            else:
                await update_document_event(
                    document_id=document_id,
                    stage=stage,
                    status=DocumentStatus.success,
                    finished_at=universal_time(),
                    duration_ms=duration_ms,
                )

            return result

        return async_wrapper

    return decorator


async def create_document_event(
    document_id: str,
    trace_id: str,
    stage: DocumentStage,
    status: DocumentStatus,
    *,
    session_ctx: Callable[[], AsyncContextManager["AsyncSession"]] = async_scoped_session_ctx,
    **kwargs,
) -> "DocumentEventDTO":
    """
    :param document_id: Идентификатор документа.
    :param trace_id: Корреляционный идентификатор запроса/задачи.
    :param stage: Стадия обработки документа.
    :param status: Статус обработки документа.
    :param session_ctx: Асинхронный контекстный менеджер, возвращающий сессию AsyncSession.
                        Функция не коммитит изменения, поэтому ваш асинхронный контекстный
                        менеджер должен содержать commit() и rollback() обработку, если
                        требуется.
    """

    async with session_ctx() as session:
        repo = DocumentEventRepository(session)
        return await repo.create(
            document_id=document_id,
            trace_id=trace_id,
            stage=stage,
            status=status,
            **kwargs,
        )


async def update_document_event(
    document_id: str,
    stage: DocumentStage,
    status: DocumentStatus,
    *,
    session_ctx: Callable[[], AsyncContextManager["AsyncSession"]] = async_scoped_session_ctx,
    **kwargs,
) -> "DocumentEventDTO":
    """
    :param document_id: Идентификатор документа.
    :param stage: Стадия обработки документа.
    :param status: Статус обработки документа.
    :param session_ctx: Асинхронный контекстный менеджер, возвращающий сессию AsyncSession.
                        Функция не коммитит изменения, поэтому ваш асинхронный контекстный
                        менеджер должен содержать commit() и rollback() обработку, если
                        требуется.
    """

    async with session_ctx() as session:
        repo = DocumentEventRepository(session)
        return await repo.update_document_event(
            document_id=document_id,
            stage=stage,
            status=status,
            **kwargs,
        )


async def get_document_meta(
    document_id: str,
    *,
    session_ctx: Callable[[], AsyncContextManager["AsyncSession"]] = async_scoped_session_ctx,
) -> "DocumentDTO":
    """
    :param document_id: Идентификатор документа.
    :param session_ctx: Асинхронный контекстный менеджер, возвращающий сессию AsyncSession.
                        Функция не коммитит изменения, поэтому ваш асинхронный контекстный
                        менеджер должен содержать commit() и rollback() обработку, если
                        требуется.
    """

    async with session_ctx() as session:
        repo = DocumentRepository(session)
        try:
            return await repo.get(document_id)
        except EntityNotFoundError as e:
            logger.error(
                "Документ не найден в БД",
                document_id=document_id,
                error_message=str(e),
            )
            raise
        
        
async def update_document_meta(
    document_id: str,
    *,
    session_ctx: Callable[[], AsyncContextManager["AsyncSession"]] = async_scoped_session_ctx,
    **kwargs,
) -> "DocumentDTO":
    """
    :param document_id: Идентификатор документа.
    :param session_ctx: Асинхронный контекстный менеджер, возвращающий сессию AsyncSession.
                        Функция не коммитит изменения, поэтому ваш асинхронный контекстный
                        менеджер должен содержать commit() и rollback() обработку, если
                        требуется.
    """
    
    async with session_ctx() as session:
        repo = DocumentRepository(session)
        try:
            return await repo.update(document_id, **kwargs)
        except EntityNotFoundError as e:
            logger.error(
                "Документ не найден в БД",
                document_id=document_id,
                error_message=str(e),
            )
            raise


@document_pipeline(stage=DocumentStage.extracting)
async def extract_text_and_metadata(
    document_id: str,
    *,
    raw_storage: "FileStorage" = defaults.raw_storage,
    silver_storage: "FileStorage" = defaults.silver_storage,
    extractor: Callable[[bytes], "ExtractionResult"] | DocumentExtractor | None = None,
    _logger: "Logger",
) -> None:
    """
    Рабочий процесс (Workflow):
        - Извлечение метаданных документа из БД.
        - Извлечение исходного документа из FileStorage (Хранилище сырых документов).
        - Извлечение текста и метаданных документа из исходного документа.
        - Сохранение извлеченных страниц документа в SilverStorage (Хранилище обработанных документов).
        - Обновление метаданных документа в БД.

    :param document_id: Идентификатор документа.
    :param raw_storage: Хранилище сырых документов.
    :param silver_storage: Хранилище обработанных документов.
    :param extractor: Callable(bytes) -> ExtractedInfo или TextExtractor.
                      Если None, импортируем стандартный extract.
    :param _logger: Логгер.
    """

    if extractor is None:
        from app.workflows.extraction import extract_text_from_file
        extractor = extract_text_from_file

    document_meta: "DocumentDTO" = await get_document_meta(document_id)
    document_bytes: bytes = raw_storage.get(document_meta.raw_storage_path)

    try:
        if isinstance(extractor, DocumentExtractor):
            extraction_result: "ExtractionResult" = extractor.extract(BytesIO(document_bytes))
        else:
            extraction_result: "ExtractionResult" = extractor(document_bytes)
    except ExtractionError:
        _logger.error("Не удалось извлечь текст и метаданные документа")
        raise

    if not extraction_result.pages or not pages_to_text(extraction_result.pages, 1):
        raise EmptyTextError()

    silver_storage_path: str = f"{document_meta.workspace_id}/{document_id}.pages.json"
    _logger.info(
        "Сохранение извлеченных страниц документа в SilverStorage",
        silver_storage_path=silver_storage_path,
    )
    document = Document(
        id=document_meta.id,
        pages=extraction_result.pages,
    )
    silver_storage.save(
        file_bytes=document.model_dump_json(include={"id", "pages"}).encode(),
        path=silver_storage_path,
    )

    _logger.info("Обновление метаданных документа")
    try:
        await update_document_meta(
            document_id,
            silver_storage_pages_path=silver_storage_path,
            page_count=extraction_result.metadata.page_count,
            author=extraction_result.metadata.author,
            creation_date=reset_timezone(extraction_result.metadata.creation_date), # TODO исправить reset_timezone, чтобы не приходилось это делать каждый раз
        )
    except Exception:
        silver_storage.delete(silver_storage_path)
        raise


# TODO написать SKIPPED, если уже определен язык на стадии EXTRACTING
@document_pipeline(stage=DocumentStage.lang_detect)
async def detect_language(
    document_id: str,
    *,
    max_chars: int = 1000,
    silver_storage: "FileStorage" = defaults.silver_storage,
    _logger: "Logger",
) -> None:
    """
    Рабочий процесс (Workflow):
        - Извлечение метаданных документа из БД.
        - Извлечение страниц документа из SilverStorage (Хранилище обработанных документов).
        - Соединение страниц в единый текст.
        - Определение языка документа.
        - Обновление метаданных документа в БД.

    :param document_id: Идентификатор документа.
    :param max_chars: Максимум символов, который будет извлечен из страниц при
                      определении языка документа.
    :param silver_storage: Хранилище обработанных документов.
    :param _logger: Логгер.
    """

    document_meta: "DocumentDTO" = await get_document_meta(document_id)

    if not document_meta.silver_storage_pages_path:
        raise RuntimeError(
            "Невозможно определить язык документа: silver_storage_pages_path отсутствует в базе данных",
        ) # TODO мб заменить ошибку на другую, но пока так

    _logger.info("Извлечение страниц документа из SilverStorage")
    document_bytes: bytes = silver_storage.get(document_meta.silver_storage_pages_path)
    document = Document.model_validate_json(document_bytes)

    if not document.pages:
        raise RuntimeError(
            "Невозможно определить язык документа: отсутствуют страницы документа в SilverStorage",
        ) # TODO мб заменить ошибку на другую, но пока так

    text: str = pages_to_text(
        pages=document.pages,
        max_chars=max_chars,
    )

    if not text.strip():
        _logger.warning("Нет текста для определения языка документа")
        return

    detected_language: str = langdetect.detect(text)

    _logger.info("Обновление метаданных документа")
    await update_document_meta(
        document_id,
        detected_language=detected_language,
    )


@document_pipeline(stage=DocumentStage.chunking)
async def split_pages_on_chunks(
    document_id: str,
    *,
    silver_storage: "FileStorage" = defaults.silver_storage,
    text_splitter: "TextSplitter" = defaults.text_splitter,
    _logger: "Logger",
) -> None:
    """
    Рабочий процесс (Workflow):
        - Извлечение метаданных документа из БД.
        - Извлечение страниц документа из SilverStorage (Хранилище обработанных документов).
        - Разбиение страниц документа на фрагменты.

    :param document_id: Идентификатор документа.
    :param silver_storage: Хранилище обработанных документов.
    :param text_splitter: Текстовый разделитель.
    :param _logger: Логгер.

    :return: Фрагменты документа.
    """

    document_meta: "DocumentDTO" = await get_document_meta(document_id)

    if not document_meta.silver_storage_pages_path:
        raise RuntimeError(
            "Невозможно разбить документ на фрагменты: silver_storage_pages_path отсутствует в базе данных",
        ) # TODO мб заменить ошибку на другую, но пока так

    _logger.info("Извлечение страниц документа из SilverStorage")
    document_bytes: bytes = silver_storage.get(document_meta.silver_storage_pages_path)
    document = Document.model_validate_json(document_bytes)

    if not document.pages:
        raise RuntimeError(
            "Невозможно разбить документ на фрагменты: отсутствуют страницы документа в SilverStorage",
        ) # TODO мб заменить ошибку на другую, но пока так

    _logger.info("Разбиение текста на чанки")
    chunks: list["DocumentChunk"] = text_splitter.split_pages(document.pages)

    silver_storage_path: str = f"{document_meta.workspace_id}/{document_id}.chunks.json"
    _logger.info(
        "Сохранение извлеченных фрагментов документа в SilverStorage",
        silver_storage_path=silver_storage_path,
    )
    document = Document(
        id=document_meta.id,
        chunks=chunks,
    )
    silver_storage.save(
        file_bytes=document.model_dump_json(include={"id", "chunks"}).encode(),
        path=silver_storage_path,
    )

    _logger.info("Обновление метаданных документа")
    try:
        await update_document_meta(
            document_id,
            silver_storage_chunks_path=silver_storage_path,
        )
    except Exception:
        silver_storage.delete(silver_storage_path)
        raise


@document_pipeline(stage=DocumentStage.embedding)
async def vectorize_chunks(
    document_id: str,
    *,
    silver_storage: "FileStorage" = defaults.silver_storage,
    vector_storage: "VectorStorage" = defaults.vector_storage,
    embedding_model: "EmbeddingModel" = defaults.embedding_model,
    _logger: "Logger",
) -> None:
    """
    Рабочий процесс (Workflow):
        - Извлечение метаданных документа из БД.
        - Создание эмбеддингов для каждого чанка, векторизация.
        - Сохранение векторов в VectorStore (Векторное хранилище).

    :param document_id: Идентификатор документа.
    :param silver_storage: Хранилище обработанных документов.
    :param vector_storage: Векторное хранилище.
    :param embedding_model: Embedding модель.
    :param _logger: Логгер.
    """

    document_meta: "DocumentDTO" = await get_document_meta(document_id)

    if not document_meta.silver_storage_chunks_path:
        raise RuntimeError(
            "Невозможно векторизовать документ: silver_storage_chunks_path отсутствует в базе данных",
        ) # TODO мб заменить ошибку на другую, но пока так

    _logger.info("Извлечение фрагментов документа из SilverStorage")
    document_bytes: bytes = silver_storage.get(document_meta.silver_storage_chunks_path)
    document = Document.model_validate_json(document_bytes)

    if not document.chunks:
        raise RuntimeError(
            "Невозможно векторизовать документ: отсутствуют фрагменты документа в SilverStorage",
        ) # TODO мб заменить ошибку на другую, но пока так

    _logger.info("Создание эмбеддингов для каждого чанка, векторизация")
    vectors: list["Vector"] = embedding_model.encode_with_payload(
        sentences=[chunk.text for chunk in document.chunks],
        payload=[
            VectorPayload(
                workspace_id=document_meta.workspace_id,
                document_id=document_id,
                chunk_id=chunk.id,
            )
            for chunk in document.chunks
        ],
    )

    _logger.info("Сохранение векторов в VectorStore")
    vector_storage.upsert(vectors)


@document_pipeline(stage=DocumentStage.classification)
async def classify_document_into_topics(
    document_id: str,
    *,
    max_chars: int = 1000,
    classifier: "Classifier" = defaults.classifier,
    silver_storage: "FileStorage" = defaults.silver_storage,
    _logger: "Logger",
) -> None:
    """
    Рабочий процесс (Workflow):
        - Извлечение метаданных документа из БД.
        - Извлечение страниц документа из SilverStorage (Хранилище обработанных документов).
        - Классификация документа на возможные темы.
        - Сохранение каждого топика и счет по топику для документа.

    :param document_id: Идентификатор документа.
    :param max_chars: Максимум символов, который будет извлечен из страниц при
                      классификации документа.
    :param classifier: Классификатор документа/текста.
    :param silver_storage: Хранилище обработанных документов.
    :param _logger: Логгер.
    """

    document_meta: "DocumentDTO" = await get_document_meta(document_id)

    if not document_meta.silver_storage_pages_path:
        raise RuntimeError(
            "Невозможно классифицировать документ: silver_storage_pages_path отсутствует в базе данных",
        ) # TODO мб заменить ошибку на другую, но пока так

    _logger.info("Извлечение страниц документа из SilverStorage")
    document_bytes: bytes = silver_storage.get(document_meta.silver_storage_pages_path)
    document = Document.model_validate_json(document_bytes)

    if not document.pages:
        raise RuntimeError(
            "Невозможно классифицировать документ: отсутствуют страницы документа в SilverStorage",
        ) # TODO мб заменить ошибку на другую, но пока так

    text: str = pages_to_text(
        pages=document.pages,
        max_chars=max_chars,
    )

    _logger.info("Классификация документа на возможные темы")
    results: list["ClassificationResult"] = classifier.classify_text(text)

    _logger.info("Сохранение каждого топика и счет по топику для документа")
    async with async_scoped_session_ctx() as session:
        topic_repo = TopicRepository(session)
        document_topic_repo = DocumentTopicRepository(session)

        for result in results:
            try:
                topic: "TopicDTO" = await topic_repo.get_topic_by_code(result.topic)
                await document_topic_repo.create(
                    document_id=document_id,
                    topic_id=topic.id,
                    score=result.score,
                    source="rules",
                )
            except EntityNotFoundError as e:
                _logger.error(
                    "Топик не найден в БД",
                    topic_code=result.topic,
                    error_message=str(e),
                )
