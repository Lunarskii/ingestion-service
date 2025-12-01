from typing import (
    Any,
    Coroutine,
)
import asyncio

from celery import (
    Task,
    group,
    chain,
    chord,
    shared_task,
)


class AsyncTask(Task):
    @classmethod
    def async_run(cls, coro: Coroutine) -> Any:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)


@shared_task(
    name="periodically_process_documents",
    bind=True,
    base=AsyncTask,
    ignore_result=True,
)
def start_processing_documents_awaiting_processing(self) -> None:
    from app.domain.document.service import DocumentProcessor
    from app.domain.document.schemas import DocumentStatus

    documents_ids: list[str] = self.async_run(
        DocumentProcessor.get_pending_documents_ids()
    )
    for document_id in documents_ids:
        self.async_run(
            DocumentProcessor.update_document_status(
                document_id=document_id,
                status=DocumentStatus.queued,
            ),
        )
        process_document.delay(document_id)


@shared_task(
    bind=True,
    base=AsyncTask,
    ignore_result=True,
)
def document_pipeline_success_callback(self, document_id: str) -> None:
    from app.domain.document.service import DocumentProcessor
    from app.domain.document.schemas import DocumentStatus

    self.async_run(
        DocumentProcessor.update_document_status(
            document_id=document_id,
            status=DocumentStatus.success,
        )
    )


@shared_task(
    bind=True,
    base=AsyncTask,
    ignore_result=True,
)
def document_pipeline_failed_callback(self, document_id: str) -> None:
    from app.domain.document.service import DocumentProcessor
    from app.domain.document.schemas import DocumentStatus

    self.async_run(
        DocumentProcessor.update_document_status(
            document_id=document_id,
            status=DocumentStatus.failed,
        )
    )


@shared_task(
    bind=True,
    base=AsyncTask,
    ignore_result=True,
)
def process_document(
    self,
    document_id: str,
    *args,
    **kwargs,
) -> None:
    from app.domain.document.service import DocumentProcessor
    from app.domain.document.schemas import DocumentStatus

    self.async_run(
        DocumentProcessor.update_document_status(
            document_id=document_id,
            status=DocumentStatus.processing,
        )
    )

    error_callback = document_pipeline_failed_callback.si(document_id)

    chain(
        extract_text_and_metadata_from_document.si(document_id).set(link_error=error_callback),
        chord(
            group(
                detect_language.si(document_id).set(link_error=error_callback),
                chain(
                    split_pages_on_chunks.si(document_id).set(link_error=error_callback),
                    vectorize_chunks.si(document_id).set(link_error=error_callback),
                ),
                classify_document_into_topics.si(document_id).set(link_error=error_callback),
            ),
            document_pipeline_success_callback.si(document_id),
        ),
    )()


@shared_task(
    bind=True,
    base=AsyncTask,
    ignore_result=True,
)
def extract_text_and_metadata_from_document(
    self,
    document_id: str,
    *args,
    **kwargs,
) -> None:
    from app.workflows.document import extract_text_and_metadata

    self.async_run(extract_text_and_metadata(document_id))


@shared_task(
    bind=True,
    base=AsyncTask,
    ignore_result=True,
)
def detect_language(
    self,
    document_id: str,
    *args,
    **kwargs,
) -> None:
    from app.workflows.document import detect_language

    self.async_run(detect_language(document_id))


@shared_task(
    bind=True,
    base=AsyncTask,
)
def split_pages_on_chunks(
    self,
    document_id: str,
    *args,
    **kwargs,
) -> None:
    from app.workflows.document import split_pages_on_chunks

    self.async_run(split_pages_on_chunks(document_id))


@shared_task(
    bind=True,
    base=AsyncTask,
    ignore_result=True,
)
def vectorize_chunks(
    self,
    document_id: str,
    *args,
    **kwargs,
) -> None:
    from app.workflows.document import vectorize_chunks

    self.async_run(vectorize_chunks(document_id))


@shared_task(
    bind=True,
    base=AsyncTask,
    ignore_result=True,
)
def classify_document_into_topics(
    self,
    document_id: str,
    *args,
    **kwargs,
) -> None:
    from app.workflows.document import classify_document_into_topics

    self.async_run(classify_document_into_topics(document_id))
