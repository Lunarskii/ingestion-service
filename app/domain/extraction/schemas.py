from datetime import datetime

from pydantic import ConfigDict

from app.schemas import BaseSchema


class Page(BaseSchema):
    """
    Страница документа

    :param num: Номер страницы.
    :type num: int
    :param text: Текст, содержащийся на странице.
    :type text: str
    """

    num: int
    text: str


class ExtractedInfo(BaseSchema):
    """
    Информация, извлечённая из документа.
    Содержит текст документа и его метаданные.

    :param pages: Весь извлечённый постранично текст.
    :type pages: list[Page]
    :param document_page_count: Количество страниц в документе, если доступно.
    :type document_page_count: int | None
    :param author: Автор документа, если доступно.
    :type author: str | None
    :param creation_date: Дата создания документа, если доступна.
    :type creation_date: datetime | None
    """

    model_config = ConfigDict(extra="allow")

    pages: list[Page]
    document_page_count: int | None = None
    author: str | None = None
    creation_date: datetime | None = None
