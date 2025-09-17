import mimetypes

import magic


def get_mime_type(file: bytes | str) -> str:
    """
    Определяет MIME-тип файла по его первым байтам (magic-определение).

    :param file: Входной файл в виде байтов или строки.
    :type file: bytes | str
    :return: Строка с MIME-типом, например ``application/pdf``.
    :rtype: str
    """

    return magic.from_buffer(file, mime=True)


def get_file_extension(file: bytes | str) -> str:
    """
    Возвращает прогнозируемое расширение файла на основании его MIME-типа.

    :param file: Входной файл в виде байтов или строки.
    :return: Расширение файла в формате ``.ext``, например ``.pdf``. Если расширение
        не удалось определить, возвращается пустая строка.
    """

    mime_type: str = get_mime_type(file)
    return mimetypes.guess_extension(mime_type) or ""
