from app.domain.database.repositories import AlchemyRepository
from app.domain.security.models import APIKeysDAO
from app.domain.security.schemas import APIKeysDTO


class APIKeysRepository(AlchemyRepository[APIKeysDAO, APIKeysDTO]):
    """
    Репозиторий для работы с API-ключами.
    """

    ...
