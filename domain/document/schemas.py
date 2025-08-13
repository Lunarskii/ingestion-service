from datetime import datetime
from enum import Enum
from typing import Any, Annotated
from io import BytesIO

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
)

from domain.document.utils import get_mime_type


class File(BaseModel):
    """
    Схема файла, используемая для передачи данных о загруженном файле.

    :ivar content: Сырые байты файла.
    :vartype content: bytes
    :ivar name: Имя файла (включая расширение).
    :vartype name: str
    :ivar size: Размер файла в байтах.
    :vartype size: int
    :ivar extension: Расширение файла (начинается с точки), например ``.pdf``.
    :vartype extension: str
    :ivar headers: Дополнительные HTTP-заголовки, переданные при загрузке файла.
    :vartype headers: dict[str, Any]
    """

    content: bytes
    name: str
    size: int
    extension: str
    headers: dict[str, Any] = {}

    @property
    def file(self) -> BytesIO:
        """
        Байтовый поток с содержимым файла.
        Возвращает :class:`BytesIO`, созданный из поля ``content``.

        :return: Объект ``BytesIO`` с данными файла.
        :rtype: BytesIO
        """

        return BytesIO(self.content)

    @property
    def type(self) -> str:
        """
        Определяет MIME-тип файла по его содержимому.

        :return: MIME-тип файла, например ``application/pdf``.
        :rtype: str
        """

        return get_mime_type(self.content)


class DocumentStatus(str, Enum):
    """
    Перечисление статусов обработки документа.

    :cvar success: Успешно.
    :vartype success: str
    :cvar failed: Неуспешно.
    :vartype failed: str
    """

    success: str = "SUCCESS"
    failed: str = "FAILED"


class DocumentMeta(BaseModel):
    """
    Метаданные обработанного документа для сохранения в репозитории.

    :ivar document_id: Уникальный идентификатор документа.
    :vartype document_id: str
    :ivar workspace_id: Идентификатор рабочего пространства.
    :vartype workspace_id: str
    :ivar media_type: MIME-тип документа, например ``application/pdf``.
    :vartype media_type: str
    :ivar detected_language: Определённый язык содержимого.
    :vartype detected_language: str | None
    :ivar document_page_count: Количество страниц.
    :vartype document_page_count: int | None
    :ivar author: Автор документа.
    :vartype author: str | None
    :ivar creation_date: Дата создания документа.
    :vartype creation_date: datetime
    :ivar raw_storage_path: Путь в ``RawStorage``, где лежит оригинальный файл.
    :vartype raw_storage_path: str
    :ivar file_size_bytes: Размер файла в байтах.
    :vartype file_size_bytes: int
    :ivar ingested_at: Время приёма/загрузки документа.
    :vartype ingested_at: datetime
    :ivar status: Статус обработки (``DocumentStatus``).
    :vartype status: DocumentStatus
    :ivar error_message: Текст ошибки, если статус ``DocumentStatus.failed``.
    :vartype error_message: str | None
    """

    model_config = ConfigDict(extra="allow")

    document_id: str
    workspace_id: str
    document_name: str
    media_type: str
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
    def datetime_to_str(self, value: datetime) -> str | None:
        """
        Сериализация datetime в строку формата YYYY-MM-DD HH:MM:SS.
        """

        if value is None:
            return value
        return datetime.strftime(value, "%Y-%m-%d %H:%M:%S")

    @field_serializer("status")
    def document_status_to_str(self, value: DocumentStatus) -> str | None:
        """
        Сериализация статуса в строковое значение.
        """

        if value is None:
            return value
        return value.value
