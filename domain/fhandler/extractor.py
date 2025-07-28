from abc import (
    ABC,
    abstractmethod,
)
from typing import IO

from pypdf import (
    PdfReader,
    DocumentInformation,
)
from docx import Document as DocxReader

from domain.fhandler.schemas import ExtractedInfo
from domain.fhandler.utils import parse_date
from domain.fhandler.exc import ExtractError


class TextExtractor(ABC):
    """
    Абстрактный базовый класс для извлечения текста и метаданных из разных
    форматов документов.

    Реализация должна предоставлять метод `_extract()`, возвращающий `ExtractedInfo`.
    Внешний метод `extract()` оборачивает вызов в общий обработчик ошибок.
    """

    def extract(self, document: IO[bytes]) -> ExtractedInfo:
        """
        Универсальный метод для извлечения текста и метаданных из переданного документа.

        :param document: Файлоподобный объект с байтами документа.
        :type document: IO[bytes]
        :return: Объект `ExtractedInfo`, включающий в себя текст и метаданные документа.
        :rtype: ExtractedInfo
        :raises ExtractError: В случае любой ошибки при разборе документа
        """

        try:
            info: ExtractedInfo = self._extract(document)
        except Exception as e:
            raise ExtractError(str(e))
        else:
            return info

    @abstractmethod
    def _extract(self, document: IO[bytes]) -> ExtractedInfo:
        """
        Абстрактный метод, реализуемый потомками для конкретного формата документа.

        :param document: Файлоподобный объект с байтами документа.
        :type document: IO[bytes]
        :return: Объект `ExtractedInfo`, включающий в себя текст и метаданные документа.
        :rtype: ExtractedInfo
        """
        ...


class PdfExtractor(TextExtractor):
    """
    Извлекает текст и метаданные из PDF-документов с помощью библиотеки pypdf.
    """

    def _extract(self, document: IO[bytes]) -> ExtractedInfo:
        document = PdfReader(document)
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
    Извлекает текст и метаданные из DOCX-документов с помощью python-docx.
    """

    def _extract(self, document: IO[bytes]) -> ExtractedInfo:
        document = DocxReader(document)
        metadata = document.core_properties
        text: str = "\n".join(paragraph.text for paragraph in document.paragraphs)
        return ExtractedInfo(
            text=text,
            document_page_count=len(document.paragraphs),
            author=metadata.author,
            creation_date=metadata.created,
        )
