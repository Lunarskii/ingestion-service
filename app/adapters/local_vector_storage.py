import os
import json
import math
import shutil
from typing import (
    Any,
    Literal,
)

from app.types import (
    Vector,
    ScoredVector,
)
from app.interfaces import VectorStorage
from app.core import logger


class LocalVectorStorage(VectorStorage):
    """
    Реализация локального векторного хранилища.
    Хранит информацию как JSON.
    """

    def __init__(self, directory: str):
        """
        Проверяет, что параметр `directory` является директорией,
        создает её при необходимости.

        :param directory: Базовый путь, куда будут сохраняться директории/файлы.

        :raises ValueError: Если переданный параметр не является директорией.
        """

        if os.path.isfile(directory):
            raise ValueError(
                f"Передаваемый параметр 'directory' должен быть директорией, "
                f"но было получено {directory}",
            )

        self.directory: str = directory
        if not directory.endswith(os.path.sep):
            self.directory += os.path.sep
        os.makedirs(self.directory, exist_ok=True)

        self._logger = logger.bind(base_dir=directory)

    @staticmethod
    def _normalize_path(path: str) -> str:
        return path.lstrip("/")

    def upsert(self, vectors: list[Vector]) -> None:
        """
        Сохраняет или обновляет список векторов.

        :param vectors: Список векторов для индексации.

        :raises FileNotFoundError: Если произошла ошибка во время записи в файл или часть пути не была создана.
                                   Возможно проблема с конкурентностью и путь был удален в процессе.
        :raises Exception: Если произошла неизвестная ошибка при записи в файл.
        """

        if not vectors:
            self._logger.warning("Не были переданы вектора для сохранения")
            return

        full_path: str = os.path.join(
            self.directory,
            f"{vectors[0].payload.workspace_id}/{vectors[0].payload.document_id}.json",
        )
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        data: list[dict[str, Any]] = [vector.model_dump() for vector in vectors]
        try:
            with open(full_path, "w") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)  # type: ignore[arg-type]
        except FileNotFoundError:
            self._logger.warning(
                "Часть пути не была создана, возможно проблема с конкурентностью и путь был удален в процессе",
                path=full_path,
            )
            raise
        except Exception as e:
            self._logger.error(
                "Неизвестная ошибка при записи в файл",
                path=full_path,
                error_message=str(e),
            )
            raise

    def search(
        self,
        embedding: list[float],
        top_k: int | Literal["all"],
        workspace_id: str,
        *,
        score_threshold: float | None = 0.35,
    ) -> list[ScoredVector]:
        """
        Ищет ближайшие по косинусному сходству векторы в JSON-индексе.

        :param embedding: Вектор-запрос для поиска похожих чанков.
        :param top_k: Максимальное число возвращаемых результатов.
        :param workspace_id: Идентификатор рабочего пространства.
        :param score_threshold: Минимальный порог оценки для результата. Если он задан,
                                менее похожие результаты не будут возвращены. Оценка
                                возвращаемого результата может быть выше или меньше
                                порогового значения в зависимости от используемой
                                функции расстояния. Например, для косинусного
                                сходства будут возвращены только более высокие оценки.

        :return: Список из не более `top_k` объектов `Vector`, упорядоченных по убыванию сходства.
        """

        base_path: str = os.path.join(self.directory, workspace_id)
        if not os.path.isdir(base_path):
            self._logger.warning(
                "Переданный путь не является директорией",
                path=base_path,
            )
            return []

        vectors: list[ScoredVector] = []

        for filename in os.listdir(base_path):
            if not filename.endswith(".json"):
                continue

            full_path: str = os.path.join(base_path, filename)
            try:
                with open(full_path, "r") as file:
                    data: list[dict[str, Any]] = json.load(file)
            except FileNotFoundError:
                self._logger.warning(
                    "Файл не найден, возможно проблема с конкурентностью и файл был удален в процессе",
                    path=full_path,
                )
                continue
            except Exception as e:
                self._logger.error(
                    "Неизвестная ошибка при чтении файла",
                    path=full_path,
                    error_message=str(e),
                )
                continue

            for vector_data in data:
                values: list[float] | None = vector_data.get("values")
                if not values:
                    continue

                similarity: float = self._cosine_similarity(values, embedding)
                if similarity >= score_threshold:
                    vectors.append(ScoredVector(**vector_data, score=similarity))

        if isinstance(top_k, str) and top_k == "all":
            return vectors

        vectors.sort(key=lambda x: x.score, reverse=True)
        return vectors[:top_k]

    def delete(self, workspace_id: str, document_id: str) -> None:
        """
        Удаляет вектора в указанном рабочем пространстве по указанному идентификатору документа.

        :param workspace_id: Идентификатор рабочего пространства.
        :param document_id: Идентификатор документа, по которому будут удалены вектора.

        :raises FileNotFoundError: Если переданный путь не является файлом.
        """

        full_path: str = os.path.join(
            self.directory,
            f"{workspace_id}/{document_id}.json",
        )
        if not os.path.isfile(full_path):
            message: str = "Переданный путь не является файлом"
            self._logger.warning(message, path=full_path)
            raise FileNotFoundError(message)
        os.remove(full_path)

    def delete_by_workspace(self, workspace_id: str) -> None:
        """
        Удаляет векторы в указанном рабочем пространстве.

        :param workspace_id: Идентификатор пространства, из которого будут удалены вектора.

        :raises FileNotFoundError: Если переданный путь не является существующей директорией.
        """

        full_path: str = os.path.join(self.directory, workspace_id)
        if not os.path.isdir(full_path):
            message: str = "Переданный путь не является существующей директорией"
            self._logger.warning(message, path=full_path)
            raise FileNotFoundError(message)
        shutil.rmtree(full_path)

    @classmethod
    def _cosine_similarity(cls, vec1: list[float], vec2: list[float]) -> float:
        """
        Вычисляет косинусное сходство между двумя векторами.

        :param vec1: Первый вектор значений.
        :param vec2: Второй вектор значений.
        :return: Значение сходства в диапазоне [0.0, 1.0].
        """

        dot_product = sum(x * y for x, y in zip(vec1, vec2))
        norm_vec1 = math.sqrt(sum(x**2 for x in vec1))
        norm_vec2 = math.sqrt(sum(x**2 for x in vec2))

        if norm_vec1 == 0 or norm_vec2 == 0:
            return 0.0

        return dot_product / (norm_vec1 * norm_vec2)
