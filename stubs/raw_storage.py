import os

from services import RawStorage
from config import stub_settings


class FileRawStorage(RawStorage):
    """
    Заглушка хранилища сырых файлов для локальных тестов и разработки.
    """

    def __init__(
        self,
        *,
        directory: str = stub_settings.raw_storage_path,
    ):
        """
        Проверяет, что `directory` является путем к директории (оканчивается слешем),
        создает её при необходимости.

        :param directory: Путь к папке, где будут храниться файлы.
        :type directory: str
        :raises ValueError: Если путь не заканчивается разделителем файловой системы.
        """

        if not directory.endswith(os.path.sep):
            raise ValueError(f"Ожидалась директория, но было получено {directory}")
        self.directory: str = directory
        os.makedirs(self.directory, exist_ok=True)

    def save(self, file_bytes: bytes, path: str) -> None:
        """
        Сохраняет бинарные данные в файл относительно `self.directory`.

        :param file_bytes: Содержимое файла.
        :type file_bytes: bytes
        :param path: Относительный путь внутри корня директории.
        :type path: str
        """

        relative_path: str = path.lstrip("/\\")
        full_path: str = os.path.join(self.directory, relative_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as file:
            file.write(file_bytes)
