from datetime import datetime

from pydantic import BaseModel


class ExtractedInfo(BaseModel):
    text: str = ""
    error_message: str = ""
    document_page_count: int | None = None
    author: str | None = None
    creation_date: datetime | None = None
