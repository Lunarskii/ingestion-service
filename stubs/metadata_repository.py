import sqlite3

from domain.schemas import DocumentMeta
from services import MetadataRepository


class SQLiteMetadataRepository(MetadataRepository):
    def __init__(
        self,
        url: str,
        *,
        table_name: str = "document_metadata",
    ):
        self.url = url
        self.table_name = table_name

    def save(self, meta: DocumentMeta) -> None:
        connection = sqlite3.connect(self.url)
        cursor = connection.cursor()

        cursor.execute(
            f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    document_id TEXT PRIMARY KEY,
                    document_type TEXT,
                    detected_language TEXT,
                    document_page_count INTEGER,
                    author TEXT,
                    creation_date TEXT
                )
            """
        )
        cursor.execute(
            f"""
                INSERT INTO {self.table_name} (
                    document_id, document_type, detected_language, document_page_count, author, creation_date
                ) VALUES (
                    :document_id, :document_type, :detected_language, :document_page_count, :author, :creation_date
                )
            """,
            meta.model_dump(),
        )
        connection.commit()
