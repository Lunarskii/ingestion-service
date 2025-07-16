from datetime import datetime
from typing import (
    Annotated,
    Any,
)
import uuid

from pydantic import (
    BaseModel,
    Field,
    field_serializer,
)


class Vector(BaseModel):
    id: Annotated[str, Field(default_factory=lambda: str(uuid.uuid4()))] # noqa
    values: list[float]
    metadata: dict[str, Any]


class DocumentMeta(BaseModel):
    document_id: str
    document_type: str
    detected_language: str
    document_page_count: int | None = None
    author: str | None = None
    creation_date: Annotated[datetime, Field(default_factory=datetime.now)]
    raw_storage_path: str
    file_size_bytes: int

    @field_serializer("creation_date")
    def datetime_to_str(self, value: datetime):
        if value is None:
            return value
        return datetime.strftime(value, "%Y-%m-%d %H:%M:%S")
