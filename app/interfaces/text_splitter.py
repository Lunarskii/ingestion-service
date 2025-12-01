from typing import (
    TYPE_CHECKING,
    Protocol,
)


if TYPE_CHECKING:
    from app.types import (
        DocumentPage,
        DocumentChunk,
    )


class TextSplitter(Protocol):
    def split_pages(
        self,
        pages: list["DocumentPage"],
        *,
        page_separator: str | None = None,
    ) -> list["DocumentChunk"]:
        ...
