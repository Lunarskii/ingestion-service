from app.schemas import BaseSchema


class PageSpan(BaseSchema):
    """
    Описание отрезка чанка, расположенного на одной странице.

    :ivar text: Текст фрагмента, который лежит на данной странице.
    :vartype text: str
    :ivar page_num: Номер страницы.
    :vartype page_num: int
    :ivar chunk_start_on_page: Позиция начала фрагмента относительно начала страницы (в символах).
    :vartype chunk_start_on_page: int
    :ivar chunk_end_on_page: Позиция конца фрагмента относительно начала страницы (в символах).
    :vartype chunk_end_on_page: int
    """

    text: str
    page_num: int
    chunk_start_on_page: int
    chunk_end_on_page: int


class Chunk(BaseSchema):
    """
    Чанк - кусок склеенного текста документа и набор PageSpan-ов, указывающих,
    какие части чанка каким страницам соответствуют.

    :ivar text: Текст чанка.
    :vartype text: str
    :ivar page_spans: Список объектов :class:`PageSpan`, каждый из которых
                      представляет часть чанка, располагающуюся на одной странице.
    :vartype page_spans: list[PageSpan]
    """

    text: str
    page_spans: list[PageSpan]

    @property
    def page_nums(self) -> list[int]:
        """
        Возвращает список номеров страниц, на которых присутствует данный чанк.

        :return: Список уникальных (в порядке появления) номеров страниц.
        :rtype: list[int]
        """

        return [page_span.page_num for page_span in self.page_spans]
