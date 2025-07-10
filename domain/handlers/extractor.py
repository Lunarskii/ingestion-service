from abc import (
    ABC,
    abstractmethod,
)
from typing import IO

from pypdf import (
    PdfReader,
    DocumentInformation,
)
from pypdf.errors import PyPdfError
from docx import Document as DocxReader
from docx.opc.exceptions import PackageNotFoundError
from zipfile import BadZipFile as BadZipFileError
import langdetect

from domain.handlers.schemas import ExtractedInfo
from domain.handlers import utils


class TextExtractor(ABC):
    def handle(self, document: IO[bytes]) -> ExtractedInfo:
        try:
            info: ExtractedInfo = self._handle(document)
        except Exception as e:
            return ExtractedInfo(error_message=f"Unknown Error: {e}")
        else:
            return info

    @abstractmethod
    def _handle(self, document: IO[bytes]) -> ExtractedInfo: ...


class PdfExtractor(TextExtractor):
    def _handle(self, document: IO[bytes]) -> ExtractedInfo:
        try:
            document = PdfReader(document)
        except PyPdfError as e:
            return ExtractedInfo(error_message=str(e))
        else:
            metadata: DocumentInformation = document.metadata
            text: str = "\n".join(page.extract_text() for page in document.pages)
            return ExtractedInfo(
                text=text,
                detected_language=langdetect.detect(text),
                document_page_count=len(document.pages),
                author=metadata.author,
                creation_date=utils.parse_date(metadata.creation_date_raw),
            )


class DocxExtractor(TextExtractor):
    def _handle(self, document: IO[bytes]) -> ExtractedInfo:
        try:
            document = DocxReader(document)
        except (PackageNotFoundError, BadZipFileError) as e:
            return ExtractedInfo(error_message=str(e))
        else:
            metadata = document.core_properties
            text: str = "\n".join(paragraph.text for paragraph in document.paragraphs)
            return ExtractedInfo(
                text=text,
                detected_language=langdetect.detect(text),
                document_page_count=len(document.paragraphs),
                author=metadata.author,
                creation_date=metadata.created,
            )
