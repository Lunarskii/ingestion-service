from typing import Annotated

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class LoggingSettings(BaseSettings):
    """
    Настройки логирования
    """

    level: Annotated[str, Field(alias="LOGGING_LEVEL")] = "INFO"
    format: Annotated[str, Field(alias="LOGGING_FORMAT")] = "{message}"
    serialize: Annotated[bool, Field(alias="LOGGING_SERIALIZE")] = True

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )
