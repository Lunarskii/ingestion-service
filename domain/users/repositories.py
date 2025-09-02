from domain.database.repositories import AlchemyRepository
from domain.users.models import (
    PermissionDAO,
    RoleDAO,
    RolePermissionDAO,
    UserDAO,
    UserRoleDAO,
    UserPermissionDAO,
)
from domain.users.schemas import (
    PermissionDTO,
    RoleDTO,
    RolePermissionDTO,
    UserDTO,
    UserRoleDTO,
    UserPermissionDTO,
)


class PermissionRepository(AlchemyRepository[PermissionDAO, PermissionDTO]):
    ...


class RoleRepository(AlchemyRepository[RoleDAO, RoleDTO]):
    ...


class RolePermissionRepository(AlchemyRepository[RolePermissionDAO, RolePermissionDTO]):
    ...


class UserRepository(AlchemyRepository[UserDAO, UserDTO]):
    ...


class UserRoleRepository(AlchemyRepository[UserRoleDAO, UserRoleDTO]):
    ...


class UserPermissionRepository(AlchemyRepository[UserPermissionDAO, UserPermissionDTO]):
    ...
