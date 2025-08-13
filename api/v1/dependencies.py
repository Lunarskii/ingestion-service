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
from domain.document.utils import get_file_extension
from domain.document.service import DocumentService
from domain.document.schemas import File
from domain.chat.service import (
    ChatSessionService,
    ChatMessageService,
    RAGService,
)
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
    """
    Возвращает настроенное хранилище сырых файлов из состояния приложения.
    """

    return request.app.state.raw_storage


async def vector_store_dependency(request: Request) -> VectorStore:
    """
    Возвращает настроенное векторное хранилище из состояния приложения.
    """

    return request.app.state.vector_store


async def metadata_repository_dependency(request: Request) -> MetadataRepository:
    """
    Возвращает настроенный репозиторий метаданных из состояния приложения.
    """

    return request.app.state.metadata_repository


async def embedding_model_dependency(request: Request) -> SentenceTransformer:
    """
    Возвращает настроенную модель эмбеддингов из состояния приложения.
    """

    return request.app.state.embedding_model


async def text_splitter_dependency(request: Request) -> TextSplitter:
    """
    Возвращает настроенный текстовый разделитель из состояния приложения.
    """

    return request.app.state.text_splitter


async def document_service_dependency(
    raw_storage: Annotated[RawStorage, Depends(raw_storage_dependency)],
    vector_store: Annotated[VectorStore, Depends(vector_store_dependency)],
    metadata_repository: Annotated[
        MetadataRepository, Depends(metadata_repository_dependency)
    ],
    embedding_model: Annotated[
        SentenceTransformer, Depends(embedding_model_dependency)
    ],
    text_splitter: Annotated[TextSplitter, Depends(text_splitter_dependency)],
) -> DocumentService:
    """
    Создаёт и возвращает экземпляр сервиса :class:`DocumentService`.
    """

    return DocumentService(
        raw_storage=raw_storage,
        vector_store=vector_store,
        metadata_repository=metadata_repository,
        embedding_model=embedding_model,
        text_splitter=text_splitter,
    )


async def chat_session_repository_dependency(
    session: Annotated[AsyncSession, Depends(scoped_session_dependency)],
) -> ChatSessionRepository:
    """
    Возвращает репозиторий ``ChatSessionRepository``, привязанный к текущей сессии ДБ.
    """

    return ChatSessionRepository(session)


async def chat_session_service_dependency(
    repository: Annotated[
        ChatSessionRepository,
        Depends(chat_session_repository_dependency),
    ],
) -> ChatSessionService:
    """
    Возвращает сервис управления чат-сессиями :class:`ChatSessionService`.
    """

    return ChatSessionService(repository=repository)


async def chat_message_repository_dependency(
    session: Annotated[AsyncSession, Depends(scoped_session_dependency)],
) -> ChatMessageRepository:
    """
    Возвращает репозиторий ``ChatMessageRepository``, привязанный к текущей сессии ДБ.
    """

    return ChatMessageRepository(session)


async def chat_message_service_dependency(
    repository: Annotated[
        ChatMessageRepository,
        Depends(chat_message_repository_dependency),
    ],
) -> ChatMessageService:
    """
    Возвращает сервис управления сообщениями чата :class:`ChatMessageService`.
    """

    return ChatMessageService(repository=repository)


async def rag_service_dependency(
    vector_store: Annotated[VectorStore, Depends(vector_store_dependency)],
    embedding_model: Annotated[
        SentenceTransformer, Depends(embedding_model_dependency)
    ],
    chat_session_service: Annotated[
        ChatSessionService, Depends(chat_session_service_dependency)
    ],
    chat_message_service: Annotated[
        ChatMessageService, Depends(chat_message_service_dependency)
    ],
) -> RAGService:
    """
    Создаёт и возвращает экземпляр сервиса :class:`RAGService`.
    """

    return RAGService(
        vector_store=vector_store,
        embedding_model=embedding_model,
        session_service=chat_session_service,
        message_service=chat_message_service,
    )


async def workspace_repository_dependency(
    session: Annotated[AsyncSession, Depends(scoped_session_dependency)],
) -> WorkspaceRepository:
    """
    Возвращает репозиторий ``WorkspaceRepository``, привязанный к текущей сессии ДБ.
    """

    return WorkspaceRepository(session)


async def workspace_service_dependency(
    repository: Annotated[
        WorkspaceRepository, Depends(workspace_repository_dependency)
    ],
) -> WorkspaceService:
    """
    Создаёт и возвращает экземпляр сервиса :class:`WorkspaceService`.
    """

    return WorkspaceService(
        repository=repository,
    )
