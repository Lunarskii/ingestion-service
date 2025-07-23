from typing import Protocol

from domain.schemas import (
    Vector,
    DocumentMeta,
)


class RawStorage(Protocol):
    """
    Интерфейс для хранения необработанных файлов.
    """

    def save(self, file_bytes: bytes, path: str) -> None:
        """
        Сохраняет файл в байтах по указанному пути.
        """
        ...


class VectorStore(Protocol):
    """
    Интерфейс для хранения и индексации векторных документов.
    """

    def upsert(self, vectors: list[Vector]) -> None:
        """
        Вставляет или обновляет векторы в хранилище.
        """
        ...

    def search(self, vector: Vector, top_k: int, workspace_id: str) -> list[Vector]:
        # TODO doc
        ...


class MetadataRepository(Protocol):
    """
    Интерфейс для хранения метаданных документа.
    """

    def save(self, meta: DocumentMeta) -> None:
        """
        Сохраняет метаданные документа.
        """
        ...
