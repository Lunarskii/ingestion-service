from typing import Annotated
import uuid

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class VectorMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")

    document_id: str
    workspace_id: str
    document_name: str
    document_page: int
    chunk_index: int
    text: str


class Vector(BaseModel):
    """
    Модель векторного представления текстового фрагмента.

    :param id: Уникальный идентификатор вектора (например, сочетание document_id и индекса фрагмента).
    :type id: str
    :param values: Список значений эмбеддинга.
    :type values: list[float]
    :param metadata: Дополнительные данные (document_id, chunk_id, текст и т.п.).
    :type metadata: VectorMetadata
    """

    id: Annotated[str, Field(default_factory=lambda: str(uuid.uuid4()))]  # noqa
    values: list[float]
    metadata: VectorMetadata
