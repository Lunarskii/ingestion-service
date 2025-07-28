from datetime import datetime

from pydantic import BaseModel


class ExtractedInfo(BaseModel):
    """
    Схема ответа от TextExtractor.extract().
    Информация, извлечённая из документа.
    Содержит текст документа и его метаданные.

    :param text: Весь извлечённый текст.
    :type text: str
    :param document_page_count: Количество страниц в документе, если доступно.
    :type document_page_count: int | None
    :param author: Автор документа, если доступно.
    :type author: str | None
    :param creation_date: Дата создания документа, если доступна.
    :type creation_date: datetime | None
    """

    text: str = ""
    document_page_count: int | None = None
    author: str | None = None
    creation_date: datetime | None = None
