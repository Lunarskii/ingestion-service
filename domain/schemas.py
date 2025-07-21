from datetime import datetime
from typing import (
    Annotated,
    Any,
)
from enum import Enum
import uuid

from pydantic import (
    BaseModel,
    Field,
    field_serializer,
)


class Vector(BaseModel):
    id: Annotated[str, Field(default_factory=lambda: str(uuid.uuid4()))]  # noqa
    values: list[float]
    metadata: dict[str, Any]


class DocumentStatus(str, Enum):
    success: str = "SUCCESS"
    failed: str = "FAILED"


class DocumentMeta(BaseModel):
    document_id: str
    workspace_id: str
    document_type: str
    detected_language: str | None = None
    document_page_count: int | None = None
    author: str | None = None
    creation_date: Annotated[datetime, Field(default_factory=datetime.now)]
    raw_storage_path: str
    file_size_bytes: int
    ingested_at: Annotated[datetime, Field(default_factory=datetime.now)]
    status: DocumentStatus = DocumentStatus.success
    error_message: str | None = None

    @field_serializer("creation_date")
    def datetime_to_str(self, value: datetime):
        if value is None:
            return value
        return datetime.strftime(value, "%Y-%m-%d %H:%M:%S")

    @field_serializer("status")
    def document_status_to_str(self, value: DocumentStatus):
        if value is None:
            return value
        return value.value
