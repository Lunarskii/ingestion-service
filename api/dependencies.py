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


def raw_storage_dependency() -> RawStorage:
    return FileRawStorage()


def vector_store_dependency() -> VectorStore:
    return JSONVectorStore()


def metadata_repository_dependency() -> MetadataRepository:
    return SQLiteMetadataRepository()


def document_processor_dependency(
    raw_storage: Annotated[RawStorage, Depends(raw_storage_dependency)],
    vector_store: Annotated[VectorStore, Depends(vector_store_dependency)],
    metadata_repository: Annotated[
        MetadataRepository, Depends(metadata_repository_dependency)
    ],
):
    return DocumentProcessor(raw_storage, vector_store, metadata_repository)
