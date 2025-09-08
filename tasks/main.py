from celery import Celery

from domain.extraction import (
    extract as extract_from_document,
    ExtractedInfo,
)
from domain.document.schemas import File
from config import settings
import time


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
    accept_content=["json"],
    result_serializer="json",
)


@app.task
def extract_text(file: File) -> ExtractedInfo:
    time.sleep(10)
    return extract_from_document(file)
