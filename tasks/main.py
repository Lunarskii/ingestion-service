from celery import Celery
from pydantic import BaseModel

from tasks.preserializers import (
    PydanticPreserializer,
    register_preserializer,
)
from config import settings


app = Celery(
    broker=settings.celery.broker_url,
    backend=settings.celery.result_backend,
)
app.conf.update(
    enable_utc=settings.celery.enable_utc,
    timezone=settings.celery.timezone,
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
app.conf.beat_schedule = {
    "process-documents-every-minute": {
        "task": "periodically_process_documents",
        "schedule": 60.0,
        "args": (),
    },
}
app.autodiscover_tasks(
    [
        "tasks.metrics",
        "domain.document.tasks",
    ],
)
register_preserializer(PydanticPreserializer, BaseModel)
