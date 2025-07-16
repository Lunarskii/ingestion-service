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


@pytest.mark.parametrize(
    "file_bytes, directory, path",
    [
        (b"some dummy file content", "tests/local_storage/raw/", f"test_result_{uuid.uuid4()}"),
        (b"some dummy file content", "tests/local_storage/", f"/raw/test_result_{uuid.uuid4()}"),
    ]
)
def test_file_raw_storage(file_bytes, directory, path):
    raw_storage = FileRawStorage(directory=directory)
    raw_storage.save(file_bytes, path)
    with open(os.path.join(directory, path.lstrip("/\\")), "rb") as file:
        assert file.read() == file_bytes


@pytest.mark.parametrize(
    "directory, path",
    [
        (f"tests/local_storage/raw/test_result_{uuid.uuid4()}", ""),
    ]
)
def test_file_raw_storage_constructor_error(directory, path):
    with pytest.raises(ValueError) as exc:
        _ = FileRawStorage(directory=directory)
    assert f"Ожидалась директория, но было получено {directory}" == str(exc.value)


@pytest.mark.parametrize(
    "directory, vectors",
    [
        (f"tests/local_storage/index/test_result_{uuid.uuid4()}/", [Vector(values=[0.1, 0.5, 1.0], metadata={"document_id": str(uuid.uuid4()), "chunk_index": 1248})]),
    ]
)
def test_json_vector_store(directory, vectors):
    values: list[float] = vectors[0].values
    chunk_index: int = vectors[0].metadata["chunk_index"]
    document_id: str = vectors[0].metadata["document_id"]
    vector_store = JSONVectorStore(directory=directory)
    vector_store.upsert(vectors)
    with open(os.path.join(directory, f"{document_id}.json")) as file:
        content: list = json.load(file)
        vector: Vector = content[0]
        assert vector["values"] == values
        assert vector["metadata"]["document_id"] == document_id
        assert vector["metadata"]["chunk_index"] == chunk_index


@pytest.mark.parametrize(
    "directory",
    [
        f"tests/local_storage/index/test_result_{uuid.uuid4()}",
    ]
)
def test_json_vector_store_constructor_error(directory):
    with pytest.raises(ValueError) as exc:
        _ = JSONVectorStore(directory=directory)
    assert f"Ожидалась директория, но было получено {directory}" == str(exc.value)


@pytest.mark.parametrize(
    "directory, vectors",
    [
        (f"tests/local_storage/index/test_result_{uuid.uuid4()}/", [Vector(values=[0.1, 0.5, 1.0], metadata={"chunk_index": 1248})]),
    ]
)
def test_json_vector_store_upsert_error(directory, vectors):
    with pytest.raises(ValueError) as exc:
        vector_store = JSONVectorStore(directory=directory)
        vector_store.upsert(vectors)
    assert "Вектор должен содержать 'document_id'" == str(exc.value)


def test_sqlite_metadata_repository_init_table():
    sqlite_url: str = f"tests/local_storage/{str(uuid.uuid4())[:8]}.db"
    table_name: str = f"table_{str(uuid.uuid4())[:8]}"
    assert not os.path.exists(sqlite_url)

    _ = SQLiteMetadataRepository(sqlite_url=sqlite_url, table_name=table_name)
    assert os.path.exists(sqlite_url)

    db_connection = sqlite3.connect(sqlite_url)
    cursor = db_connection.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    row = cursor.fetchone()
    db_connection.close()

    assert row is not None and row[0] == table_name


@pytest.mark.parametrize(
    "metadata_kwargs",
    [
        {
            "document_id": "id1",
            "document_type": "PDF",
            "detected_language": "en",
            "document_page_count": 5,
            "author": "Alice",
            "creation_date": datetime(2025, 1, 1, 12, 0, 0),
            "raw_storage_path": "/tmp/id1/doc.pdf",
            "file_size_bytes": 12345,
        },
        {
            "document_id": "id2",
            "document_type": "DOCX",
            "detected_language": "ru",
            "document_page_count": None,
            "author": None,
            "creation_date": datetime(2000, 12, 19, 12, 3, 57),
            "raw_storage_path": "",
            "file_size_bytes": 0,
        }
    ]
)
def test_sqlite_metadata_repository_save(metadata_kwargs):
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
    assert row["document_type"] == metadata.document_type
    assert row["detected_language"] == metadata.detected_language
    assert row["document_page_count"] == metadata.document_page_count
    assert row["author"] == metadata.author
    assert row["creation_date"] == metadata.creation_date.strftime("%Y-%m-%d %H:%M:%S")
    assert row["raw_storage_path"] == metadata.raw_storage_path
    assert row["file_size_bytes"] == metadata.file_size_bytes
