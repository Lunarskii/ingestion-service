from datetime import datetime

from pydantic import BaseModel


class ExtractedInfo(BaseModel):
    text: str = ""
    error_message: str = ""
    detected_language: str | None = None
    document_page_count: int | None = None
    author: str | None = None
    creation_date: datetime | None = None
