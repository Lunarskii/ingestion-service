from sqlalchemy.orm import Mapped

from app.domain.database.models import BaseDAO
from app.domain.database.mixins import (
    IDMixin,
    CreatedAtMixin,
)


class APIKeysDAO(BaseDAO, IDMixin, CreatedAtMixin):
    """
    DAO (ORM) модель, представляющая API-ключ.

    :ivar id: Идентификатор API-ключа.
    :ivar key_hash: Хэш API-ключа.
    :ivar label: Название API-ключа.
    :ivar is_active: Флаг валидности API-ключа. Если False, то не валиден.
    :ivar created_at: Время создания API-ключа.
    """

    __tablename__ = "api_keys"

    key_hash: Mapped[str]
    label: Mapped[str]
    is_active: Mapped[bool]
