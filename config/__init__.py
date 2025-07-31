from typing import Any
import sys

from loguru import logger

from config.api import APISettings
from config.storage import StorageSettings
from config.document import DocumentRestrictionSettings
from config.log import LogSettings
from config.embedding import EmbeddingSettings
from config.splitter import TextSplitterSettings
from config.database import DatabaseSettings


api_settings = APISettings()
storage_settings = StorageSettings()
document_restriction_settings = DocumentRestrictionSettings()
log_settings = LogSettings()
embedding_settings = EmbeddingSettings()
text_splitter_settings = TextSplitterSettings()
database_settings = DatabaseSettings()

__logger_kwargs: dict[str, Any] = {
    "level": log_settings.level,
    "format": log_settings.format,
    "serialize": log_settings.serialize,
}
logger.remove()
logger.add(
    sys.stdout,
    **__logger_kwargs,
)
logger.add(
    "logs/app_{time:YYYY-MM-DD}.log",
    rotation=log_settings.rotation,
    retention=log_settings.retention,
    compression=log_settings.compression,
    **__logger_kwargs,
)

__all__ = [
    "APISettings",
    "StorageSettings",
    "DocumentRestrictionSettings",
    "LogSettings",
    "EmbeddingSettings",
    "TextSplitterSettings",
    "DatabaseSettings",
    "api_settings",
    "storage_settings",
    "document_restriction_settings",
    "log_settings",
    "embedding_settings",
    "text_splitter_settings",
    "database_settings",
    "logger",
]
