import os
import json
import math

from domain.schemas import Vector
from services import VectorStore
from services.exc import (
    VectorStoreMissingMetadata,
    VectorStoreDocumentsNotFound,
    VectorStoreMissingData,
)
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
        Сохраняет векторы в JSON-файл, именованный workspace_id/document_id.json.
        """

        if not vectors:
            raise VectorStoreMissingData()

        document_id: str | None = vectors[0].metadata.get("document_id", None)
        workspace_id: str | None = vectors[0].metadata.get("workspace_id", None)
        if not (document_id and workspace_id):
            raise VectorStoreMissingMetadata()

        full_path: str = os.path.join(self.directory, f"{workspace_id}/{document_id}.json")
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        data = [vector.model_dump() for vector in vectors]
        with open(full_path, "w") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    def search(self, vector: Vector, top_k: int, workspace_id: str) -> list[Vector]:
        # TODO doc
        base_path: str = os.path.join(self.directory, f"{workspace_id}/")
        similarities: list[tuple[Vector, float]] = []

        if not os.path.isdir(base_path) or not (docs_list := os.listdir(base_path)):
            raise VectorStoreDocumentsNotFound()

        for filename in docs_list:
            if filename.endswith(".json"):
                filename = f"{base_path}/{filename}"
                with open(filename, "r") as file:
                    data: dict = json.load(file)
                    for vec_data in data:
                        file_vec = Vector(**vec_data)
                        similarities.append((file_vec, self._cosine_similarity(file_vec.values, vector.values)))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return [vec for vec, _ in similarities[:top_k]]

    @classmethod
    def _cosine_similarity(cls, vec1: list[float], vec2: list[float]) -> float:
        """
        Вычисляет косинусное сходство между двумя векторами.
        """

        dot_product = sum(x * y for x, y in zip(vec1, vec2))
        norm_vec1 = math.sqrt(sum(x**2 for x in vec1))
        norm_vec2 = math.sqrt(sum(x**2 for x in vec2))

        if norm_vec1 == 0 or norm_vec2 == 0:
            return 0.0

        return dot_product / (norm_vec1 * norm_vec2)
