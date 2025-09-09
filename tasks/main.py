import time

from celery import Celery
from pydantic import BaseModel

from domain.extraction import (
    extract as extract_from_document,
    ExtractedInfo,
)
from domain.document.schemas import File
from config import settings

from tasks.preserializers import (
    PydanticPreserializer,
    register_preserializer,
)


app = Celery(
    broker=settings.celery.broker_url,
    backend=settings.celery.result_backend,
)
app.conf.update(
    worker_prefetch_multiplier=settings.celery.worker_prefetch_multiplier,
    task_acks_late=settings.celery.task_acks_late,
    task_time_limit=settings.celery.task_time_limit,
    task_soft_time_limit=settings.celery.task_soft_time_limit,
    task_max_retries=settings.celery.task_max_retries,
    task_retry_backoff=settings.celery.task_retry_backoff,
    task_retry_jitter=settings.celery.task_retry_jitter,
    task_serializer="json",
    result_serializer="json",
    event_serializer="json",
    accept_content=["application/json"],
    result_accept_content=["application/json"],
)
register_preserializer(PydanticPreserializer, BaseModel)


@app.task(bind=True)
def extract_text(self, file: File) -> ExtractedInfo:
    self.update_state(state="EXTRACTING")
    time.sleep(30)
    return extract_from_document(file)
