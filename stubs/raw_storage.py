from services import RawStorage
from config import default_settings


class FileRawStorage(RawStorage):
    def save(self, file_bytes: bytes, path: str) -> None:
        with open(default_settings.raw_storage_path, "wb") as file:
            file.write(file_bytes)
