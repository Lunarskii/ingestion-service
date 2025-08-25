from datetime import datetime

import pytest

from utils.datetime import parse_iso8824_date, parse_date


class TestParseISO8824Date:
    @pytest.mark.parametrize(
        "input_text, expected",
        [
            (None, None),
            # Без префикса — добавится D:
            ("20230717", datetime(2023, 7, 17)),
            # Только год
            ("D:2023", datetime(2023, 1, 1)),
            # Год+месяц+день
            ("D:20231225", datetime(2023, 12, 25)),
            # Год+месяц+день+часы+минуты+секунды
            ("D:20231225123045", datetime(2023, 12, 25, 12, 30, 45)),
            # С часовым поясом +02:00 (отнимется 2 часа)
            ("D:20231225123045+02'00'", datetime(2023, 12, 25, 10, 30, 45)),
            # С часовым поясом -01:30 (отнимет -1.5 часа => добавит 1.5)
            ("D:20231225123045-01'30'", datetime(2023, 12, 25, 14, 0, 45)),
            # UTC обозначение Z
            ("D:20231225123045Z", datetime(2023, 12, 25, 12, 30, 45)),
        ],
    )
    def test_various_iso_formats(self, input_text, expected):
        result = parse_iso8824_date(input_text)
        assert result == expected

    def test_invalid_format_returns_none(self):
        assert parse_iso8824_date("D:20A3") is None
        assert parse_iso8824_date("random text") is None


class TestParseDate:
    @pytest.mark.parametrize(
        "text, expected",
        [
            (None, None),
            # Пустая строка → None
            ("", None),
            ("   ", None),
            # С использованием parse_iso8824_date
            ("D:20230101120000", datetime(2023, 1, 1, 12, 0, 0)),
            # ISO8601
            ("2023-07-17T12:34:56", datetime(2023, 7, 17, 12, 34, 56)),
            ("2023-07-17 12:34:56", datetime(2023, 7, 17, 12, 34, 56)),
            ("2023-07-17", datetime(2023, 7, 17)),
            # Европейский формат
            ("17.07.2023 08:15:30", datetime(2023, 7, 17, 8, 15, 30)),
            ("17.07.2023", datetime(2023, 7, 17)),
            # Fuzzy‑парсинг dateutil
            ("July 17, 2023 14:00", datetime(2023, 7, 17, 14, 0)),
        ],
    )
    def test_parse_known_formats(self, text, expected):
        result = parse_date(text)
        assert result == expected
