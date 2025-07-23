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

from domain.fhandler.schemas import ExtractedInfo
from domain.fhandler.utils import parse_date


class TextExtractor(ABC):
    """
    Класс для извлечения текста из документов.
    """

    def extract(self, document: IO[bytes]) -> ExtractedInfo:
        """
        Извлекает текст из документа.

        :param document: Исходный документ в виде буфера (файл-подобного объекта).
        :type document: IO[bytes] or BytesIO

        :return: Извлеченный текст и метаданные документа.
        :rtype: ExtractedInfo
        """

        try:
            info: ExtractedInfo = self._extract(document)
        except Exception as e:
            return ExtractedInfo(error_message=f"Unknown Error: {e}")
        else:
            return info

    @abstractmethod
    def _extract(self, document: IO[bytes]) -> ExtractedInfo: ...


class PdfExtractor(TextExtractor):
    """
    Класс для извлечения текста из документов типа PDF.
    """

    def _extract(self, document: IO[bytes]) -> ExtractedInfo:
        try:
            document = PdfReader(document)
        except PyPdfError as e:
            return ExtractedInfo(error_message=str(e))
        else:
            metadata: DocumentInformation = document.metadata
            text: str = "\n".join(page.extract_text() for page in document.pages)
            return ExtractedInfo(
                text=text,
                document_page_count=len(document.pages),
                author=metadata.author,
                creation_date=parse_date(metadata.creation_date_raw),
            )


class DocxExtractor(TextExtractor):
    """
    Класс для извлечения текста из документов типа DocX.
    """

    def _extract(self, document: IO[bytes]) -> ExtractedInfo:
        try:
            document = DocxReader(document)
        except (PackageNotFoundError, BadZipFileError) as e:
            return ExtractedInfo(error_message=str(e))
        else:
            metadata = document.core_properties
            text: str = "\n".join(paragraph.text for paragraph in document.paragraphs)
            return ExtractedInfo(
                text=text,
                document_page_count=len(document.paragraphs),
                author=metadata.author,
                creation_date=metadata.created,
            )
