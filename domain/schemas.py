from pydantic import ConfigDict

from schemas.base import BaseSchema
from schemas.mixins import UUIDMixin


class VectorMetadata(BaseSchema):
    """
    Метаданные вектора.

    :ivar document_id: Идентификатор документа.
    :vartype document_id: str
    :ivar workspace_id: Идентификатор пространства.
    :vartype workspace_id: str
    :ivar document_name: Имя документа.
    :vartype document_name: str
    :ivar document_page: Страница документа.
    :vartype document_page: int
    :ivar text: Текст на странице документа.
    :vartype text: str
    """

    model_config = ConfigDict(extra="allow")

    document_id: str
    workspace_id: str
    document_name: str
    document_page: int
    text: str


class Vector(BaseSchema, UUIDMixin):
    """
    Схема векторного представления текстового фрагмента.

    :ivar id: Уникальный идентификатор вектора (например, сочетание document_id и индекса фрагмента).
    :vartype id: str
    :ivar values: Список значений эмбеддинга.
    :vartype values: list[float]
    :ivar metadata: Дополнительные данные (document_id, chunk_id, текст и т.п.).
    :vartype metadata: VectorMetadata
    """

    values: list[float]
    metadata: VectorMetadata
