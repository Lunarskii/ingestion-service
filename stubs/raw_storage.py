import os

from services import RawStorage
from config import storage_settings


class FileRawStorage(RawStorage):
    """
    Реализация RawStorage для локальной разработки.
    """

    def __init__(
        self,
        *,
        directory: str = storage_settings.raw_storage_path,
    ):
        self.directory: str = directory
        os.makedirs(directory, exist_ok=True)

    def save(self, file_bytes: bytes, path: str) -> None:
        """
        Сохраняет файл на локальный диск.
        """

        full_path: str = os.path.join(self.directory, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as file:
            file.write(file_bytes)
