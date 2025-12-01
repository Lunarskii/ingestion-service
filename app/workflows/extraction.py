from app.domain.extraction.extractors import DocumentExtractor
from app.domain.extraction.schemas import ExtractionResult
from app.domain.extraction.factory import ExtractorFactory
from app.domain.extraction.exceptions import ExtractionError
from app.utils.file import get_file_extension


def extract_text_from_file(
    file: bytes,
    *,
    factory: ExtractorFactory = ExtractorFactory(),
) -> ExtractionResult:
    """
    Извлекает текст и метаданные из переданного файла.

    Определяет автоматически расширение файла по MIME-типу, по первым байтам файла.
    Используйте индивидуальные экстракторы, например PdfExtractor или DocxExtractor,
    если вам нужна более строгая типизация.

    :param file: Объект файла с атрибутами ``name`` (str) и ``file`` (байтовый поток, например ``BytesIO``).
    :param factory: Фабрика для получения экземпляров ``TextExtractor``. По умолчанию
                    создаётся экземпляр ``ExtractorFactory()`` при импорте модуля; при необходимости
                    для тестирования/инъекций рекомендуется передавать фабрику явно.

    :return: Результат извлечения: страницы документа и метаданные документа.
    :raises ExtractionError: Если не найден нужный экстрактор или экстрактор выбросил
                             ошибку при обработке файла.
    """

    extension: str = get_file_extension(file)
    try:
        extractor: DocumentExtractor = factory.get_extractor(extension)
    except ExtractionError:
        pass
    else:
        return extractor.extract(file)
    raise ExtractionError(f"Нет экстрактора для документа с расширением {extension}")
