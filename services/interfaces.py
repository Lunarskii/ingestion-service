from typing import Protocol

from domain.schemas import (
    Vector,
    DocumentMeta,
)


class RawStorage(Protocol):
    def save(self, file_bytes: bytes, path: str) -> None: ...


class VectorStore(Protocol):
    def upsert(self, vectors: list[Vector]) -> None: ...


class MetadataRepository(Protocol):
    def save(self, meta: DocumentMeta) -> None: ...
