from pydantic import ConfigDict

from app.schemas import (
    BaseSchema,
    UUIDMixin,
)


class VectorMetadata(BaseSchema):
    """
    Метаданные вектора.

    :ivar document_id: Идентификатор документа.
    :vartype document_id: str
    :ivar workspace_id: Идентификатор пространства.
    :vartype workspace_id: str
    :ivar document_name: Имя документа.
    :vartype document_name: str
    :ivar page_start: Страница, на которой находится начало источника (фрагмента документа).
    :vartype page_start: int
    :ivar page_end: Страница, на которой находится конец источника (фрагмента документа).
    :vartype page_end: int
    :ivar text: Текст на странице документа.
    :vartype text: str
    """

    model_config = ConfigDict(extra="allow")

    document_id: str
    workspace_id: str
    document_name: str
    page_start: int
    page_end: int
    text: str


class Vector(BaseSchema, UUIDMixin):
    """
    Схема векторного представления текстового фрагмента.

    :ivar id: Уникальный идентификатор вектора (UUID в строковом виде).
    :vartype id: str
    :ivar values: Список значений эмбеддинга.
    :vartype values: list[float]
    :ivar metadata: Дополнительные данные (document_id, chunk_id, текст и т.п.).
    :vartype metadata: VectorMetadata
    """

    values: list[float]
    metadata: VectorMetadata
