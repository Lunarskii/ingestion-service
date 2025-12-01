from pydantic import Field

from app.schemas import BaseSchema
from app.types import (
    DocumentPage,
    DocumentMetadata,
)


class ExtractionResult(BaseSchema):
    """
    Информация, извлечённая из документа.
    Содержит страницы документа и метаданные документа.
    """

    pages: list[DocumentPage] = Field(..., description="Страницы документа")
    metadata: DocumentMetadata = Field(..., description="Метаданные документа")
