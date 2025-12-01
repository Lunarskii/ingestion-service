from typing import (
    Any,
    Callable,
)
from functools import wraps

from celery.events.state import Task

from app.metrics.celery import metrics
from app.metrics.celery.state import events_state as _events_state


def _event(required_event_type: str | None = None) -> Callable[[Callable], Callable]:
    def decorator(func) -> Callable:
        @wraps(func)
        def wrapper(
            event: dict[str, Any],
            *args,
            **kwargs,
        ) -> Any:
            if (
                required_event_type
                and (event_type := event.get("type")) != required_event_type
            ):
                raise AttributeError(
                    f"Ожидался тип события {required_event_type}, но был получен {event_type}"
                )
            return func(event, *args, **kwargs)

        return wrapper

    return decorator


@_event(required_event_type="task-sent")
def on_task_sent(event: dict[str, Any]) -> None: ...


@_event(required_event_type="task-received")
def on_task_received(event: dict[str, Any]) -> None:
    task_id: str = event["uuid"]
    task: Task = _events_state.tasks.get(task_id)
    task_name: str = task.name
    task_received: bool = task.received
    task_status: str = task.state
    worker_name: str = event["hostname"]

    if task_received:
        metrics.worker_prefetched_tasks_count.labels(task_name, worker_name).inc()
        metrics.worker_tasks_total.labels(task_name, worker_name, task_status).inc()


@_event(required_event_type="task-started")
def on_task_started(event: dict[str, Any]) -> None:
    task_id: str = event["uuid"]
    task: Task = _events_state.tasks.get(task_id)
    task_name: str = task.name
    task_started: int = task.started
    task_received: int = task.received
    worker_name: str = event["hostname"]

    if task_started and task_received:
        metrics.task_prefetch_time_seconds.labels(task_name, worker_name).set(
            task_started - task_received
        )
        metrics.worker_prefetched_tasks_count.labels(task_name, worker_name).dec()


@_event(required_event_type="task-succeeded")
def on_task_succeeded(event: dict[str, Any]) -> None:
    task_id: str = event["uuid"]
    task: Task = _events_state.tasks.get(task_id)
    task_name: str = task.name
    task_started: int = task.started
    task_received: int = task.received
    task_runtime: int = task.runtime
    worker_name: str = event["hostname"]

    if task_received and task_started:
        metrics.task_runtime_seconds.labels(task_name, worker_name).observe(
            task_runtime
        )


@_event(required_event_type="task-failed")
def on_task_failed(event: dict[str, Any]) -> None:
    task_id: str = event["uuid"]
    task: Task = _events_state.tasks.get(task_id)
    task_started: int = task.started
    task_received: int = task.received

    if task_received and task_started:
        ...


@_event(required_event_type="task-rejected")
def on_task_rejected(event: dict[str, Any]) -> None: ...


@_event(required_event_type="task-revoked")
def on_task_revoked(event: dict[str, Any]) -> None: ...


@_event(required_event_type="task-retried")
def on_task_retried(event: dict[str, Any]) -> None: ...


@_event(required_event_type="worker-online")
def on_worker_online(event: dict[str, Any]) -> None:
    worker_name: str = event["hostname"]
    metrics.worker_online_status.labels(worker_name).set(1)


@_event(required_event_type="worker-heartbeat")
def on_worker_heartbeat(event: dict[str, Any]) -> None:
    worker_name: str = event["hostname"]
    metrics.worker_online_status.labels(worker_name).set(1)
    if active_tasks_count := event.get("active"):
        metrics.worker_active_tasks_count.labels(worker_name).set(active_tasks_count)


@_event(required_event_type="worker-offline")
def on_worker_offline(event: dict[str, Any]) -> None:
    worker_name: str = event["hostname"]
    metrics.worker_online_status.labels(worker_name).set(0)
