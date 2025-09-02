from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from domain.users.repositories import (
    PermissionRepository,
    RoleRepository,
    RolePermissionRepository,
    UserRepository,
    UserRoleRepository,
    UserPermissionRepository,
)
from domain.database.dependencies import scoped_session_dependency
from domain.database.uow import (
    UnitOfWork,
    UnitOfWorkFactory,
)


async def user_uow_dependency(
    session: Annotated[AsyncSession, Depends(scoped_session_dependency)],
) -> UnitOfWork:
    """
    Возвращает UnitOfWork с предзарегистрированными репозиториями:
        * ``PermissionRepository``
        * ``RoleRepository``
        * ``RolePermissionRepository``
        * ``UserRepository``
        * ``UserRoleRepository``
        * ``UserPermissionRepository``
    """

    async with UnitOfWorkFactory.get_uow(
        session,
        PermissionRepository,
        RoleRepository,
        RolePermissionRepository,
        UserRepository,
        UserRoleRepository,
        UserPermissionRepository,
    ) as uow:
        yield uow
