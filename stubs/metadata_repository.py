from datetime import datetime
import os
import sqlite3
import typing
import types

from domain.schemas import DocumentMeta
from services import MetadataRepository
from config import storage_settings


class SQLiteMetadataRepository(MetadataRepository):
    def __init__(
        self,
        *,
        sqlite_url: str = storage_settings.sqlite_url,
        table_name: str = "document_metadata",
    ):
        self.url = sqlite_url
        self.table_name = table_name
        os.makedirs(os.path.dirname(sqlite_url), exist_ok=True)
        self.db_connection = sqlite3.connect(self.url)
        self._create_table()

    def save(self, meta: DocumentMeta) -> None:
        """
        Сохраняет метаданные документа в базе данных SQLite.
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

    def _create_table(self):
        """
        Создает таблицу в базе данных, если она не существует.
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
        _PYTHON_TO_SQLITE = {
            str: "TEXT",
            datetime: "TEXT",
            int: "INTEGER",
            bool: "INTEGER",
            float: "REAL",
            bytes: "BLOB",
        }

        origin = typing.get_origin(type_)

        if origin is (typing.Union, types.UnionType):
            args = [arg for arg in typing.get_args(type_) if arg is not type(None)]
            if len(args) == 1:
                return cls._convert_type_to_sqlite_type(args[0])
            return _PYTHON_TO_SQLITE.get(str)
        return _PYTHON_TO_SQLITE.get(type_, "TEXT")
