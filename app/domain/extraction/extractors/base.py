from typing import TYPE_CHECKING
from abc import (
    ABC,
    abstractmethod,
)
from io import BytesIO

from app.domain.extraction.exceptions import ExtractionError


if TYPE_CHECKING:
    from app.domain.extraction.schemas import ExtractionResult


class DocumentExtractor(ABC):
    """
    Абстрактный базовый класс для извлечения текста и метаданных из разных
    форматов документов.
    """

    def extract(self, document: bytes | BytesIO) -> "ExtractionResult":
        """
        Универсальный метод для извлечения текста и метаданных из переданного документа.

        :param document: File-like объект с байтами документа или байты документа.

        :return: Результат извлечения: страницы документа и метаданные документа.
        :raises ExtractError: В случае любой ошибки при разборе документа.
        """

        if isinstance(document, bytes):
            document = BytesIO(document)

        try:
            info: "ExtractionResult" = self._extract(document)
        except Exception as e:
            raise ExtractionError(str(e))
        else:
            return info

    @abstractmethod
    def _extract(self, document: BytesIO) -> "ExtractionResult":
        """
        Абстрактный метод, реализуемый потомками для конкретного формата документа.

        :param document: File-like объект с байтами документа.

        :return: Результат извлечения: страницы документа и метаданные документа.
        """
        ...
