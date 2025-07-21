class ApplicationError(Exception):
    """
    Общий базовый класс для всех исключений.
    """

    message: str = "Application error"
    error_code: str = "unknown_error"

    def __init__(
        self,
        message: str | None = None,
        error_code: str | None = None,
    ):
        self.message = message or self.message
        self.error_code = error_code or self.error_code
        super().__init__(
            self.message,
            self.error_code,
        )


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
