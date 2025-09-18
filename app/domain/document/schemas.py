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

from app.schemas import (
    BaseSchema,
    BaseDTO,
    UUIDMixin,
)
from app.utils.file import get_mime_type
from app.utils.datetime import (
    serialize_datetime_to_str,
    reset_timezone,
)


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


# TODO upd doc
class DocumentStatus(str, Enum):
    """
    Перечисление статусов обработки документа.

    :cvar success: Успешно.
    :cvar failed: Неуспешно.
    """

    pending: str = "PENDING"
    queued: str = "QUEUED"
    running: str = "RUNNING"
    extracting: str = "EXTRACTING"
    chunking: str = "CHUNKING"
    embedding: str = "EMBEDDING"
    success: str = "SUCCESS"
    failed: str = "FAILED"


class Document(BaseSchema):
    """
    Метаданные документа.

    :ivar id: Уникальный идентификатор документа.
    :ivar workspace_id: Идентификатор рабочего пространства.
    :ivar name: Имя документа.
    :ivar media_type: MIME-тип документа, например ``application/pdf``.
    :ivar detected_language: Определённый язык содержимого.
    :ivar page_count: Количество страниц в документе.
    :ivar author: Автор документа.
    :ivar creation_date: Дата создания документа.
    :ivar raw_storage_path: Путь в ``RawStorage``, где хранится исходный документ.
    :ivar silver_storage_path: Путь в ``SilverStorage``, где хранится обработанный документ.
    :ivar size_bytes: Размер файла в байтах.
    :ivar ingested_at: Время приёма/загрузки документа.
    :ivar status: Статус обработки (``DocumentStatus``).
    :ivar error_message: Текст ошибки, если статус ``DocumentStatus.failed``.
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
    silver_storage_path: str | None = None
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
    :ivar workspace_id: Идентификатор рабочего пространства.
    :ivar name: Имя документа.
    :ivar media_type: MIME-тип документа, например ``application/pdf``.
    :ivar detected_language: Определённый язык содержимого.
    :ivar page_count: Количество страниц в документе.
    :ivar author: Автор документа.
    :ivar creation_date: Дата создания документа.
    :ivar raw_storage_path: Путь в ``RawStorage``, где хранится исходный документ.
    :ivar silver_storage_path: Путь в ``SilverStorage``, где хранится обработанный документ.
    :ivar size_bytes: Размер файла в байтах.
    :ivar ingested_at: Время приёма/загрузки документа.
    :ivar status: Статус обработки (``DocumentStatus``).
    :ivar error_message: Текст ошибки, если статус ``DocumentStatus.failed``.
    """

    workspace_id: str
    name: str
    media_type: str
    detected_language: str | None = None
    page_count: int | None = None
    author: str | None = None
    creation_date: datetime | None = None
    raw_storage_path: str
    silver_storage_path: str | None = None
    size_bytes: int
    ingested_at: Annotated[datetime, Field(default_factory=datetime.now)]
    status: DocumentStatus = DocumentStatus.success
    error_message: str | None = None

    @field_serializer("creation_date")
    def reset_timezone(self, value: datetime) -> datetime | None:
        return reset_timezone(value)
