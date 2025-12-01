from typing import TYPE_CHECKING
from functools import partial

from app.domain.classifier.utils import sync_topics_with_db
from app.utils.singleton import singleton_registry
from app.core import (
    settings,
    logger,
)


if TYPE_CHECKING:
    from fastapi import FastAPI


async def on_startup_event_handler(app: "FastAPI") -> None:
    """
    - Запускает синхронизацию topics.yml с базой данных.

    :param app: Экземпляр FastAPI, в котором будут установлены состояния.
    """

    try:
        await sync_topics_with_db(settings.classifier.topics_path)
    except Exception as e:
        logger.warning(
            "Произошла ошибка при синхронизации топиков: возможно, топики уже созданы",
            error_message=str(e),
        )


async def on_shutdown_event_handler(app: "FastAPI") -> None:
    """
    - Закрывает (уничтожает) все объекты в реестре синглтонов, если они были там созданы.
    """

    await singleton_registry.close_all()


def setup_event_handlers(app: "FastAPI") -> None:
    """
    Регистрирует обработчики событий приложения.
    """

    app.add_event_handler("startup", partial(on_startup_event_handler, app))
    app.add_event_handler("shutdown", partial(on_shutdown_event_handler, app))
