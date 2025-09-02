from domain.users.service import UserService


async def user_service_dependency() -> UserService:
    return UserService()
