from unittest.mock import (
    MagicMock,
    create_autospec,
    call,
)
from typing import Any
import os

from tests.conftest import ValueGenerator
from tests.mock_utils import (
    call_args,
    assert_called_once_with,
)
from domain.document.service import DocumentService
from domain.document.schemas import File
from domain.document.schemas import Document
from domain.embedding.schemas import (
    VectorMetadata,
    Vector,
)
from domain.extraction.schemas import (
    Page,
    ExtractedInfo,
)
from domain.extraction import extract as extract_from_document


class TestDocumentService:
    def test_process_success(
        self,
        monkeypatch,
        mock_raw_storage: MagicMock,
        mock_vector_store: MagicMock,
        mock_metadata_repository: MagicMock,
        mock_embedding_model: MagicMock,
        mock_text_splitter: MagicMock,
        tmp_document: Any,
        document_id: str = ValueGenerator.uuid(),
        workspace_id: str = ValueGenerator.uuid(),
    ):
        file_bytes, path, file_extension = tmp_document()
        vector: list[float] = ValueGenerator.float_vector()
        chunks: list[str] = ValueGenerator.chunks(1)
        file = File(
            content=file_bytes,
            name=os.path.basename(path),
            size=len(file_bytes),
            extension=file_extension,
        )
        pages: list[Page] = [
            Page(num=i, text=ValueGenerator.text())
            for i in range(ValueGenerator.integer(1))
        ]
        extracted_info = ExtractedInfo(
            pages=pages,
            document_page_count=len(pages),
            author=ValueGenerator.text(),
            creation_date=ValueGenerator.datetime(),
        )
        vectors: list[Vector] = [
            Vector(
                id=f"{document_id}-{i}",
                values=vector,
                metadata=VectorMetadata(
                    document_id=document_id,
                    workspace_id=workspace_id,
                    document_name=file.name,
                    document_page=i,
                    text=chunks[0],
                ),
            )
            for i in range(len(pages))
        ]

        mock_text_splitter.split_text.return_value = chunks
        mock_vector = MagicMock()
        mock_vector.tolist.return_value = vector
        mock_embedding_model.encode.return_value = [
            mock_vector for _ in range(len(pages))
        ]
        mock_extract_function = create_autospec(
            extract_from_document, return_value=extracted_info, spec_set=True
        )
        monkeypatch.setattr(
            "domain.document.service.extract_from_document", mock_extract_function
        )

        document_service = DocumentService(
            raw_storage=mock_raw_storage,  # noqa
            vector_store=mock_vector_store,  # noqa
            metadata_repository=mock_metadata_repository,  # noqa
            embedding_model=mock_embedding_model,  # noqa
            text_splitter=mock_text_splitter,  # noqa
        )
        document_service.process(
            file=file,
            document_id=document_id,
            workspace_id=workspace_id,
        )

        assert_called_once_with(
            mock_raw_storage.save,
            file_bytes=file.content,
            path=f"{workspace_id}/{document_id}{file_extension}",
        )

        assert_called_once_with(
            mock_extract_function,
            file=file,
        )

        mock_text_splitter.split_text.assert_has_calls(
            [call(text=page.text) for page in pages]
        )

        assert_called_once_with(
            mock_embedding_model.encode,
            sentences=[chunks[0] for _ in range(len(pages))],
        )

        assert_called_once_with(
            mock_vector_store.upsert,
            vectors=vectors,
        )

        mock_metadata_repository.save.assert_called_once()
        args = call_args(mock_metadata_repository.save)
        assert isinstance(args["meta"], Document)
        assert args["meta"].document_id == document_id
        assert args["meta"].workspace_id == workspace_id

    def test_process_handles_exceptions(
        self,
        mock_raw_storage: MagicMock,
        mock_vector_store: MagicMock,
        mock_metadata_repository: MagicMock,
        mock_embedding_model: MagicMock,
        mock_text_splitter: MagicMock,
        tmp_document: Any,
        document_id: str = ValueGenerator.uuid(),
        workspace_id: str = ValueGenerator.uuid(),
    ):
        file_bytes, path, file_extension = tmp_document()
        file = File(
            content=file_bytes,
            name=os.path.basename(path),
            size=len(file_bytes),
            extension=file_extension,
        )

        mock_raw_storage.save = MagicMock(side_effect=Exception("process error"))
        mock_metadata_repository.save = MagicMock(
            side_effect=Exception("process error")
        )

        document_service = DocumentService(
            raw_storage=mock_raw_storage,  # noqa
            vector_store=mock_vector_store,  # noqa
            metadata_repository=mock_metadata_repository,  # noqa
            embedding_model=mock_embedding_model,  # noqa
            text_splitter=mock_text_splitter,  # noqa
        )
        document_service.process(
            file=file,
            document_id=document_id,
            workspace_id=workspace_id,
        )
