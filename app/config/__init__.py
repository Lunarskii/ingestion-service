from functools import cached_property

from app.config.settings import (
    APISettings as _APISettings,
    DatabaseSettings as _DatabaseSettings,
    DocumentRestrictionSettings as _DocumentRestrictionSettings,
    EmbeddingSettings as _EmbeddingSettings,
    TextSplitterSettings as _TextSplitterSettings,
    DatetimeSettings as _DatetimeSettings,
    KeycloakSettings as _KeycloakSettings,
    CelerySettings as _CelerySettings,
)
from app.config.logging import logger


class Settings:
    """
    Настройки приложения.
    """

    @cached_property
    def api(self) -> _APISettings:
        return _APISettings()

    @cached_property
    def db(self) -> _DatabaseSettings:
        return _DatabaseSettings()

    @cached_property
    def document_restriction(self) -> _DocumentRestrictionSettings:
        return _DocumentRestrictionSettings()

    @cached_property
    def embedding(self) -> _EmbeddingSettings:
        return _EmbeddingSettings()

    @cached_property
    def text_splitter(self) -> _TextSplitterSettings:
        return _TextSplitterSettings()

    @cached_property
    def datetime(self) -> _DatetimeSettings:
        return _DatetimeSettings()

    @cached_property
    def keycloak(self) -> _KeycloakSettings:
        return _KeycloakSettings()

    @cached_property
    def celery(self) -> _CelerySettings:
        return _CelerySettings()


settings = Settings()


__all__ = [
    "Settings",
    "settings",
    "logger",
]
