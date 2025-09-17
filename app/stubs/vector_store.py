import os
import json
import math
import shutil
from typing import Any

from app.domain.embedding.schemas import Vector
from app.services import VectorStore


class JSONVectorStore(VectorStore):
    """
    Заглушка векторного хранилища для локальных тестов и разработки.
    """

    def __init__(self, directory: str):
        """
        Проверяет, что `directory` является путем к директории (оканчивается слешем),
        создает её при необходимости.

        :param directory: Путь к папке, где будут храниться вектора.
        :type directory: str
        :raises ValueError: Если путь не заканчивается разделителем файловой системы.
        """

        if not directory.endswith(os.path.sep):
            raise ValueError(f"Ожидалась директория, но было получено {directory}")
        self.directory: str = directory
        os.makedirs(self.directory, exist_ok=True)

    @staticmethod
    def _normalize_path(path: str) -> str:
        return path.lstrip("/")

    def upsert(self, vectors: list[Vector]) -> None:
        """
        Сохраняет или обновляет список векторов.

        :param vectors: Список векторов для индексации.
        :type vectors: list[Vector]
        """

        if not vectors:
            return

        full_path: str = os.path.join(
            self.directory,
            f"{vectors[0].metadata.workspace_id}/{vectors[0].metadata.document_id}.json",
        )
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        data: list[dict[str, Any]] = [vector.model_dump() for vector in vectors]
        with open(full_path, "w") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)  # type: ignore[arg-type]

    def search(
        self,
        embedding: list[float],
        top_k: int,
        workspace_id: str,
    ) -> list[Vector]:
        """
        Ищет ближайшие по косинусному сходству векторы в JSON-индексе.

        :param embedding: Вектор-запрос для поиска похожих чанков.
        :type embedding: list[float]
        :param top_k: Максимальное число возвращаемых результатов.
        :type top_k: int
        :param workspace_id: Идентификатор рабочего пространства.
        :type workspace_id: str
        :return: Список из не более `top_k` объектов `Vector`, упорядоченных по убыванию сходства.
        :rtype: list[Vector]
        """

        base_path: str = os.path.join(self.directory, f"{workspace_id}/")

        if not os.path.isdir(base_path):
            return []

        similarities: list[tuple[Vector, float]] = []
        docs_list: list[str] = os.listdir(base_path)
        for filename in docs_list:
            if filename.endswith(".json"):
                filename = f"{base_path}/{filename}"
                with open(filename, "r") as file:
                    data: list[dict[str, Any]] = json.load(file)
                    for vector_data in data:
                        _vector = Vector(**vector_data)
                        similarities.append(
                            (
                                _vector,
                                self._cosine_similarity(_vector.values, embedding),
                            )
                        )

        similarities.sort(key=lambda x: x[1], reverse=True)
        return [vec for vec, _ in similarities[:top_k]]

    def delete(self, workspace_id: str, document_id: str | None = None) -> None:
        """
        Удаляет файл(-ы) индекса: конкретный документ или все пространство.

        :param workspace_id: Идентификатор пространства.
        :type workspace_id: str | None
        :param document_id: Идентификатор документа. Если указан, удаляется конкретный файл документа.
        :type document_id: str | None
        """

        if workspace_id:
            workspace_id = self._normalize_path(workspace_id)
            if document_id:
                document_id = self._normalize_path(document_id)
                full_path: str = os.path.join(
                    self.directory,
                    f"{workspace_id}/{document_id}.json",
                )
                if os.path.isfile(full_path):
                    os.remove(full_path)
            else:
                full_path: str = os.path.join(self.directory, workspace_id)
                if os.path.isdir(full_path):
                    shutil.rmtree(full_path)

    @classmethod
    def _cosine_similarity(cls, vec1: list[float], vec2: list[float]) -> float:
        """
        Вычисляет косинусное сходство между двумя векторами.

        :param vec1: Первый вектор значений.
        :type vec1: list[float]
        :param vec2: Второй вектор значений.
        :type vec2: list[float]
        :return: Значение сходства в диапазоне [0.0, 1.0].
        :rtype: float
        """

        dot_product = sum(x * y for x, y in zip(vec1, vec2))
        norm_vec1 = math.sqrt(sum(x**2 for x in vec1))
        norm_vec2 = math.sqrt(sum(x**2 for x in vec2))

        if norm_vec1 == 0 or norm_vec2 == 0:
            return 0.0

        return dot_product / (norm_vec1 * norm_vec2)
