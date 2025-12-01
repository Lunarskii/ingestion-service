from datetime import datetime
from enum import Enum
from typing import Annotated
from io import BytesIO
from uuid import uuid4

from pydantic import (
    Field,
    field_serializer,
)

from app.schemas import (
    BaseSchema,
    BaseDTO,
    IDMixin,
    UUIDMixin,
)
from app.utils.datetime import (
    universal_time,
    serialize_datetime_to_str,
    reset_timezone,
)


class File(BaseSchema):
    """
    Схема файла, используемая для передачи данных о загруженном файле.

    :ivar content: Сырые байты файла.
    :ivar name: Имя файла (включая расширение).
    """

    content: bytes
    name: str

    @property
    def file(self) -> BytesIO:
        """
        :return: In-memory байтовый поток.
        """

        return BytesIO(self.content)

    @property
    def type(self) -> str:
        """
        :return: MIME-тип файла, например ``application/pdf``.
        """

        from app.utils.file import get_mime_type
        return get_mime_type(self.content)

    @property
    def extension(self) -> str:
        """
        :return: Расширение файла (начинается с точки), например ``.pdf``.
        """

        from app.utils.file import get_file_extension
        return get_file_extension(self.content)

    @property
    def size(self) -> int:
        """
        :return: Размер файла в байтах.
        """

        return len(self.content)

    @property
    def sha256(self) -> str:
        """
        :return: sha256 хэш файла.
        """

        from app.domain.security.utils import hash_sha256
        return hash_sha256(self.content)


class DocumentStage(str, Enum):
    """
    Перечисление стадий обработки документа.

    :cvar extracting: Извлекаются текст и метаданные.
    :cvar chunking: Текст делится на чанки (фрагменты).
    :cvar embedding: Чанки (фрагменты) векторизуются.
    :cvar classification: Документ классифицируется на темы.
    :cvar lang_detect: Определяется язык документа.
    """

    extracting = "EXTRACTING"
    chunking = "CHUNKING"
    embedding = "EMBEDDING"
    classification = "CLASSIFICATION"
    lang_detect = "LANGDETECT"


class DocumentStatus(str, Enum):
    """
    Перечисление статусов обработки документа.

    :cvar pending: Ожидает добавления в очередь на обработку.
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


class Document(BaseSchema):
    """
    Метаданные документа.

    :ivar id: Уникальный идентификатор документа.
    :ivar workspace_id: Идентификатор рабочего пространства.
    :ivar source_id: Идентификатор источника.
    :ivar run_id: Идентификатор запуска краулера.
    :ivar trace_id: Корреляционный идентификатор запроса/задачи.
    :ivar sha256: Уникальный хэш байтов документа.
    :ivar raw_url: Адрес, откуда документ был загружен (HTTP URL).
    :ivar title: Имя документа.
    :ivar media_type: MIME-тип документа, например ``application/pdf``.
    :ivar detected_language: Определённый язык содержимого.
    :ivar page_count: Количество страниц в документе.
    :ivar author: Автор документа.
    :ivar creation_date: Дата создания документа.
    :ivar raw_storage_path: Путь в ``RawStorage``, где хранится исходный документ.
    :ivar silver_storage_path: Путь в ``SilverStorage``, где хранится обработанный документ.
    :ivar size_bytes: Размер файла в байтах.
    :ivar fetched_at: Время скачивания у источника (краулер или др.)
    :ivar stored_at: Время, когда документ сохранили в сырое хранилище.
    :ivar ingested_at: Время приёма/загрузки документа.
    :ivar status: Статус обработки (``DocumentStatus``).
    :ivar error_message: Текст ошибки, если статус ``DocumentStatus.failed``.
    """

    id: Annotated[
        str,
        Field(serialization_alias="document_id"),
    ]
    workspace_id: str
    source_id: str
    run_id: str | None = None
    trace_id: str
    sha256: str
    raw_url: str | None = None
    title: Annotated[
        str,
        Field(serialization_alias="document_name"),
    ]
    media_type: str
    detected_language: str | None = None
    page_count: Annotated[
        int | None,
        Field(serialization_alias="document_page_count"),
    ] = None
    author: Annotated[
        str | None,
        Field(serialization_alias="document_author"),
    ] = None
    creation_date: datetime | None = None
    raw_storage_path: str
    silver_storage_pages_path: str | None = None
    silver_storage_chunks_path: str | None = None
    size_bytes: Annotated[
        int,
        Field(serialization_alias="document_size_bytes"),
    ]
    fetched_at: Annotated[datetime, Field(default_factory=universal_time)]
    stored_at: Annotated[datetime, Field(default_factory=universal_time)]
    ingested_at: Annotated[datetime, Field(default_factory=universal_time)]
    status: DocumentStatus
    error_message: str | None = None

    @field_serializer(
        "creation_date",
        "fetched_at",
        "stored_at",
        "ingested_at",
    )
    def datetime_to_str(self, value: datetime) -> str | None:
        return serialize_datetime_to_str(value)

    @classmethod
    def from_dto(cls, dto: "DocumentDTO") -> "Document":
        return Document(
            id=dto.id,
            workspace_id=dto.workspace_id,
            source_id=dto.source_id,
            run_id=dto.run_id,
            trace_id=dto.trace_id,
            sha256=dto.sha256,
            raw_url=dto.raw_url,
            title=dto.title,
            media_type=dto.media_type,
            detected_language=dto.detected_language,
            page_count=dto.page_count,
            author=dto.author,
            creation_date=dto.creation_date,
            raw_storage_path=dto.raw_storage_path,
            silver_storage_pages_path=dto.silver_storage_pages_path,
            silver_storage_chunks_path=dto.silver_storage_chunks_path,
            size_bytes=dto.size_bytes,
            fetched_at=dto.fetched_at,
            stored_at=dto.stored_at,
            ingested_at=dto.ingested_at,
            status=dto.status,
            error_message=dto.error_message,
        )


class DocumentEvent(BaseSchema):
    id: Annotated[
        int,
        Field(serialization_alias="trace_id"),
    ]
    document_id: str
    trace_id: str | None = None
    stage: DocumentStage
    status: DocumentStatus
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_ms: float | None = None
    error_message: str | None = None


class DocumentDTO(BaseDTO, UUIDMixin):
    """
    DTO (Data Transfer Object) для представления метаданных документа.

    :ivar id: Идентификатор документа.
    :ivar workspace_id: Идентификатор рабочего пространства.
    :ivar source_id: Идентификатор источника.
    :ivar run_id: Идентификатор запуска краулера.
    :ivar trace_id: Корреляционный идентификатор запроса/задачи.
    :ivar sha256: Уникальный хэш байтов документа.
    :ivar raw_url: Адрес, откуда документ был загружен (HTTP URL).
    :ivar title: Имя документа.
    :ivar media_type: MIME-тип документа, например ``application/pdf``.
    :ivar detected_language: Определённый язык содержимого.
    :ivar page_count: Количество страниц в документе.
    :ivar author: Автор документа.
    :ivar creation_date: Дата создания документа.
    :ivar raw_storage_path: Путь в RawStorage (сырое хранилище), где хранится исходный документ.
    :ivar silver_storage_pages_path: Путь в хранилище обработанных документов, где хранятся страницы документа.
    :ivar silver_storage_chunks_path: Путь в хранилище обработанных документов, где хранятся фрагменты документа.
    :ivar size_bytes: Размер файла в байтах.
    :ivar fetched_at: Время скачивания у источника (краулер или др.)
    :ivar stored_at: Время, когда документ сохранили в сырое хранилище.
    :ivar ingested_at: Время приёма/загрузки документа.
    :ivar status: Статус обработки (``DocumentStatus``).
    :ivar error_message: Текст ошибки, если статус ``DocumentStatus.failed``.
    """

    workspace_id: str
    source_id: str
    run_id: str | None = None
    trace_id: Annotated[str, Field(default_factory=lambda: str(uuid4()))]  # type: ignore
    sha256: str
    raw_url: str | None = None
    title: str
    media_type: str
    detected_language: str | None = None
    page_count: int | None = None
    author: str | None = None
    creation_date: datetime | None = None
    raw_storage_path: str
    silver_storage_pages_path: str | None = None
    silver_storage_chunks_path: str | None = None
    size_bytes: int
    fetched_at: Annotated[datetime, Field(default_factory=universal_time)]
    stored_at: Annotated[datetime, Field(default_factory=universal_time)]
    ingested_at: Annotated[datetime, Field(default_factory=universal_time)]
    status: DocumentStatus
    error_message: str | None = None

    @field_serializer("creation_date")
    def reset_timezone(self, value: datetime) -> datetime | None:
        return reset_timezone(value)


class DocumentEventDTO(BaseDTO, IDMixin):
    """
    DTO (Data Transfer Object), представляющий описание события в пайплайне обработки документа.

    :ivar id: Идентификатор события.
    :ivar document_id: Идентификатор документа.
    :ivar trace_id: Корреляционный идентификатор запроса/задачи.
    :ivar stage: Стадия обработки документа.
    :ivar status: Статус обработки документа.
    :ivar started_at: Время начала выполнения задачи.
    :ivar finished_at: Время конца выполнения задачи.
    :ivar duration_ms: Суммарное время выполнения задачи в миллисекундах.
    :ivar error_message: Текст ошибки, если задача провалилась.
    """

    document_id: str
    trace_id: str
    stage: DocumentStage
    status: DocumentStatus
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_ms: float | None = None
    error_message: str | None = None
