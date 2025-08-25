from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)
import sqlalchemy as sa

from domain.document.schemas import DocumentStatus
from domain.database.models import BaseDAO
from domain.database.mixins import UUIDMixin


class DocumentDAO(BaseDAO, UUIDMixin):
    __tablename__ = "documents"

    workspace_id: Mapped[UUID]
    name: Mapped[str]
    media_type: Mapped[str]
    detected_language: Mapped[str] = mapped_column(nullable=True)
    page_count: Mapped[int] = mapped_column(nullable=True)
    author: Mapped[str] = mapped_column(nullable=True)
    creation_date: Mapped[datetime] = mapped_column(nullable=True)
    raw_storage_path: Mapped[str]
    size_bytes: Mapped[int]
    ingested_at: Mapped[datetime]
    status: Mapped[DocumentStatus] = mapped_column(
        sa.Enum(
            DocumentStatus,
            name="document_status",
            native_enum=False,
        ),
    )
    error_message: Mapped[str]
