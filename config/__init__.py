from config.settings import (
    APISettings as _APISettings,
    DatabaseSettings as _DatabaseSettings,
    DocumentRestrictionSettings as _DocumentRestrictionSettings,
    EmbeddingSettings as _EmbeddingSettings,
    TextSplitterSettings as _TextSplitterSettings,
    StubSettings as _StubSettings,
    MinIOSettings as _MinIOSettings,
    QdrantSettings as _QdrantSettings,
    DatetimeSettings as _DatetimeSettings,
    KeycloakSettings as _KeycloakSettings,
    CelerySettings as _CelerySettings,
)
from config.logging import logger


class Settings:
    """
    Настройки приложения.
    """

    api = _APISettings()
    db = _DatabaseSettings()
    document_restriction = _DocumentRestrictionSettings()
    embedding = _EmbeddingSettings()
    text_splitter = _TextSplitterSettings()
    stub = _StubSettings()
    minio = _MinIOSettings()
    qdrant = _QdrantSettings()
    datetime = _DatetimeSettings()
    keycloak = _KeycloakSettings()
    celery = _CelerySettings()


settings = Settings()

__all__ = [
    "Settings",
    "settings",
    "logger",
]
