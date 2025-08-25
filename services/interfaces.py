from typing import (
    Protocol,
    Any,
)

from pydantic import BaseModel

from domain.embedding import Vector


class RawStorage(Protocol):
    """
    Интерфейс для сервиса сохранения необработанных ("сырых") файлов.
    """

    def save(self, file_bytes: bytes, path: str) -> None:
        """
        Сохраняет бинарные данные файла в сырое хранилище.

        :param file_bytes: Содержимое файла в виде байтов.
        :type file_bytes: bytes
        :param path: Логический или файловый путь, по которому нужно сохранить файл.
        :type path: str
        """
        ...

    def get(self, path: str) -> bytes:
        """
        Возвращает бинарные данные файла по указанному пути.

        :param path: Логический или файловый путь к файлу.
        :type path: str
        :return: Содержимое файла в виде байтов.
        :rtype: bytes
        """
        ...

    def delete(self, path: str) -> None:
        """
        Удаляет файл или префикс (директорию) по указанному пути.

        :param path: Путь к файлу или префикс (например, директория) для удаления.
        :type path: str
        """
        ...

    def exists(self, path: str) -> bool:
        ...


class VectorStore(Protocol):
    """
    Интерфейс для хранилища векторных представлений документа.
    """

    def upsert(self, vectors: list[Vector]) -> None:
        """
        Добавляет или обновляет список векторов в хранилище.

        :param vectors: Список объектов `Vector`, содержащих значения эмбеддингов
                        и сопутствующие метаданные.
        :type vectors: list[Vector]
        """
        ...

    def search(
        self,
        vector: list[float],
        top_k: int,
        workspace_id: str,
    ) -> list[Vector]:
        """
        Выполняет поиск наиболее похожих векторов в заданном рабочем пространстве.

        :param vector: Вектор-запрос, для которого ищутся ближайшие по сходству вектора.
        :type vector: list[float]
        :param top_k: Максимальное количество возвращаемых результатов.
        :type top_k: int
        :param workspace_id: Идентификатор рабочего пространства для сегрегации индекса.
        :type workspace_id: str
        :return: Список из не более `top_k` объектов `Vector`, отсортированных по релевантности.
        :rtype: list[Vector]
        """
        ...

    def delete(self, workspace_id: str, document_id: str | None = None) -> None:
        """
        Удаляет векторы по workspace_id или конкретному документу (document_id).

        Если указан только ``workspace_id``, удаляется весь индекс пространства.
        Если указан также и ``document_id``, удаляется конкретный файл индекса в пространстве.

        :param workspace_id: Идентификатор рабочего пространства.
        :type workspace_id: str | None
        :param document_id: Идентификатор документа (опционально).
        :type document_id: str | None
        """
        ...


class Repository(Protocol):
    async def create(self, **kwargs: Any) -> BaseModel:
        ...

    async def get(self, key: Any) -> BaseModel:
        ...

    async def get_n(
        self,
        limit: int | None = None,
        offset: int | None = None,
        **kwargs: Any,
    ) -> list[BaseModel]:
        ...

    async def update(self, key: Any, **kwargs: Any) -> BaseModel:
        ...

    async def delete(self, key: Any) -> None:
        ...

    async def exists(self, key: Any) -> bool:
        ...
