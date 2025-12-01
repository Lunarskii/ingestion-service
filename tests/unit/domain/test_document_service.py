from typing import Any
from unittest.mock import MagicMock

import pytest

from tests.generators import (
    DocumentGenerator,
    ValueGenerator,
)
from tests.mappers import document_dto_to_scheme
from tests.mock_utils import assert_called_once_with
from app.domain.document.service import DocumentService
from app.domain.document.schemas import (
    File,
    DocumentStatus,
    DocumentDTO,
)
from app.domain.document.exceptions import (
    DocumentNotFoundError,
    DuplicateDocumentError,
)
from app.domain.database.exceptions import EntityNotFoundError


class TestDocumentService:
    @pytest.mark.asyncio
    async def test_get_documents_returns_list(
        self,
        monkeypatch,
        mock_raw_storage: MagicMock,
        mock_document_repo: MagicMock,
        workspace_id: str = ValueGenerator.uuid(),
    ):
        documents: list[DocumentDTO] = DocumentGenerator.document_dto(10)
        mock_document_repo.get_n.return_value = documents
        monkeypatch.setattr(
            "app.domain.document.service.DocumentRepository",
            lambda session: mock_document_repo,
        )

        document_service = DocumentService()
        assert await document_service.get_documents(workspace_id) == document_dto_to_scheme(documents)

        assert_called_once_with(
            mock_document_repo.get_n,
            workspace_id=workspace_id,
        )

    @pytest.mark.asyncio
    async def test_document_file_returns_file(
        self,
        monkeypatch,
        mock_raw_storage: MagicMock,
        mock_document_repo: MagicMock,
        document_id: str = ValueGenerator.uuid(),
    ):
        document: DocumentDTO = DocumentGenerator.document_dto()
        mock_document_repo.get.return_value = document
        monkeypatch.setattr(
            "app.domain.document.service.DocumentRepository",
            lambda session: mock_document_repo,
        )

        document_bytes: bytes = ValueGenerator.bytes()
        mock_raw_storage.get.return_value = document_bytes

        document_service = DocumentService()
        result: File = await document_service.get_document_file(
            document_id,
            raw_storage=mock_raw_storage,  # noqa
        )

        assert result == File(
            content=document_bytes,
            name=document.title,
        )

        assert_called_once_with(
            mock_document_repo.get,
            id=document_id,
        )

        assert_called_once_with(
            mock_raw_storage.get,
            path=document.raw_storage_path,
        )

    @pytest.mark.asyncio
    async def test_document_not_found(
        self,
        monkeypatch,
        mock_raw_storage: MagicMock,
        mock_document_repo: MagicMock,
        document_id: str = ValueGenerator.uuid(),
    ):
        mock_document_repo.get.side_effect = EntityNotFoundError()
        monkeypatch.setattr(
            "app.domain.document.service.DocumentRepository",
            lambda session: mock_document_repo,
        )

        document_service = DocumentService()
        with pytest.raises(DocumentNotFoundError):
            await document_service.get_document_file(
                document_id,
                raw_storage=mock_raw_storage,  # noqa
            )

    @pytest.mark.asyncio
    async def test_save_document_metadata_success(
        self,
        monkeypatch,
        mock_document_repo: MagicMock,
    ):
        document: DocumentDTO = DocumentGenerator.document_dto()
        mock_document_repo.get_n.return_value = None
        mock_document_repo.create.return_value = document
        monkeypatch.setattr(
            "app.domain.document.service.DocumentRepository",
            lambda session: mock_document_repo,
        )

        document_service = DocumentService()
        assert await document_service.save_document_metadata(document) == document_dto_to_scheme(document)

        assert_called_once_with(
            mock_document_repo.get_n,
            workspace_id=document.workspace_id,
            sha256=document.sha256,
        )

        assert_called_once_with(
            mock_document_repo.create,
            **document.model_dump(),
        )

    @pytest.mark.asyncio
    async def test_save_document_metadata_raises_duplicate(
        self,
        monkeypatch,
        mock_document_repo: MagicMock,
    ):
        document: DocumentDTO = DocumentGenerator.document_dto()
        mock_document_repo.get_n.return_value = [document]
        monkeypatch.setattr(
            "app.domain.document.service.DocumentRepository",
            lambda session: mock_document_repo,
        )

        document_service = DocumentService()
        with pytest.raises(DuplicateDocumentError):
            await document_service.save_document_metadata(document)

    @pytest.mark.asyncio
    async def test_save_document_success(
        self,
        monkeypatch,
        mock_raw_storage: MagicMock,
        mock_document_repo: MagicMock,
        tmp_document: Any,
    ):
        file, raw_storage_path = tmp_document()

        document: DocumentDTO = DocumentGenerator.document_dto()
        document.title = file.name
        document.raw_storage_path = f"{document.workspace_id}/{document.id}{file.extension}"
        document.size_bytes = file.size
        document.status = DocumentStatus.pending
        mock_document_repo.get_n.return_value = None
        mock_document_repo.create.return_value = document
        monkeypatch.setattr(
            "app.domain.document.service.DocumentRepository",
            lambda session: mock_document_repo,
        )

        document_service = DocumentService()
        await document_service.save_document(
            file=file,
            workspace_id=document.workspace_id,
            document_id=document.id,
            raw_storage=mock_raw_storage,  # noqa
        )

        assert_called_once_with(
            mock_raw_storage.save,
            file_bytes=file.content,
            path=document.raw_storage_path,
        )

        assert_called_once_with(
            mock_document_repo.create,
            **document.model_dump(
                include={
                    "id",
                    "workspace_id",
                    "title",
                    "raw_storage_path",
                    "size_bytes",
                    "status",
                },
            ),
        )

    @pytest.mark.asyncio
    async def test_save_document_failed(
        self,
        monkeypatch,
        mock_raw_storage: MagicMock,
        mock_document_repo: MagicMock,
        tmp_document: Any,
        error_message: str = "error message"
    ):
        file, raw_storage_path = tmp_document()

        document: DocumentDTO = DocumentGenerator.document_dto()
        document.title = file.name
        document.raw_storage_path = f"{document.workspace_id}/{document.id}{file.extension}"
        document.size_bytes = file.size
        document.status = DocumentStatus.failed
        document.error_message = error_message
        mock_document_repo.get_n.return_value = None
        mock_document_repo.create.return_value = document
        monkeypatch.setattr(
            "app.domain.document.service.DocumentRepository",
            lambda session: mock_document_repo,
        )

        mock_raw_storage.save.side_effect = Exception(error_message)

        document_service = DocumentService()
        await document_service.save_document(
            file=file,
            workspace_id=document.workspace_id,
            document_id=document.id,
            raw_storage=mock_raw_storage,  # noqa
        )

        assert_called_once_with(
            mock_raw_storage.save,
            file_bytes=file.content,
            path=document.raw_storage_path,
        )

        assert_called_once_with(
            mock_document_repo.create,
            **document.model_dump(
                include={
                    "id",
                    "workspace_id",
                    "title",
                    "raw_storage_path",
                    "size_bytes",
                    "status",
                    "error_message",
                },
            ),
        )
