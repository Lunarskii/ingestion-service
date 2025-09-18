from typing import (
    TYPE_CHECKING,
    Coroutine,
)
from functools import partial
import asyncio

from app.domain.embedding.base import EmbeddingModel
from app.domain.text_splitter.base import TextSplitter
from app.domain.security.service import KeycloakClient
from config import settings
from config.adapters import (
    raw_storage_adapter,
    vector_store_adapter,
)
from app.utils.singleton import singleton_registry


if TYPE_CHECKING:
    from fastapi import FastAPI


async def on_startup_event_handler(app: "FastAPI") -> None:
    """
    Инициализирует внешние сервисы и сохраняет их в ``app.state``.

    Инициализация выполняется параллельно через ``asyncio.to_thread`` + ``asyncio.gather``
    для избежания блокировки основного ивент-лупа.

    :param app: Экземпляр FastAPI, в котором будут установлены состояния.
    :type app: FastAPI
    """

    def __init_object(cls, *args, **kwargs) -> Coroutine:
        return asyncio.to_thread(
            partial(
                cls,
                *args,
                **kwargs,
            )
        )

    tasks: list[Coroutine] = [
        __init_object(
            EmbeddingModel,
            model_name_or_path=settings.embedding.model_name,
            device=settings.embedding.device,
            cache_folder=settings.embedding.cache_folder,
            token=settings.embedding.token,
            batch_size=settings.embedding.batch_size,
        ),
        __init_object(
            TextSplitter,
            chunk_size=settings.text_splitter.chunk_size,
            chunk_overlap=settings.text_splitter.chunk_overlap,
        ),
        __init_object(
            KeycloakClient,
            url=settings.keycloak.url,
            client_id=settings.keycloak.client_id,
            client_secret=settings.keycloak.client_secret,
            realm=settings.keycloak.realm,
            redirect_uri=settings.keycloak.redirect_uri,
            scope=settings.keycloak.scope,
        ),
    ]

    (
        embedding_model,
        text_splitter,
        keycloak,
    ) = await asyncio.gather(*tasks)

    keycloak.add_swagger_config(app)

    app.state.raw_storage = raw_storage_adapter.get_instance()  # type: ignore[attr-defined]
    app.state.vector_store = vector_store_adapter.get_instance()  # type: ignore[attr-defined]
    app.state.embedding_model = embedding_model  # type: ignore[attr-defined]
    app.state.text_splitter = text_splitter  # type: ignore[attr-defined]
    app.state.keycloak = keycloak  # type: ignore[attr-defined]


async def on_shutdown_event_handler(app: "FastAPI") -> None:
    await singleton_registry.close_all()


def setup_event_handlers(app: "FastAPI") -> None:
    """
    Регистрирует обработчики событий приложения.
    """

    app.add_event_handler("startup", partial(on_startup_event_handler, app))
    app.add_event_handler("shutdown", partial(on_shutdown_event_handler, app))
