import sqlite3

from domain.schemas import DocumentMeta
from services import MetadataRepository

from config import default_settings


class SQLiteMetadataRepository(MetadataRepository):
    def save(self, meta: DocumentMeta) -> None:
        connection = sqlite3.connect(default_settings.sqlite_url)
        cursor = connection.cursor()

        cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS document_metadata (
                    id TEXT PRIMARY KEY,
                    type TEXT,
                    detected_language TEXT,
                    document_page_count INTEGER,
                    author TEXT,
                    creation_date TEXT
                )
            """
        )
        cursor.execute(
            """
                INSERT INTO document_meta (
                    id, type, detected_language, document_page_count, author, creation_date
                ) VALUES (
                    :id, :type, :detected_language, :document_page_count, :author, :creation_date
                )
            """,
            meta.model_dump(by_alias=True),
        )
        connection.commit()
