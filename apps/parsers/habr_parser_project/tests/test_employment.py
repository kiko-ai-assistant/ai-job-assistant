import pytest

from habr_parser.employment import map_employment_types


@pytest.mark.parametrize(
    ("location_type", "employment", "expected"),
    [
        ("TELECOMMUTE", "FULL_TIME", ["REMOTE"]),
        (None, "FULL_TIME", ["OFFICE"]),
        (None, None, ["OFFICE"]),
        ("TELECOMMUTE", "CONTRACTOR", ["REMOTE", "CONTRACT"]),
        (None, "CONTRACTOR", ["CONTRACT"]),
        (None, ["FULL_TIME", "CONTRACTOR"], ["CONTRACT"]),
        ("telecommute", "contractor", ["REMOTE", "CONTRACT"]),
    ],
)
def test_mapping_always_returns_at_least_one_known_type(location_type, employment, expected):
    assert map_employment_types(location_type, employment) == expected
