from typing import Any

from tests.generators import ValueGenerator
from app.infrastructure.storage_minio import MinIORawStorage


class TestMinIORawStorage:
    def test_save_writes_bytes_correct(
        self,
        minio: MinIORawStorage,
        tmp_document: Any,
    ):
        file, path = tmp_document()

        assert not minio.exists(path)
        minio.save(file.content, path)
        assert minio.exists(path)
        minio.delete(path)
        assert not minio.exists(path)

    def test_get_bytes_correct(
        self,
        minio: MinIORawStorage,
        tmp_document: Any,
    ):
        file, path = tmp_document()

        assert not minio.exists(path)
        minio.save(file.content, path)
        assert minio.exists(path)
        assert minio.get(path) == file.content
        minio.delete(path)
        assert not minio.exists(path)

    def test_delete_correct(
        self,
        minio: MinIORawStorage,
        tmp_document: Any,
    ):
        file, path = tmp_document()

        assert not minio.exists(path)
        minio.save(file.content, path)
        assert minio.exists(path)
        minio.delete(path)
        assert not minio.exists(path)

    def test_delete_dir_correct(
        self,
        minio: MinIORawStorage,
        tmp_document: Any,
    ):
        dir_name: str = "test_dir_name"
        path1: str = f"{dir_name}/{ValueGenerator.uuid()}.ext"
        path2: str = f"{dir_name}/{ValueGenerator.uuid()}.ext"
        file, _ = tmp_document()

        assert not minio.exists(path1)
        assert not minio.exists(path2)
        minio.save(file.content, path1)
        minio.save(file.content, path2)
        assert minio.exists(path1)
        assert minio.exists(path2)
        minio.delete_dir(dir_name)
        assert not minio.exists(path1)
        assert not minio.exists(path2)

    def test_exists_correct_path(
        self,
        minio: MinIORawStorage,
        tmp_document: Any,
    ):
        file, path = tmp_document()

        assert not minio.exists(path)
        minio.save(file.content, path)
        assert minio.exists(path)
        minio.delete(path)
        assert not minio.exists(path)

    def test_exists_invalid_path(
        self,
        minio: MinIORawStorage,
    ):
        path: str = f"{ValueGenerator.path()}{ValueGenerator.uuid()}.ext"
        assert not minio.exists(path)
