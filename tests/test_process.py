import pytest
import uuid
from datetime import datetime

from domain.process import process_file
from services import (
    RawStorage,
    VectorStore,
    MetadataRepository,
)
from domain.schemas import (
    Vector,
    DocumentMeta,
)


# @pytest.mark.asyncio
def test_process_file_pdf(mocker):
    with open("tests/resources/1mb.pdf", "rb") as file:
        file_bytes: bytes = file.read()

    document_id: str = str(uuid.uuid4())

    mock_raw_storage = mocker.create_autospec(RawStorage, instance=True)
    mock_vector_store = mocker.create_autospec(VectorStore, instance=True)
    mock_metadata_repository = mocker.create_autospec(MetadataRepository, instance=True)

    process_file(
        file_bytes,
        "1mb.pdf",
        document_id=document_id,
        raw_storage=mock_raw_storage,
        vector_store=mock_vector_store,
        metadata_repository=mock_metadata_repository,
    )

    mock_raw_storage.save.assert_called_once()
    file_bytes, path = mock_raw_storage.save.call_args.args
    assert file_bytes.startswith(b"%PDF-")
    assert document_id in path

    # mock_vector_store.upsert.assert_called_once()
    # vectors: list[Vector] = mock_vector_store.upsert.call_args.args[0]
    # assert isinstance(vectors, list) and all(isinstance(vector, Vector) for vector in vectors)

    mock_metadata_repository.save.assert_called_once()
    metadata: DocumentMeta = mock_metadata_repository.save.call_args.args[0]
    assert metadata.document_id == document_id
    assert isinstance(metadata.creation_date, datetime) or metadata.creation_date is None


def test_process_file_docx(mocker):
    with open("tests/resources/1mb.docx", "rb") as file:
        file_bytes: bytes = file.read()

    document_id: str = str(uuid.uuid4())

    mock_raw_storage = mocker.create_autospec(RawStorage, instance=True)
    mock_vector_store = mocker.create_autospec(VectorStore, instance=True)
    mock_metadata_repository = mocker.create_autospec(MetadataRepository, instance=True)

    process_file(
        file_bytes,
        "1mb.docx",
        document_id=document_id,
        raw_storage=mock_raw_storage,
        vector_store=mock_vector_store,
        metadata_repository=mock_metadata_repository,
    )

    mock_raw_storage.save.assert_called_once()
    file_bytes, path = mock_raw_storage.save.call_args.args
    assert file_bytes.startswith(b"%PDF-")
    assert document_id in path

    # mock_vector_store.upsert.assert_called_once()
    # vectors: list[Vector] = mock_vector_store.upsert.call_args.args[0]
    # assert isinstance(vectors, list) and all(isinstance(vector, Vector) for vector in vectors)

    mock_metadata_repository.save.assert_called_once()
    metadata: DocumentMeta = mock_metadata_repository.save.call_args.args[0]
    assert metadata.document_id == document_id
    assert isinstance(metadata.creation_date, datetime) or metadata.creation_date is None
