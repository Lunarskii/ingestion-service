from typing import (
    Callable,
    AsyncContextManager,
)
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.document.schemas import (
    File,
    DocumentStage,
    DocumentStatus,
    Document,
    DocumentDTO,
    DocumentEventDTO,
)
from app.domain.document.repositories import (
    DocumentRepository,
    DocumentEventRepository,
)
from app.domain.document.exceptions import (
    DocumentNotFoundError,
    ValidationError,
    DuplicateDocumentError,
)
from app.domain.document.validators import (
    ChainValidator,
    ExtensionValidator,
    SizeValidator,
)
from app.domain.database.dependencies import async_scoped_session_ctx
from app.domain.database.exceptions import EntityNotFoundError
from app.interfaces import FileStorage
from app.defaults import defaults
from app.core import (
    settings,
    logger,
)


class DocumentService:
    def __init__(self):
        self.validator = ChainValidator(
            (
                ExtensionValidator(allowed_extensions=settings.document_restriction.allowed_extensions),
                SizeValidator(max_size_bytes=settings.document_restriction.max_upload_mb * 1024 * 1024),
            ),
        )

    async def get_documents(
        self,
        workspace_id: str,
        *,
        session_ctx: Callable[[], AsyncContextManager["AsyncSession"]] = async_scoped_session_ctx,
    ) -> list[Document]:
        """
        Возвращает список документов в заданном рабочем пространстве.

        :param workspace_id: Идентификатор рабочего пространства.
        :param session_ctx: Асинхронный контекстный менеджер, возвращающий сессию AsyncSession.
                            Функция не коммитит изменения, поэтому ваш асинхронный контекстный
                            менеджер должен содержать commit() и rollback() обработку, если
                            требуется.
        """

        async with session_ctx() as session:
            repo = DocumentRepository(session)
            documents: list[DocumentDTO] = await repo.get_n(workspace_id=workspace_id)
        return [Document.from_dto(document) for document in documents]

    async def get_document_file(
        self,
        document_id: str,
        *,
        raw_storage: FileStorage = defaults.raw_storage,
        session_ctx: Callable[[], AsyncContextManager["AsyncSession"]] = async_scoped_session_ctx,
    ) -> File:
        """
        Возвращает файл (байты документа + название документа) по идентификатору документа.

        :param document_id: Идентификатор документа.
        :param raw_storage: Сырое хранилище, откуда будет извлечен файл.
        :param session_ctx: Асинхронный контекстный менеджер, возвращающий сессию AsyncSession.
                            Функция не коммитит изменения, поэтому ваш асинхронный контекстный
                            менеджер должен содержать commit() и rollback() обработку, если
                            требуется.
        """

        try:
            async with session_ctx() as session:
                repo = DocumentRepository(session)
                document: DocumentDTO = await repo.get(document_id)
        except EntityNotFoundError:
            raise DocumentNotFoundError()

        document_bytes: bytes = raw_storage.get(document.raw_storage_path)
        return File(
            content=document_bytes,
            name=document.title,
        )

    async def save_document_metadata(
        self,
        document: DocumentDTO,
        *,
        session_ctx: Callable[[], AsyncContextManager["AsyncSession"]] = async_scoped_session_ctx,
    ) -> Document:
        """
        Сохраняет метаданные документа в базу данных для последующего ожидания обработки.

        :param document: Метаданные документа.
        :param session_ctx: Асинхронный контекстный менеджер, возвращающий сессию AsyncSession.
                            Функция не коммитит изменения, поэтому ваш асинхронный контекстный
                            менеджер должен содержать commit() и rollback() обработку, если
                            требуется.
        """

        _logger = logger.bind(
            document_id=document.id,
            workspace_id=document.workspace_id,
            trace_id=document.trace_id,
        )

        async with session_ctx() as session:
            repo = DocumentRepository(session)

            _logger.info("Проверка документа на дубликат")
            if await repo.get_n(
                workspace_id=document.workspace_id,
                sha256=document.sha256,
            ):
                _logger.info("Документ является дубликатом, пропуск")
                raise DuplicateDocumentError()

            _logger.info("Сохранение документа в базу данных")
            document = await repo.create(**document.model_dump())
        return Document.from_dto(document)

    async def save_document(
        self,
        file: File,
        workspace_id: str,
        *,
        document_id: str | None = None,
        trace_id: str | None = None,
        raw_storage: FileStorage = defaults.raw_storage,
    ) -> Document:
        """
        Сохраняет исходный документ в RawStorage (Сырое хранилище документов).

        :param file: Схема файла, содержащая его байты и метаданные.
        :param workspace_id: Идентификатор рабочего пространства.
        :param document_id: Идентификатор документа.
        :param trace_id: Корреляционный идентификатор запроса/задачи.
        :param raw_storage: Сырое хранилище, куда будет сохранен документ.

        :return: Метаданные документа.
        """

        if not document_id:
            document_id = str(uuid4())
        if not trace_id:
            trace_id = str(uuid4())

        _logger = logger.bind(
            document_id=document_id,
            workspace_id=workspace_id,
            trace_id=trace_id,
        )

        _logger.info("Проверка на тип и размер документа")
        try:
            self.validator(file.content)
        except ValidationError as e:
            _logger.error(
                "Документ не прошел проверку на тип и размер файла",
                error_message=str(e),
            )
            raise

        document = DocumentDTO(
            id=document_id,
            workspace_id=workspace_id,
            source_id="manual:upload",
            trace_id=trace_id,
            sha256=file.sha256,
            title=file.name,
            media_type=file.type,
            raw_storage_path=f"{workspace_id}/{document_id}{file.extension}",
            size_bytes=file.size,
            status=DocumentStatus.pending,
        )

        try:
            _logger.info(
                "Сохранение исходного документа",
                raw_storage_path=document.raw_storage_path,
            )
            raw_storage.save(file.content, document.raw_storage_path)
        except Exception as e:
            error_message: str = str(e)
            _logger.error(
                "Не удалось сохранить документ",
                error_message=error_message,
            )
            document.status = DocumentStatus.failed
            document.error_message = error_message

        try:
            return await self.save_document_metadata(document)
        except Exception:
            raw_storage.delete(document.raw_storage_path)
            raise


class DocumentProcessor:
    @classmethod
    async def update_document(cls, document_id: str, **kwargs) -> DocumentDTO:
        async with async_scoped_session_ctx() as session:
            document_repo = DocumentRepository(session)
            return await document_repo.update(document_id, **kwargs)

    @classmethod
    async def update_document_status(
        cls,
        document_id: str,
        status: DocumentStatus,
    ) -> DocumentDTO:
        """
        Обновляет статус документа в БД.

        :param document_id: Идентификатор документа.
        :param status: Статус документа.
        """

        return await cls.update_document(document_id, status=status)

    @classmethod
    async def get_pending_documents_ids(cls) -> list[str]:
        """
        Возвращает список идентификаторов документов, ожидающих добавления в очередь на обработку.
        """

        async with async_scoped_session_ctx() as session:
            document_repo = DocumentRepository(session)
            return await document_repo.get_pending_documents_ids()
