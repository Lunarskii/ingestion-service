from functools import partial
from typing import (
    Any,
    Annotated,
    Callable,
)
import threading

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)

from infrastructure.storage_minio import MinIORawStorage
from infrastructure.vectorstore_qdrant import QdrantVectorStore
from stubs import (
    FileRawStorage,
    JSONVectorStore,
)


class StubSettings(BaseSettings):
    """
    Настройки хранилищ для локальной разработки.
    """

    raw_storage_path: Annotated[str, Field(alias="RAW_STORAGE_PATH")] = (
        "./local_storage/raw/"
    )
    silver_storage_path: Annotated[str, Field(alias="SILVER_STORAGE_PATH")] = (
        "./local_storage/silver/"
    )
    index_path: Annotated[str, Field(alias="INDEX_PATH")] = "./local_storage/index/"

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
    bucket_raw: Annotated[str, Field(alias="MINIO_BUCKET_RAW")] = "raw-zone"
    bucket_silver: Annotated[str, Field(alias="MINIO_BUCKET_SILVER")] = "silver-zone"
    access_key: Annotated[str | None, Field(alias="MINIO_ACCESS_KEY")] = None
    secret_key: Annotated[str | None, Field(alias="MINIO_SECRET_KEY")] = None
    session_token: Annotated[str | None, Field(alias="MINIO_SESSION_TOKEN")] = None
    secure: Annotated[bool, Field(alias="MINIO_SECURE")] = False
    region: Annotated[str | None, Field(alias="MINIO_REGION")] = None

    @property
    def is_configured(self) -> bool:
        return bool(self.endpoint and self.bucket_raw and self.bucket_silver)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_parse_none_str="None",
        extra="ignore",
    )


class QdrantSettings(BaseSettings):
    """
    Настройки для векторного хранилища Qdrant.
    """

    url: Annotated[str | None, Field(alias="QDRANT_URL")] = None
    collection: Annotated[str, Field(alias="QDRANT_COLLECTION")] = "notebook_chunks"
    host: Annotated[str | None, Field(alias="QDRANT_HOST")] = None
    port: Annotated[int, Field(alias="QDRANT_PORT")] = 6333
    grpc_port: Annotated[int, Field(alias="QDRANT_GRPC_PORT")] = 6334
    api_key: Annotated[str | None, Field(alias="QDRANT_API_KEY")] = None
    use_https: Annotated[bool, Field(alias="QDRANT_USE_HTTPS")] = False
    prefer_grpc: Annotated[bool, Field(alias="QDRANT_PREFER_GRPC")] = False
    timeout: Annotated[int | None, Field(alias="QDRANT_TIMEOUT")] = 30
    vector_size: Annotated[int, Field(alias="QDRANT_VECTOR_SIZE")] = 384
    distance: Annotated[str, Field(alias="QDRANT_DISTANCE")] = "Cosine"

    @property
    def is_configured(self) -> bool:
        return bool(
            self.collection
            and (
                self.url
                or self.host
                and self.port
                or self.host
                and self.grpc_port
                and self.prefer_grpc
            )
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_parse_none_str="None",
        extra="ignore",
    )
    
    
stub_settings = StubSettings()
minio_settings = MinIOSettings()
qdrant_settings = QdrantSettings()


class LazyAdapter:
    def __init__(self, factory: Callable[[], Any]):
        self._factory: Callable[[], Any] = factory
        self._instance: Any = None
        self._lock = threading.Lock()

    def get_instance(self):
        if self._instance is None:
            with self._lock:
                if self._instance is None:
                    self._instance = self._factory()
        return self._instance


if minio_settings.is_configured:
    raw_storage_adapter = LazyAdapter(
        partial(
            MinIORawStorage,
            endpoint=minio_settings.endpoint,
            bucket_name=minio_settings.bucket_raw,
            access_key=minio_settings.access_key,
            secret_key=minio_settings.secret_key,
            session_token=minio_settings.session_token,
            secure=minio_settings.secure,
            region=minio_settings.region,
        ),
    )
    silver_storage_adapter = LazyAdapter(
        partial(
            MinIORawStorage,
            endpoint=minio_settings.endpoint,
            bucket_name=minio_settings.bucket_silver,
            access_key=minio_settings.access_key,
            secret_key=minio_settings.secret_key,
            session_token=minio_settings.session_token,
            secure=minio_settings.secure,
            region=minio_settings.region,
        ),
    )
else:
    raw_storage_adapter = LazyAdapter(
        partial(
            FileRawStorage,
            directory=stub_settings.raw_storage_path,
        ),
    )
    silver_storage_adapter = LazyAdapter(
        partial(
            FileRawStorage,
            directory=stub_settings.silver_storage_path,
        ),
    )
    
if qdrant_settings.is_configured:
    vector_store_adapter = LazyAdapter(
        partial(
            QdrantVectorStore,
            url=qdrant_settings.url,
            collection_name=qdrant_settings.collection,
            host=qdrant_settings.host,
            port=qdrant_settings.port,
            grpc_port=qdrant_settings.grpc_port,
            api_key=qdrant_settings.api_key,
            https=qdrant_settings.use_https,
            prefer_grpc=qdrant_settings.prefer_grpc,
            timeout=qdrant_settings.timeout,
            vector_size=qdrant_settings.vector_size,
            distance=qdrant_settings.distance,
        ),
    )
else:
    vector_store_adapter = LazyAdapter(
        partial(
            JSONVectorStore,
            directory=stub_settings.index_path,
        ),
    )
