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
from domain.extraction.exceptions import ExtractionError


if TYPE_CHECKING:
    from domain.document.schemas import File


def extract(
    file: "File",
    *,
    factory: ExtractorFactory = ExtractorFactory(),
) -> ExtractedInfo:
    """
    Попытка извлечь текст и метаданные из переданного файла, перебирая все суффиксы его имени.

    Функция итерирует `Path(file.name).suffixes` (например, для `archive.tar.gz` —
    ``['.tar', '.gz']``), для каждого суффикса пробует получить соответствующий
    экстрактор через ``factory.get_extractor`` и при первом успешном варианте
    вызывает ``extractor.extract(file.file)``.

    :param file: Объект файла с атрибутами ``name`` (str) и ``file`` (байтовый поток, например ``BytesIO``).
    :type file: File
    :param factory: Фабрика для получения экземпляров ``TextExtractor``. По умолчанию
        создаётся экземпляр ``ExtractorFactory()`` при импорте модуля; при необходимости
        для тестирования/инъекций рекомендуется передавать фабрику явно.
    :type factory: ExtractorFactory
    :return: Схема ``ExtractedInfo``, включающая в себя текст и метаданные документа.
    :rtype: ExtractedInfo
    :raises ExtractionError: Если ни для одного из суффиксов имени файла не найден подходящий экстрактор,
        либо если фабрика выбросила ошибку при попытке получить экстрактор.
    """

    path = Path(file.name)
    suffixes: list[str] = path.suffixes
    for suffix in suffixes:
        try:
            extractor: TextExtractor = factory.get_extractor(suffix)
        except ExtractionError:
            pass
        else:
            return extractor.extract(file.file)
    raise ExtractionError(
        f"Нет экстрактора для документа '{file.name}' с расширениями {suffixes}"
    )


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
