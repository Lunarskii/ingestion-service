from datetime import datetime
import os
import uuid
import json
import sqlite3

import pytest

from stubs import (
    FileRawStorage,
    JSONVectorStore,
    SQLiteMetadataRepository,
)
from domain.schemas import (
    Vector,
    DocumentMeta,
)
from services.exc import (
    VectorStoreMissingMetadata,
    VectorStoreDocumentsNotFound,
    VectorStoreMissingData,
)
from tests.conftest import assert_any_exception


class TestFileRawStorage:
    @pytest.mark.parametrize(
        "file_bytes, directory, path",
        [
            (
                b"some dummy file content",
                "tests/local_storage/raw/",
                f"test_result_{uuid.uuid4()}",
            ),
            (
                b"some dummy file content",
                "tests/local_storage/",
                f"/raw/test_result_{uuid.uuid4()}",
            ),
        ],
    )
    def test_save_writes_bytes_to_correct_location(self, file_bytes, directory, path):
        raw_storage = FileRawStorage(directory=directory)
        raw_storage.save(file_bytes, path)
        with open(os.path.join(directory, path.lstrip("/\\")), "rb") as file:
            assert file.read() == file_bytes

    @pytest.mark.parametrize(
        "directory, path",
        [
            (f"tests/local_storage/raw/test_result_{uuid.uuid4()}", ""),
        ],
    )
    def test_init_raises_for_non_directory_path(self, directory, path):
        with pytest.raises(ValueError) as exc:
            _ = FileRawStorage(directory=directory)
        assert f"Ожидалась директория, но было получено {directory}" == str(exc.value)


class TestJSONVectorStore:
    @pytest.mark.parametrize(
        "directory, vectors",
        [
            (
                f"tests/local_storage/index/test_result_{uuid.uuid4()}/",
                [
                    Vector(
                        values=[0.1, 0.5, 1.0],
                        metadata={
                            "document_id": str(uuid.uuid4()),
                            "workspace_id": str(uuid.uuid4()),
                            "chunk_index": 1248,
                        },
                    )
                ],
            ),
        ],
    )
    def test_upsert_creates_json_file_with_correct_content(self, directory, vectors):
        values: list[float] = vectors[0].values
        chunk_index: int = vectors[0].metadata["chunk_index"]
        document_id: str = vectors[0].metadata["document_id"]
        workspace_id: str = vectors[0].metadata["workspace_id"]
        vector_store = JSONVectorStore(directory=directory)
        vector_store.upsert(vectors)
        with open(os.path.join(directory, f"{workspace_id}/{document_id}.json")) as file:
            content: list = json.load(file)
            vector: Vector = content[0]
            assert vector["values"] == values
            assert vector["metadata"]["document_id"] == document_id
            assert vector["metadata"]["workspace_id"] == workspace_id
            assert vector["metadata"]["chunk_index"] == chunk_index

    @pytest.mark.parametrize(
        "directory",
        [
            f"tests/local_storage/index/test_result_{uuid.uuid4()}",
        ],
    )
    def test_init_raises_for_non_directory_path(self, directory):
        with pytest.raises(ValueError) as exc:
            _ = JSONVectorStore(directory=directory)
        assert f"Ожидалась директория, но было получено {directory}" == str(exc.value)

    @pytest.mark.parametrize(
        "directory, vectors",
        [
            (
                f"tests/local_storage/index/test_result_{uuid.uuid4()}/",
                [Vector(values=[0.1, 0.5, 1.0], metadata={"chunk_index": 1248})],
            ),
        ],
    )
    def test_upsert_raises_missing_document_id(self, directory, vectors):
        vector_store = JSONVectorStore(directory=directory)
        with pytest.raises(VectorStoreMissingMetadata) as exc:
            vector_store.upsert(vectors)
        assert_any_exception(VectorStoreMissingMetadata, exc)

    def test_upsert_raises_missing_vectors(self):
        vector_store = JSONVectorStore(directory=f"tests/local_storage/index/test_result_{uuid.uuid4()}/")
        with pytest.raises(VectorStoreMissingData) as exc:
            vector_store.upsert([])
        assert_any_exception(VectorStoreMissingData, exc)

    def test_search_returns_correct_vectors(self):
        workspace_id: str = str(uuid.uuid4())
        directory = f"tests/local_storage/index/test_result_{uuid.uuid4()}/"
        vector_store = JSONVectorStore(directory=directory)

        document_id: str = str(uuid.uuid4())
        vectors1: list[Vector] = [
            Vector(values=[0.1, 0.2, 0.3], metadata={"document_id": document_id, "workspace_id": workspace_id}),
            Vector(values=[0.4, 0.5, 0.6], metadata={"document_id": document_id, "workspace_id": workspace_id}),
        ]
        vector_store.upsert(vectors1)

        document_id = str(uuid.uuid4())
        vectors2: list[Vector] = [
            Vector(values=[0.7, 0.8, 0.9], metadata={"document_id": document_id, "workspace_id": workspace_id}),
            Vector(values=[0.9, 0.8, 0.7], metadata={"document_id": document_id, "workspace_id": workspace_id}),
            Vector(values=[0.0, 0.0, 0.0], metadata={"document_id": document_id, "workspace_id": workspace_id}),
        ]
        vector_store.upsert(vectors2)

        question_vector = Vector(values=[0.1, 0.3, 0.6])
        top_k: int = 2
        expected_vectors: list[Vector] = list(vectors1)
        retrieved_vectors: list[Vector] = vector_store.search(question_vector, top_k, workspace_id)
        assert retrieved_vectors == expected_vectors

    def test_search_raises_for_empty_workspace(self):
        workspace_id: str = str(uuid.uuid4())
        directory = f"tests/local_storage/index/test_result_{uuid.uuid4()}/"
        vector_store = JSONVectorStore(directory=directory)
        vector = Vector(values=[])
        top_k: int = 10

        with pytest.raises(VectorStoreDocumentsNotFound) as exc:
            vector_store.search(vector, top_k, workspace_id)
        assert_any_exception(VectorStoreDocumentsNotFound, exc)


class TestSQLiteMetadataRepository:
    def test_init_creates_database_and_table(self):
        sqlite_url: str = f"tests/local_storage/{str(uuid.uuid4())[:8]}.db"
        table_name: str = f"table_{str(uuid.uuid4())[:8]}"
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
        ],
    )
    def test_save_inserts_metadata_correctly(self, metadata_kwargs):
        sqlite_url: str = f"tests/local_storage/{str(uuid.uuid4())[:8]}.db"
        table_name: str = f"table_{str(uuid.uuid4())[:8]}"
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
