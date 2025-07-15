import os
import sqlite3

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
                    document_id, document_type, detected_language, document_page_count, author, creation_date, raw_storage_path, file_size_bytes
                ) VALUES (
                    :document_id, :document_type, :detected_language, :document_page_count, :author, :creation_date, :raw_storage_path, :file_size_bytes
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
                    document_type TEXT,
                    detected_language TEXT,
                    document_page_count INTEGER,
                    author TEXT,
                    creation_date TEXT,
                    raw_storage_path TEXT,
                    file_size_bytes INTEGER
                )
            """
        )
        self.db_connection.commit()
