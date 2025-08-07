from typing import (
    Annotated,
    Any,
)
import sys

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)
from loguru import logger


class LoggingSettings(BaseSettings):
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


settings = LoggingSettings()

__logger_kwargs: dict[str, Any] = {
    "level": settings.level,
    "format": settings.format,
    "serialize": settings.serialize,
}
logger.remove()
logger.add(
    sys.stdout,
    **__logger_kwargs,
)
logger.add(
    "logs/app_{time:YYYY-MM-DD}.log",
    rotation=settings.rotation,
    retention=settings.retention,
    compression=settings.compression,
    **__logger_kwargs,
)
