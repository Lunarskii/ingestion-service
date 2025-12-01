from io import BytesIO
from datetime import datetime

from pypdf import (
    PdfReader,
    DocumentInformation as PdfMetadata,
)

from .base import DocumentExtractor
from app.domain.extraction.schemas import (
    ExtractionResult,
    DocumentPage,
    DocumentMetadata,
)
from app.utils.datetime import parse_date


class PdfExtractor(DocumentExtractor):
    """
    Извлекает текст и метаданные из PDF-документов с помощью библиотеки ``pypdf``.
    """

    def _extract(self, document: BytesIO) -> ExtractionResult:
        document = PdfReader(document)

        pages: list[DocumentPage] = []
        for page_num, page in enumerate(document.pages, 1):
            text: str = page.extract_text()
            if text and (text := text.strip()):
                pages.append(DocumentPage(num=page_num, text=text))

        metadata: PdfMetadata | None = document.metadata
        if metadata:
            creation_date: str | None = metadata.creation_date_raw
            if creation_date:
                try:
                    creation_date: datetime | None = parse_date(creation_date)
                except Exception:
                    creation_date = None

            document_metadata = DocumentMetadata(
                title=metadata.title,
                page_count=len(pages),
                author=metadata.author,
                creation_date=creation_date,
                keywords=metadata.keywords,
                subject=metadata.subject,
            )
        else:
            document_metadata = DocumentMetadata(page_count=len(pages))

        return ExtractionResult(
            pages=pages,
            metadata=document_metadata,
        )
