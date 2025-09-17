from prometheus_client import start_http_server
from celery.signals import worker_process_init

from config import (
    settings,
    logger,
)

@worker_process_init.connect
def start_metrics_server(**kwargs):
    """
    Запускает HTTP-сервер Prometheus в каждом процессе воркера.
    """

    prometheus_host: str = settings.celery.metrics_host
    prometheus_port: int = settings.celery.metrics_port
    try:
        start_http_server(
            addr=prometheus_host,
            port=prometheus_port,
        )
        logger.info(
            f"HTTP-сервер (Prometheus) метрик запущен на "
            f"{prometheus_host}:{prometheus_port}",
            prometheus_host=prometheus_host,
            prometheus_port=prometheus_port,
        )
    except Exception as e:
        logger.exception(
            "Не удалось запустить HTTP-сервер (Prometheus) метрик",
            error_message=str(e),
        )
