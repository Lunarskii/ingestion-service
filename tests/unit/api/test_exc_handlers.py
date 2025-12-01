import json
from types import SimpleNamespace

import pytest

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from services.api.exc_handlers import (
    application_exception_handler,
    unhandled_exception_handler,
    setup_exception_handlers,
)

from app.core import settings
from app.exceptions.base import (
    ApplicationError,
    UnexpectedError,
)


class TestExceptionHandlers:
    @pytest.mark.asyncio
    async def test_application_exception_handler_includes_debug_msg_when_debug(
        self, monkeypatch
    ):
        monkeypatch.setattr(
            settings, "exception", SimpleNamespace(error_detail_level="debug")
        )

        ex = SimpleNamespace(
            message="Some error",
            error_code="exception_error_code",
            debug_message="some debug message",
            status_code=400,
            headers={"X-Test": "1"},
        )

        response: JSONResponse = await application_exception_handler(None, ex)

        assert isinstance(response, JSONResponse)
        assert response.status_code == ex.status_code

        body = json.loads(response.body.decode())
        assert body.get("msg") == ex.message
        assert body.get("code") == ex.error_code
        assert body.get("debug_msg") == ex.debug_message
        assert response.headers.get("X-Test") == ex.headers.get("X-Test")

    @pytest.mark.asyncio
    async def test_application_exception_handler_without_debug_level(self, monkeypatch):
        monkeypatch.setattr(
            settings, "exception", SimpleNamespace(error_detail_level="safe")
        )

        ex = SimpleNamespace(
            message="Some error",
            error_code="exception_error_code",
            debug_message="some debug message",
            status_code=422,
            headers={},
        )
        response: JSONResponse = await application_exception_handler(None, ex)

        assert isinstance(response, JSONResponse)
        assert response.status_code == ex.status_code

        body = json.loads(response.body.decode())
        assert body.get("msg") == ex.message
        assert body.get("code") == ex.error_code
        assert "debug_msg" not in body

    @pytest.mark.asyncio
    async def test_unhandled_exception_handler_returns_unexpected_error(self):
        ex = Exception("unexpected exception")
        response: JSONResponse = await unhandled_exception_handler(None, ex)

        assert isinstance(response, JSONResponse)
        assert response.status_code == UnexpectedError.status_code

        body = json.loads(response.body.decode())
        assert body.get("msg") == UnexpectedError.message
        assert body.get("code") == UnexpectedError.error_code

        headers = UnexpectedError.headers or {}
        for header_key, header_value in headers.items():
            assert header_key in response.headers
            assert response.headers.get(header_key) == header_value

    def test_setup_exception_handlers_registers_handlers(self):
        app = FastAPI()
        setup_exception_handlers(app)

        handlers = getattr(app, "exception_handlers", {})
        assert ApplicationError in handlers
        assert Exception in handlers
