import time

from prometheus_client import start_http_server
from celery.events import EventReceiver

from celery_exporter import (
    events,
    metrics,
)
from tasks.main import app


class Exporter:
    def run(self) -> None:
        # start_http_server(port=settings.PORT, registry=metrics.registry)
        ...

    @classmethod
    def collect_worker_metrics(cls) -> None:
        handlers = {
            "task-sent": events.on_task_sent,
            "task-received": events.on_task_received,
            "task-started": events.on_task_started,
            "task-succeeded": events.on_task_succeeded,
            "task-failed": events.on_task_failed,
            "task-rejected": events.on_task_rejected,
            "task-revoked": events.on_task_revoked,
            "task-retried": events.on_task_retried,
            "worker-online": events.on_worker_online,
            "worker-heartbeat": events.on_worker_heartbeat,
            "worker-offline": events.on_worker_offline,
        }

        with app.connection() as connection:
            try:
                while True:
                    receiver = EventReceiver(
                        channel=connection,
                        handlers=handlers,
                        app=app,
                    )
                    receiver.capture()
            except (KeyboardInterrupt, SystemExit) as e:
                raise e
            except Exception:
                ...

            time.sleep(5) # TODO задать время из конфига
