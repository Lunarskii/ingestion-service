from typing import (
    Annotated,
    Any,
)
import sys
import logging
import inspect

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


class InterceptHandler(logging.Handler):
    """
    Класс-обработчик для перенаправления стандартного логирования Python
    в ``loguru``-логгер.

    Этот обработчик перехватывает записи из встроенного модуля :mod:`logging`
    и перенаправляет их в :class:`loguru.logger`.
    Таким образом можно использовать единый логгер во всём приложении,
    сохраняя совместимость с библиотеками, которые используют стандартный
    Python-логгер.
    """

    def emit(self, record: logging.LogRecord) -> None:
        """
        Перехватывает лог-запись и передаёт её в :class:`loguru.logger`.
        Автоматически маппит уровень логирования и сохраняет стек вызова.

        :param record: Лог-запись.
        :type record: logging.LogRecord
        """

        try:
            level: str = logger.level(record.levelname).name
        except ValueError:
            level: int = record.levelno

        frame_records: list[inspect.FrameInfo] = inspect.stack()
        depth: int = 0
        for i, frame_info in enumerate(frame_records):
            module: str = frame_info.frame.f_globals.get("__name__", "")
            if not module.startswith("logging") and module != __name__:
                depth = i
                break

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


logging.basicConfig(handlers=[InterceptHandler()], level=logging.NOTSET, force=True)
logging.getLogger().setLevel(logging.CRITICAL)
for noisy in ("uvicorn", "gunicorn", "httpx"):
    logging.getLogger(noisy).setLevel(logging.CRITICAL)
