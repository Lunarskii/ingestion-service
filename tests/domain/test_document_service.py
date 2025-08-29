from unittest.mock import (
    MagicMock,
    create_autospec,
)
from typing import Any
import os

import pytest

from tests.conftest import ValueGenerator
from tests.mock_utils import assert_called_once_with
from domain.document.service import DocumentService
from domain.document.schemas import (
    File,
    DocumentStatus,
)
from domain.document.repositories import DocumentRepository
from domain.embedding import (
    VectorMetadata,
    Vector,
)
from domain.text_splitter import (
    Chunk,
    PageSpan,
)
from domain.extraction import (
    extract as extract_from_document,
    Page,
    ExtractedInfo,
)


mock_document_repo = create_autospec(DocumentRepository, instance=True)


def _get_repo_side_effect(repo_type):
    if repo_type is DocumentRepository:
        return mock_document_repo
    raise KeyError(f"Неожиданный тип репозитория: {repo_type!r}")


class TestDocumentService:
    @pytest.mark.asyncio
    async def test_process_success(
        self,
        monkeypatch,
        mock_uow: MagicMock,
        mock_raw_storage: MagicMock,
        mock_vector_store: MagicMock,
        mock_embedding_model: MagicMock,
        mock_text_splitter: MagicMock,
        tmp_document: Any,
        document_id: str = ValueGenerator.uuid(),
        workspace_id: str = ValueGenerator.uuid(),
    ):
        mock_document_repo.reset_mock()

        file_bytes, path, file_extension = tmp_document()
        vector: list[float] = ValueGenerator.float_vector()
        chunks: list[Chunk] = [
            Chunk(
                text=ValueGenerator.text(),
                page_spans=[
                    PageSpan(
                        text=ValueGenerator.text(),
                        page_num=ValueGenerator.integer(),
                        chunk_start_on_page=ValueGenerator.integer(),
                        chunk_end_on_page=ValueGenerator.integer(),
                    )
                    for _ in range(1, 3)
                ],
            )
            for _ in range(ValueGenerator.integer(2))
        ]
        file = File(
            content=file_bytes,
            name=os.path.basename(path),
            size=len(file_bytes),
            extension=file_extension,
        )
        pages: list[Page] = [
            Page(
                num=i,
                text=ValueGenerator.text(),
            )
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
                values=vector,
                metadata=VectorMetadata(
                    document_id=document_id,
                    workspace_id=workspace_id,
                    document_name=file.name,
                    page_start=chunk.page_spans[0].page_num,
                    page_end=chunk.page_spans[-1].page_num,
                    text=chunk.text,
                ),
            )
            for chunk in chunks
        ]

        mock_uow.get_repository.side_effect = _get_repo_side_effect
        mock_text_splitter.split_pages.return_value = chunks
        mock_embedding_model.encode.return_value = vectors
        mock_extract_function = create_autospec(
            extract_from_document,
            return_value=extracted_info,
            spec_set=True,
        )
        monkeypatch.setattr(
            "domain.document.service.extract_from_document",
            mock_extract_function,
        )

        document_service = DocumentService(
            raw_storage=mock_raw_storage,  # noqa
            vector_store=mock_vector_store,  # noqa
            embedding_model=mock_embedding_model,  # noqa
            text_splitter=mock_text_splitter,  # noqa
        )
        await document_service.process(
            file=file,
            document_id=document_id,
            workspace_id=workspace_id,
            uow=mock_uow,
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

        assert_called_once_with(
            mock_text_splitter.split_pages,
            pages=pages,
        )

        assert_called_once_with(
            mock_embedding_model.encode,
            sentences=[chunk.text for chunk in chunks],
            metadata=[v.metadata for v in vectors],
        )

        assert_called_once_with(
            mock_vector_store.upsert,
            vectors=vectors,
        )

        assert_called_once_with(
            mock_document_repo.create,
            id=document_id,
            workspace_id=workspace_id,
            name=file.name,
            media_type=file.type,
            raw_storage_path=f"{workspace_id}/{document_id}{file_extension}",
            size_bytes=file.size,
            status=DocumentStatus.success,
            page_count=extracted_info.document_page_count,
            author=extracted_info.author,
            creation_date=extracted_info.creation_date,
        )

    @pytest.mark.asyncio
    async def test_process_handles_exceptions(
        self,
        mock_uow: MagicMock,
        mock_raw_storage: MagicMock,
        mock_vector_store: MagicMock,
        mock_embedding_model: MagicMock,
        mock_text_splitter: MagicMock,
        tmp_document: Any,
        document_id: str = ValueGenerator.uuid(),
        workspace_id: str = ValueGenerator.uuid(),
    ):
        mock_document_repo.reset_mock()

        file_bytes, path, file_extension = tmp_document()
        file = File(
            content=file_bytes,
            name=os.path.basename(path),
            size=len(file_bytes),
            extension=file_extension,
        )

        mock_uow.get_repository.side_effect = _get_repo_side_effect
        mock_raw_storage.save = MagicMock(side_effect=Exception("process error"))

        document_service = DocumentService(
            raw_storage=mock_raw_storage,  # noqa
            vector_store=mock_vector_store,  # noqa
            embedding_model=mock_embedding_model,  # noqa
            text_splitter=mock_text_splitter,  # noqa
        )
        await document_service.process(
            file=file,
            document_id=document_id,
            workspace_id=workspace_id,
            uow=mock_uow,
        )

        assert_called_once_with(
            mock_document_repo.create,
            id=document_id,
            workspace_id=workspace_id,
            name=file.name,
            media_type=file.type,
            raw_storage_path=f"{workspace_id}/{document_id}{file_extension}",
            size_bytes=file.size,
            status=DocumentStatus.failed,
        )
