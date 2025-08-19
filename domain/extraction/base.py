from abc import (
    ABC,
    abstractmethod,
)
from datetime import datetime
from io import BytesIO

from pypdf import (
    PdfReader,
    DocumentInformation as PdfMetadata,
)
from docx import Document as DocxReader
from docx.opc.coreprops import CoreProperties as DocxMetadata
import mammoth
import weasyprint

from domain.extraction.schemas import (
    Page,
    ExtractedInfo,
)
from domain.extraction.utils import parse_date
from domain.extraction.exceptions import ExtractionError


class TextExtractor(ABC):
    """
    Абстрактный базовый класс для извлечения текста и метаданных из разных
    форматов документов.

    Реализация должна предоставлять метод `_extract()`, возвращающий `ExtractedInfo`.
    Внешний метод `extract()` оборачивает вызов в общий обработчик ошибок.
    """

    def extract(self, document: BytesIO) -> ExtractedInfo:
        """
        Универсальный метод для извлечения текста и метаданных из переданного документа.

        :param document: Файлоподобный объект с байтами документа.
        :type document: BytesIO
        :return: Схема ``ExtractedInfo``, включающая в себя текст и метаданные документа.
        :rtype: ExtractedInfo
        :raises ExtractError: В случае любой ошибки при разборе документа
        """

        try:
            info: ExtractedInfo = self._extract(document)
        except Exception as e:
            raise ExtractionError(str(e))
        else:
            return info

    @abstractmethod
    def _extract(self, document: BytesIO) -> ExtractedInfo:
        """
        Абстрактный метод, реализуемый потомками для конкретного формата документа.

        :param document: Файлоподобный объект с байтами документа.
        :type document: BytesIO
        :return: Схема ``ExtractedInfo``, включающая в себя текст и метаданные документа.
        :rtype: ExtractedInfo
        """
        ...


class PdfExtractor(TextExtractor):
    """
    Извлекает текст и метаданные из PDF-документов с помощью библиотеки ``pypdf``.
    """

    def _extract(self, document: BytesIO) -> ExtractedInfo:
        document = PdfReader(document)
        metadata: PdfMetadata | None = document.metadata
        pages: list[Page] = [
            Page(num=page_num, text=page.extract_text() or "")
            for page_num, page in enumerate(document.pages)
        ]

        return ExtractedInfo(
            pages=pages,
            document_page_count=len(pages),
            author=metadata.author if metadata else None,
            creation_date=parse_date(metadata.creation_date_raw if metadata else None),
        )


class DocxExtractor(TextExtractor):
    """
    Извлекает текст и метаданные из DOCX-документов с помощью библиотеки ``python-docx``.
    """

    def _extract(self, document: BytesIO) -> ExtractedInfo:
        docx_document = DocxReader(document)
        metadata: DocxMetadata = docx_document.core_properties
        author: str = metadata.author
        creation_date: datetime = metadata.created

        pdf_document = PdfReader(BytesIO(self._convert_to_pdf(document)))
        pages: list[Page] = [
            Page(num=page_num, text=page.extract_text())
            for page_num, page in enumerate(pdf_document.pages)
        ]

        return ExtractedInfo(
            pages=pages,
            document_page_count=len(pages),
            author=author,
            creation_date=creation_date,
        )

    @classmethod
    def _convert_to_pdf(cls, document: BytesIO) -> bytes:
        html = mammoth.convert_to_html(document).value
        return weasyprint.HTML(string=html).write_pdf()
