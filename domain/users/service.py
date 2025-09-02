from domain.users.schemas import (
    CreateUserRequest,
    UpdateUserRequest,
    UserDTO,
)
from domain.users.repositories import UserRepository
from domain.security.utils import hash_password
from domain.database.uow import UnitOfWork


class UserService:
    async def signup(self,
        user: CreateUserRequest,
        uow: UnitOfWork,
    ) -> UserDTO:
        user_repo = uow.get_repository(UserRepository)
        return await user_repo.create(
            username=user.username,
            password=hash_password(user.password),
        )

    # TODO при обновлении старого пароля на новый пароль нужно какое-то подтверждение (сам старый пароль)
    async def update_user(
        self,
        user_id: str,
        user: UpdateUserRequest,
        uow: UnitOfWork,
    ) -> UserDTO:
        user_repo = uow.get_repository(UserRepository)
        user_update_dict: dict = user.model_dump(
            exclude={"password"},
            exclude_unset=True,
            exclude_none=True,
        )

        if user.password is not None:
            user_update_dict["password"] = hash_password(user.password)

        return await user_repo.update(
            id=user_id,
            **user_update_dict,
        )
