from typing import Any
import sys
import logging
import inspect

from loguru import logger

from app.core.config import settings


__logger_kwargs: dict[str, Any] = {
    "level": settings.loguru.level,
    "format": settings.loguru.format,
    "serialize": settings.loguru.serialize,
}

logger.remove()
logger.add(
    sys.stdout,
    **__logger_kwargs,
)
logger.add(
    "logs/app_{time:YYYY-MM-DD}.log", # TODO вынести в конфиг
    rotation=settings.loguru.rotation,
    retention=settings.loguru.retention,
    compression=settings.loguru.compression,
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
for noisy in ("httpx", "fontTools", "fontTools.subset"):
    logging.getLogger(noisy).setLevel(logging.CRITICAL)
