from unittest.mock import MagicMock
import uuid

import pytest

from domain.process import DocumentProcessor
from services import (
    RawStorage,
    VectorStore,
    MetadataRepository,
)
from domain.schemas import (
    Vector,
    DocumentMeta,
)


@pytest.fixture
def mock_raw_storage(mocker):
    return mocker.MagicMock(spec=RawStorage)


@pytest.fixture
def mock_vector_store(mocker):
    return mocker.MagicMock(spec=VectorStore)


@pytest.fixture
def mock_metadata_repository(mocker):
    return mocker.MagicMock(spec=MetadataRepository)


@pytest.fixture
def document_processor(
    mock_raw_storage: MagicMock,
    mock_vector_store: MagicMock,
    mock_metadata_repository: MagicMock,
) -> DocumentProcessor:
    return DocumentProcessor(
        raw_storage=mock_raw_storage,
        vector_store=mock_vector_store,
        metadata_repository=mock_metadata_repository,
    )


@pytest.mark.parametrize(
    "path, file_extension",
    [
        ("tests/resources/1mb.docx", ".docx"),
        ("tests/resources/1mb.pdf", ".pdf"),
    ],
)
def test_process_document(
    document_processor: DocumentProcessor,
    mock_raw_storage: MagicMock,
    mock_vector_store: MagicMock,
    mock_metadata_repository: MagicMock,
    path: str,
    file_extension: str,
):
    with open(path, "rb") as file:
        file_bytes: bytes = file.read()
    document_id: str = str(uuid.uuid4())
    workspace_id: str = str(uuid.uuid4())

    document_processor.process(
        file_bytes=file_bytes,
        document_id=document_id,
        workspace_id=workspace_id,
    )

    mock_raw_storage.save.assert_called_once_with(
        file_bytes, f"{workspace_id}/{document_id}{file_extension}"
    )

    mock_vector_store.upsert.assert_called_once()
    args, _ = mock_vector_store.upsert.call_args
    assert len(args[0]) > 0
    assert isinstance(args[0], list) and all(
        isinstance(vector, Vector) for vector in args[0]
    )
    assert args[0][0].metadata["document_id"] == document_id

    mock_metadata_repository.save.assert_called_once()
    args, _ = mock_metadata_repository.save.call_args
    assert isinstance(args[0], DocumentMeta)
    assert args[0].document_id == document_id
