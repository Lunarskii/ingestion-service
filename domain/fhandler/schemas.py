from typing import Any
from io import BytesIO

from pydantic import BaseModel

from domain.fhandler.utils import get_mime_type


class File(BaseModel):
    content: bytes
    name: str
    size: int
    extension: str
    headers: dict[str, Any]

    @property
    def file(self) -> BytesIO:
        return BytesIO(self.content)

    @property
    def type(self) -> str:
        return get_mime_type(self.content)
