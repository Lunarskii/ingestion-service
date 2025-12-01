from io import BytesIO

from pypdf import PdfReader
from docx import Document as DocxReader
from docx.opc.coreprops import CoreProperties as DocxMetadata
import mammoth
import weasyprint

from .base import DocumentExtractor
from app.domain.extraction.schemas import (
    ExtractionResult,
    DocumentPage,
    DocumentMetadata,
)


class DocxExtractor(DocumentExtractor):
    """
    Извлекает текст и метаданные из DOCX-документов с помощью библиотеки ``python-docx``.
    """

    def _extract(self, document: BytesIO) -> ExtractionResult:
        docx_document = DocxReader(document)
        metadata: DocxMetadata = docx_document.core_properties

        pdf_document = PdfReader(BytesIO(self._convert_to_pdf(document)))
        pages: list[DocumentPage] = []
        for page_num, page in enumerate(pdf_document.pages, 1):
            text: str = page.extract_text()
            if text and (text := text.strip()):
                pages.append(DocumentPage(num=page_num, text=text))

        return ExtractionResult(
            pages=pages,
            metadata=DocumentMetadata(
                title=metadata.title,
                language=metadata.language,
                page_count=len(pages),
                author=metadata.author,
                creation_date=metadata.created,
                keywords=metadata.keywords,
                category=metadata.category,
                subject=metadata.subject,
            ),
        )

    @classmethod
    def _convert_to_pdf(cls, document: BytesIO) -> bytes:
        html = mammoth.convert_to_html(document).value
        return weasyprint.HTML(string=html).write_pdf()
