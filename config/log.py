from typing import Annotated

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class LogSettings(BaseSettings):
    """
    Настройки логирования
    """

    level: Annotated[str, Field(alias="LOG_LEVEL")] = "INFO"
    format: Annotated[str, Field(alias="LOG_FORMAT")] = "{message}"
    serialize: Annotated[bool, Field(alias="LOG_SERIALIZE")] = True
    rotation: Annotated[str | int, Field(alias="LOG_ROTATION")] = "1 day"
    retention: Annotated[str | int, Field(alias="LOG_RETENTION")] = "14 days"
    compression: Annotated[str, Field(alias="LOG_COMPRESSION")] = "zip"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
