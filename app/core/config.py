from typing import Literal
from functools import cached_property

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

    title: str = Field(default="Ingestion Service", alias="API_TITLE")
    description: str = Field(default="", alias="API_DESCRIPTION")
    version: str = Field(default="0.1.0", alias="API_VERSION")
    openapi_url: str | None = Field(default="/openapi.json", alias="OPENAPI_URL")
    openapi_prefix: str = Field(default="", alias="OPENAPI_PREFIX")
    docs_url: str | None = Field(default="/docs", alias="DOCS_URL")
    redoc_url: str | None = Field(default=None, alias="REDOC_URL")
    root_path: str = Field(default="", alias="ROOT_PATH")
    api_key_required: bool = Field(default=True, alias="API_KEY_REQUIRED")
    api_auth_required: bool = Field(default=True, alias="API_AUTH_REQUIRED")


class DatabaseSettings(BaseSettings):
    """
    Настройки базы данных
    """

    url: str = Field(
        default="sqlite+aiosqlite:///./local_storage/sqlite.db",
        alias="DATABASE_URL",
    )
    echo: bool = Field(default=False, alias="DATABASE_ECHO")
    echo_pool: bool = Field(default=False, alias="DATABASE_ECHO_POOL")
    pool_pre_ping: bool = Field(default=True, alias="DATABASE_POOL_PRE_PING")
    auto_flush: bool = Field(default=False, alias="DATABASE_AUTO_FLUSH")
    auto_commit: bool = Field(default=False, alias="DATABASE_AUTO_COMMIT")
    expire_on_commit: bool = Field(default=False, alias="DATABASE_EXPIRE_ON_COMMIT")


class DocumentRestrictionSettings(BaseSettings):
    """
    Настройки ограничений документа.
    """

    max_upload_mb: int = Field(default=25, alias="DR_MAX_UPLOAD_MB")
    allowed_extensions: set[str] = Field(
        default={".pdf", ".docx"},
        alias="DR_ALLOWED_EXTENSIONS",
    )


class EmbeddingSettings(BaseSettings):
    """
    Настройки Embedding модели.
    """

    model_name: str = Field(
        default="sentence-transformers/LaBSE",
        alias="EMBEDDING_MODEL_NAME",
    )
    device: str | None = Field(default=None, alias="EMBEDDING_DEVICE")
    cache_folder: str | None = Field(default=None, alias="EMBEDDING_CACHE_FOLDER")
    token: bool | str | None = Field(default=None, alias="EMBEDDING_TOKEN")
    batch_size: int = Field(default=32, alias="EMBEDDING_BATCH_SIZE")


class RerankerSettings(BaseSettings):
    model_name: str = Field(
        default="cross-encoder/ms-marco-MiniLM-L-6-v2",
        alias="RERANKER_MODEL_NAME",
    )
    device: str | None = Field(default=None, alias="RERANKER_DEVICE")
    cache_folder: str | None = Field(default=None, alias="RERANKER_CACHE_FOLDER")
    token: bool | str | None = Field(default=None, alias="RERANKER_TOKEN")
    batch_size: int = Field(default=32, alias="RERANKER_BATCH_SIZE")


class TextSplitterSettings(BaseSettings):
    """
    Настройки для разделителя текста.
    """

    chunk_size: int = Field(default=500, alias="TEXT_SPLITTER_CHUNK_SIZE")
    chunk_overlap: int = Field(default=50, alias="TEXT_SPLITTER_CHUNK_OVERLAP")


class StubSettings(BaseSettings):
    """
    Настройки хранилищ для локальной разработки.
    """

    raw_storage_path: str = Field(
        default="./local_storage/raw/",
        alias="RAW_STORAGE_PATH",
    )
    silver_storage_path: str = Field(
        default="./local_storage/silver/",
        alias="SILVER_STORAGE_PATH",
    )
    index_path: str = Field(
        default="./local_storage/index/",
        alias="INDEX_PATH",
    )


class MinIOSettings(BaseSettings):
    """
    Настройки для файлового S3 хранилища MinIO.
    """

    endpoint: str | None = Field(default=None, alias="MINIO_ENDPOINT")
    bucket_raw: str = Field(default="raw-zone", alias="MINIO_BUCKET_RAW")
    bucket_silver: str = Field(default="silver-zone", alias="MINIO_BUCKET_SILVER")
    access_key: str | None = Field(default=None, alias="MINIO_ACCESS_KEY")
    secret_key: str | None = Field(default=None, alias="MINIO_SECRET_KEY")
    session_token: str | None = Field(default=None, alias="MINIO_SESSION_TOKEN")
    secure: bool = Field(default=False, alias="MINIO_SECURE")
    region: str | None = Field(default=None, alias="MINIO_REGION")

    @property
    def is_configured(self) -> bool:
        return bool(self.endpoint and self.bucket_raw and self.bucket_silver)


class QdrantSettings(BaseSettings):
    """
    Настройки для векторного хранилища Qdrant.
    """

    url: str | None = Field(default=None, alias="QDRANT_URL")
    collection: str = Field(default="notebook_chunks", alias="QDRANT_COLLECTION")
    host: str | None = Field(default=None, alias="QDRANT_HOST")
    port: int = Field(default=6333, alias="QDRANT_PORT")
    grpc_port: int = Field(default=6334, alias="QDRANT_GRPC_PORT")
    api_key: str | None = Field(default=None, alias="QDRANT_API_KEY")
    use_https: bool = Field(default=False, alias="QDRANT_USE_HTTPS")
    prefer_grpc: bool = Field(default=False, alias="QDRANT_PREFER_GRPC")
    timeout: int | None = Field(default=30, alias="QDRANT_TIMEOUT")
    vector_size: int = Field(default=768, alias="QDRANT_VECTOR_SIZE")
    distance: str = Field(default="Cosine", alias="QDRANT_DISTANCE")

    @property
    def is_configured(self) -> bool:
        return bool(
            self.collection
            and (
                self.url
                or (self.host and self.port)
                or (self.host and self.grpc_port and self.prefer_grpc)
            )
        )


class OllamaSettings(BaseSettings):
    url: str | None = Field(default=None, alias="OLLAMA_URL")
    api_key: str | None = Field(default=None, alias="OLLAMA_API_KEY")
    model: str | None = Field(default=None, alias="OLLAMA_MODEL")
    timeout: int = Field(default=30, alias="OLLAMA_TIMEOUT_SECONDS")

    @property
    def is_configured(self) -> bool:
        return bool(self.url and self.model)


class OpenAISettings(BaseSettings):
    url: str | None = Field(default=None, alias="OPENAI_URL")
    websocket_url: str | None = Field(default=None, alias="OPENAI_WEBSOCKET_URL")
    api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    model: str | None = Field(default=None, alias="OPENAI_MODEL")
    organization: str | None = Field(default=None, alias="OPENAI_ORGANIZATION")
    project: str | None = Field(default=None, alias="OPENAI_PROJECT")
    webhook_secret: str | None = Field(default=None, alias="OPENAI_WEBHOOK_SECRET")
    timeout: int = Field(default=30, alias="OPENAI_TIMEOUT_SECONDS")
    max_retries: int = Field(default=2, alias="OPENAI_MAX_RETRIES")

    @property
    def is_configured(self) -> bool:
        return bool(self.url and self.model)


class LoguruSettings(BaseSettings):
    """
    Настройки логирования.
    """

    level: str = Field(default="INFO", alias="LOG_LEVEL")
    format: str = Field(default="{message}", alias="LOG_FORMAT")
    serialize: bool = Field(default=True, alias="LOG_SERIALIZE")
    rotation: str | int = Field(default="1 day", alias="LOG_ROTATION")
    retention: str | int = Field(default="14 days", alias="LOG_RETENTION")
    compression: str = Field(default="zip", alias="LOG_COMPRESSION")


class DatetimeSettings(BaseSettings):
    """
    Настройки времени приложения.
    """

    serialization_format: str = Field(
        default="%Y-%m-%d %H:%M:%S",
        alias="DATETIME_SERIALIZATION_FORMAT",
    )


class KeycloakSettings(BaseSettings):
    """
    Настройки для системы идентификации Keycloak.
    """

    url: str | None = Field(default=None, alias="KEYCLOAK_URL")
    client_id: str | None = Field(default=None, alias="KEYCLOAK_CLIENT_ID")
    client_secret: str | None = Field(default=None, alias="KEYCLOAK_CLIENT_SECRET")
    realm: str | None = Field(default=None, alias="KEYCLOAK_REALM")
    redirect_uri: str | None = Field(default=None, alias="KEYCLOAK_REDIRECT_URI")
    scope: str = Field(default="openid email profile", alias="KEYCLOAK_SCOPE")


class CelerySettings(BaseSettings):
    """
    Настройки для распределенной очереди задач Celery.
    """

    broker_url: str | None = Field(default=None, alias="CELERY_BROKER_URL")
    result_backend: str | None = Field(default=None, alias="CELERY_RESULT_BACKEND")
    enable_utc: bool = Field(default=True, alias="CELERY_ENABLE_UTC")
    timezone: str | None = Field(default="UTC", alias="CELERY_TIMEZONE")
    task_acks_late: bool = Field(default=True, alias="CELERY_TASK_ACKS_LATE")
    task_time_limit: int = Field(default=300, alias="CELERY_TASK_TIME_LIMIT")
    task_soft_time_limit: int = Field(
        default=270,
        alias="CELERY_TASK_SOFT_TIME_LIMIT",
    )
    task_max_retries: int = Field(default=5, alias="CELERY_TASK_MAX_RETRIES")
    task_retry_backoff: int = Field(default=2, alias="CELERY_TASK_RETRY_BACKOFF")
    task_retry_jitter: bool = Field(default=True, alias="CELERY_TASK_RETRY_JITTER")
    worker_prefetch_multiplier: int = Field(
        default=1,
        alias="CELERY_WORKER_PREFETCH_MULTIPLIER",
    )
    metrics_host: str = Field(default="localhost", alias="CELERY_METRICS_HOST")
    metrics_port: int = Field(default=9091, alias="CELERY_METRICS_PORT")
    collect_events_metrics_interval_s: int = Field(
        default=5,
        alias="CELERY_COLLECT_EVENTS_METRICS_INTERVAL_S",
    )
    collect_queue_metrics_interval_s: int = Field(
        default=5,
        alias="CELERY_COLLECT_QUEUE_METRICS_INTERVAL_S",
    )


class ExceptionSettings(BaseSettings):
    """
    Настройки исключений.
    """

    error_detail_level: Literal["safe", "debug"] = Field(
        default="safe",
        alias="ERROR_DETAIL_LEVEL",
    )


class ClassifierSettings(BaseSettings):
    """
    Настройки классификатора тем.
    """

    topics_path: str = Field(default="./topics.yml", alias="CLASSIFIER_TOPICS_PATH")
    rules_path: str = Field(default="./rules.yml", alias="CLASSIFIER_RULES_PATH")
    default_top_k: int = Field(default=5, alias="CLASSIFIER_DEFAULT_TOP_K")


class KafkaSettings(BaseSettings):
    """
    Настройки брокера сообщений Kafka.
    """

    broker: str = Field(default="kafka:9092", alias="KAFKA_BROKER")
    topic_doc_new: str = Field(default="cti.doc.new.v1", alias="KAFKA_TOPIC_DOC_NEW")
    group_id: str = Field(default="iuwc-kb-consumer", alias="KAFKA_GROUP_ID")
    max_retries: int = Field(default=3, alias="KAFKA_MAX_RETRIES")
    retry_backoff_ms: int = Field(default=500, alias="KAFKA_RETRY_BACKOFF_MS")


class ChatSettings(BaseSettings):
    """
    Настройки чата.
    """

    chat_history_memory_limit: int = Field(
        default=4,
        alias="CHAT_HISTORY_MEMORY_LIMIT",
    )


class Settings:
    """
    Настройки приложения.
    """

    @cached_property
    def api(self) -> APISettings:
        return APISettings()

    @cached_property
    def db(self) -> DatabaseSettings:
        return DatabaseSettings()

    @cached_property
    def document_restriction(self) -> DocumentRestrictionSettings:
        return DocumentRestrictionSettings()

    @cached_property
    def embedding(self) -> EmbeddingSettings:
        return EmbeddingSettings()

    @cached_property
    def reranker(self) -> RerankerSettings:
        return RerankerSettings()

    @cached_property
    def text_splitter(self) -> TextSplitterSettings:
        return TextSplitterSettings()

    @cached_property
    def datetime(self) -> DatetimeSettings:
        return DatetimeSettings()

    @cached_property
    def keycloak(self) -> KeycloakSettings:
        return KeycloakSettings()

    @cached_property
    def celery(self) -> CelerySettings:
        return CelerySettings()

    @cached_property
    def exception(self) -> ExceptionSettings:
        return ExceptionSettings()

    @cached_property
    def classifier(self) -> ClassifierSettings:
        return ClassifierSettings()

    @cached_property
    def stub(self) -> StubSettings:
        return StubSettings()

    @cached_property
    def minio(self) -> MinIOSettings:
        return MinIOSettings()

    @cached_property
    def qdrant(self) -> QdrantSettings:
        return QdrantSettings()

    @cached_property
    def ollama(self) -> OllamaSettings:
        return OllamaSettings()

    @cached_property
    def openai(self) -> OpenAISettings:
        return OpenAISettings()

    @cached_property
    def loguru(self) -> LoguruSettings:
        return LoguruSettings()

    @cached_property
    def kafka(self) -> KafkaSettings:
        return KafkaSettings()

    @cached_property
    def chat(self) -> ChatSettings:
        return ChatSettings()


settings = Settings()
