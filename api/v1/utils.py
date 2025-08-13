from urllib.parse import quote


def build_content_disposition(filename: str, inline: bool = True) -> str:
    """
    Возвращает корректный Content-Disposition с ASCII-фолбэком и filename* (RFC5987).
    """

    disposition = "inline" if inline else "attachment"
    ascii_fallback = (
        "".join(
            ch if ord(ch) < 128 and ch not in ('"', "\\") else "_" for ch in filename
        )
        or "file"
    )
    filename_star = quote(filename, safe="")
    return f"{disposition}; filename=\"{ascii_fallback}\"; filename*=UTF-8''{filename_star}"
