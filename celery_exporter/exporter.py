import time
from threading import Thread

from prometheus_client import start_http_server
from celery.events import EventReceiver
import ssl

from celery_exporter import (
    events,
    metrics,
    collectors,
)
from tasks.main import app
from config import logger


class Exporter:
    def run(
        self,
        host: str = "0.0.0.0",
        port: int = 9000,
        certfile: str | None = None,
        keyfile: str | None = None,
        client_cafile: str | None = None,
        client_capath: str | None = None,
        protocol: int = ssl.PROTOCOL_TLS_SERVER,
        client_auth_required: bool = False,
    ):
        print(f"{host}:{port}")
        try:
            start_http_server(
                port=port,
                addr=host,
                registry=metrics.registry,
                certfile=certfile,
                keyfile=keyfile,
                client_cafile=client_cafile,
                client_capath=client_capath,
                protocol=protocol,
                client_auth_required=client_auth_required,
            )
            logger.info(
                f"HTTP-сервер Prometheus-метрик запущен на {host}:{port}",
                prometheus_host=host,
                prometheus_port=port,
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

    @classmethod
    def collect_events_metrics(cls) -> None:
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

                time.sleep(5) # TODO задать время из конфига [COLLECT_EVENTS_METRICS_INTERVAL]

    @classmethod
    def collect_queue_metrics(cls) -> None:
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

                time.sleep(5) # TODO задать время из конфига [COLLECT_QUEUE_METRICS_INTERVAL]

