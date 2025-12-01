import os

import pytest

from tests.generators import ValueGenerator
from app.stubs import FileRawStorage


class TestFileRawStorage:
    def test_init_raises_for_non_directory_path(
        self,
        tmp_document,
    ):
        _, path = tmp_document()
        with pytest.raises(ValueError):
            FileRawStorage(directory=path)

    @pytest.mark.parametrize(
        "directory, path",
        [
            (ValueGenerator.path(), ValueGenerator.uuid()),
            (ValueGenerator.path(1), ValueGenerator.uuid()),
        ],
    )
    def test_save_writes_bytes_to_correct_location(
        self,
        tmp_path,
        directory: str,
        path: str,
    ):
        directory = f"{tmp_path}/{directory}"
        file_bytes: bytes = ValueGenerator.bytes()

        raw_storage = FileRawStorage(directory=directory)
        raw_storage.save(file_bytes, path)

        with open(os.path.join(directory, path), "rb") as file:
            assert file.read() == file_bytes

    def test_get_bytes_from_correct_location(
        self,
        tmp_path,
        directory: str = ValueGenerator.path(),
        path: str = ValueGenerator.uuid(),
    ):
        directory = f"{tmp_path}/{directory}"
        file_bytes: bytes = ValueGenerator.bytes()

        raw_storage = FileRawStorage(directory=directory)
        raw_storage.save(file_bytes, path)

        assert file_bytes == raw_storage.get(path)

    def test_get_bytes_from_invalid_location(
        self,
        tmp_path,
        directory: str = ValueGenerator.path(),
        path: str = ValueGenerator.uuid(),
    ):
        directory = f"{tmp_path}/{directory}"

        raw_storage = FileRawStorage(directory=directory)

        with pytest.raises(FileNotFoundError):
            raw_storage.get(path)

    def test_delete_file_from_correct_location(
        self,
        tmp_path,
        directory: str = ValueGenerator.path(),
        path: str = ValueGenerator.uuid(),
    ):
        directory = f"{tmp_path}/{directory}"
        full_path: str = os.path.join(directory, path)
        file_bytes: bytes = ValueGenerator.bytes()

        raw_storage = FileRawStorage(directory=directory)
        raw_storage.save(file_bytes, path)

        with open(full_path, "rb") as file:
            assert file.read() == file_bytes

        raw_storage.delete(path)

        with pytest.raises(FileNotFoundError):
            open(full_path, "rb")

    def test_delete_directory_from_correct_location(
        self,
        tmp_path,
        directory: str = ValueGenerator.path(),
        path: str = ValueGenerator.uuid(),
    ):
        directory = f"{tmp_path}/{directory}"
        full_path: str = os.path.join(directory, path)
        file_bytes: bytes = ValueGenerator.bytes()

        raw_storage = FileRawStorage(directory=directory)
        raw_storage.save(file_bytes, path)

        with open(full_path, "rb") as file:
            assert file.read() == file_bytes

        raw_storage.delete_dir(os.path.dirname(path))

        with pytest.raises(FileNotFoundError):
            open(full_path, "rb")
