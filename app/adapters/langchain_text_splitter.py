from typing import (
    TYPE_CHECKING,
    Literal,
    Callable,
)

from app.interfaces import TextSplitter

from app.types import (
    DocumentPageSpan,
    DocumentChunk,
)


if TYPE_CHECKING:
    from app.types import DocumentPage


class LangChainTextSplitter(TextSplitter):
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
        :param chunk_size: Максимальная длина фрагмента (в символах).
        :param chunk_overlap: Перекрытие между соседними фрагментами (в символах).
        :param length_function: Функция для измерения длины строки (по умолчанию len).
        :param keep_separator: Как сохранять разделитель при разбиении (см. RecursiveCharacterTextSplitter).
        :param add_start_index: Добавлять ли индекс старта фрагмента.
        :param strip_whitespace: Удалять ли внешние пробелы при разбиении.
        :param separators: Список разделителей для RecursiveCharacterTextSplitter.
        :param is_separator_regex: Считать ли разделители регулярными выражениями.
        :param page_separator: Строка, которая вставляется между страницами при склейке (по умолчанию "\\n").
        """

        from langchain.text_splitter import RecursiveCharacterTextSplitter

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

    def split_pages(
        self,
        pages: list["DocumentPage"],
        *,
        page_separator: str | None = None,
    ) -> list[DocumentChunk]:
        """
        Разбивает список страниц на фрагменты и вычисляет перекрытия с каждой страницей.

        Алгоритм (вкратце):
          1. Склеиваем страницы в единый текст, вставляя ``page_separator`` между страницами.
             При этом запоминаем абсолютные позиции начала и конца каждой страницы в
             этом склеенном тексте.
          2. Вызываем ``splitter.split_text(text)``, чтобы получить последовательность
             фрагментов.
          3. Для каждого фрагмента находим его индекс в объединённом тексте (ищем с позиции
             ``search_position``, чтобы поддерживать порядок и избегать нахождения "старых"
             совпадений).
          4. Вычисляем перекрытие фрагмента с каждой страницей и формируем ``PageSpan``
             для каждого непустого перекрытия.
          5. Формируем фрагмент.

        :param pages: Список страниц документа для разбития на фрагменты.
        :param page_separator: Строка, которая вставляется между страницами при склейке (по умолчанию "\\n").

        :return: Если список страниц пуст, то возвращается пустой список фрагментов, иначе
                 список фрагментов.

        Особенности и гарантии
        ---------------------
        * Если один и тот же текст фрагмента встречается в объединённом тексте более одного
          раза - мы сначала пытаемся найти вхождение начиная с `search_position`, чтобы
          поддержать порядок; если не находим - ищем по всему тексту; в крайнем случае
          используем `search_position` как позицию начала.
        * Для каждого найденного перекрытия вычисляются относительные индексы в пределах
          исходной страницы (`chunk_start_on_page`, `chunk_end_on_page`), пригодные для
          извлечения подстроки из `page.text`.
        * Внутренние позиции считаются в символах строки Python (не в байтах).
        """

        if not pages:
            return []

        page_separator = page_separator or self.page_separator or "\n"

        page_starts: list[int] = []
        page_ends: list[int] = []
        current_position: int = 0
        text: str = ""

        for i, page in enumerate(pages):
            page_starts.append(current_position)
            current_position += len(page.text)
            page_ends.append(current_position)
            current_position += len(page_separator)
            if i < len(pages) - 1:
                text += f"{page.text}{page_separator}"
            else:
                text += page.text

        chunks: list[DocumentChunk] = []
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

            page_spans: list[DocumentPageSpan] = []
            for page, page_start, page_end in zip(pages, page_starts, page_ends):
                overlap_start: int = max(chunk_start, page_start)
                overlap_end: int = min(chunk_end, page_end)

                if overlap_start < overlap_end:
                    chunk_start_on_page: int = overlap_start - page_start
                    chunk_end_on_page: int = overlap_end - page_start

                    page_spans.append(
                        DocumentPageSpan(
                            num=page.num,
                            text=page.text[chunk_start_on_page:chunk_end_on_page],
                            chunk_start_on_page=chunk_start_on_page,
                            chunk_end_on_page=chunk_end_on_page,
                        ),
                    )

            chunks.append(
                DocumentChunk(
                    text=chunk,
                    page_spans=page_spans,
                ),
            )

        return chunks
