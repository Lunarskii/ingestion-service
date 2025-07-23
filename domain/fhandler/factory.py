from domain.fhandler.extractor import (
    TextExtractor,
    PdfExtractor,
    DocxExtractor,
)


class ExtractorFactory:
    """
    Фабрика для получения узкоспециализированных экземпляров класса, наследуемых от TextExtractor.
    """

    _map: dict[str, type[TextExtractor]] = {
        "pdf": PdfExtractor,
        "docx": DocxExtractor,
    }

    @classmethod
    def get_extractor(cls, extension: str) -> TextExtractor:
        """
        Создает и отдает нужный экстрактор, способный обработать файл с определенным расширением.

        :param extension: Расширение файла. Например: '.pdf' или 'pdf'
        :type extension: str

        :return: Экстрактор текста
        :rtype: TextExtractor
        """

        if extension.startswith("."):
            extension = extension[1:]
        extractor_cls: type[TextExtractor] = cls._map.get(extension)
        if not extractor_cls:
            raise ValueError(f"Нет экстрактора для расширения '{extension}'")
        return extractor_cls()
