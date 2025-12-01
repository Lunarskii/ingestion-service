from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
)


registry = CollectorRegistry(auto_describe=True)
BUCKETS = Histogram.DEFAULT_BUCKETS


task_sent_total = Counter(
    name="celery_task_sent_total",
    documentation="Отправляется, когда публикуется сообщение о задаче",
    labelnames=["task", "worker"],
    registry=registry,
)
task_received_total = Counter(
    name="celery_task_received_total",
    documentation="Отправляется, когда worker получает задачу",
    labelnames=["task", "worker"],
    registry=registry,
)
task_started_total = Counter(
    name="celery_task_started_total",
    documentation="Отправляется перед тем, как worker выполнит задачу",
    labelnames=["task", "worker"],
    registry=registry,
)
task_succeeded_total = Counter(
    name="celery_task_succeeded_total",
    documentation="Отправляется, если задача выполнена успешно",
    labelnames=["task", "worker"],
    registry=registry,
)
task_failed_total = Counter(
    name="celery_task_failed_total",
    documentation="Отправляется, если выполнение задачи завершилось неудачей",
    labelnames=["task", "worker", "exception"],
    registry=registry,
)
task_rejected_total = Counter(
    name="celery_task_rejected_total",
    documentation="Задача была отклонена worker-ом, возможно, для повторной вставки в очередь или перемещения в очередь с отложенным ответом",
    labelnames=["task", "worker"],
    registry=registry,
)
task_revoked_total = Counter(
    name="celery_task_revoked_total",
    documentation="Отправляется, если задача была отменена",
    labelnames=["task", "worker"],
    registry=registry,
)
task_retried_total = Counter(
    name="celery_task_retried_total",
    documentation="Отправляется, если задача выполнена неудачно, но будет повторена в будущем",
    labelnames=["task", "worker"],
    registry=registry,
)

task_runtime_seconds = Histogram(
    name="celery_task_runtime_seconds",
    documentation="Гистограмма результатов измерений времени выполнения задачи",
    labelnames=["task", "worker"],
    registry=registry,
    buckets=BUCKETS,
)
task_prefetch_time_seconds = Gauge(
    name="celery_task_prefetch_time_seconds",
    documentation="Время, затраченное задачей на ожидание выполнения в worker-е",
    labelnames=["task", "worker"],
    registry=registry,
)

worker_online_status = Gauge(
    name="celery_worker_online_status",
    documentation="Статус worker-а. Если онлайн, то (1), иначе (0)",
    labelnames=["worker"],
    registry=registry,
)
worker_tasks_total = Gauge(
    name="celery_worker_tasks_total",
    documentation="Количество задач в worker-е",
    labelnames=["task", "worker", "status"],
    registry=registry,
)
worker_active_tasks_count = Gauge(
    name="celery_worker_active_tasks_count",
    documentation="Количество задач, которые в данный момент выполняет worker",
    labelnames=["worker"],
    registry=registry,
)
worker_prefetched_tasks_count = Gauge(
    name="celery_worker_prefetched_tasks_count",
    documentation="Количество задач определенного типа, предварительно выбранных для обработки worker-ом",
    labelnames=["task", "worker"],
    registry=registry,
)

queue_depth = Gauge(
    name="celery_queue_depth",
    documentation="Количество сообщений в очереди брокера",
    labelnames=["queue_name"],
    registry=registry,
)
active_consumer_count = Gauge(
    name="celery_active_consumer_count",
    documentation="Количество активных потребителей в очереди брокера",
    labelnames=["queue_name"],
    registry=registry,
)
active_worker_count = Gauge(
    name="celery_active_worker_count",
    documentation="Количество активных worker-ов в очереди брокера",
    labelnames=["queue_name"],
    registry=registry,
)
active_process_count = Gauge(
    name="celery_active_process_count",
    documentation="Количество активных процессов в очереди брокера",
    labelnames=["queue_name"],
    registry=registry,
)
