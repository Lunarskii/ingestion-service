from exceptions.base import (
    RawStorageError,
    VectorStoreError,
    MetadataRepositoryError,
)


class RawStorageSaveError(RawStorageError):
    message = "Ошибка при попытке сохранения файла в хранилище."
    error_code = "raw_storage_save_failed"


class RawStorageInvalidPath(RawStorageSaveError):
    message = ""
    error_code = "raw_storage_invalid_path"


class VectorStoreUpsertError(VectorStoreError):
    ...


class MetadataRepositorySaveError(MetadataRepositoryError):
    ...
