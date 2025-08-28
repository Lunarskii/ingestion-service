from datetime import datetime
from enum import Enum
from typing import (
    Any,
    Annotated,
)
from io import BytesIO

from pydantic import (
    Field,
    field_serializer,
)

from schemas.base import (
    BaseSchema,
    BaseDTO,
)
from schemas.mixins import UUIDMixin
from utils.file import get_mime_type
from utils.datetime import serialize_datetime_to_str


class File(BaseSchema):
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


class Document(BaseSchema):
    """
    Метаданные документа.

    :ivar id: Уникальный идентификатор документа.
    :vartype id: str
    :ivar workspace_id: Идентификатор рабочего пространства.
    :vartype workspace_id: str
    :ivar name: Имя документа.
    :vartype name: str
    :ivar media_type: MIME-тип документа, например ``application/pdf``.
    :vartype media_type: str
    :ivar detected_language: Определённый язык содержимого.
    :vartype detected_language: str | None
    :ivar page_count: Количество страниц в документе.
    :vartype page_count: int | None
    :ivar author: Автор документа.
    :vartype author: str | None
    :ivar creation_date: Дата создания документа.
    :vartype creation_date: datetime
    :ivar raw_storage_path: Путь в ``RawStorage``, где лежит оригинальный файл.
    :vartype raw_storage_path: str
    :ivar size_bytes: Размер файла в байтах.
    :vartype size_bytes: int
    :ivar ingested_at: Время приёма/загрузки документа.
    :vartype ingested_at: datetime
    :ivar status: Статус обработки (``DocumentStatus``).
    :vartype status: DocumentStatus
    :ivar error_message: Текст ошибки, если статус ``DocumentStatus.failed``.
    :vartype error_message: str | None
    """

    id: Annotated[
        str,
        Field(serialization_alias="document_id"),
    ]
    workspace_id: str
    name: Annotated[
        str,
        Field(serialization_alias="document_name"),
    ]
    media_type: str
    detected_language: str | None = None
    page_count: Annotated[
        int | None,
        Field(serialization_alias="document_page_count"),
    ] = None
    author: Annotated[
        str | None,
        Field(serialization_alias="document_author"),
    ] = None
    creation_date: datetime | None = None
    raw_storage_path: str
    size_bytes: Annotated[
        int,
        Field(serialization_alias="document_size_bytes"),
    ]
    ingested_at: Annotated[datetime, Field(default_factory=datetime.now)]
    status: DocumentStatus = DocumentStatus.success
    error_message: str | None = None

    @field_serializer("creation_date", "ingested_at")
    def datetime_to_str(self, value: datetime) -> str | None:
        return serialize_datetime_to_str(value)


class DocumentDTO(BaseDTO, UUIDMixin):
    """
    DTO (Data Transfer Object) для представления метаданных документа.

    :ivar id: Уникальный идентификатор документа.
    :vartype id: str
    :ivar workspace_id: Идентификатор рабочего пространства.
    :vartype workspace_id: str
    :ivar name: Имя документа.
    :vartype name: str
    :ivar media_type: MIME-тип документа, например ``application/pdf``.
    :vartype media_type: str
    :ivar detected_language: Определённый язык содержимого.
    :vartype detected_language: str | None
    :ivar page_count: Количество страниц в документе.
    :vartype page_count: int | None
    :ivar author: Автор документа.
    :vartype author: str | None
    :ivar creation_date: Дата создания документа.
    :vartype creation_date: datetime
    :ivar raw_storage_path: Путь в ``RawStorage``, где лежит оригинальный файл.
    :vartype raw_storage_path: str
    :ivar size_bytes: Размер файла в байтах.
    :vartype size_bytes: int
    :ivar ingested_at: Время приёма/загрузки документа.
    :vartype ingested_at: datetime
    :ivar status: Статус обработки (``DocumentStatus``).
    :vartype status: DocumentStatus
    :ivar error_message: Текст ошибки, если статус ``DocumentStatus.failed``.
    :vartype error_message: str | None
    """

    workspace_id: str
    name: str
    media_type: str
    detected_language: str | None = None
    page_count: int | None = None
    author: str | None = None
    creation_date: datetime | None = None
    raw_storage_path: str
    size_bytes: int
    ingested_at: Annotated[datetime, Field(default_factory=datetime.now)]
    status: DocumentStatus = DocumentStatus.success
    error_message: str | None = None

    @field_serializer("creation_date")
    def reset_timezone(self, value: datetime) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=None)
