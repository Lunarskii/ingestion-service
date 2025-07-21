import sys

from loguru import logger

from config.api import APISettings
from config.storage import StorageSettings
from config.document import DocumentSettings
from config.logging import LoggingSettings


api_settings = APISettings()
storage_settings = StorageSettings()
document_settings = DocumentSettings()
logging_settings = LoggingSettings()

logger.remove()
logger.add(
    sys.stdout,
    level=logging_settings.level,
    format=logging_settings.format,
    serialize=logging_settings.serialize,
)

__all__ = [
    "APISettings",
    "StorageSettings",
    "DocumentSettings",
    "LoggingSettings",
    "api_settings",
    "storage_settings",
    "document_settings",
    "logging_settings",
    "logger",
]
