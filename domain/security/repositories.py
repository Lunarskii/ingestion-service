from domain.database.repositories import AlchemyRepository
from domain.security.models import APIKeysDAO
from domain.security.schemas import APIKeysDTO


class APIKeysRepository(AlchemyRepository[APIKeysDAO, APIKeysDTO]):
    """
    Репозиторий для работы с API-ключами.
    """

    ...
