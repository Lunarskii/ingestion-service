import pytest

from tests.conftest import ValueGenerator
from app.infrastructure import MinIORawStorage
from app.config import settings


@pytest.fixture
def minio() -> MinIORawStorage:
    return MinIORawStorage(
        endpoint=settings.minio.endpoint,
        bucket_name=settings.minio.bucket_raw,
        access_key=settings.minio.access_key,
        secret_key=settings.minio.secret_key,
        session_token=settings.minio.session_token,
        secure=settings.minio.secure,
        region=settings.minio.region,
    )


class TestMinIORawStorage:
    def test_save_writes_bytes_correct(
        self,
        minio: MinIORawStorage,
    ):
        file_bytes: bytes = b"some dummy file content"
        path: str = f"{ValueGenerator.path()}{ValueGenerator.uuid()}.ext"

        assert not minio.exists(path)
        minio.save(file_bytes, path)
        assert minio.exists(path)
        minio.delete(path)
        assert not minio.exists(path)

    def test_get_bytes_correct(
        self,
        minio: MinIORawStorage,
    ):
        file_bytes: bytes = b"some dummy file content"
        path: str = f"{ValueGenerator.path()}{ValueGenerator.uuid()}.ext"

        assert not minio.exists(path)
        minio.save(file_bytes, path)
        assert minio.exists(path)
        assert minio.get(path) == file_bytes
        minio.delete(path)
        assert not minio.exists(path)

    def test_delete_correct(
        self,
        minio: MinIORawStorage,
    ):
        file_bytes: bytes = b"some dummy file content"
        path: str = f"{ValueGenerator.path()}{ValueGenerator.uuid()}.ext"

        assert not minio.exists(path)
        minio.save(file_bytes, path)
        assert minio.exists(path)
        minio.delete(path)
        assert not minio.exists(path)

    def test_exists_correct_path(
        self,
        minio: MinIORawStorage,
    ):
        file_bytes: bytes = b"some dummy file content"
        path: str = f"{ValueGenerator.path()}{ValueGenerator.uuid()}.ext"

        assert not minio.exists(path)
        minio.save(file_bytes, path)
        assert minio.exists(path)
        minio.delete(path)
        assert not minio.exists(path)

    def test_exists_invalid_path(
        self,
        minio: MinIORawStorage,
    ):
        path: str = f"{ValueGenerator.path()}{ValueGenerator.uuid()}.ext"
        assert not minio.exists(path)
