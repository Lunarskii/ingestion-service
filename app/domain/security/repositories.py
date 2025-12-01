from app.adapters.sqlalchemy_repository import AlchemyRepository
from app.domain.security.models import APIKeysDAO
from app.domain.security.schemas import APIKeysDTO


class APIKeysRepository(AlchemyRepository[APIKeysDAO, APIKeysDTO]):
    """
    Репозиторий для работы с API-ключами.
    """

    ...
