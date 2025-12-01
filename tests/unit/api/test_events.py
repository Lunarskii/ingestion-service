import pytest
import asyncio
from types import SimpleNamespace

from services.api.events import (
    on_startup_event_handler,
    on_shutdown_event_handler,
    setup_event_handlers,
)
from app.core import settings


class DummyApp:
    def __init__(self):
        self.handlers: list[tuple[str, object]] = []

    def add_event_handler(self, event_name: str, handler):
        self.handlers.append((event_name, handler))


class TestFastAPIEvents:
    @pytest.mark.asyncio
    async def test_on_startup_calls_sync_topics_with_settings_path(self, monkeypatch):
        called = []

        async def fake_sync_topics_with_db(path):
            called.append(path)
            return None

        monkeypatch.setattr(
            "services.api.events.sync_topics_with_db", fake_sync_topics_with_db
        )

        monkeypatch.setattr(
            settings, "classifier", SimpleNamespace(topics_path="topics.yml")
        )

        await on_startup_event_handler(
            app=DummyApp(),
        )

        assert called == ["topics.yml"]

    @pytest.mark.asyncio
    async def test_on_shutdown_calls_singleton_registry_close_all(self, monkeypatch):
        called = {"closed": False}

        async def fake_close_all():
            called["closed"] = True

        monkeypatch.setattr(
            "services.api.events.singleton_registry.close_all", fake_close_all
        )

        await on_shutdown_event_handler(
            app=DummyApp(),
        )

        assert called["closed"]

    @pytest.mark.asyncio
    async def test_setup_event_handlers_registers_and_handlers_call_underlying_functions(
        self,
        monkeypatch,
    ):
        startup_called = []
        shutdown_called = []

        async def fake_sync_topics_with_db(path):
            startup_called.append(path)
            return None

        async def fake_close_all():
            shutdown_called.append(True)
            return None

        monkeypatch.setattr(
            "services.api.events.sync_topics_with_db", fake_sync_topics_with_db
        )
        monkeypatch.setattr(
            "services.api.events.singleton_registry.close_all", fake_close_all
        )

        monkeypatch.setattr(
            settings, "classifier", type("C", (), {"topics_path": "topics.yml"})
        )

        app = DummyApp()
        setup_event_handlers(app)

        event_names = [name for name, _ in app.handlers]
        assert "startup" in event_names
        assert "shutdown" in event_names

        startup_handler = next(
            handler for name, handler in app.handlers if name == "startup"
        )
        shutdown_handler = next(
            handler for name, handler in app.handlers if name == "shutdown"
        )

        coro = startup_handler()
        assert asyncio.iscoroutine(coro)
        await coro
        assert startup_called == ["topics.yml"]

        coro2 = shutdown_handler()
        assert asyncio.iscoroutine(coro2)
        await coro2
        assert shutdown_called == [True]
