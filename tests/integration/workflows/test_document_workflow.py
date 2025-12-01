from typing import (
    Any,
    Callable,
    AsyncContextManager,
)

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from tests.generators import ValueGenerator
from app.workflows.document import (
    extract_text_and_metadata,
    detect_language,
    split_pages_on_chunks,
    vectorize_chunks,
    classify_document_into_topics,
)
from app.domain.document.service import DocumentService
from app.domain.document.schemas import (
    Document,
    DocumentDTO,
    DocumentStatus,
)
from app.domain.document.repositories import DocumentRepository
from app.types import Vector
from app.domain.text_splitter import Chunk
from app.domain.classifier.repositories import DocumentTopicRepository
from app.domain.classifier.utils import sync_topics_with_db
from app.domain.workspace.service import WorkspaceService
from app.domain.workspace.schemas import Workspace
from app.domain.workspace.repositories import WorkspaceRepository
from app.domain.database.dependencies import async_scoped_session_ctx
from app.interfaces import (
    RawStorage,
    VectorStorage,
)
from app.defaults import defaults
from app.core import settings


@pytest.mark.asyncio(loop_scope="session")
async def test_document_pipeline_success(
    tmp_document: Any,
    raw_storage: RawStorage = defaults.raw_storage,
    silver_storage: RawStorage = defaults.silver_storage,
    vector_store: VectorStorage = defaults.vector_storage,
    session_ctx: Callable[[], AsyncContextManager["AsyncSession"]] = async_scoped_session_ctx,
):
    await sync_topics_with_db(settings.classifier.topics_path)

    ws_service = WorkspaceService()
    ws_name: str = ValueGenerator.uuid()
    workspace: Workspace = await ws_service.create_workspace(ws_name)
    async with session_ctx() as session:
        repo = WorkspaceRepository(session)
        assert await repo.exists(workspace.id)

    doc_service = DocumentService()
    file, _ = tmp_document(doc_type=".pdf")
    document_id: str = ValueGenerator.uuid()
    document: Document = await doc_service.save_document(file, workspace.id, document_id=document_id)
    async with session_ctx() as session:
        repo = DocumentRepository(session)
        assert await repo.exists(document.id)
        assert await repo.update(document.id, status=DocumentStatus.processing)
    assert raw_storage.exists(f"{workspace.id}/{document.id}{file.extension}")

    await extract_text_and_metadata(document.id)
    assert silver_storage.exists(f"{workspace.id}/{document.id}.json")
    async with session_ctx() as session:
        repo = DocumentRepository(session)
        _: DocumentDTO = await repo.get(document.id)
        assert _.page_count
        assert _.author
        assert _.creation_date

    await detect_language(document.id)
    async with session_ctx() as session:
        repo = DocumentRepository(session)
        _: DocumentDTO = await repo.get(document.id)
        assert _.detected_language

    chunks: list[Chunk] = await split_pages_on_chunks(document.id)

    await vectorize_chunks(document.id, chunks)
    vectors: list[Vector] = vector_store.search(
        embedding=ValueGenerator.float_vector(),
        top_k=1_000_000,
        workspace_id=workspace.id,
    )
    assert len(vectors) == len(chunks)

    await classify_document_into_topics(document.id)
    # async with session_ctx() as session:
    #     repo = DocumentTopicRepository(session)
    #     assert await repo.get_n(document_id=document.id) != []

    await ws_service.delete_workspace(workspace.id)
