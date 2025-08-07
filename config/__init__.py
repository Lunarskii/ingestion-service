from config.settings import (
    APISettings as _APISettings,
    DatabaseSettings as _DatabaseSettings,
    DocumentRestrictionSettings as _DocumentRestrictionSettings,
    EmbeddingModelSettings as _EmbeddingModelSettings,
    TextSplitterSettings as _TextSplitterSettings,
    StubSettings as _StubSettings,
    MinIOSettings as _MinIOSettings,
)
from config.logging import logger


class Settings:
    api = _APISettings()
    db = _DatabaseSettings()
    document_restriction = _DocumentRestrictionSettings()
    embedding_model = _EmbeddingModelSettings()
    text_splitter = _TextSplitterSettings()
    stub = _StubSettings()
    minio = _MinIOSettings()


settings = Settings()

__all__ = [
    "Settings",
    "settings",
    "logger",
]
