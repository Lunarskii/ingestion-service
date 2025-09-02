from uuid import UUID

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
import sqlalchemy as sa


from domain.database.models import BaseDAO
from domain.database.mixins import (
    IDMixin,
    UUIDMixin,
)


class PermissionDAO(BaseDAO, IDMixin):
    __tablename__ = "permissions"

    name: Mapped[str] = mapped_column(unique=True)
    description: Mapped[str] = mapped_column(nullable=True)


class RoleDAO(BaseDAO, IDMixin):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(unique=True)
    description: Mapped[str] = mapped_column(nullable=True)


class RolePermissionDAO(BaseDAO):
    __tablename__ = "roles_permissions"

    role_id: Mapped[int] = mapped_column(
        sa.ForeignKey("role.id", ondelete="CASCADE"),
        primary_key=True,
    )
    permission_id: Mapped[int] = mapped_column(
        sa.ForeignKey("permission.id", ondelete="CASCADE"),
        primary_key=True,
    )


class UserDAO(BaseDAO, UUIDMixin):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[bytes]
    active: Mapped[bool] = mapped_column(
        default=True,
        server_default="True",
    )

    roles: Mapped["UserRoleDAO"] = relationship(back_populates="user")
    permissions: Mapped["UserPermissionDAO"] = relationship(back_populates="user")


class UserRoleDAO(BaseDAO):
    __tablename__ = "users_roles"

    user_id: Mapped[UUID] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user: Mapped["UserDAO"] = relationship(back_populates="roles")

    role_id: Mapped[int] = mapped_column(
        sa.ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    )


class UserPermissionDAO(BaseDAO):
    __tablename__ = "users_permissions"

    user_id: Mapped[UUID] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user: Mapped["UserDAO"] = relationship(back_populates="permissions")

    permission_id: Mapped[int] = mapped_column(
        sa.ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    allowed: Mapped[bool] = mapped_column(
        default=True,
        server_default="True",
    )
