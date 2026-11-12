from datetime import UTC, datetime

import pytest

from habr_parser.dates import parse_iso_datetime


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("2026-11-10T09:15:00+03:00", datetime(2026, 11, 10, 6, 15, tzinfo=UTC)),
        ("2026-11-10T06:15:00Z", datetime(2026, 11, 10, 6, 15, tzinfo=UTC)),
        ("2026-11-10T06:15:00", datetime(2026, 11, 10, 6, 15, tzinfo=UTC)),
        ("2026-11-10", datetime(2026, 11, 10, tzinfo=UTC)),
    ],
)
def test_results_are_timezone_aware_utc(raw, expected):
    assert parse_iso_datetime(raw) == expected


@pytest.mark.parametrize("raw", [None, "", "yesterday", 12345])
def test_unparseable_values_give_none(raw):
    assert parse_iso_datetime(raw) is None
