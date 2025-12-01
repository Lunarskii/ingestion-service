from typing import (
    Any,
    Coroutine,
)
import asyncio

from celery import (
    Task,
    shared_task,
)


class AsyncTask(Task):
    @staticmethod
    def async_run(coro: Coroutine) -> Any:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)


@shared_task(
    name="periodically_sync_topics_with_db",
    bind=True,
    base=AsyncTask,
    ignore_result=True,
)
def sync_topics_with_db(self) -> None:
    from app.domain.classifier.utils import sync_topics_with_db as _sync_topics
    from app.core import settings

    self.async_run(_sync_topics(settings.classifier.topics_path))
