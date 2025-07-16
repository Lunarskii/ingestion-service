import os
import json

from domain.schemas import Vector
from services import VectorStore
from config import storage_settings


class JSONVectorStore(VectorStore):
    """
    Реализация VectorStore для локальной разработки.
    """

    def __init__(
        self,
        *,
        directory: str = storage_settings.index_path,
    ):
        if not directory.endswith(os.path.sep):
            raise ValueError(f"Ожидалась директория, но было получено {directory}")
        self.directory: str = directory
        os.makedirs(self.directory, exist_ok=True)

    def upsert(self, vectors: list[Vector]) -> None:
        """
        Сохраняет векторы в JSON-файл, именованный 'document_id'.json.
        """

        if not vectors:
            return

        document_id: str | None = vectors[0].metadata.get("document_id", None)
        if not document_id:
            raise ValueError("Вектор должен содержать 'document_id'")

        full_path: str = os.path.join(self.directory, f"{document_id}.json")
        data = [vector.model_dump() for vector in vectors]
        with open(full_path, "w") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
