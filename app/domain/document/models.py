from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)
from sqlalchemy.schema import UniqueConstraint
import sqlalchemy as sa

from app.domain.document.schemas import (
    DocumentStage,
    DocumentStatus,
)
from app.domain.database.models import BaseDAO
from app.domain.database.mixins import (
    UUIDMixin,
    IDMixin,
)


class DocumentDAO(BaseDAO, UUIDMixin):
    """
    DAO (ORM) модель, представляющая метаданные документа.

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
    :ivar raw_storage_path: Путь в ``RawStorage``, где хранится исходный документ.
    :ivar silver_storage_path: Путь в ``SilverStorage``, где хранится обработанный документ.
    :ivar size_bytes: Размер файла в байтах.
    :ivar fetched_at: Время скачивания у источника (краулер или др.)
    :ivar stored_at: Время, когда документ сохранили в сырое хранилище.
    :ivar ingested_at: Время приёма/загрузки документа.
    :ivar status: Статус обработки (``DocumentStatus``).
    :ivar error_message: Текст ошибки, если статус ``DocumentStatus.failed``.
    """

    __tablename__ = "documents"

    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "sha256",
            name="uq_documents_workspace_id_sha256",
        ),
    )

    workspace_id: Mapped[UUID]
    source_id: Mapped[str]
    run_id: Mapped[UUID] = mapped_column(nullable=True)
    trace_id: Mapped[UUID]
    sha256: Mapped[str]
    raw_url: Mapped[str] = mapped_column(nullable=True)
    title: Mapped[str]
    media_type: Mapped[str]
    detected_language: Mapped[str] = mapped_column(nullable=True)
    page_count: Mapped[int] = mapped_column(nullable=True)
    author: Mapped[str] = mapped_column(nullable=True)
    creation_date: Mapped[datetime] = mapped_column(nullable=True)
    raw_storage_path: Mapped[str]
    silver_storage_pages_path: Mapped[str] = mapped_column(nullable=True)
    silver_storage_chunks_path: Mapped[str] = mapped_column(nullable=True)
    size_bytes: Mapped[int]
    fetched_at: Mapped[datetime]
    stored_at: Mapped[datetime]
    ingested_at: Mapped[datetime]
    status: Mapped[DocumentStatus] = mapped_column(
        sa.Enum(
            DocumentStatus,
            name="document_status",
            native_enum=False,
        ),
    )
    error_message: Mapped[str] = mapped_column(nullable=True)


class DocumentEventDAO(BaseDAO, IDMixin):
    """
    DAO (ORM) модель, представляющая описание события в пайплайне обработки документа.

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

    __tablename__ = "document_events"

    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "stage",
            name="uq_document_events_document_id_stage",
        ),
    )

    document_id: Mapped[UUID]
    trace_id: Mapped[UUID]
    stage: Mapped[DocumentStage] = mapped_column(
        sa.Enum(
            DocumentStage,
            name="document_stage",
            native_enum=False,
        )
    )
    status: Mapped[DocumentStatus] = mapped_column(
        sa.Enum(
            DocumentStatus,
            name="document_status",
            native_enum=False,
        ),
    )
    started_at: Mapped[datetime] = mapped_column(nullable=True)
    finished_at: Mapped[datetime] = mapped_column(nullable=True)
    duration_ms: Mapped[float] = mapped_column(nullable=True)
    error_message: Mapped[str] = mapped_column(nullable=True)
