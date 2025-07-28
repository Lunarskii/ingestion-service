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


@lru_cache
def get_raw_storage(settings: StorageSettings = storage_settings) -> RawStorage:
    """
    Инициализирует и кэширует реализацию RawStorage.

    Возвращает FileRawStorage (по умолчанию) или любую другую реализацию интерфейса RawStorage, которая будет
    добавлена. В противном случае выбрасывает ValueError.

    :param settings: Настройки хранилищ.
    :type settings: StorageSettings
    :return: Экземпляр реализации интерфейса RawStorage.
    :rtype: RawStorage
    :raises ValueError: Если переменная окружения RAW_STORAGE_PATH не установлена.
    """

    if settings.raw_storage_path:
        return FileRawStorage()
    raise ValueError("Переменная окружения 'RAW_STORAGE_PATH' не установлена или установлена неверно.")


@lru_cache
def get_vector_store(settings: StorageSettings = storage_settings) -> VectorStore:
    """
    Инициализирует и кэширует реализацию VectorStore.

    Возвращает JSONVectorStore (по умолчанию) или любую другую реализацию интерфейса VectorStore, которая будет
    добавлена. В противном случае выбрасывает ValueError.

    :param settings: Настройки хранилищ.
    :type settings: StorageSettings
    :return: Экземпляр реализации интерфейса VectorStore.
    :rtype: VectorStore
    :raises ValueError: Если переменная окружения INDEX_PATH не установлена.
    """

    if settings.index_path:
        return JSONVectorStore()
    raise ValueError("Переменная окружения 'INDEX_PATH' не установлена или установлена неверно.")


@lru_cache
def get_metadata_repository(settings: StorageSettings = storage_settings) -> MetadataRepository:
    """
    Инициализирует и кэширует реализацию MetadataRepository.

    Возвращает SQLiteMetadataRepository (по умолчанию) или любую другую реализацию интерфейса MetadataRepository,
    которая будет добавлена. В противном случае выбрасывает ValueError.

    :param settings: Настройки хранилищ.
    :type settings: StorageSettings
    :return: Экземпляр реализации интерфейса MetadataRepository.
    :rtype: MetadataRepository
    :raises ValueError: Если переменная окружения SQLITE_URL не установлена.
    """

    if settings.sqlite_url:
        return SQLiteMetadataRepository()
    raise ValueError("Переменная окружения 'SQLITE_URL' не установлена или установлена неверно.")


@lru_cache
def get_embedding_model(settings: EmbeddingSettings = embedding_settings) -> SentenceTransformer:
    """
    Инициализирует и кэширует модель SentenceTransformer для создания эмбеддингов.

    :param settings: Настройки модели.
    :type settings: EmbeddingSettings
    :return: Экземпляр SentenceTransformer.
    :rtype: SentenceTransformer
    :raises ValueError: Если переменная окружения EMBEDDING_MODEL_NAME не установлена.
    """

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
    """
    Инициализирует и кэширует текстовый разделитель для разбиения текста на чанки.

    :param settings: Настройки для разделителя текста.
    :type settings: TextSplitterSettings
    :return: Экземпляр RecursiveCharacterTextSplitter.
    :rtype: RecursiveCharacterTextSplitter
    """

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
    """
    Собирает и кэширует DocumentProcessor, инжектируя все зависимости.

    :param raw_storage: Сервис для сохранения исходных файлов.
    :type raw_storage: RawStorage
    :param vector_store: Сервис для хранения векторов.
    :type vector_store: VectorStore
    :param metadata_repository: Сервис для метаданных.
    :type metadata_repository: MetadataRepository
    :param embedding_model: Модель для создания эмбеддингов.
    :type embedding_model: SentenceTransformer
    :param text_splitter: Текстовый разделитель.
    :type text_splitter: RecursiveCharacterTextSplitter
    :return: Экземпляр DocumentProcessor.
    :rtype: DocumentProcessor
    """

    return DocumentProcessor(
        raw_storage=raw_storage,
        vector_store=vector_store,
        metadata_repository=metadata_repository,
        embedding_model=embedding_model,
        text_splitter=text_splitter,
    )
