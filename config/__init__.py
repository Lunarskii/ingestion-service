from config.api import APISettings as _APISettings
from config.storage import StorageSettings as _StorageSettings


api_settings = _APISettings()
storage_settings = _StorageSettings()

__all__ = [
    "api_settings",
    "storage_settings",
]
