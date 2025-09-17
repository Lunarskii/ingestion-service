from typing import Iterable
import time
import logging
import threading
from urllib.parse import urlparse

from redis import Redis
from celery import Celery
import requests

from celery_exporter import metrics
from celery_exporter.state import events_state as _events_state
from config import settings


def _get_redis_client(broker_url: str) -> Redis:
    return Redis.from_url(broker_url, decode_responses=True)


def _get_redis_queue_length(redis_client: Redis, queue_name: str) -> int:
    try:
        return redis_client.llen(queue_name)
    except Exception:
        return 0


def collect_redis_queues(redis_url: str, queues: Iterable[str]) -> None:
    redis_client: Redis = _get_redis_client(redis_url)
    for queue in queues:
        length: int = _get_redis_queue_length(redis_client, queue)
        metrics.queue_depth.labels(queue).set(length)


# ---- RabbitMQ collector via Management API ----
def get_rabbit_queue_stats(mgmt_url: str, vhost: str, queue_name: str, user: str, pwd: str) -> dict:
    url = f"{mgmt_url}/api/queues/{requests.utils.quote(vhost, safe='')}/{requests.utils.quote(queue_name, safe='')}"
    try:
        r = requests.get(url, auth=(user, pwd), timeout=5)
        r.raise_for_status()
        js = r.json()
        return {
            "messages_ready": js.get("messages_ready", 0),
            "messages_unacknowledged": js.get("messages_unacknowledged", 0),
            "messages_total": js.get("messages", 0),
            "consumers": js.get("consumers", 0),
        }
    except Exception:
        logger.exception("Failed to fetch RabbitMQ stats for %s", queue_name)
        return {"messages_ready": 0, "messages_unacknowledged": 0, "messages_total": 0, "consumers": 0}

def collect_rabbit_queues(mgmt_url: str, vhost: str, queues: Iterable[str], user: str, pwd: str):
    for q in queues:
        stats = get_rabbit_queue_stats(mgmt_url, vhost, q, user, pwd)
        metrics.queue_depth.labels(queue_name=q).set(stats["messages_total"])
        metrics.active_consumer_count.labels(queue_name=q).set(stats["consumers"])
        # дополнительно set unack/ready в отдельные gauges при наличии

# ---- Celery inspect-based collector ----
def collect_inspect_counts(app: Celery):
    ins = app.control.inspect(timeout=2.0)
    try:
        active = ins.active() or {}
        reserved = ins.reserved() or {}
        # суммируем количество активных / резервных задач по worker
        for worker, tasks in active.items():
            metrics.worker_active_tasks_count.labels(worker).set(len(tasks))
        # пример: считаем total tasks per worker per status (simplified)
        # Можно разбить по task_name/worker/status как тебе нужно
    except Exception:
        logger.exception("Celery inspect failed")

# ---- Poll loop that orchestrates collectors ----
def _poll_loop(stop_event: threading.Event):
    poll_interval = getattr(settings, "metrics_poll_interval", 5)
    broker = settings.celery.broker_url
    parsed = urlparse(broker)
    use_redis = parsed.scheme.startswith("redis")
    # queues to monitor можно брать из config
    queues = settings.monitor_queues

    # rabbit config if needed
    mgmt = getattr(settings, "rabbit_mgmt_url", None)
    vhost = getattr(settings, "rabbit_vhost", "/")
    rabbit_user = getattr(settings, "rabbit_user", None)
    rabbit_pwd = getattr(settings, "rabbit_pwd", None)

    app = Celery()  # или импортируй существующий app

    while not stop_event.is_set():
        try:
            if use_redis:
                collect_redis_queues(broker, queues)
            elif mgmt:
                collect_rabbit_queues(mgmt, vhost, queues, rabbit_user, rabbit_pwd)
            # общие collectors
            collect_inspect_counts(app)
        except Exception:
            logger.exception("Collector loop failed")
        stop_event.wait(poll_interval)

def start_pollers_in_thread() -> threading.Event:
    stop = threading.Event()
    t = threading.Thread(target=_poll_loop, args=(stop,), daemon=True)
    t.start()
    return stop
