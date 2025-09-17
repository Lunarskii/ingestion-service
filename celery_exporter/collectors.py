from typing import Any
from collections import defaultdict

from celery import Celery
from celery.app.control import Inspect
from kombu.connection import Connection
from amqp import ChannelError
from amqp.protocol import queue_declare_ok_t

from celery_exporter import metrics
from config import logger


def collect_queues_metrics(
    app: Celery,
    connection: Connection,
) -> None:
    transport = connection.info()["transport"]
    expected_transports: set[str] = {"redis", "rediss", "amqp", "amqps", "memory", "sentinel"}

    if transport not in expected_transports:
        logger.warning(
            f"Отслеживание длины очереди недоступно",
            transport=transport,
            expected_transports=expected_transports,
        )

    inspect: Inspect = app.control.inspect()

    stats = inspect.stats() or {}
    concurrency_per_worker = {
        worker: len(stats_["pool"].get("processes", []))
        for worker, stats_ in stats.items()
    }
    processes_per_queue: dict[str, int] = defaultdict(int)
    workers_per_queue: dict[str, int] = defaultdict(int)

    queues: set[str] = set()
    active_queues: dict[str, Any] = inspect.active_queues() or {}

    for worker_name, queue_info_list in active_queues.items():
        for queue_info in queue_info_list:
            queue: str = queue_info["name"]
            workers_per_queue[queue] += 1
            processes_per_queue[queue] += concurrency_per_worker.get(worker_name, 0)
            queues.add(queue)

    for queue in queues:
        metrics.active_worker_count.labels(queue).set(workers_per_queue[queue])
        metrics.active_process_count.labels(queue).set(processes_per_queue[queue])

        if transport in {"amqp", "amqps", "memory"}:
            queue_info: queue_declare_ok_t | None = _rabbitmq_queue_info(connection, queue)
            if queue_info:
                consumer_count: int = queue_info.consumer_count
                queue_length: int = queue_info.message_count
            else:
                consumer_count: int = 0
                queue_length: int = 0

            metrics.active_consumer_count.labels(queue).set(consumer_count)
            metrics.queue_depth.labels(queue).set(queue_length)
        elif transport in {"redis", "rediss", "sentinel"}:
            queue_length: int = _redis_queue_length(connection, queue)
            metrics.queue_depth.labels(queue).set(queue_length)


def _rabbitmq_queue_info(connection: Connection, queue: str) -> queue_declare_ok_t | None:
    try:
        return connection.default_channel.queue_declare(
            queue=queue,
            passive=True,
        )
    except ChannelError as e:
        raise e


def _redis_queue_length(connection: Connection, queue: str) -> int:
    try:
        return connection.channel().client.llen(queue)
    except Exception:
        return 0
