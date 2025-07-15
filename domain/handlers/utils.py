from datetime import (
    datetime,
    timedelta,
)
import re

from dateutil import parser as dateutil_parser


def parse_iso8824_date(text: str) -> datetime | None:
    """
    Конвертирует строковый формат даты PDF в datetime. Наивный UTC: конвертирует к UTC+0.

    :param text: Дата в строковом формате
    :type text: str

    :return: Дата в формате datetime
    :rtype: datetime
    """

    if text is None:
        return None

    if text[0].isdigit():
        text = "D:" + text

    pdf_date_re = (
        r"^D:"
        r"(?P<year>\d{4})"
        r"(?P<month>\d{2})?"
        r"(?P<day>\d{2})?"
        r"(?P<hour>\d{2})?"
        r"(?P<minute>\d{2})?"
        r"(?P<second>\d{2})?"
        r"(?P<tz_sign>[+\-Zz])?"
        r"(?P<tz_hour>\d{2})?"
        r"'?(?P<tz_minute>\d{2})?'?"
    )

    if match := re.match(pdf_date_re, text):
        gd: dict[str, str] = match.groupdict()

        dt = datetime(
            year=int(gd.get("year")),
            month=int(gd.get("month") or 1),
            day=int(gd.get("day") or 1),
            hour=int(gd.get("hour") or 0),
            minute=int(gd.get("minute") or 0),
            second=int(gd.get("second") or 0),
        )

        if sign := gd.get("tz_sign"):
            offset = timedelta(
                hours=int(gd.get("tz_hour", 0)),
                minutes=int(gd.get("tz_minute", 0)),
            )
            if sign == "-":
                offset = -offset
            dt -= offset

        return dt


def parse_date(text: str) -> datetime | None:
    """
    Конвертирует строковый формат PDF, ISO и неструктурированных дат в datetime.

    :param text: Дата в строковом формате
    :type text: str

    :return: Дата в формате datetime
    :rtype: datetime
    """

    if not text:
        return None
    text = text.strip()

    if dt := parse_iso8824_date(text):
        return dt

    for fmt in (
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d.%m.%Y %H:%M:%S",
        "%d.%m.%Y",
    ):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass

    try:
        return dateutil_parser.parse(text, fuzzy=True)
    except (ValueError, OverflowError):
        pass
