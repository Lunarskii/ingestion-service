from exceptions.base import ApplicationError


class RawStorageError(ApplicationError):
    """
    Базовый класс для ошибок RawStorage.
    """

    message = "RawStorage error"
    error_code = "raw_storage_error"


class VectorStoreError(ApplicationError):
    """
    Базовый класс для ошибок VectorStore.
    """

    message = "VectorStore error"
    error_code = "vector_store_error"


class MetadataRepositoryError(ApplicationError):
    """
    Базовый класс для ошибок MetadataRepository.
    """

    message = "MetadataRepository error"
    error_code = "metadata_repository_error"
