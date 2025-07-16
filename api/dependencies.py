from typing import Annotated

from fastapi import Depends

from services.interfaces import (
    RawStorage,
    VectorStore,
    MetadataRepository,
)
from stubs import (
    FileRawStorage,
    JSONVectorStore,
    SQLiteMetadataRepository,
)
from domain.process import DocumentProcessor
from config import storage_settings


def raw_storage_dependency() -> RawStorage:
    if storage_settings.raw_storage_path:
        return FileRawStorage()
    raise ValueError("Переменная окружения 'RAW_STORAGE_PATH' не установлена или установлена неверно.")


def vector_store_dependency() -> VectorStore:
    if storage_settings.index_path:
        return JSONVectorStore()
    raise ValueError("Переменная окружения 'INDEX_PATH' не установлена или установлена неверно.")


def metadata_repository_dependency() -> MetadataRepository:
    if storage_settings.sqlite_url:
        return SQLiteMetadataRepository()
    raise ValueError("Переменная окружения 'SQLITE_URL' не установлена или установлена неверно.")


def document_processor_dependency(
    raw_storage: Annotated[RawStorage, Depends(raw_storage_dependency)],
    vector_store: Annotated[VectorStore, Depends(vector_store_dependency)],
    metadata_repository: Annotated[
        MetadataRepository, Depends(metadata_repository_dependency)
    ],
):
    return DocumentProcessor(raw_storage, vector_store, metadata_repository)
