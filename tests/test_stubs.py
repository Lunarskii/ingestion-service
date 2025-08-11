from datetime import (
    datetime,
    timezone,
)
import os
import json
import sqlite3

import pytest

from tests.conftest import ValueGenerator
from stubs import (
    FileRawStorage,
    JSONVectorStore,
    SQLiteMetadataRepository,
)
from domain.schemas import (
    Vector,
)
from domain.document.schemas import DocumentMeta
from services.exc import (
    VectorStoreMissingMetadata,
    VectorStoreDocumentsNotFound,
    VectorStoreMissingData,
)
from tests.conftest import assert_any_exception


class TestFileRawStorage:
    @pytest.mark.parametrize(
        "directory, path",
        [
            (ValueGenerator.path(), ValueGenerator.uuid()),
            (ValueGenerator.path(1), ValueGenerator.uuid()),
        ],
    )
    def test_save_writes_bytes_to_correct_location(
        self,
        tmp_path,
        directory,
        path,
    ):
        directory = f"{tmp_path}/{directory}"
        file_bytes = b"some dummy file content"

        raw_storage = FileRawStorage(directory=directory)
        raw_storage.save(file_bytes, path)

        with open(os.path.join(directory, path), "rb") as file:
            assert file.read() == file_bytes

    @pytest.mark.parametrize(
        "directory, path",
        [
            (f"{ValueGenerator.path()}{ValueGenerator.uuid()}", ""),
            (f"{ValueGenerator.path(1)}{ValueGenerator.uuid()}", ""),
            (ValueGenerator.uuid(), ""),
        ],
    )
    def test_init_raises_for_non_directory_path(
        self,
        tmp_path,
        directory,
        path,
    ):
        directory = f"{tmp_path}/{directory}"
        with pytest.raises(ValueError) as exc:
            _ = FileRawStorage(directory=directory)
        assert f"Ожидалась директория, но было получено {directory}" == str(exc.value)


class TestJSONVectorStore:
    @pytest.mark.parametrize(
        "directory, vectors",
        [
            (f"{ValueGenerator.path()}", [ValueGenerator.vector()]),
            (f"{ValueGenerator.path(1)}", [ValueGenerator.vector()]),
            (f"{ValueGenerator.path()}", ValueGenerator.vectors()),
        ],
    )
    def test_upsert_creates_json_file_with_correct_content(
        self,
        tmp_path,
        directory,
        vectors,
    ):
        directory = f"{tmp_path}/{directory}"
        document_id: str = vectors[0].metadata["document_id"]
        workspace_id: str = vectors[0].metadata["workspace_id"]

        vector_store = JSONVectorStore(directory=directory)
        vector_store.upsert(vectors)

        full_path: str = os.path.join(directory, f"{workspace_id}/{document_id}.json")
        with open(full_path) as file:
            content: list = json.load(file)
            for v1, v2 in zip(content, vectors):
                assert v1["values"] == v2.values
                assert v1["metadata"] == v2.metadata

    @pytest.mark.parametrize(
        "directory",
        [
            f"{ValueGenerator.path()}{ValueGenerator.uuid()}",
            f"{ValueGenerator.path(1)}{ValueGenerator.uuid()}",
            ValueGenerator.uuid(),
        ],
    )
    def test_init_raises_for_non_directory_path(self, tmp_path, directory):
        directory: str = f"{tmp_path}/{directory}"
        with pytest.raises(ValueError) as exc:
            _ = JSONVectorStore(directory=directory)
        assert f"Ожидалась директория, но было получено {directory}" == str(exc.value)

    def test_upsert_raises_missing_document_id(self, tmp_path):
        directory: str = f"{tmp_path}/{ValueGenerator.path()}"
        vectors: list[Vector] = [ValueGenerator.vector(document_id=False)]

        vector_store = JSONVectorStore(directory=directory)
        with pytest.raises(VectorStoreMissingMetadata) as exc:
            vector_store.upsert(vectors)
        assert_any_exception(VectorStoreMissingMetadata, exc)

    def test_upsert_raises_missing_workspace_id(self, tmp_path):
        directory: str = f"{tmp_path}/{ValueGenerator.path()}"
        vectors: list[Vector] = [ValueGenerator.vector(workspace_id=False)]

        vector_store = JSONVectorStore(directory=directory)
        with pytest.raises(VectorStoreMissingMetadata) as exc:
            vector_store.upsert(vectors)
        assert_any_exception(VectorStoreMissingMetadata, exc)

    def test_upsert_raises_missing_vectors(self, tmp_path):
        directory: str = f"{tmp_path}/{ValueGenerator.path()}"
        vectors: list[Vector] = []

        vector_store = JSONVectorStore(directory=directory)
        with pytest.raises(VectorStoreMissingData) as exc:
            vector_store.upsert(vectors)
        assert_any_exception(VectorStoreMissingData, exc)

    def test_search_returns_correct_vectors(self, tmp_path):
        directory: str = f"{tmp_path}/{ValueGenerator.path()}"
        workspace_id: str = ValueGenerator.uuid()

        vector_store = JSONVectorStore(directory=directory)

        document_id: str = ValueGenerator.uuid()
        vectors1: list[Vector] = [
            Vector(
                values=[0.1, 0.2, 0.3],
                metadata={"document_id": document_id, "workspace_id": workspace_id},
            ),
            Vector(
                values=[0.4, 0.5, 0.6],
                metadata={"document_id": document_id, "workspace_id": workspace_id},
            ),
        ]
        vector_store.upsert(vectors1)

        document_id = ValueGenerator.uuid()
        vectors2: list[Vector] = [
            Vector(
                values=[0.7, 0.8, 0.9],
                metadata={"document_id": document_id, "workspace_id": workspace_id},
            ),
            Vector(
                values=[0.9, 0.8, 0.7],
                metadata={"document_id": document_id, "workspace_id": workspace_id},
            ),
            Vector(
                values=[0.0, 0.0, 0.0],
                metadata={"document_id": document_id, "workspace_id": workspace_id},
            ),
        ]
        vector_store.upsert(vectors2)

        question_vector = Vector(values=[0.1, 0.3, 0.6])
        top_k: int = 2
        expected_vectors: list[Vector] = list(vectors1)
        retrieved_vectors: list[Vector] = vector_store.search(question_vector, top_k, workspace_id)
        assert retrieved_vectors == expected_vectors

    def test_search_raises_for_empty_workspace(self, tmp_path, workspace_id):
        directory: str = f"{tmp_path}/{ValueGenerator.path()}"
        vector: Vector = ValueGenerator.vector(workspace_id=False)
        top_k: int = 5

        vector_store = JSONVectorStore(directory=directory)
        with pytest.raises(VectorStoreDocumentsNotFound) as exc:
            vector_store.search(vector, top_k, workspace_id)
        assert_any_exception(VectorStoreDocumentsNotFound, exc)


class TestSQLiteMetadataRepository:
    def test_init_creates_database_and_table(self, tmp_path):
        sqlite_url: str = f"{tmp_path}/{ValueGenerator.path()}{ValueGenerator.word()}.db"
        table_name: str = f"{ValueGenerator.word()}"
        assert not os.path.exists(sqlite_url)

        _ = SQLiteMetadataRepository(sqlite_url=sqlite_url, table_name=table_name)
        assert os.path.exists(sqlite_url)

        db_connection = sqlite3.connect(sqlite_url)
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        )
        row = cursor.fetchone()
        db_connection.close()

        assert row is not None and row[0] == table_name

    @pytest.mark.parametrize(
        "metadata_kwargs",
        [
            {
                "document_id": "id1",
                "workspace_id": "ws1",
                "document_type": "PDF",
                "detected_language": "en",
                "document_page_count": 5,
                "author": "Alice",
                "creation_date": datetime(2025, 1, 1, 12, 0, 0),
                "raw_storage_path": "/tmp/id1/doc.pdf",
                "file_size_bytes": 12345,
                "ingested_at": datetime(1111, 7, 8, 9, 10, 11),
                "status": "SUCCESS",
                "error_message": "bad request",
            },
            {
                "document_id": "id2",
                "workspace_id": "ws2",
                "document_type": "DOCX",
                "detected_language": "ru",
                "document_page_count": None,
                "author": None,
                "creation_date": datetime(2000, 12, 19, 12, 3, 57),
                "raw_storage_path": "",
                "file_size_bytes": 0,
                "ingested_at": datetime(1111, 7, 8, 9, 10, 11),
                "status": "FAILED",
                "error_message": None,
            },
            {
                "document_id": "id3",
                "workspace_id": "ws3",
                "document_type": "DOCX",
                "detected_language": "ru",
                "document_page_count": None,
                "author": None,
                "creation_date": datetime.now(timezone.utc),
                "raw_storage_path": "",
                "file_size_bytes": 0,
                "ingested_at": datetime.now(timezone.utc),
                "status": "FAILED",
                "error_message": None,
            },
        ],
    )
    def test_save_inserts_metadata_correctly(self, tmp_path, metadata_kwargs):
        sqlite_url: str = f"{tmp_path}/{ValueGenerator.path()}{ValueGenerator.word()}.db"
        table_name: str = f"{ValueGenerator.word()}"

        metadata_repository = SQLiteMetadataRepository(sqlite_url=sqlite_url, table_name=table_name)
        metadata = DocumentMeta(**metadata_kwargs)

        metadata_repository.save(metadata)

        db_connection = sqlite3.connect(sqlite_url)
        db_connection.row_factory = sqlite3.Row
        cursor = db_connection.cursor()
        cursor.execute(f"SELECT * FROM {table_name} WHERE document_id = ?", (metadata.document_id,))
        row = cursor.fetchone()
        db_connection.close()

        assert row is not None
        assert row["document_id"] == metadata.document_id
        assert row["workspace_id"] == metadata.workspace_id
        assert row["document_type"] == metadata.document_type
        assert row["detected_language"] == metadata.detected_language
        assert row["document_page_count"] == metadata.document_page_count
        assert row["author"] == metadata.author
        assert row["creation_date"] == metadata.creation_date.strftime("%Y-%m-%d %H:%M:%S")
        assert row["raw_storage_path"] == metadata.raw_storage_path
        assert row["file_size_bytes"] == metadata.file_size_bytes
        assert row["ingested_at"] == metadata.ingested_at.strftime("%Y-%m-%d %H:%M:%S")
        assert row["status"] == metadata.status
        assert row["error_message"] == metadata.error_message
