from stubs import (
    FileRawStorage,
    JSONVectorStore,
    SQLiteMetadataRepository,
)


async def raw_storage_dependency():
    return FileRawStorage()


async def vector_store_dependency():
    return JSONVectorStore()


async def metadata_repository_dependency():
    return SQLiteMetadataRepository()
