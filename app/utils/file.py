import mimetypes

import magic


_types_map: dict[str, str] = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}


def get_mime_type(file: bytes | str) -> str:
    """
    Определяет MIME-тип файла по его первым байтам (magic-определение).

    :param file: Входной файл в виде байтов или строки.

    :return: Строка с MIME-типом, например ``application/pdf``.
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
    extension: str | None = mimetypes.guess_extension(mime_type)
    if not extension:
        extension = _types_map.get(mime_type, None)
    return extension or ""
