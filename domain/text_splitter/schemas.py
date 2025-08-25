from schemas.base import BaseSchema


class PageSpan(BaseSchema):
    text: str
    page_num: int
    chunk_start_on_page: int
    chunk_end_on_page: int


class Chunk(BaseSchema):
    text: str
    page_spans: list[PageSpan]

    @property
    def page_nums(self) -> list[int]:
        return [page_span.page_num for page_span in self.page_spans]
