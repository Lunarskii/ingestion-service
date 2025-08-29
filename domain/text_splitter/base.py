from typing import (
    Literal,
    Callable,
)

from langchain.text_splitter import RecursiveCharacterTextSplitter

from domain.text_splitter.schemas import (
    PageSpan,
    Chunk,
)
from domain.extraction.schemas import Page


class TextSplitter:
    """
    Обертка над RecursiveCharacterTextSplitter, работающая с разделением страниц.
    """

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        length_function: Callable[[str], int] = len,
        keep_separator: Literal["start", "end"] | bool = True,
        add_start_index: bool = False,
        strip_whitespace: bool = True,
        separators: list[str] | None = None,
        is_separator_regex: bool = False,
        page_separator: str = "\n",
    ):
        """
        :param chunk_size: Максимальная длина чанка (в символах).
        :type chunk_size: int
        :param chunk_overlap: Перекрытие между соседними чанками (в символах).
        :type chunk_overlap: int
        :param length_function: Функция для измерения длины строки (по умолчанию len).
        :type length_function: Callable[[str], int]
        :param keep_separator: Как сохранять разделитель при разбиении (см. RecursiveCharacterTextSplitter).
        :type keep_separator: Literal["start", "end"] | bool
        :param add_start_index: Добавлять ли индекс старта чанка.
        :type add_start_index: bool
        :param strip_whitespace: Удалять ли внешние пробелы при разбиении.
        :type strip_whitespace: bool
        :param separators: Список разделителей для RecursiveCharacterTextSplitter.
        :type separators: list[str] | None
        :param is_separator_regex: Считать ли разделители регулярными выражениями.
        :type is_separator_regex: bool
        :param page_separator: Строка, которая вставляется между страницами при склейке
                               полного текста (по умолчанию "\n").
        :type page_separator: str
        """

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=length_function,
            keep_separator=keep_separator,
            add_start_index=add_start_index,
            strip_whitespace=strip_whitespace,
            separators=separators,
            is_separator_regex=is_separator_regex,
        )
        self.page_separator = page_separator

    def split_pages(self, pages: list[Page]) -> list[Chunk]:
        """
        Разбивает список страниц на чанки и вычисляет перекрытия с каждой страницей.

        Алгоритм (вкратце):
          1. Склеиваем страницы в единый текст, вставляя `page_separator` между страницами.
             При этом запоминаем абсолютные позиции начала и конца каждой страницы в
             этом склеенном тексте.
          2. Вызываем `splitter.split_text(text)`, чтобы получить последовательность
             чанков (строк).
          3. Для каждого чанка находим его индекс в объединённом тексте (ищем с позиции
             `search_position`, чтобы поддерживать порядок и избегать нахождения "старых"
             совпадений).
          4. Вычисляем перекрытие чанка с каждой страницей и формируем объект
             :class:`PageSpan` для каждого непустого перекрытия.
          5. Формируем объект :class:`Chunk` с полем ``text`` и списком ``page_spans``.

        :param pages: Список страниц для разбиения. Элемент - объект :class:`Page`
                      (с полем `num` и `text`).
        :type pages: list[Page]
        :return: Список объектов :class:`Chunk`. Пустой список возвращается, если
                 входной `pages` пуст.
        :rtype: list[Chunk]

        Особенности и гарантии
        ---------------------
        * Если один и тот же текст чанка встречается в объединённом тексте более одного
          раза - мы сначала пытаемся найти вхождение начиная с `search_position` чтобы
          поддержать порядок; если не находим - ищем по всему тексту; в крайнем случае
          используем `search_position` как позицию начала.
        * Для каждого найденного перекрытия вычисляются относительные индексы в пределах
          исходной страницы (`chunk_start_on_page`, `chunk_end_on_page`), пригодные для
          извлечения подстроки из `page.text`.
        * Внутренние позиции считаются в символах строки Python (не в байтах).

        :raises ValueError: если объекты в `pages` не имеют атрибутов `num` и `text`.
        """

        if not pages:
            return []

        page_starts: list[int] = []
        page_ends: list[int] = []
        current_position: int = 0
        text: str = ""

        for i, page in enumerate(pages):
            page_starts.append(current_position)
            current_position += len(page.text)
            page_ends.append(current_position)
            current_position += len(self.page_separator)
            text += (
                f"{page.text}{self.page_separator}" if i < len(pages) - 1 else page.text
            )

        chunks: list[Chunk] = []
        search_position: int = 0

        for chunk in self.splitter.split_text(text):
            idx: int = text.find(chunk, search_position)
            if idx == -1:
                idx = text.find(chunk)
                if idx == -1:
                    idx = search_position

            chunk_start: int = idx
            chunk_end: int = idx + len(chunk)
            search_position = chunk_end

            page_spans: list[PageSpan] = []
            for page, page_start, page_end in zip(pages, page_starts, page_ends):
                overlap_start: int = max(chunk_start, page_start)
                overlap_end: int = min(chunk_end, page_end)

                if overlap_start < overlap_end:
                    chunk_start_on_page: int = overlap_start - page_start
                    chunk_end_on_page: int = overlap_end - page_start

                    page_spans.append(
                        PageSpan(
                            text=page.text[chunk_start_on_page:chunk_end_on_page],
                            page_num=page.num,
                            chunk_start_on_page=chunk_start_on_page,
                            chunk_end_on_page=chunk_end_on_page,
                        )
                    )

            chunks.append(
                Chunk(
                    text=chunk,
                    page_spans=page_spans,
                ),
            )

        return chunks
