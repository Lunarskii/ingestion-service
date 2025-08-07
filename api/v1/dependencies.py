from typing import Annotated

from fastapi import (
    Depends,
    UploadFile,
    Request,
)
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import TextSplitter
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.exc import (
    UnsupportedFileTypeError,
    FileTooLargeError,
)
from domain.fhandler.utils import get_file_extension
from domain.fhandler.service import DocumentProcessor
from domain.fhandler.schemas import File
from domain.chat.service import ChatService
from domain.chat.repositories import (
    ChatSessionRepository,
    ChatMessageRepository,
)
from domain.workspace.service import WorkspaceService
from domain.workspace.repositories import WorkspaceRepository
from domain.database.dependencies import scoped_session_dependency
from services import (
    RawStorage,
    VectorStore,
    MetadataRepository,
)
from config import (
    Settings,
    settings as _settings,
)


async def validate_upload_file(
    file: UploadFile,
    settings: Annotated[Settings, Depends(lambda: _settings)],
) -> File:
    """
    Валидирует загружаемый файл по расширению и размеру.

    :param file: Загружаемый файл из запроса multipart/form-data.
    :type file: UploadFile
    :param settings: Ограничения на типы и максимальный размер файла.
    :type settings: DocumentRestrictionSettings
    :return: Полные байты файла и метаданные файла.
    :rtype: File
    :raises UnsupportedFileTypeError: Если расширение файла не входит в разрешенный список.
    :raises FileTooLargeError: Если размер файла превышает максимально допустимый.
    """

    ext: str = get_file_extension(await file.read(8192))
    if ext not in settings.document_restriction.allowed_extensions:
        raise UnsupportedFileTypeError(
            f"Неподдерживаемый формат {ext!r}. Поддерживаются: {settings.document_restriction.allowed_extensions}"
        )
    await file.seek(0)

    if file.size > (settings.document_restriction.max_upload_mb * 1024 * 1024):
        raise FileTooLargeError(
            f"Размер файла превышает максимально допустимый размер {settings.document_restriction.max_upload_mb}MB"
        )

    return File(
        content=await file.read(),
        name=file.filename,
        size=file.size,
        extension=ext,
        headers=file.headers,
    )


async def raw_storage_dependency(request: Request) -> RawStorage:
    return request.app.state.raw_storage


async def vector_store_dependency(request: Request) -> VectorStore:
    return request.app.state.vector_store


async def metadata_repository_dependency(request: Request) -> MetadataRepository:
    return request.app.state.metadata_repository


async def embedding_model_dependency(request: Request) -> SentenceTransformer:
    return request.app.state.embedding_model


async def text_splitter_dependency(request: Request) -> TextSplitter:
    return request.app.state.text_splitter


async def document_processor_dependency(
    raw_storage: Annotated[RawStorage, Depends(raw_storage_dependency)],
    vector_store: Annotated[VectorStore, Depends(vector_store_dependency)],
    metadata_repository: Annotated[MetadataRepository, Depends(metadata_repository_dependency)],
    embedding_model: Annotated[SentenceTransformer, Depends(embedding_model_dependency)],
    text_splitter: Annotated[TextSplitter, Depends(text_splitter_dependency)],
) -> DocumentProcessor:
    return DocumentProcessor(
        raw_storage=raw_storage,
        vector_store=vector_store,
        metadata_repository=metadata_repository,
        embedding_model=embedding_model,
        text_splitter=text_splitter,
    )


async def chat_session_repository_dependency(
    session: Annotated[AsyncSession, Depends(scoped_session_dependency)],
) -> ChatSessionRepository:
    return ChatSessionRepository(session)


async def chat_message_repository_dependency(
    session: Annotated[AsyncSession, Depends(scoped_session_dependency)],
) -> ChatMessageRepository:
    return ChatMessageRepository(session)


async def chat_service_dependency(
    vector_store: Annotated[VectorStore, Depends(vector_store_dependency)],
    embedding_model: Annotated[SentenceTransformer, Depends(embedding_model_dependency)],
    chat_session_repository: Annotated[ChatSessionRepository, Depends(chat_session_repository_dependency)],
    chat_message_repository: Annotated[ChatMessageRepository, Depends(chat_message_repository_dependency)],
) -> ChatService:
    return ChatService(
        vector_store=vector_store,
        embedding_model=embedding_model,
        chat_session_repository=chat_session_repository,
        chat_message_repository=chat_message_repository,
    )


async def workspace_repository_dependency(
    session: Annotated[AsyncSession, Depends(scoped_session_dependency)],
) -> WorkspaceRepository:
    return WorkspaceRepository(session)


async def workspace_service_dependency(
    workspace_repository: Annotated[WorkspaceRepository, Depends(workspace_repository_dependency)],
) -> WorkspaceService:
    return WorkspaceService(
        workspace_repository=workspace_repository,
    )
