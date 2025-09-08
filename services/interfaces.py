from typing import (
    Protocol,
    Any,
)

from pydantic import BaseModel

from domain.embedding import Vector


class RawStorage(Protocol):
    """
    Интерфейс для сервиса сохранения необработанных ("сырых") файлов.

    Реализация может быть основана на локальной файловой системе,
    облачном хранилище (например, AWS S3, GCP Storage, MinIO) или
    распределённых файловых системах.
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

        В случае, если путь указывает на префикс, должны быть удалены все вложенные файлы.

        :param path: Путь к файлу или префикс (например, директория) для удаления.
        :type path: str
        """

        ...

    def exists(self, path: str) -> bool:
        """
        Проверяет, существует ли файл по указанному пути.

        :param path: Путь к файлу.
        :type path: str
        :return: True, если файл существует, иначе False.
        :rtype: bool
        """

        ...


class VectorStore(Protocol):
    """
    Интерфейс для хранилища векторных представлений документов.

    Используется для добавления, поиска и удаления векторных эмбеддингов
    (например, для реализации поиска по смыслу).
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
        embedding: list[float],
        top_k: int,
        workspace_id: str,
    ) -> list[Vector]:
        """
        Выполняет поиск наиболее похожих векторов в заданном рабочем пространстве.

        :param embedding: Вектор-запрос, для которого ищутся ближайшие по сходству вектора.
        :type embedding: list[float]
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
    """
    Универсальный интерфейс репозитория для CRUD-операций над моделями.

    Конкретные реализации могут работать с:
        - базой данных (SQL, NoSQL);
        - внешним API;
        - in-memory структурами данных (например, для тестов).
    """

    async def create(self, **kwargs) -> BaseModel:
        """
        Создаёт и сохраняет новый объект.

        :param kwargs: Аргументы, необходимые для создания объекта.
        :return: Созданный объект.
        :rtype: BaseModel
        """

        ...

    async def get(self, key: Any) -> BaseModel:
        """
        Получает объект по ключу (например, по ID).

        :param key: Уникальный идентификатор объекта.
        :return: Объект модели.
        :rtype: BaseModel
        """

        ...

    async def get_n(
        self,
        limit: int | None = None,
        offset: int | None = None,
        **kwargs,
    ) -> list[BaseModel]:
        """
        Возвращает список объектов с возможностью пагинации и фильтрации.

        :param limit: Максимальное количество объектов (опционально).
        :type limit: int | None
        :param offset: Смещение для пагинации (опционально).
        :type offset: int | None
        :param kwargs: Дополнительные параметры фильтрации.
        :return: Список объектов.
        :rtype: list[BaseModel]
        """

        ...

    async def update(self, key: Any, **kwargs) -> BaseModel:
        """
        Обновляет существующий объект по ключу.

        :param key: Уникальный идентификатор объекта.
        :param kwargs: Поля и их новые значения.
        :return: Обновлённый объект.
        :rtype: BaseModel
        """

        ...

    async def delete(self, key: Any) -> None:
        """
        Удаляет объект по ключу.

        :param key: Уникальный идентификатор объекта.
        """

        ...

    async def exists(self, key: Any) -> bool:
        """
        Проверяет существование объекта по ключу.

        :param key: Уникальный идентификатор объекта.
        :return: True, если объект существует, иначе False.
        :rtype: bool
        """

        ...
