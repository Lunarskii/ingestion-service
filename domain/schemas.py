from datetime import datetime

from pydantic import BaseModel


class Vector(BaseModel):
    document_id: str
    embedding: list[float]
    metadata: dict


# TODO нужно привести creation_date к единому виду (без TZ) при сериализации
class DocumentMeta(BaseModel):
    document_id: str
    document_type: str | None = None
    detected_language: str | None = None
    document_page_count: int | None = None
    author: str | None = None
    creation_date: datetime | None = None
