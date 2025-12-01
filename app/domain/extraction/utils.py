from typing import Iterable

from app.domain.extraction.schemas import DocumentPage


# TODO перенести в другое место или что-то с этим сделать
def pages_to_text(pages: Iterable[DocumentPage], max_chars: int = 0) -> str:
    """
    Соединяет страницы в единый текст, пока не достигнет порога.

    :param pages: Страницы документа.
    :param max_chars: Максимум символов, который будет извлечен из страниц.
                      Если 0, то будет извлечен весь текст.
    """

    if max_chars == 0:
        return " ".join(page.text for page in pages)

    text: str = ""
    for page in pages:
        if page.text:
            text += f" {page.text}" if text else page.text
            if len(text) >= max_chars:
                break
    return text[:max_chars]
