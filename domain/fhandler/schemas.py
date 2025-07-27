from datetime import datetime

from pydantic import BaseModel


class ExtractedInfo(BaseModel):
    """
    Схема, которая содержит извлеченный из документа текст и метаданные документа.
    """

    text: str = ""
    document_page_count: int | None = None
    author: str | None = None
    creation_date: datetime | None = None
