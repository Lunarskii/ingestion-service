from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    status,
)

from api.v1.users.dependencies import user_service_dependency
from domain.users.dependencies import user_uow_dependency
from domain.users.service import UserService
from domain.users.schemas import (
    CreateUserRequest,
    UpdateUserRequest,
    User,
    UserDTO,
)
from domain.users.repositories import UserRepository
from domain.database.uow import UnitOfWork


router = APIRouter(prefix="/users")


@router.post("", status_code=status.HTTP_201_CREATED)
async def signup(
    user: CreateUserRequest,
    service: Annotated[UserService, Depends(user_service_dependency)],
    uow: Annotated[UnitOfWork, Depends(user_uow_dependency)],
) -> User:
    user: UserDTO = await service.signup(
        user=user,
        uow=uow,
    )
    return User(
        id=user.id,
        username=user.username,
        active=user.active,
    )


@router.get("", status_code=status.HTTP_200_OK)
async def list_users(
    uow: Annotated[UnitOfWork, Depends(user_uow_dependency)],
) -> list[User]:
    user_repo = uow.get_repository(UserRepository)
    users: list[UserDTO] = await user_repo.get_n()
    return [
        User(
            id=user.id,
            username=user.username,
            active=user.active,
        )
        for user in users
    ]


@router.get("/{user_id}", status_code=status.HTTP_200_OK)
async def get_user(
    user_id: str,
    uow: Annotated[UnitOfWork, Depends(user_uow_dependency)],
) -> User:
    user_repo = uow.get_repository(UserRepository)
    user = await user_repo.get(user_id)
    return User(
        id=user.id,
        username=user.username,
        active=user.active,
    )


@router.get("/me")
async def me() -> User:
    ...


@router.patch("/{user_id}", status_code=status.HTTP_200_OK)
async def update_user(
    user_id: str,
    user: UpdateUserRequest,
    service: Annotated[UserService, Depends(user_service_dependency)],
    uow: Annotated[UnitOfWork, Depends(user_uow_dependency)],
) -> User:
    user: UserDTO = await service.update_user(
        user_id=user_id,
        user=user,
        uow=uow,
    )
    return User(
        id=user.id,
        username=user.username,
        active=user.active,
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    uow: Annotated[UnitOfWork, Depends(user_uow_dependency)],
) -> None:
    user_repo = uow.get_repository(UserRepository)
    await user_repo.delete(user_id)


@router.post("/{user_id}", status_code=status.HTTP_200_OK)
async def deactivate_user(
    user_id: str,
    service: Annotated[UserService, Depends(user_service_dependency)],
    uow: Annotated[UnitOfWork, Depends(user_uow_dependency)],
) -> User:
    user: UserDTO = await service.update_user(
        user_id=user_id,
        user=UpdateUserRequest(active=False),
        uow=uow,
    )
    return User(
        id=user.id,
        username=user.username,
        active=user.active,
    )
