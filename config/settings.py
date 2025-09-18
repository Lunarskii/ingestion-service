from typing import Annotated

from pydantic import Field
from pydantic_settings import (
    BaseSettings as _BaseSettings,
    SettingsConfigDict,
)


class BaseSettings(_BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_parse_none_str="None",
        extra="ignore",
    )


class APISettings(BaseSettings):
    """
    Настройки API (FastAPI).
    """

    title: Annotated[str, Field(alias="API_TITLE")] = "Ingestion Service"
    description: Annotated[str, Field(alias="API_DESCRIPTION")] = ""
    version: Annotated[str, Field(alias="API_VERSION")] = "0.1.0"
    openapi_url: Annotated[str | None, Field(alias="OPENAPI_URL")] = "/openapi.json"
    openapi_prefix: Annotated[str, Field(alias="API_PREFIX")] = ""
    docs_url: Annotated[str | None, Field(alias="DOCS_URL")] = "/docs"
    redoc_url: Annotated[str | None, Field(alias="REDOC_URL")] = "/redoc"
    root_path: Annotated[str, Field(alias="ROOT_PATH")] = ""


class DatabaseSettings(BaseSettings):
    """
    Настройки базы данных
    """

    url: Annotated[str, Field(alias="DATABASE_URL")] = (
        "sqlite+aiosqlite:///./local_storage/sqlite.db"
    )
    echo: Annotated[bool, Field(alias="DATABASE_ECHO")] = False
    echo_pool: Annotated[bool, Field(alias="DATABASE_ECHO_POOL")] = False
    pool_pre_ping: Annotated[bool, Field(alias="DATABASE_POOL_PRE_PING")] = True
    auto_flush: Annotated[bool, Field(alias="DATABASE_AUTO_FLUSH")] = False
    auto_commit: Annotated[bool, Field(alias="DATABASE_AUTO_COMMIT")] = False
    expire_on_commit: Annotated[bool, Field(alias="DATABASE_EXPIRE_ON_COMMIT")] = False


class DocumentRestrictionSettings(BaseSettings):
    """
    Настройки ограничений документа.
    """

    max_upload_mb: Annotated[int, Field(alias="DR_MAX_UPLOAD_MB")] = 25
    allowed_extensions: Annotated[set[str], Field(alias="DR_ALLOWED_EXTENSIONS")] = {
        ".pdf",
        ".docx",
    }


class EmbeddingSettings(BaseSettings):
    """
    Настройки Embedding модели.
    """

    model_name: Annotated[str, Field(alias="EMBEDDING_MODEL_NAME")] = (
        "sentence-transformers/all-MiniLM-L6-v2"
    )
    device: Annotated[str | None, Field(alias="EMBEDDING_DEVICE")] = None
    cache_folder: Annotated[str | None, Field(alias="EMBEDDING_CACHE_FOLDER")] = None
    token: Annotated[bool | str | None, Field(alias="EMBEDDING_TOKEN")] = None
    batch_size: Annotated[int, Field(alias="EMBEDDING_BATCH_SIZE")] = 32


class TextSplitterSettings(BaseSettings):
    """
    Настройки для разделителя текста.
    """

    chunk_size: Annotated[int, Field(alias="TEXT_SPLITTER_CHUNK_SIZE")] = 500
    chunk_overlap: Annotated[int, Field(alias="TEXT_SPLITTER_CHUNK_OVERLAP")] = 50


class DatetimeSettings(BaseSettings):
    """
    Настройки времени приложения.
    """

    serialization_format: Annotated[
        str,
        Field(alias="DATETIME_SERIALIZATION_FORMAT"),
    ] = "%Y-%m-%d %H:%M:%S"


class KeycloakSettings(BaseSettings):
    """
    Настройки для системы идентификации Keycloak.
    """

    url: Annotated[str, Field(alias="KEYCLOAK_URL")]
    client_id: Annotated[str, Field(alias="KEYCLOAK_CLIENT_ID")]
    client_secret: Annotated[str | None, Field(alias="KEYCLOAK_CLIENT_SECRET")] = None
    realm: Annotated[str, Field(alias="KEYCLOAK_REALM")]
    redirect_uri: Annotated[str, Field(alias="KEYCLOAK_REDIRECT_URI")]
    scope: Annotated[str, Field(alias="KEYCLOAK_SCOPE")] = "openid email profile"


class CelerySettings(BaseSettings):
    """
    Настройки для распределенной очереди задач Celery.
    """

    broker_url: Annotated[str, Field(alias="CELERY_BROKER_URL")]
    result_backend: Annotated[str | None, Field(alias="CELERY_RESULT_BACKEND")] = None
    enable_utc: Annotated[bool, Field(alias="CELERY_ENABLE_UTC")] = True
    timezone: Annotated[str | None, Field(alias="CELERY_TIMEZONE")] = "UTC"
    metrics_host: Annotated[str, Field(alias="CELERY_METRICS_HOST")] = "localhost"
    metrics_port: Annotated[int, Field(alias="CELERY_METRICS_PORT")] = 9002
    task_acks_late: Annotated[bool, Field(alias="CELERY_TASK_ACKS_LATE")] = True
    task_time_limit: Annotated[int, Field(alias="CELERY_TASK_TIME_LIMIT")] = 300
    task_soft_time_limit: Annotated[int, Field(alias="CELERY_TASK_SOFT_TIME_LIMIT")] = 270
    task_max_retries: Annotated[int, Field(alias="CELERY_TASK_MAX_RETRIES")] = 5
    task_retry_backoff: Annotated[int, Field(alias="CELERY_TASK_RETRY_BACKOFF")] = 2
    task_retry_jitter: Annotated[bool, Field(alias="CELERY_TASK_RETRY_JITTER")] = True
    worker_prefetch_multiplier: Annotated[int, Field(alias="CELERY_WORKER_PREFETCH_MULTIPLIER")] = 1
