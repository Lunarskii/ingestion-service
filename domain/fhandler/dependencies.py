from functools import lru_cache

from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter

from domain.fhandler.service import DocumentProcessor
from services import (
    RawStorage,
    VectorStore,
    MetadataRepository,
)
from stubs import (
    FileRawStorage,
    JSONVectorStore,
    SQLiteMetadataRepository,
)
from config import (
    StorageSettings,
    EmbeddingSettings,
    TextSplitterSettings,
    storage_settings,
    embedding_settings,
    text_splitter_settings,
)


# TODO сделать индивидуальные исключения, например config.exc.py, в которых будет ошибка EnvironmentVariableError


@lru_cache
def get_raw_storage(settings: StorageSettings = storage_settings) -> RawStorage:
    if settings.raw_storage_path:
        return FileRawStorage()
    raise ValueError("Переменная окружения 'RAW_STORAGE_PATH' не установлена или установлена неверно.")


@lru_cache
def get_vector_store(settings: StorageSettings = storage_settings) -> VectorStore:
    if settings.index_path:
        return JSONVectorStore()
    raise ValueError("Переменная окружения 'INDEX_PATH' не установлена или установлена неверно.")


@lru_cache
def get_metadata_repository(settings: StorageSettings = storage_settings) -> MetadataRepository:
    if settings.sqlite_url:
        return SQLiteMetadataRepository()
    raise ValueError("Переменная окружения 'SQLITE_URL' не установлена или установлена неверно.")


@lru_cache
def get_embedding_model(settings: EmbeddingSettings = embedding_settings) -> SentenceTransformer:
    if settings.model_name:
        return SentenceTransformer(
            model_name_or_path=settings.model_name,
            device=settings.device,
            cache_folder=settings.cache_folder,
            token=settings.token,
        )
    raise ValueError("Переменная окружения 'EMBEDDING_MODEL_NAME' не установлена или установлена неверно.")


@lru_cache
def get_text_splitter(settings: TextSplitterSettings = text_splitter_settings) -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )


@lru_cache
def get_document_processor(
    raw_storage: RawStorage = get_raw_storage(),
    vector_store: VectorStore = get_vector_store(),
    metadata_repository: MetadataRepository = get_metadata_repository(),
    embedding_model: SentenceTransformer = get_embedding_model(),
    text_splitter: RecursiveCharacterTextSplitter = get_text_splitter(),
) -> DocumentProcessor:
    return DocumentProcessor(
        raw_storage=raw_storage,
        vector_store=vector_store,
        metadata_repository=metadata_repository,
        embedding_model=embedding_model,
        text_splitter=text_splitter,
    )
