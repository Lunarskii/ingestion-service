import mimetypes

import magic


def get_file_extension(file: bytes | str) -> str:
    """
    Определяет расширение файла по его первым байтам, хедеру.

    :param file: Любой файл в виде байтов или строки.
    :type file: bytes | str

    :return: Расширение файла в формате '.ext', например '.pdf' или '.docx'.
    :rtype: str
    """

    mime_type: str = magic.from_buffer(file, mime=True)
    return mimetypes.guess_extension(mime_type) or ""
