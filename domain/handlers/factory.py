from domain.handlers import (
    TextExtractor,
    PdfExtractor,
    DocxExtractor,
)


class ExtractorFactory:
    _map: dict[str, type[TextExtractor]] = {
        "pdf": PdfExtractor,
        "docx": DocxExtractor,
    }

    @classmethod
    def get_extractor(cls, extension: str) -> TextExtractor:
        if extension.startswith("."):
            extension = extension[1:]
        extractor_cls: type[TextExtractor] = cls._map.get(extension)
        if not extractor_cls:
            raise ValueError(f"No extractor for extension '{extension}'")
        return extractor_cls()
