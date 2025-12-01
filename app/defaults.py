from typing import (
    Any,
    Callable,
)
from functools import (
    cached_property,
    partial,
)
import threading

from app.adapters.transformers_embedding_model import TransformersEmbeddingModel
from app.adapters.transformers_reranker import CrossEncoderReranker
from app.adapters.langchain_text_splitter import LangChainTextSplitter
from app.domain.security.service import KeycloakClient
from app.domain.classifier.rules import Classifier
from app.core.config import settings
from app.interfaces import (
    EmbeddingModel,
    FileStorage,
    LLMClient,
    Reranker,
    TextSplitter,
    VectorStorage,
)
from app.core import logger


# TODO move to core


class LazyFactory:
    def __init__(self, factory: Callable[[], Any]):
        self._factory: Callable[[], Any] = factory
        self._instance: Any = None
        self._lock = threading.Lock()

    @property
    def instance(self) -> Any:
        if self._instance is None:
            with self._lock:
                if self._instance is None:
                    self._instance = self._factory()
        return self._instance

    def new_instance(self) -> Any:
        return self._factory()


if settings.minio.is_configured:
    from app.adapters.minio_file_storage import MinIOFileStorage

    logger.info(
        "Выбран адаптер FileStorage: MinIO",
        endpoint=settings.minio.endpoint,
        bucket_raw=settings.minio.bucket_raw,
        bucket_silver=settings.minio.bucket_silver,
        secure=settings.minio.secure,
        region=settings.minio.region,
    )
    _raw_storage_factory = LazyFactory(
        partial(
            MinIOFileStorage,
            endpoint=settings.minio.endpoint,
            bucket_name=settings.minio.bucket_raw,
            access_key=settings.minio.access_key,
            secret_key=settings.minio.secret_key,
            session_token=settings.minio.session_token,
            secure=settings.minio.secure,
            region=settings.minio.region,
        ),
    )
    _silver_storage_factory = LazyFactory(
        partial(
            MinIOFileStorage,
            endpoint=settings.minio.endpoint,
            bucket_name=settings.minio.bucket_silver,
            access_key=settings.minio.access_key,
            secret_key=settings.minio.secret_key,
            session_token=settings.minio.session_token,
            secure=settings.minio.secure,
            region=settings.minio.region,
        ),
    )
else:
    from app.adapters.local_file_storage import LocalFileStorage

    logger.info(
        "Выбран адаптер FileStorage: Локальное хранилище",
        raw_storage_path=settings.stub.raw_storage_path,
        silver_storage_path=settings.stub.silver_storage_path,
    )
    _raw_storage_factory = LazyFactory(
        partial(
            LocalFileStorage,
            directory=settings.stub.raw_storage_path,
        ),
    )
    _silver_storage_factory = LazyFactory(
        partial(
            LocalFileStorage,
            directory=settings.stub.silver_storage_path,
        ),
    )

if settings.qdrant.is_configured:
    from app.adapters.qdrant_vector_storage import QdrantVectorStorage

    logger.info(
        "Выбран адаптер VectorStorage: Qdrant",
        url=settings.qdrant.url,
        collection=settings.qdrant.collection,
        host=settings.qdrant.host,
        port=settings.qdrant.port,
        grpc_port=settings.qdrant.grpc_port,
        https=settings.qdrant.use_https,
        prefer_grpc=settings.qdrant.prefer_grpc,
        timeout=settings.qdrant.timeout,
        vector_size=settings.qdrant.vector_size,
        distance=settings.qdrant.distance,
    )
    _vector_storage_factory = LazyFactory(
        partial(
            QdrantVectorStorage,
            url=settings.qdrant.url,
            collection_name=settings.qdrant.collection,
            host=settings.qdrant.host,
            port=settings.qdrant.port,
            grpc_port=settings.qdrant.grpc_port,
            api_key=settings.qdrant.api_key,
            https=settings.qdrant.use_https,
            prefer_grpc=settings.qdrant.prefer_grpc,
            timeout=settings.qdrant.timeout,
            vector_size=settings.qdrant.vector_size,
            distance=settings.qdrant.distance,
        ),
    )
else:
    from app.adapters.local_vector_storage import LocalVectorStorage

    logger.info(
        "Выбран адаптер VectorStorage: Локальное хранилище",
        vector_store_path=settings.stub.index_path,
    )
    _vector_storage_factory = LazyFactory(
        partial(
            LocalVectorStorage,
            directory=settings.stub.index_path,
        ),
    )

if settings.ollama.is_configured:
    from app.adapters.ollama_llm_client import OllamaClient

    logger.info(
        "Выбран адаптер LLMClient: Ollama",
        url=settings.ollama.url,
        model=settings.ollama.model,
        timeout=settings.ollama.timeout,
    )
    _llm_client_factory = LazyFactory(
        partial(
            OllamaClient,
            url=settings.ollama.url,
            model=settings.ollama.model,
            api_key=settings.ollama.api_key,
            timeout=settings.ollama.timeout,
        ),
    )
elif settings.openai.is_configured:
    from app.adapters.openai_llm_client import OpenAIClient

    logger.info(
        "Выбран адаптер LLMClient: OpenAI",
        url=settings.openai.url,
        websocket_url=settings.openai.websocket_url,
        model=settings.openai.model,
        organization=settings.openai.organization,
        project=settings.openai.project,
        timeout=settings.openai.timeout,
        max_retries=settings.openai.max_retries,
    )
    _llm_client_factory = LazyFactory(
        partial(
            OpenAIClient,
            url=settings.openai.url,
            websocket_url=settings.openai.websocket_url,
            api_key=settings.openai.api_key,
            model=settings.openai.model,
            organization=settings.openai.organization,
            project=settings.openai.project,
            webhook_secret=settings.openai.webhook_secret,
            timeout=settings.openai.timeout,
            max_retries=settings.openai.max_retries,
        ),
    )
else:
    from app.adapters.local_llm_client import LocalLLMClient

    logger.info("Выбран адаптер LLMClient: Локальная заглушка")
    _llm_client_factory = LazyFactory(LocalLLMClient)

_embedding_model_factory = LazyFactory(
    partial(
        TransformersEmbeddingModel,
        model_name_or_path=settings.embedding.model_name,
        device=settings.embedding.device,
        cache_folder=settings.embedding.cache_folder,
        token=settings.embedding.token,
        batch_size=settings.embedding.batch_size,
    ),
)

_reranker_factory = LazyFactory(
    partial(
        CrossEncoderReranker,
        model_name_or_path=settings.reranker.model_name,
        device=settings.reranker.device,
        cache_folder=settings.reranker.cache_folder,
        token=settings.reranker.token,
        batch_size=settings.reranker.batch_size,
    )
)

_text_splitter_factory = LazyFactory(
    partial(
        LangChainTextSplitter,
        chunk_size=settings.text_splitter.chunk_size,
        chunk_overlap=settings.text_splitter.chunk_overlap,
    ),
)

_keycloak_client_factory = LazyFactory(
    partial(
        KeycloakClient,
        url=settings.keycloak.url,
        client_id=settings.keycloak.client_id,
        client_secret=settings.keycloak.client_secret,
        realm=settings.keycloak.realm,
        redirect_uri=settings.keycloak.redirect_uri,
        scope=settings.keycloak.scope,
    ),
)

_classifier_factory = LazyFactory(
    partial(
        Classifier,
        rules_path=settings.classifier.rules_path,
    ),
)


class Defaults:
    @cached_property
    def raw_storage(self) -> FileStorage:
        return _raw_storage_factory.instance

    @cached_property
    def silver_storage(self) -> FileStorage:
        return _silver_storage_factory.instance

    @cached_property
    def vector_storage(self) -> VectorStorage:
        return _vector_storage_factory.instance

    @cached_property
    def llm_client(self) -> LLMClient:
        return _llm_client_factory.instance

    @cached_property
    def embedding_model(self) -> EmbeddingModel:
        return _embedding_model_factory.instance

    @cached_property
    def reranker(self) -> Reranker:
        return _reranker_factory.instance

    @cached_property
    def text_splitter(self) -> TextSplitter:
        return _text_splitter_factory.instance

    @cached_property
    def keycloak_client(self) -> KeycloakClient:
        return _keycloak_client_factory.instance

    @cached_property
    def classifier(self) -> Classifier:
        return _classifier_factory.instance


defaults = Defaults()
