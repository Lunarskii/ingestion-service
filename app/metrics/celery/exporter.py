import time
from threading import Thread

from prometheus_client import start_http_server
from celery.events import EventReceiver
import ssl

from app.metrics.celery import (
    events,
    metrics,
    collectors,
)
from services.celery_worker.main import app
from app.core import logger


class Exporter:
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 9000,
        *,
        certfile: str | None = None,
        keyfile: str | None = None,
        client_cafile: str | None = None,
        client_capath: str | None = None,
        protocol: int = ssl.PROTOCOL_TLS_SERVER,
        client_auth_required: bool = False,
        collect_events_metrics_interval_s: int = 5,
        collect_queue_metrics_interval_s: int = 5,
    ):
        self.host = host
        self.port = port
        self.certfile = certfile
        self.keyfile = keyfile
        self.client_cafile = client_cafile
        self.client_capath = client_capath
        self.protocol = protocol
        self.client_auth_required = client_auth_required
        self.collect_events_metrics_interval_s = collect_events_metrics_interval_s
        self.collect_queue_metrics_interval_s = collect_queue_metrics_interval_s

    def run(self):
        try:
            start_http_server(
                port=self.port,
                addr=self.host,
                registry=metrics.registry,
                certfile=self.certfile,
                keyfile=self.keyfile,
                client_cafile=self.client_cafile,
                client_capath=self.client_capath,
                protocol=self.protocol,
                client_auth_required=self.client_auth_required,
            )
            logger.info(
                f"HTTP-сервер Prometheus-метрик запущен на {self.host}:{self.port}",
                prometheus_host=self.host,
                prometheus_port=self.port,
            )
        except Exception as e:
            logger.error(
                "Не удалось запустить HTTP-сервер Prometheus-метрик",
                error_message=str(e),
            )
            raise e

        threads: list[Thread] = [
            Thread(target=self.collect_events_metrics),
            Thread(target=self.collect_queue_metrics),
        ]
        for thread in threads:
            thread.start()

    def collect_events_metrics(self) -> None:
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
            while True:
                try:
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

                time.sleep(self.collect_events_metrics_interval_s)

    def collect_queue_metrics(self) -> None:
        with app.connection() as connection:
            while True:
                try:
                    collectors.collect_queues_metrics(
                        app=app,
                        connection=connection,
                    )
                except (KeyboardInterrupt, SystemExit) as e:
                    raise e
                except Exception:
                    ...

                time.sleep(self.collect_queue_metrics_interval_s)
