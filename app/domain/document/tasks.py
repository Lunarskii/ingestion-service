from typing import (
    TYPE_CHECKING,
    Any,
    Coroutine,
)
from io import BytesIO
import asyncio
import json

from celery import (
    Task,
    group,
    chain,
    shared_task,
)


if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.domain.database.uow import UnitOfWork
    from app.domain.text_splitter import Chunk


class DatabaseTask(Task):
    @property
    def session(self) -> "AsyncSession":
        from app.domain.database.dependencies import get_async_scoped_session
        return get_async_scoped_session()

    @property
    def uow(self) -> "UnitOfWork":
        from app.domain.database.uow import UnitOfWork
        return UnitOfWork(self.session)

    def async_query(
        self,
        uow: "UnitOfWork",
        coroutines: Coroutine | tuple[Coroutine] | list[Coroutine],
    ) -> Any | list[Any]:
        async def async_with_uow() -> Any | list[Any]:
            async with uow:
                if isinstance(coroutines, Coroutine):
                    return await coroutines
                return [await coro for coro in coroutines]

        loop = asyncio.get_event_loop()
        return loop.run_until_complete(async_with_uow())


@shared_task(
    name="periodically_process_documents",
    bind=True,
    base=DatabaseTask,
    ignore_result=True,
)
def start_processing_documents_awaiting_processing(self) -> None:
    from app.domain.document.repositories import DocumentRepository
    from app.domain.document.schemas import (
        DocumentStatus,
        DocumentDTO,
    )

    uow: "UnitOfWork" = self.uow
    document_repo = uow.get_repository(DocumentRepository)
    documents: list[DocumentDTO] = self.async_query(
        uow=uow,
        coroutines=document_repo.get_n(status=DocumentStatus.pending),
    )
    self.async_query(
        uow=uow,
        coroutines=[
            document_repo.update(
                id=document.id,
                status=DocumentStatus.queued,
            )
            for document in documents
        ],
    )
    for document in documents:
        process_document.delay(document.id)


@shared_task(
    bind=True,
    base=DatabaseTask,
    ignore_result=True,
)
def process_document(self, document_id: str) -> None:
    from app.domain.document.repositories import DocumentRepository
    from app.domain.document.schemas import DocumentStatus

    uow: "UnitOfWork" = self.uow
    document_repo = uow.get_repository(DocumentRepository)
    self.async_query(
        uow=uow,
        coroutines=document_repo.update(
            id=document_id,
            status=DocumentStatus.running,
        ),
    )

    chain(
        extract_text_and_metadata_from_document.si(document_id),
        group(
            detect_language.si(document_id),
            chain(
                split_pages_on_chunks.si(document_id),
                vectorize_chunks.s(document_id=document_id),
            ),
        ),
    )()


@shared_task(
    bind=True,
    base=DatabaseTask,
    ignore_result=True,
)
def extract_text_and_metadata_from_document(self, document_id: str) -> None:
    from app.domain.document.repositories import DocumentRepository
    from app.domain.document.schemas import (
        DocumentStatus,
        DocumentDTO,
    )
    from app.services import RawStorage
    from app.config.adapters import (
        raw_storage_adapter,
        silver_storage_adapter,
    )
    from app.domain.extraction import (
        extract as extract_from_document,
        ExtractedInfo,
    )
    from app.utils.datetime import reset_timezone

    uow: "UnitOfWork" = self.uow
    document_repo = uow.get_repository(DocumentRepository)
    self.async_query(
        uow=uow,
        coroutines=document_repo.update(
            id=document_id,
            status=DocumentStatus.extracting,
        ),
    )
    document_meta: DocumentDTO = self.async_query(
        uow=uow,
        coroutines=document_repo.get(
            id=document_id,
        ),
    )

    raw_storage: RawStorage = raw_storage_adapter.get_instance()
    document: bytes = raw_storage.get(document_meta.raw_storage_path)

    extracted_info: ExtractedInfo = extract_from_document(document)
    pages_json: str = json.dumps(
        obj=[
            page.model_dump()
            for page in extracted_info.pages
        ],
    )

    silver_storage: RawStorage = silver_storage_adapter.get_instance()
    silver_storage.save(
        file_bytes=pages_json.encode(),
        path=document_meta.silver_storage_path,
    )

    self.async_query(
        uow=uow,
        coroutines=document_repo.update(
            id=document_id,
            page_count=extracted_info.document_page_count,
            author=extracted_info.author,
            creation_date=reset_timezone(extracted_info.creation_date),
        ),
    )


@shared_task(
    bind=True,
    base=DatabaseTask,
    ignore_result=True,
)
def detect_language(
    self,
    document_id: str,
    min_chars: int = 1000,
) -> None:
    from app.domain.document.repositories import DocumentRepository
    from app.domain.document.schemas import DocumentDTO
    from app.config.adapters import silver_storage_adapter
    from app.services import RawStorage
    import langdetect

    uow: "UnitOfWork" = self.uow
    document_repo = uow.get_repository(DocumentRepository)
    document_meta: DocumentDTO = self.async_query(
        uow=uow,
        coroutines=document_repo.get(
            id=document_id,
        ),
    )

    silver_storage: RawStorage = silver_storage_adapter.get_instance()
    document: bytes = silver_storage.get(document_meta.silver_storage_path)
    pages: list[dict[str, Any]] = json.load(BytesIO(document))

    text: str = ""
    for page in pages:
        if page_text := page.get("text"):
            text += f" {page_text}" if text else page_text
            if len(text) >= min_chars:
                break

    self.async_query(
        uow=uow,
        coroutines=document_repo.update(
            id=document_id,
            detected_language=langdetect.detect(text),
        )
    )


@shared_task(
    bind=True,
    base=DatabaseTask,
)
def split_pages_on_chunks(
    self,
    document_id: str,
) -> list["Chunk"]:
    from app.domain.document.repositories import DocumentRepository
    from app.domain.document.schemas import (
        DocumentStatus,
        DocumentDTO,
    )
    from app.services import RawStorage
    from app.config.adapters import silver_storage_adapter
    from app.config import settings
    from app.domain.text_splitter import TextSplitter
    from app.domain.extraction import Page

    uow: "UnitOfWork" = self.uow
    document_repo = uow.get_repository(DocumentRepository)
    self.async_query(
        uow=uow,
        coroutines=document_repo.update(
            id=document_id,
            status=DocumentStatus.chunking,
        ),
    )
    document_meta: DocumentDTO = self.async_query(
        uow=uow,
        coroutines=document_repo.get(
            id=document_id,
        ),
    )

    silver_storage: RawStorage = silver_storage_adapter.get_instance()
    document: bytes = silver_storage.get(document_meta.silver_storage_path)
    pages: list[dict[str, Any]] = json.load(BytesIO(document))

    text_splitter = TextSplitter(
        chunk_size=settings.text_splitter.chunk_size,
        chunk_overlap=settings.text_splitter.chunk_overlap,
    )
    return text_splitter.split_pages(
        [
            Page(
                num=page.get("num"),
                text=page.get("text"),
            )
            for page in pages
        ],
    )


# TODO Создать отдельный класс тасок, напр. EmbeddingModelTask, чтобы кэшировать эмбеддинг модель между похожими тасками
@shared_task(
    bind=True,
    base=DatabaseTask,
    ignore_result=True,
)
def vectorize_chunks(
    self,
    chunks: list["Chunk"],
    document_id: str,
) -> None:
    from app.domain.document.repositories import DocumentRepository
    from app.domain.document.schemas import (
        DocumentStatus,
        DocumentDTO,
    )
    from app.domain.embedding import (
        EmbeddingModel,
        Vector,
        VectorMetadata,
    )
    from app.config.adapters import vector_store_adapter
    from app.config import settings
    from app.services import VectorStore

    uow: "UnitOfWork" = self.uow
    document_repo = uow.get_repository(DocumentRepository)
    self.async_query(
        uow=uow,
        coroutines=document_repo.update(
            id=document_id,
            status=DocumentStatus.embedding,
        ),
    )
    document_meta: DocumentDTO = self.async_query(
        uow=uow,
        coroutines=document_repo.get(
            id=document_id,
        )
    )

    embedding_model = EmbeddingModel(
        model_name_or_path=settings.embedding.model_name,
        device=settings.embedding.device,
        cache_folder=settings.embedding.cache_folder,
        token=settings.embedding.token,
    )
    vectors: list[Vector] = embedding_model.encode(
        sentences=[chunk.text for chunk in chunks],
        metadata=[
            VectorMetadata(
                document_id=document_id,
                workspace_id=document_meta.workspace_id,
                document_name=document_meta.name,
                page_start=chunk.page_spans[0].page_num,
                page_end=chunk.page_spans[-1].page_num,
                text=chunk.text,
            )
            for chunk in chunks
        ],
    )

    vector_store: VectorStore = vector_store_adapter.get_instance()
    vector_store.upsert(vectors)
