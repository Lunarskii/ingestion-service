from exceptions.storage import (
    RawStorageError,
    VectorStoreError,
    MetadataRepositoryError,
)
from exceptions.base import status


class RawStorageSaveError(RawStorageError):
    message = "Ошибка при попытке сохранения файла в хранилище."
    error_code = "raw_storage_save_failed"


class RawStorageInvalidPath(RawStorageSaveError):
    message = ""
    error_code = "raw_storage_invalid_path"


class VectorStoreDocumentsNotFound(VectorStoreError):
    message = "'workspace_id' отсутствует или в этом рабочем пространстве нет документов."
    error_code = "documents_not_found"
    status_code = status.HTTP_404_NOT_FOUND


class VectorStoreMissingMetadata(VectorStoreError):
    message = "Отсутствует поле 'document_id' или 'workspace_id' в метаданных вектора"
    error_code = "missing_metadata"
    status_code = status.HTTP_400_BAD_REQUEST


class VectorStoreMissingData(VectorStoreError):
    message = "Вектора отсутствуют, сохранение невозможно."
    error_code = "missing_data"
    status_code = status.HTTP_400_BAD_REQUEST


class MetadataRepositorySaveError(MetadataRepositoryError): ...
