import pytest

from tests.conftest import ValueGenerator
from infrastructure.storage_minio import MinIORawStorage
from config import settings


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

        assert minio.exists(path) == False
        minio.save(file_bytes, path)
        assert minio.exists(path) == True
        minio.delete(path)
        assert minio.exists(path) == False

    def test_get_bytes_correct(
        self,
        minio: MinIORawStorage,
    ):
        file_bytes: bytes = b"some dummy file content"
        path: str = f"{ValueGenerator.path()}{ValueGenerator.uuid()}.ext"

        assert minio.exists(path) == False
        minio.save(file_bytes, path)
        assert minio.exists(path) == True
        assert minio.get(path) == file_bytes
        minio.delete(path)
        assert minio.exists(path) == False

    def test_delete_correct(
        self,
        minio: MinIORawStorage,
    ):
        file_bytes: bytes = b"some dummy file content"
        path: str = f"{ValueGenerator.path()}{ValueGenerator.uuid()}.ext"

        assert minio.exists(path) == False
        minio.save(file_bytes, path)
        assert minio.exists(path) == True
        minio.delete(path)
        assert minio.exists(path) == False

    def test_exists_correct_path(
        self,
        minio: MinIORawStorage,
    ):
        file_bytes: bytes = b"some dummy file content"
        path: str = f"{ValueGenerator.path()}{ValueGenerator.uuid()}.ext"

        assert minio.exists(path) == False
        minio.save(file_bytes, path)
        assert minio.exists(path) == True
        minio.delete(path)
        assert minio.exists(path) == False

    def test_exists_invalid_path(
        self,
        minio: MinIORawStorage,
    ):
        path: str = f"{ValueGenerator.path()}{ValueGenerator.uuid()}.ext"
        assert minio.exists(path) == False
