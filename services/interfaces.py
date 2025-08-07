from typing import (
    Protocol,
    Any,
)

from domain.schemas import (
    Vector,
    DocumentMeta,
)


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

    def get(self, path: str) -> bytes: ...

    def delete(self, path: str) -> None: ...


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

    def search(self, vector: list[float], top_k: int, workspace_id: str) -> list[Vector]:
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


class MetadataRepository(Protocol):
    """
    Интерфейс для репозитория метаданных документов.
    """

    def save(self, meta: DocumentMeta) -> None:
        """
        Сохраняет метаданные обработанного документа.

        :param meta: Объект `DocumentMeta`, содержащий всю информацию о документе и его статусе.
        :type meta: DocumentMeta
        """
        ...

    def get(self, **data: Any) -> list[DocumentMeta]:
        """
        Извлекает все сохраненные метаданные документов для заданного фильтра.

        :param data: Словарь аргументов, по которому фильтруются документы.
        :type data: Any
        :return: Список объектов `DocumentMeta`.
        :rtype: list[DocumentMeta]
        """
        ...
