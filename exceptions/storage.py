from exceptions.base import ApplicationError


class RawStorageError(ApplicationError):
    """
    Общий базовый класс для всех исключений RawStorage.
    """

    message = "RawStorage error"
    error_code = "raw_storage_error"


class VectorStoreError(ApplicationError):
    """
    Общий базовый класс для всех исключений VectorStore.
    """

    message = "VectorStore error"
    error_code = "vector_store_error"


class MetadataRepositoryError(ApplicationError):
    """
    Общий базовый класс для всех исключений MetadataRepository.
    """

    message = "MetadataRepository error"
    error_code = "metadata_repository_error"
