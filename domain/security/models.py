from sqlalchemy.orm import Mapped

from domain.database.models import BaseDAO
from domain.database.mixins import (
    IDMixin,
    CreatedAtMixin,
)


class APIKeysDAO(BaseDAO, IDMixin, CreatedAtMixin):
    __tablename__ = "api_keys"

    key_hash: Mapped[bytes]
    label: Mapped[str]
    is_active: Mapped[bool]
