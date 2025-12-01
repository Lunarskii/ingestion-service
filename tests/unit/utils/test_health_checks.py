from unittest.mock import Mock

from redis import RedisError

from app.utils.health import (
    check_redis,
    check_celery_workers,
)


class TestRedisHealthCheck:
    def test_check_redis_ok(self):
        redis = Mock()
        redis.ping.return_value = True

        assert check_redis(redis) == "ok"

    def test_check_redis_ping_failed(self):
        redis = Mock()
        redis.ping.return_value = False

        result = check_redis(redis)
        assert result["status"] == "unavailable"
        assert "ping failed" in result["error_message"]

    def test_check_redis_exception(self):
        def raise_err(*args, **kwargs):
            raise RedisError("connection refused")

        redis = Mock()
        redis.ping.side_effect = raise_err

        result = check_redis(redis)
        assert result["status"] == "unavailable"
        assert "connection refused" in result["error_message"]


class TestCeleryHealthCheck:
    @staticmethod
    def make_inspect(
        ping_resp,
        active_resp=None,
        reserved_resp=None,
        queues_resp=None,
        stats_resp=None,
    ) -> Mock:
        inspect_obj = Mock()
        inspect_obj.ping.return_value = ping_resp
        inspect_obj.active.return_value = active_resp
        inspect_obj.reserved.return_value = reserved_resp
        inspect_obj.active_queues.return_value = queues_resp
        inspect_obj.stats.return_value = stats_resp
        return inspect_obj

    def test_check_celery_workers_ok(self):
        ping = {"worker1": "pong", "worker2": "pong"}
        active = {"worker1": [1, 2], "worker2": []}
        reserved = {"worker1": [1], "worker2": [1, 2, 3]}
        queues = {
            "worker1": [{"name": "default"}],
            "worker2": [{"name": "queue2"}, {"name": "queue3"}],
        }
        stats = {"worker1": {"pid": 123}, "worker2": {"pid": 456}}

        inspect_obj = self.make_inspect(ping, active, reserved, queues, stats)
        app = Mock()
        app.control.inspect.return_value = inspect_obj

        result = check_celery_workers(app)
        assert result["status"] == "ok"
        assert result["available"] == 2
        assert "worker1" in result["workers"]
        assert result["workers"]["worker1"]["active"] == 2
        assert result["workers"]["worker2"]["queues"] == ["queue2", "queue3"]

    def test_check_celery_workers_ping_failed(self):
        inspect_obj = self.make_inspect(None, {}, {}, {}, {})
        app = Mock()
        app.control.inspect.return_value = inspect_obj

        result = check_celery_workers(app)
        assert result["status"] == "unavailable"
        assert result["available"] == 0

    def test_check_celery_workers_exception(self):
        def bad_inspect(timeout=None):
            raise RuntimeError("connection timeout")

        app = Mock()
        app.control.inspect.side_effect = bad_inspect

        result = check_celery_workers(app)
        assert result["status"] == "unavailable"
        assert "connection timeout" in result["error_message"]
