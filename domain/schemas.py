from datetime import datetime
from typing import Annotated

from pydantic import (
    BaseModel,
    Field,
    UUID4,
)


class Vector(BaseModel): ...


class DocumentMeta(BaseModel):
    id_: Annotated[UUID4, Field(alias="id", serialization_alias="id")]
    type_: Annotated[str | None, Field(alias="type", serialization_alias="type")] = None
    detected_language: str | None = None
    document_page_count: int | None = None
    author: str | None = None
    creation_date: datetime | None = None
