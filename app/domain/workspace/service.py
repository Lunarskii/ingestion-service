from typing import (
    Callable,
    AsyncContextManager,
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.workspace.repositories import WorkspaceRepository
from app.domain.workspace.schemas import (
    Workspace,
    WorkspaceDTO,
)
from app.domain.database.dependencies import async_scoped_session_ctx
from app.interfaces import (
    FileStorage,
    VectorStorage,
)
from app.defaults import defaults


class WorkspaceService:
    async def get_workspaces(
        self,
        *,
        session_ctx: Callable[[], AsyncContextManager["AsyncSession"]] = async_scoped_session_ctx,
    ) -> list[Workspace]:
        """
        Возвращает список всех рабочих пространств.

        :param session_ctx: Асинхронный контекстный менеджер, возвращающий сессию AsyncSession.
                            Функция не коммитит изменения, поэтому ваш асинхронный контекстный
                            менеджер должен содержать commit() и rollback() обработку, если
                            требуется.
        """

        async with session_ctx() as session:
            repo = WorkspaceRepository(session)
            workspaces: list[WorkspaceDTO] = await repo.get_n()
        return [Workspace.from_dto(workspace) for workspace in workspaces]

    async def create_workspace(
        self,
        name: str,
        *,
        session_ctx: Callable[[], AsyncContextManager["AsyncSession"]] = async_scoped_session_ctx,
    ) -> Workspace:
        """
        Создаёт новое рабочее пространство с заданным именем.

        :param name: Имя рабочего пространства.
        :param session_ctx: Асинхронный контекстный менеджер, возвращающий сессию AsyncSession.
                            Функция не коммитит изменения, поэтому ваш асинхронный контекстный
                            менеджер должен содержать commit() и rollback() обработку, если
                            требуется.
        """

        async with session_ctx() as session:
            repo = WorkspaceRepository(session)
            workspace: WorkspaceDTO = await repo.create(name=name)
        return Workspace.from_dto(workspace)

    async def delete_workspace(
        self,
        workspace_id: str,
        *,
        raw_storage: FileStorage = defaults.raw_storage,
        silver_storage: FileStorage = defaults.silver_storage,
        vector_storage: VectorStorage = defaults.vector_storage,
        session_ctx: Callable[[], AsyncContextManager["AsyncSession"]] = async_scoped_session_ctx,
    ) -> None:
        """
        Удаляет рабочее пространство и все связанные с ним данные.

        :param workspace_id: Идентификатор рабочего пространства.
        :param raw_storage: Хранилище сырых документов.
        :param silver_storage: Хранилище обработанных документов.
        :param vector_storage: Векторное хранилище.
        :param session_ctx: Асинхронный контекстный менеджер, возвращающий сессию AsyncSession.
                            Функция не коммитит изменения, поэтому ваш асинхронный контекстный
                            менеджер должен содержать commit() и rollback() обработку, если
                            требуется.
        """

        async with session_ctx() as session:
            repo = WorkspaceRepository(session)
            await repo.delete(workspace_id)
        raw_storage.delete_dir(workspace_id)
        silver_storage.delete_dir(workspace_id)
        vector_storage.delete_by_workspace(workspace_id)
