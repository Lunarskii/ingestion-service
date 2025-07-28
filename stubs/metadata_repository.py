from datetime import datetime
import os
import sqlite3
import typing
import types

from domain.schemas import DocumentMeta
from services import MetadataRepository
from config import storage_settings


class SQLiteMetadataRepository(MetadataRepository):
    """
    Заглушка репозитория метаданных для локальных тестов и разработки.

    Создает или подключается к локальной SQLite-базе и обеспечивает
    методы сохранения и извлечения `DocumentMeta`.
    """

    def __init__(
        self,
        *,
        sqlite_url: str = storage_settings.sqlite_url,
        table_name: str = "document_metadata",
    ):
        """
        Инициализирует соединение и создает таблицу, если её нет.

        :param sqlite_url: Путь к файлу SQLite, например `tests/local.db`.
        :type sqlite_url: str
        :param table_name: Имя таблицы для метаданных.
        :type table_name: str
        """

        self.url = sqlite_url
        self.table_name = table_name
        os.makedirs(os.path.dirname(sqlite_url), exist_ok=True)
        self.db_connection = sqlite3.connect(self.url, check_same_thread=False)
        self._create_table()

    def save(self, meta: DocumentMeta) -> None:
        """
        Сохраняет объект `DocumentMeta` в базу данных.

        :param meta: Метаданные документа.
        :type meta: DocumentMeta
        """

        cursor = self.db_connection.cursor()
        cursor.execute(
            f"""
                INSERT INTO {self.table_name} (
                    {",".join(DocumentMeta.model_fields.keys())}
                ) VALUES (
                    :{",:".join(DocumentMeta.model_fields.keys())}
                )
            """,
            meta.model_dump(),
        )
        self.db_connection.commit()

    def get(self, workspace_id: str) -> list[DocumentMeta]:
        """
        Возвращает все записи `DocumentMeta` для заданного workspace_id.

        :param workspace_id: Идентификатор рабочего пространства.
        :type workspace_id: str
        :return: Список объектов DocumentMeta.
        :rtype: list[DocumentMeta]
        """

        cursor = self.db_connection.cursor()
        cursor.execute(
            f"SELECT * FROM {self.table_name} WHERE workspace_id = ?", (workspace_id,)
        )
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        return [DocumentMeta(**dict(zip(columns, row))) for row in rows]

    def _create_table(self):
        """
        Создает таблицу метаданных в SQLite, если она не существует.

        Типы столбцов определяются динамически через `_convert_type_to_sqlite_type`.
        """

        cursor = self.db_connection.cursor()
        cursor.execute(
            f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    document_id TEXT PRIMARY KEY,
                    {",".join([f"{key} {self._convert_type_to_sqlite_type(value.annotation)}" for key, value in DocumentMeta.model_fields.items()][1:])}
                )
            """
        )
        self.db_connection.commit()

    @classmethod
    def _convert_type_to_sqlite_type(cls, type_: typing.Any) -> str:
        """
        Конвертация Python-типов в соответствующие SQLite-типизации.

        Поддерживает примитивы и Optional[...].

        :param type_: Любой Python-тип или Union.
        :return: Соответствующий SQLite тип как строка.
        :rtype: str
        """

        _PYTHON_TO_SQLITE = {
            str: "TEXT",
            datetime: "TEXT",
            int: "INTEGER",
            bool: "INTEGER",
            float: "REAL",
            bytes: "BLOB",
        }

        origin = typing.get_origin(type_)

        if origin in (typing.Union, types.UnionType):
            args = [arg for arg in typing.get_args(type_) if arg is not type(None)]
            if len(args) == 1:
                return cls._convert_type_to_sqlite_type(args[0])
            return _PYTHON_TO_SQLITE.get(str)
        return _PYTHON_TO_SQLITE.get(type_, "TEXT")
