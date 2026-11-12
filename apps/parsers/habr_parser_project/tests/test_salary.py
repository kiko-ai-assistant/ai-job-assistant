import pytest

from habr_parser.salary import build_salary


def monetary(currency="RUR", **value):
    return {"@type": "MonetaryAmount", "currency": currency, "value": value}


def test_range_is_mapped_and_currency_is_normalised():
    salary = build_salary(monetary(minValue=200_000, maxValue=300_000))

    assert (salary.from_, salary.to, salary.currency) == (200_000, 300_000, "RUB")
    assert salary.text == "200000-300000 RUB"


def test_only_lower_bound():
    salary = build_salary(monetary("USD", minValue=3000))

    assert (salary.from_, salary.to, salary.currency) == (3000, None, "USD")
    assert salary.text == "from 3000 USD"


def test_only_upper_bound():
    salary = build_salary(monetary(maxValue=90_000))

    assert (salary.from_, salary.to) == (None, 90_000)
    assert salary.text == "up to 90000 RUB"


def test_single_value_becomes_both_bounds():
    salary = build_salary(monetary(value=120_000))

    assert (salary.from_, salary.to) == (120_000, 120_000)


def test_bare_number_value_is_supported():
    salary = build_salary({"currency": "RUB", "value": 50_000})

    assert (salary.from_, salary.to) == (50_000, 50_000)


def test_numeric_strings_are_accepted():
    salary = build_salary(monetary(minValue="100000", maxValue="150000.0"))

    assert (salary.from_, salary.to) == (100_000, 150_000)


@pytest.mark.parametrize(
    "raw",
    [
        None,
        {},
        monetary(minValue=0, maxValue=0),  # zero means "not specified"
        monetary(currency=None, minValue=100),  # bounds without currency
        monetary(currency="ROUBLE", minValue=100),  # not an ISO-like 3 letter code
        monetary(minValue="n/a"),
        {"currency": "RUB", "value": None},
    ],
)
def test_salary_is_omitted_when_it_cannot_be_valid(raw):
    assert build_salary(raw) is None
