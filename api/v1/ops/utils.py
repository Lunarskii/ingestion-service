from typing import Any

from redis import (
    Redis,
    RedisError,
)
from celery import Celery
from celery.app.control import Inspect


def check_redis(
    url: str,
    timeout: float = 1.0,
) -> str | dict[str, Any]:
    try:
        redis = Redis.from_url(
            url=url,
            socket_connect_timeout=timeout,
            socket_timeout=timeout,
            decode_responses=True,
        )
        if not redis.ping():
            return {
                "status": "unavailable",
                "error_message": "ping failed",
            }
    except (RedisError, Exception) as e:
        return {
            "status": "unavailable",
            "error_message": str(e),
        }
    else:
        return "ok"


def check_celery_workers(
    app: Celery,
    timeout: float = 1.0,
) -> dict[str, Any]:
    try:
        inspect: Inspect = app.control.inspect(timeout=timeout)

        ping = inspect.ping()
        if not ping:
            return {
                "status": "unavailable",
                "error_message": "ping failed",
                "workers": {},
                "available": 0,
            }

        active = inspect.active() or {}
        reserved = inspect.reserved() or {}
        queues = inspect.active_queues() or {}
        stats = inspect.stats() or {}
        workers_info: dict[str, dict[str, Any]] = {}

        for worker_name in ping.keys():
            workers_info[worker_name] = {
                "ping": True,
                "active": len(active.get(worker_name, [])),
                "reserved": len(reserved.get(worker_name, [])),
                "queues": [
                    queue.get("name")
                    for queue in queues.get(worker_name, [])
                ],
                "stats": stats.get(worker_name, {}),
            }
    except Exception as e:
        return {
            "status": "unavailable",
            "error_message": str(e),
            "workers": {},
            "available": 0,
        }
    else:
        return {
            "status": "ok",
            "workers": workers_info,
            "available": len(workers_info),
        }
