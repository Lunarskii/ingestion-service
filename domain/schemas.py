from datetime import datetime

from pydantic import (
    BaseModel,
    field_serializer,
)


class Vector(BaseModel):
    document_id: str
    embedding: list[float]
    metadata: dict


class DocumentMeta(BaseModel):
    document_id: str
    document_type: str
    detected_language: str
    document_page_count: int | None = None
    author: str | None = None
    creation_date: datetime
    raw_storage_path: str
    file_size_bytes: int

    @field_serializer("creation_date")
    def datetime_to_str(self, value: datetime):
        if value is None:
            return value
        return datetime.strftime(value, "%Y-%m-%d %H:%M:%S")
