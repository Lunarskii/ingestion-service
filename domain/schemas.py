from datetime import datetime
from enum import Enum
from typing import Annotated
import uuid

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
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


class DocumentStatus(str, Enum):
    """
    Статусы обработки документа.

    - SUCCESS: Успешная обработка.
    - FAILED: Обработка завершилась с ошибкой.
    """

    success: str = "SUCCESS"
    failed: str = "FAILED"


class DocumentMeta(BaseModel):
    """
    Метаданные обработанного документа для сохранения в репозитории.

    :param document_id: Уникальный идентификатор документа.
    :type document_id: str
    :param workspace_id: Идентификатор рабочего пространства.
    :type workspace_id: str
    :param document_type: Тип документа (PDF, DOCX и т.п.).
    :type document_type: str
    :param detected_language: Определённый язык содержимого.
    :type detected_language: str | None
    :param document_page_count: Количество страниц.
    :type document_page_count: int | None
    :param author: Автор документа.
    :type author: str | None
    :param creation_date: Дата создания документа.
    :type creation_date: datetime
    :param raw_storage_path: Путь в RawStorage, где лежит оригинальный файл.
    :type raw_storage_path: str
    :param file_size_bytes: Размер файла в байтах.
    :type file_size_bytes: int
    :param ingested_at: Время приёма/загрузки документа.
    :type ingested_at: datetime
    :param status: Статус обработки (DocumentStatus).
    :type status: DocumentStatus
    :param error_message: Текст ошибки, если статус FAILED.
    :type error_message: str | None
    """

    document_id: str
    workspace_id: str
    document_type: str
    detected_language: str | None = None
    document_page_count: int | None = None
    author: str | None = None
    creation_date: Annotated[datetime | None, Field(default_factory=datetime.now)]
    raw_storage_path: str
    file_size_bytes: int
    ingested_at: Annotated[datetime, Field(default_factory=datetime.now)]
    status: DocumentStatus = DocumentStatus.success
    error_message: str | None = None

    @field_serializer("creation_date", "ingested_at")
    def datetime_to_str(self, value: datetime):
        """
        Сериализация datetime в строку формата YYYY-MM-DD HH:MM:SS.
        """

        if value is None:
            return value
        return datetime.strftime(value, "%Y-%m-%d %H:%M:%S")

    @field_serializer("status")
    def document_status_to_str(self, value: DocumentStatus):
        """
        Сериализация статуса в строковое значение.
        """

        if value is None:
            return value
        return value.value
