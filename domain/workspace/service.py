from domain.workspace.repositories import WorkspaceRepository
from domain.workspace.schemas import WorkspaceDTO
from domain.workspace.exceptions import (
    WorkspaceAlreadyExistsError,
    WorkspaceCreationError,
    WorkspaceRetrievalError,
    WorkspaceDeletionError,
)
from services import (
    RawStorage,
    VectorStore,
    MetadataRepository,
)
from config import logger


class WorkspaceService:
    """
    Сервис для управления рабочими пространствами.
    """

    def __init__(
        self,
        repository: WorkspaceRepository,
    ):
        """
        :param repository: Репозиторий для работы с пространством.
        :type repository: WorkspaceRepository
        """

        self.repository = repository

    async def create(self, name: str) -> WorkspaceDTO:
        """
        Создаёт новое рабочее пространство с заданным именем.

        :param name: Уникальное имя для создаваемого пространства.
        :type name: str
        :return: Созданное пространство в виде DTO.
        :rtype: WorkspaceDTO
        :raises WorkspaceRetrievalError: Если произошла ошибка при проверке существующих пространств.
        :raises WorkspaceAlreadyExistsError: Если пространство с таким именем уже существует.
        :raises WorkspaceCreationError: В случае ошибки при создании пространства.
        """

        context_logger = logger.bind(name=name)

        try:
            workspace = await self.repository.get_by_name(name)
        except Exception as e:
            context_logger.error(
                WorkspaceRetrievalError.message,
                error_message=str(e),
            )
            raise WorkspaceRetrievalError()
        else:
            if workspace:
                raise WorkspaceAlreadyExistsError()

        try:
            context_logger.info("Создание нового пространства")
            workspace = WorkspaceDTO(name=name)
            workspace = await self.repository.create(**workspace.model_raw_dump())
        except Exception as e:
            context_logger.error(
                WorkspaceCreationError.message,
                error_message=str(e),
            )
            raise WorkspaceCreationError()
        else:
            return workspace

    async def delete(
        self,
        workspace_id: str,
        raw_storage: RawStorage,
        vector_store: VectorStore,
        metadata_repository: MetadataRepository,
    ) -> None:
        """
        Удаляет пространство и все связанные с ним данные.

        :param workspace_id: Идентификатор пространства для удаления.
        :type workspace_id: str
        :param raw_storage: Сервис для управления сырыми файлами.
        :type raw_storage: RawStorage
        :param vector_store: Сервис векторного хранилища.
        :type vector_store: VectorStore
        :param metadata_repository: Репозиторий метаданных.
        :type metadata_repository: MetadataRepository
        :raises WorkspaceDeletionError: В случае любой ошибки при удалении.
        """

        context_logger = logger.bind(workspace_id=workspace_id)

        try:
            context_logger.info(
                "Удаление пространства и всех связанных с ним документов, векторов, метаданных и сообщений"
            )
            await self.repository.delete(workspace_id)
            raw_storage.delete(f"{workspace_id}/")
            vector_store.delete(workspace_id)
            metadata_repository.delete(workspace_id=workspace_id)
        except Exception as e:
            context_logger.error(
                WorkspaceDeletionError.message,
                error_message=str(e),
            )
            raise WorkspaceDeletionError()

    async def workspaces(self) -> list[WorkspaceDTO]:
        """
        Возвращает список всех рабочих пространств.

        :return: Список DTO рабочих пространств.
        :rtype: list[WorkspaceDTO]
        :raises WorkspaceRetrievalError: В случае ошибки при получении списка.
        """

        try:
            logger.info("Получение списка пространств")
            workspaces: list[WorkspaceDTO] = await self.repository.get_n()
        except Exception as e:
            error_message: str = "Не удалось получить список пространств"
            logger.error(
                error_message,
                error_message=str(e),
            )
            raise WorkspaceRetrievalError(error_message)
        else:
            return workspaces
