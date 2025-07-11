import os

from services import RawStorage


class FileRawStorage(RawStorage):
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(self.path), exist_ok=True)

    def save(self, file_bytes: bytes, path: str) -> None:
        with open(path, "wb") as file:
            file.write(file_bytes)
