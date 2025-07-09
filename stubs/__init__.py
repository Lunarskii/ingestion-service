from services import (
    RawStorage,
    VectorStore,
    MetadataRepository,
)
from domain.schemas import (
    Vector,
    DocumentMeta,
)


class FileRawStorage(RawStorage):
    path: str = "./local_storage/raw/"

    def save(self, file_bytes: bytes, path: str) -> None:
        with open(path, "wb") as file:
            file.write(file_bytes)


class JSONVectorStore(VectorStore):
    path: str = "./local_storage/index/"

    def upsert(self, vectors: list[Vector]) -> None: ...


class SQLiteMetadataRepository(MetadataRepository):
    path: str = "сохраняет метаданные в локальный файл SQLite"

    def save(self, meta: DocumentMeta) -> None: ...
