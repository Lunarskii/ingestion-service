from typing import Annotated

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_parse_none_str="None",
        extra="ignore",
    )


class DatabaseSettings(BaseSettings):
    """
    Настройки базы данных
    """

    dialect: Annotated[str, Field(alias="DATABASE_DIALECT")] = "postgresql"
    driver: Annotated[str, Field(alias="DATABASE_DRIVER")] = "asyncpg"
    username: Annotated[str, Field(alias="DATABASE_USERNAME")]
    password: Annotated[str, Field(alias="DATABASE_PASSWORD")]
    host: Annotated[str, Field(alias="DATABASE_HOST")]
    port: Annotated[int, Field(alias="DATABASE_PORT")]
    name: Annotated[str, Field(alias="DATABASE_NAME")]
    echo: Annotated[bool, Field(alias="DATABASE_ECHO")] = False
    echo_pool: Annotated[bool, Field(alias="DATABASE_ECHO_POOL")] = False
    pool_pre_ping: Annotated[bool, Field(alias="DATABASE_POOL_PRE_PING")] = True
    auto_flush: Annotated[bool, Field(alias="DATABASE_AUTO_FLUSH")] = False
    auto_commit: Annotated[bool, Field(alias="DATABASE_AUTO_COMMIT")] = False
    expire_on_commit: Annotated[bool, Field(alias="DATABASE_EXPIRE_ON_COMMIT")] = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def url(self) -> str:
        return f"{self.dialect}+{self.driver}://{self.username}:{self.password}@{self.host}:{self.port}/{self.name}"


class DocumentRestrictionSettings(BaseSettings):
    """
    Настройки (ограничения) документа.
    """

    max_upload_mb: Annotated[int, Field(alias="DR_MAX_UPLOAD_MB")] = 25
    allowed_extensions: Annotated[set[str], Field(alias="DR_ALLOWED_EXTENSIONS")] = {
        ".pdf",
        ".docx",
    }

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class EmbeddingModelSettings(BaseSettings):
    """
    Настройки Embedding модели.
    """

    model_name: Annotated[str, Field(alias="EMBEDDING_MODEL_NAME")] = (
        "sentence-transformers/all-MiniLM-L6-v2"
    )
    device: Annotated[str | None, Field(alias="EMBEDDING_MODEL_DEVICE")] = None
    cache_folder: Annotated[str | None, Field(alias="EMBEDDING_MODEL_CACHE_FOLDER")] = (
        None
    )
    token: Annotated[bool | str | None, Field(alias="EMBEDDING_MODEL_TOKEN")] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_parse_none_str="None",
        extra="ignore",
    )


class TextSplitterSettings(BaseSettings):
    """
    Настройки для разделителя текста.
    """

    chunk_size: Annotated[int, Field(alias="TEXT_SPLITTER_CHUNK_SIZE")] = 500
    chunk_overlap: Annotated[int, Field(alias="TEXT_SPLITTER_CHUNK_OVERLAP")] = 50

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class StubSettings(BaseSettings):
    """
    Настройки хранилищ для локальной разработки.
    """

    raw_storage_path: Annotated[str, Field(alias="RAW_STORAGE_PATH")] = (
        "./local_storage/raw/"
    )
    index_path: Annotated[str, Field(alias="INDEX_PATH")] = "./local_storage/index/"
    sqlite_url: Annotated[str, Field(alias="SQLITE_URL")] = "./local_storage/sqlite.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class MinIOSettings(BaseSettings):
    """
    Настройки для файлового S3 хранилища MinIO.
    """

    endpoint: Annotated[str | None, Field(alias="MINIO_ENDPOINT")] = None
    bucket: Annotated[str | None, Field(alias="MINIO_BUCKET")] = None
    access_key: Annotated[str | None, Field(alias="MINIO_ACCESS_KEY")] = None
    secret_key: Annotated[str | None, Field(alias="MINIO_SECRET_KEY")] = None
    session_token: Annotated[str | None, Field(alias="MINIO_SESSION_TOKEN")] = None
    secure: Annotated[bool, Field(alias="MINIO_SECURE")] = False
    region: Annotated[str | None, Field(alias="MINIO_REGION")] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_parse_none_str="None",
        extra="ignore",
    )

    @property
    def is_configured(self) -> bool:
        return bool(
            self.endpoint and
            self.bucket and
            self.access_key and
            self.secret_key
        )


class QdrantSettings(BaseSettings):
    """
    Настройки для векторного хранилища Qdrant.
    """

    url: Annotated[str | None, Field(alias="QDRANT_URL")] = None
    collection: Annotated[str | None, Field(alias="QDRANT_COLLECTION")] = None
    host: Annotated[str | None, Field(alias="QDRANT_HOST")] = None
    port: Annotated[int, Field(alias="QDRANT_PORT")] = 6333
    grpc_port: Annotated[int, Field(alias="QDRANT_GRPC_PORT")] = 6334
    api_key: Annotated[str | None, Field(alias="QDRANT_API_KEY")] = None
    use_https: Annotated[bool, Field(alias="QDRANT_USE_HTTPS")] = False
    prefer_grpc: Annotated[bool, Field(alias="QDRANT_PREFER_GRPC")] = False
    timeout: Annotated[int | None, Field(alias="QDRANT_TIMEOUT")] = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_parse_none_str="None",
        extra="ignore",
    )

    @property
    def is_configured(self) -> bool:
        return bool(
            self.collection and (
                self.url or
                self.host and self.port or
                self.host and self.grpc_port and self.prefer_grpc
            )
        )
