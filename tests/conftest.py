from typing import (
    TYPE_CHECKING,
    Any,
)
import random
import os

import pytest
from fastapi.testclient import TestClient


if TYPE_CHECKING:
    from app.domain.document.schemas import File


def pytest_configure(config):
    os.environ["API_KEY_REQUIRED"] = "False"
    os.environ["API_AUTH_REQUIRED"] = "False"


@pytest.fixture
def tmp_document(tmp_path) -> Any:
    from tests.generators import DocumentGenerator

    _map: dict[int, tuple] = {
        0: (DocumentGenerator.pdf, ".pdf"),
        1: (DocumentGenerator.docx, ".docx"),
    }

    def _make(
        target_bytes: int = 1_000_000,
        doc_type: str | None = None,
    ) -> tuple["File", str]:
        from app.domain.document.schemas import File

        if doc_type:
            if doc_type == ".pdf":
                func, file_extension = _map[0]
            elif doc_type == ".docx":
                func, file_extension = _map[1]
            else:
                raise NotImplementedError()
        else:
            func, file_extension = _map[random.randint(0, len(_map) - 1)]
        file_name: str = f"document_{target_bytes}{file_extension}"
        path = tmp_path / file_name
        func(path, target_bytes)
        with open(path, "rb") as file:
            file_bytes: bytes = file.read()
        file = File(
            content=file_bytes,
            name=file_name,
        )
        return file, str(path)

    return _make


@pytest.fixture
def test_api_client() -> TestClient:
    from services.api.main import app

    dependencies = app.dependency_overrides.copy()  # noqa
    client = TestClient(app)
    try:
        yield client
    finally:
        app.dependency_overrides.clear()  # noqa
        app.dependency_overrides.update(dependencies)  # noqa
