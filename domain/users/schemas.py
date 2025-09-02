from typing import Annotated

from pydantic import Field

from schemas.base import (
    BaseSchema,
    BaseDTO,
)
from schemas.mixins import (
    IDMixin,
    UUIDMixin,
)


class CreateUserRequest(BaseSchema):
    username: str
    password: str


class UpdateUserRequest(BaseSchema):
    username: str | None = None
    password: str | None = None
    active: bool | None = None


# user response
class User(BaseSchema):
    id: Annotated[
        str,
        Field(serialization_alias="user_id"),
    ]
    username: str
    active: bool


class PermissionDTO(BaseDTO, IDMixin):
    name: str
    description: str


class RoleDTO(BaseDTO, IDMixin):
    name: str
    description: str


class RolePermissionDTO(BaseDTO):
    role_id: int
    permission_id: int


class UserDTO(BaseDTO, UUIDMixin):
    username: str
    password: Annotated[bytes, Field(strict=True)]
    active: bool


class UserRoleDTO(BaseDTO):
    user_id: str
    role_id: int


class UserPermissionDTO(BaseDTO):
    user_id: str
    permission_id: int
