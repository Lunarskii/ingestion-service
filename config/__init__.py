from config.api import APISettings as _APISettings
from config.default import DefaultSettings as _DefaultSettings


api_settings = _APISettings()
default_settings = _DefaultSettings()

__all__ = [
    "api_settings",
    "default_settings",
]
