from typing import TYPE_CHECKING
from pathlib import Path

from domain.extraction.base import (
    TextExtractor,
    PdfExtractor,
    DocxExtractor,
)
from domain.extraction.schemas import (
    Page,
    ExtractedInfo,
)
from domain.extraction.factory import ExtractorFactory
from domain.extraction.exc import ExtractionError


if TYPE_CHECKING:
    from domain.document.schemas import File


def extract(
    file: "File",
    *,
    factory: ExtractorFactory = ExtractorFactory(),
) -> ExtractedInfo:
    path = Path(file.name)
    suffixes: list[str] = path.suffixes
    for suffix in suffixes:
        try:
            extractor: TextExtractor = factory.get_extractor(suffix)
        except ExtractionError:
            pass
        else:
            return extractor.extract(file.file)
    raise ExtractionError(f"Нет экстрактора для документа '{file.name}' с расширениями {suffixes}")


__all__ = [
    "TextExtractor",
    "PdfExtractor",
    "DocxExtractor",
    "Page",
    "ExtractedInfo",
    "ExtractorFactory",
    "ExtractionError",
    "extract",
]
