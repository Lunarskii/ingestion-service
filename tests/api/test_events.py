from fastapi.testclient import TestClient

from api.main import app


async def _fake_to_thread(func, *args, **kwargs):
    return func(*args, **kwargs)


class TestAPIEvents:
    def test_startup_sets_app_state(self, monkeypatch):
        monkeypatch.setattr("asyncio.to_thread", _fake_to_thread)

        with TestClient(app):
            assert app.state.raw_storage is not None
            assert app.state.vector_store is not None
            assert app.state.embedding_model is not None
            assert app.state.text_splitter is not None
