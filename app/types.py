from typing import (
    Union,
    Optional,
)
from datetime import datetime
from enum import Enum
from functools import cached_property
import uuid

from pydantic import (
    Field,
    ConfigDict,
    StrictInt,
    StrictStr,
)

from app.schemas import BaseSchema


VectorId = Union[
    StrictInt,
    StrictStr,
]
WorkspaceId = Union[StrictStr,]
DocumentId = Union[StrictStr,]
DocumentPageId = Union[StrictStr,]
DocumentChunkId = Union[StrictStr,]
TraceId = Union[StrictStr,]


class VectorPayload(BaseSchema):
    """
    Полезная нагрузка вектора.

    :ivar workspace_id: Идентификатор рабочего пространства.
    :ivar document_id: Идентификатор документа.
    :ivar chunk_id: Идентификатор фрагмента.
    """

    model_config = ConfigDict(extra="allow")

    workspace_id: str = Field(..., description="Идентификатор рабочего пространства")
    document_id: str = Field(..., description="Идентификатор документа")
    chunk_id: str = Field(..., description="Идентификатор фрагмента")


class Vector(BaseSchema):
    """
    Схема векторного представления текстового фрагмента.

    :ivar id: Идентификатор вектора.
    :ivar values: Вектор точки.
    :ivar payload: Полезная нагрузка - значения, присвоенные точке.
    """

    id: VectorId = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Идентификатор вектора",
    )
    values: list[float] = Field(..., description="Вектор точки")
    payload: Optional[VectorPayload] = Field(
        default=None,
        description="Полезная нагрузка - значения, присвоенные точке",
    )


# TODO добавить схему, которая хранит list[ScoredVector], и дать ему описание нынешнего класса ScoredVector, так как "Результат" является списком этих векторов, а не только каждый вектор
class ScoredVector(BaseSchema):
    """
    Результат поиска в векторном хранилище.

    :ivar id: Идентификатор вектора.
    :ivar values: Вектор точки.
    :ivar payload: Полезная нагрузка - значения, присвоенные точке.
    :ivar score: Расстояние от точек вектора до вектора запроса.
    """

    id: VectorId = Field(..., description="Идентификатор вектора")
    values: list[float] = Field(..., description="Вектор точки")
    payload: Optional[VectorPayload] = Field(
        default=None,
        description="Полезная нагрузка - значения, присвоенные точке",
    )
    score: float = Field(..., description="Расстояние от точек вектора до вектора запроса")


class DocumentProcessingStage(str, Enum):
    """
    Перечисление стадий обработки документа.

    :cvar extracting: Извлечение текста и метаданных.
    :cvar chunking: Деление текста на фрагменты.
    :cvar embedding: Векторизация фрагментов, создание эмбеддингов.
    :cvar classification: Классифицирование документа на темы.
    :cvar lang_detect: Определение языка документа.
    """

    extracting = "EXTRACTING"
    chunking = "CHUNKING"
    embedding = "EMBEDDING"
    classification = "CLASSIFICATION"
    lang_detect = "LANGDETECT"


class DocumentProcessingStatus(str, Enum):
    """
    Перечисление статусов обработки документа.

    :cvar pending: Ожидание добавления в очередь на обработку.
    :cvar queued: В очереди на обработку, но еще не обрабатывается.
    :cvar processing: Обрабатывается.
    :cvar success: Успешно.
    :cvar failed: Неуспешно.
    :cvar skipped: Пропущено.
    """

    pending = "PENDING"
    queued = "QUEUED"
    processing = "PROCESSING"
    success = "SUCCESS"
    failed = "FAILED"
    skipped = "SKIPPED"


class DocumentMetadata(BaseSchema):
    """
    Метаданные документа.

    :ivar title: Имя документа.
    :ivar mime_type: MIME-тип документа.
    :ivar language: Язык документа.
    :ivar page_count: Количество страниц в документе.
    :ivar author: Автор документа.
    :ivar creation_date: Дата создания документа.
    :ivar size_bytes: Размер документа в байтах.
    :ivar sha256: Хэш байтов документа.
    :ivar keywords: Список ключевых слов/тегов.
    :ivar category: Категория/рубрика документа.
    :ivar subject: Тема/подтема документа.
    """

    model_config = ConfigDict(extra="allow")

    title: Optional[str] = Field(default=None, description="Имя документа")
    mime_type: Optional[str] = Field(default=None, description="MIME-тип документа")
    language: Optional[str] = Field(default=None, description="Язык документа")
    page_count: Optional[int] = Field(default=None, description="Количество страниц в документе")
    author: Optional[str] = Field(default=None, description="Автор документа")
    creation_date: Optional[datetime] = Field(default=None, description="Дата создания документа")
    size_bytes: Optional[int] = Field(default=None, description="Размер документа в байтах")
    sha256: Optional[str] = Field(default=None, description="Хэш байтов документа")
    keywords: Optional[str] = Field(default=None, description="Список ключевых слов/тегов")
    category: Optional[str] = Field(default=None, description="Категория/рубрика документа")
    subject: Optional[str] = Field(default=None, description="Тема/подтема документа")


class DocumentPage(BaseSchema):
    """
    Страница документа.

    :ivar id: Идентификатор страницы документа.
    :ivar num: Номер страницы документа.
    :ivar text: Текст, содержащийся на странице документа.
    """

    id: DocumentPageId = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Идентификатор страницы документа",
    )
    num: int = Field(..., description="Номер страницы документа")
    text: str = Field(..., description="Текст, содержащийся на странице документа")


class DocumentPageSpan(BaseSchema):
    """
    Описание части фрагмента, расположенного на одной странице.

    :ivar num: Номер страницы документа.
    :ivar text: Текст фрагмента, содержащийся на данной странице.
    :ivar chunk_start_on_page: Позиция начала фрагмента относительно начала страницы (в символах).
    :ivar chunk_end_on_page: Позиция конца фрагмента относительно начала страницы (в символах).
    """

    num: int = Field(..., description="Номер страницы документа")
    text: str = Field(..., description="Текст фрагмента, содержащийся на данной странице")
    chunk_start_on_page: int = Field(
        ...,
        description="Позиция начала фрагмента относительно начала страницы (в символах)",
    )
    chunk_end_on_page: int = Field(
        ...,
        description="Позиция конца фрагмента относительно начала страницы (в символах)",
    )


class DocumentChunk(BaseSchema):
    """
    Фрагмент страницы документа.

    :ivar id: Идентификатор фрагмента документа.
    :ivar text: Текст фрагмента.
    :ivar page_spans: Части фрагмента, располагающиеся на странице документа.
    """

    id: DocumentChunkId = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Идентификатор фрагмента документа",
    )
    text: str = Field(..., description="Текст фрагмента")
    page_spans: list[DocumentPageSpan] = Field(
        ...,
        description="Список частей фрагмента, располагающихся на странице документа",
    )

    @cached_property
    def page_nums(self) -> list[int]:
        """
        Возвращает номера страниц, на которых присутствует данный фрагмент.

        :return: Список уникальных (в порядке появления) номеров страниц.
        """

        return [page_span.num for page_span in self.page_spans]

    @cached_property
    def page_start(self) -> int:
        """
        Страница, на которой находится начало фрагмента документа.
        """

        return self.page_spans[0].num

    @cached_property
    def page_end(self) -> int:
        """
        Страница, на которой находится конец фрагмента документа.
        """

        return self.page_spans[-1].num


class Document(BaseSchema):
    """
    Документ.

    :ivar id: Идентификатор документа.
    :ivar workspace_id: Идентификатор рабочего пространства.
    :ivar source_id: Идентификатор источника.
    :ivar run_id: Идентификатор запуска краулера.
    :ivar trace_id: Корреляционный идентификатор запроса/задачи.
    :ivar metadata: Метаданные документа.
    :ivar pages: Страницы документа.
    :ivar chunks: Фрагменты документа.
    :ivar raw_url: Адрес, откуда документ был загружен (HTTP URL).
    :ivar raw_storage_path: Путь в сыром хранилище, где хранится исходный документ.
    :ivar silver_storage_pages_path: Путь в хранилище обработанных документов, где хранятся страницы документа.
    :ivar silver_storage_chunks_path: Путь в хранилище обработанных документов, где хранятся фрагменты документа.
    :ivar fetched_at: Время скачивания у источника (краулер или др.).
    :ivar stored_at: Время сохранения документа в сырое хранилище.
    :ivar ingested_at: Время приёма/загрузки документа.
    :ivar stage: Стадия обработки документа.
    :ivar status: Статус обработки документа.
    :ivar error_message: Текст ошибки, если статус 'FAILED'.
    """

    id: DocumentId = Field(..., description="Идентификатор документа")
    workspace_id: Optional[WorkspaceId] = Field(
        default=None,
        description="Идентификатор рабочего пространства",
    )
    source_id: Optional[str] = Field(default=None, description="Идентификатор источника")
    run_id: Optional[str] = Field(default=None, description="Идентификатор запуска краулера")
    trace_id: Optional[TraceId] = Field(
        default=None,
        description="Корреляционный идентификатор запроса/задачи",
    )
    metadata: Optional[DocumentMetadata] = Field(default=None, description="Метаданные документа")
    pages: Optional[list[DocumentPage]] = Field(default=None, description="Страницы документа")
    chunks: Optional[list[DocumentChunk]] = Field(default=None, description="Фрагменты документа")
    raw_url: Optional[str] = Field(
        default=None,
        description="Адрес, откуда документ был загружен (HTTP URL)",
    )
    raw_storage_path: Optional[str] = Field(
        default=None,
        description="Путь в сыром хранилище, где хранится исходный документ",
    )
    silver_storage_pages_path: Optional[str] = Field(
        default=None,
        description="Путь в хранилище обработанных документов, где хранятся страницы документа",
    )
    silver_storage_chunks_path: Optional[str] = Field(
        default=None,
        description="Путь в хранилище обработанных документов, где хранятся фрагменты документа",
    )
    fetched_at: Optional[datetime] = Field(
        default=None,
        description="Время скачивания у источника (краулер или др.)",
    )
    stored_at: Optional[datetime] = Field(
        default=None,
        description="Время сохранения документа в сырое хранилище",
    )
    ingested_at: Optional[datetime] = Field(
        default=None,
        description="Время приёма/загрузки документа",
    )
    stage: Optional[DocumentProcessingStage] = Field(
        default=None,
        description="Стадия обработки документа",
    )
    status: Optional[DocumentProcessingStatus] = Field(
        default=None,
        description="Статус обработки документа",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Текст ошибки, если статус 'FAILED'",
    )
