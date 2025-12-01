from pathlib import Path
import os

import pytest
from testcontainers.postgres import PostgresContainer
from testcontainers.kafka import KafkaContainer
from testcontainers.qdrant import QdrantContainer
from testcontainers.minio import MinioContainer
from testcontainers.redis import RedisContainer
from alembic.config import Config as AlembicConfig
from alembic import command as alembic_command

from app.infrastructure.storage_minio import MinIORawStorage
from app.infrastructure.vectorstore_qdrant import QdrantVectorStorage


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI_PATH = PROJECT_ROOT / "alembic.ini"
ALEMBIC_SCRIPT_LOCATION = str(PROJECT_ROOT / "alembic")


def run_alembic_migrations(sqlalchemy_url: str) -> None:
    cfg = AlembicConfig(str(ALEMBIC_INI_PATH))
    cfg.set_main_option("script_location", ALEMBIC_SCRIPT_LOCATION)
    cfg.set_main_option("sqlalchemy.url", sqlalchemy_url)
    alembic_command.upgrade(cfg, "head")


_pg_container: PostgresContainer | None = None
_minio_container: MinioContainer | None = None
_qdrant_container: QdrantContainer | None = None
_kafka_container: KafkaContainer | None = None


def pytest_configure(config):
    global _pg_container
    _pg_container = PostgresContainer("postgres:18")
    _pg_container.start()
    url: str = _pg_container.get_connection_url()
    url = url.replace("psycopg2", "asyncpg", 1)
    url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    os.environ["DATABASE_URL"] = url
    run_alembic_migrations(url)

    global _minio_container
    _minio_container = MinioContainer("minio/minio:RELEASE.2025-07-23T15-54-02Z")
    _minio_container.start()
    host: str = _minio_container.get_container_host_ip()
    port: int = _minio_container.get_exposed_port(9000)
    os.environ["MINIO_ENDPOINT"] = f"{host}:{port}"
    os.environ["MINIO_ACCESS_KEY"] = "minioadmin"
    os.environ["MINIO_SECRET_KEY"] = "minioadmin"

    global _qdrant_container
    _qdrant_container = QdrantContainer("qdrant/qdrant:v1.15")
    _qdrant_container.start()
    host: str = _qdrant_container.get_container_host_ip()
    port: int = _qdrant_container.get_exposed_port(6333)
    os.environ["QDRANT_URL"] = f"http://{host}:{port}"

    global _kafka_container
    _kafka_container = KafkaContainer()
    _kafka_container.start()
    bootstrap: str = _kafka_container.get_bootstrap_server()
    os.environ["KAFKA_BROKER"] = bootstrap


def pytest_unconfigure(config):
    global _pg_container
    if _pg_container:
        _pg_container.stop()

    global _minio_container
    if _minio_container:
        _minio_container.stop()

    global _qdrant_container
    if _qdrant_container:
        _qdrant_container.stop()

    global _kafka_container
    if _kafka_container:
        _kafka_container.stop()


@pytest.fixture
def minio() -> MinIORawStorage:
    from app.core import settings

    return MinIORawStorage(
        endpoint=settings.minio.endpoint,
        bucket_name="test-bucket",
        access_key=settings.minio.access_key,
        secret_key=settings.minio.secret_key,
        session_token=settings.minio.session_token,
        secure=settings.minio.secure,
        region=settings.minio.region,
    )


@pytest.fixture
def qdrant():
    from app.core import settings

    return QdrantVectorStorage(
        url=settings.qdrant.url,
        collection_name="test-collection",
        grpc_port=settings.qdrant.grpc_port,
        api_key=settings.qdrant.api_key,
        https=settings.qdrant.use_https,
        prefer_grpc=settings.qdrant.prefer_grpc,
        timeout=settings.qdrant.timeout,
        vector_size=settings.qdrant.vector_size,
        distance=settings.qdrant.distance,
    )


@pytest.fixture
def kafka():
    from app.core import settings
    from services.kafka_consumer.worker import KafkaConsumerWorker
    from services.kafka_consumer.consumers.document_events import save_document_meta

    return KafkaConsumerWorker(
        topics={
            settings.kafka.topic_doc_new: save_document_meta,
        },
        bootstrap_servers=settings.kafka.broker,
        group_id=settings.kafka.group_id,
    )


# @pytest.fixture(scope="session")
# def redis_container():
#     with RedisContainer() as container:
#         container.start()
#         host: str = container.get_container_host_ip()
#         port: int = container.get_exposed_port(6379)
#         url: str = f"redis://{host}:{port}"
#
#         os.environ["CELERY_BROKER_URL"] = f"{url}/0"
#         os.environ["CELERY_RESULT_BACKEND"] = f"{url}/1"
#
#         yield url
