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
        page_separator: str = "\n\n",
    ):
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
            text += f"{page.text}{self.page_separator}" if i < len(pages) - 1 else page.text

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
