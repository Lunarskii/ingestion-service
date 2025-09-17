from app.domain.extraction.base import (
    TextExtractor,
    PdfExtractor,
    DocxExtractor,
)
from app.domain.extraction.exceptions import ExtractionError


class ExtractorFactory:
    """
    Фабрика для получения экземпляров экстракторов текста, основанных на расширении файла.
    Использует внутреннюю карту ``_map``, связывающую расширения с классами-реализациями.
    """

    _map: dict[str, type[TextExtractor]] = {
        "pdf": PdfExtractor,
        "docx": DocxExtractor,
    }

    @classmethod
    def get_extractor(cls, extension: str) -> TextExtractor:
        """
        Возвращает экстрактор, подходящий для обработки файла с заданным расширением.

        Принимает расширение файла, например ``pdf`` или ``.docx``. Если расширение начинается с
        точки, точка будет отброшена.

        :param extension: Расширение файла (с точкой или без).
        :type extension: str
        :return: Экземпляр класса, наследник ``TextExtractor``, подходящий для данного формата.
        :rtype: TextExtractor
        :raises ExtractError: Если нет зарегистрированного экстрактора для переданного расширения.
        """

        extension = extension.lstrip(".")
        extractor_cls: type[TextExtractor] = cls._map.get(extension)
        if not extractor_cls:
            raise ExtractionError(f"Нет экстрактора для расширения '{extension}'")
        return extractor_cls()
