from typing import Any
from io import BytesIO

from pydantic import BaseModel


class File(BaseModel):
    content: bytes
    name: str
    size: int
    extension: str
    headers: dict[str, Any]

    @property
    def file(self) -> BytesIO:
        return BytesIO(self.content)
