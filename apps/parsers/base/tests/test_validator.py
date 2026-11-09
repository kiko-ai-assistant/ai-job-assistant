from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from parsers_base.models.vacancy import CreateVacancyRequest, LocationDTO, SalaryDTO
from parsers_base.validation.rules import (
    DEFAULT_ALLOWED_SOURCES,
    MAX_COMPANY_LEN,
    MAX_DESCRIPTION_LEN,
    MAX_FUTURE_TIME_SKEW,
    MAX_LOC_CITY_LEN,
    MAX_LOC_COUNTRY_LEN,
    MAX_LOC_TEXT_LEN,
    MAX_SALARY_LEN,
    MAX_SALARY_VAL,
    MAX_TITLE_LEN,
    MAX_URL_LEN,
    MIN_COMPANY_LEN,
    MIN_DESCRIPTION_LEN,
    MIN_LOC_CITY_LEN,
    MIN_LOC_COUNTRY_LEN,
    MIN_LOC_TEXT_LEN,
    MIN_SALARY_LEN,
    MIN_SALARY_VAL,
    MIN_TITLE_LEN,
    MIN_URL_LEN,
    VACANCY_VALID_UP_TO,
)
from parsers_base.validation.validator import VacancyValidator


def make_salary(**kwargs: Any) -> SalaryDTO:
    return SalaryDTO.model_validate(kwargs)


def build_valid_vacancy(**kwargs: Any) -> CreateVacancyRequest:
    now = kwargs.pop("now", datetime.now(UTC))
    desc = (
        "We are seeking an experienced Go developer to join our core backend engineering "
        "team and build scalable systems. " * 4
    )
    defaults = {
        "external_id": "ext-1001",
        "source": "telegram",
        "title": "Senior Go Developer",
        "company": "Tech Corp",
        "salary": make_salary(
            text="от 2000 до 3000 USD",
            from_=2000,
            to=3000,
            currency="USD",
            gross=True,
        ),
        "grade": "senior",
        "employment_types": ["remote", "office"],
        "location": LocationDTO(
            text="Remote or Moscow",
            country="Russia",
            city="Moscow",
        ),
        "description": desc,
        "url": "https://t.me/tech_jobs/1001",
        "published_at": now - timedelta(hours=2),
        "parsed_at": now - timedelta(hours=1),
    }
    defaults.update(kwargs)
    return CreateVacancyRequest(**defaults)


def test_validator_happy_path_full() -> None:
    now = datetime.now(UTC)
    vacancy = build_valid_vacancy(now=now)
    validator = VacancyValidator()
    result = validator.validate(vacancy, now=now)
    assert result.is_valid
    assert result.reasons == []


def test_validator_happy_path_minimal() -> None:
    now = datetime.now(UTC)
    vacancy = build_valid_vacancy(
        company=None,
        salary=None,
        location=None,
        now=now,
    )
    validator = VacancyValidator()
    result = validator.validate(vacancy, now=now)
    assert result.is_valid
    assert result.reasons == []


@pytest.mark.parametrize(
    ("mutate_kwargs", "expected_reason_substr"),
    [
        ({"external_id": ""}, "external_id"),
        ({"external_id": "   "}, "external_id"),
        ({"source": ""}, "source"),
        ({"source": "invalid_source"}, "source"),
        ({"title": "A" * (MIN_TITLE_LEN - 1)}, "title"),
        ({"title": "A" * (MAX_TITLE_LEN + 1)}, "title"),
        ({"title": "   "}, "title"),
        ({"company": "A" * (MIN_COMPANY_LEN - 1)}, "company"),
        ({"company": "A" * (MAX_COMPANY_LEN + 1)}, "company"),
        ({"description": "A" * (MIN_DESCRIPTION_LEN - 1)}, "description"),
        ({"description": "A" * (MAX_DESCRIPTION_LEN + 1)}, "description"),
        ({"description": "   "}, "description"),
        ({"url": "A" * (MIN_URL_LEN - 1)}, "url"),
        ({"url": "A" * (MAX_URL_LEN + 1)}, "url"),
        ({"url": "   "}, "url"),
        ({"grade": ""}, "grade"),
        ({"grade": "principal"}, "grade"),
        ({"employment_types": []}, "employment_types"),
        ({"employment_types": ["freelance"]}, "employment_type"),
    ],
)
def test_validator_field_rejections(
    mutate_kwargs: dict[str, Any],
    expected_reason_substr: str,
) -> None:
    now = datetime.now(UTC)
    vacancy = build_valid_vacancy(now=now, **mutate_kwargs)
    validator = VacancyValidator()
    result = validator.validate(vacancy, now=now)
    assert not result.is_valid
    assert any(expected_reason_substr in r for r in result.reasons)


@pytest.mark.parametrize(
    ("salary_dto", "expected_reason"),
    [
        (
            make_salary(from_=5000, to=3000, currency="USD"),
            "salary_from cannot be greater than salary_to",
        ),
        (
            make_salary(from_=2000, to=None, currency=None),
            "currency is required when salary bounds are specified",
        ),
        (
            make_salary(from_=None, to=4000, currency=None),
            "currency is required when salary bounds are specified",
        ),
        (
            make_salary(from_=None, to=None, currency="USD"),
            "currency cannot be specified without salary bounds",
        ),
        (
            make_salary(from_=1000, to=2000, currency="US"),
            "currency",
        ),
        (
            make_salary(from_=1000, to=2000, currency="USDD"),
            "currency",
        ),
        (
            make_salary(from_=-1, to=2000, currency="USD"),
            "salary_from",
        ),
        (
            make_salary(from_=MAX_SALARY_VAL + 1, to=None, currency="USD"),
            "salary_from",
        ),
        (
            make_salary(from_=None, to=-1, currency="USD"),
            "salary_to",
        ),
        (
            make_salary(from_=None, to=MAX_SALARY_VAL + 1, currency="USD"),
            "salary_to",
        ),
        (
            make_salary(text="A" * (MIN_SALARY_LEN - 1)),
            "salary",
        ),
        (
            make_salary(text="A" * (MAX_SALARY_LEN + 1)),
            "salary",
        ),
    ],
)
def test_validator_salary_invariants(salary_dto: SalaryDTO, expected_reason: str) -> None:
    now = datetime.now(UTC)
    vacancy = build_valid_vacancy(salary=salary_dto, now=now)
    validator = VacancyValidator()
    result = validator.validate(vacancy, now=now)
    assert not result.is_valid
    assert any(expected_reason in r for r in result.reasons)


@pytest.mark.parametrize(
    ("location_dto", "expected_reason"),
    [
        (
            LocationDTO(city="Berlin", country=None),
            "city cannot be specified without country",
        ),
        (
            LocationDTO(city="Berlin", country=""),
            "city cannot be specified without country",
        ),
        (
            LocationDTO(country="A" * (MIN_LOC_COUNTRY_LEN - 1)),
            "country",
        ),
        (
            LocationDTO(country="A" * (MAX_LOC_COUNTRY_LEN + 1)),
            "country",
        ),
        (
            LocationDTO(country="Germany", city="A" * (MIN_LOC_CITY_LEN - 1)),
            "city",
        ),
        (
            LocationDTO(country="Germany", city="A" * (MAX_LOC_CITY_LEN + 1)),
            "city",
        ),
        (
            LocationDTO(text="A" * (MIN_LOC_TEXT_LEN - 1)),
            "location",
        ),
        (
            LocationDTO(text="A" * (MAX_LOC_TEXT_LEN + 1)),
            "location",
        ),
    ],
)
def test_validator_location_invariants(location_dto: LocationDTO, expected_reason: str) -> None:
    now = datetime.now(UTC)
    vacancy = build_valid_vacancy(location=location_dto, now=now)
    validator = VacancyValidator()
    result = validator.validate(vacancy, now=now)
    assert not result.is_valid
    assert any(expected_reason in r for r in result.reasons)


@pytest.mark.parametrize(
    ("published_delta", "parsed_delta", "expected_reason_substr"),
    [
        (
            -timedelta(days=7, seconds=10),
            -timedelta(days=1),
            "published_at",
        ),
        (
            timedelta(minutes=6),
            timedelta(minutes=6),
            "published_at",
        ),
        (
            -timedelta(hours=1),
            -timedelta(hours=2),
            "parsed_at",
        ),
        (
            -timedelta(hours=1),
            timedelta(minutes=6),
            "parsed_at",
        ),
    ],
)
def test_validator_date_invariants(
    published_delta: timedelta,
    parsed_delta: timedelta,
    expected_reason_substr: str,
) -> None:
    now = datetime.now(UTC)
    vacancy = build_valid_vacancy(
        published_at=now + published_delta,
        parsed_at=now + parsed_delta,
        now=now,
    )
    validator = VacancyValidator()
    result = validator.validate(vacancy, now=now)
    assert not result.is_valid
    assert any(expected_reason_substr in r for r in result.reasons)


def test_validator_missing_dates() -> None:
    now = datetime.now(UTC)
    vacancy = build_valid_vacancy(now=now)
    vacancy_dict_pub_none = vacancy.model_dump()
    vacancy_dict_pub_none["published_at"] = None

    class MockVacancy:
        def __init__(self, **kwargs: Any) -> None:
            self.__dict__.update(kwargs)

    mock_pub_none = MockVacancy(**vacancy_dict_pub_none)
    validator = VacancyValidator()
    result = validator.validate(mock_pub_none, now=now)
    assert not result.is_valid
    assert any("published_at is required" in r for r in result.reasons)

    vacancy_dict_parsed_none = vacancy.model_dump()
    vacancy_dict_parsed_none["parsed_at"] = None
    mock_parsed_none = MockVacancy(**vacancy_dict_parsed_none)
    result2 = validator.validate(mock_parsed_none, now=now)
    assert not result2.is_valid
    assert any("parsed_at is required" in r for r in result2.reasons)


def test_validator_naive_dates() -> None:
    naive_now = datetime(2026, 11, 8, 12, 0, 0)
    vacancy = build_valid_vacancy(
        published_at=naive_now - timedelta(hours=2),
        parsed_at=naive_now - timedelta(hours=1),
    )
    validator = VacancyValidator()
    result = validator.validate(vacancy, now=naive_now)
    assert result.is_valid
    assert result.reasons == []


@pytest.mark.parametrize(
    ("source", "grade", "employment_types"),
    [
        ("HH", "INTERN", ["REMOTE"]),
        ("Telegram", "Junior", ["Office", "HYBRID"]),
        ("ozon", "middle", ["contract"]),
        ("MTS", "Senior", ["remote", "contract"]),
        ("hh", "Lead", ["hybrid"]),
    ],
)
def test_validator_case_insensitivity(
    source: str,
    grade: str,
    employment_types: list[str],
) -> None:
    now = datetime.now(UTC)
    vacancy = build_valid_vacancy(
        source=source,
        grade=grade,
        employment_types=employment_types,
        now=now,
    )
    validator = VacancyValidator()
    result = validator.validate(vacancy, now=now)
    assert result.is_valid
    assert result.reasons == []


def test_validator_custom_allowed_sources() -> None:
    now = datetime.now(UTC)
    validator = VacancyValidator(allowed_sources={"custom_feed", "linkedin"})

    valid_custom = build_valid_vacancy(source="custom_feed", now=now)
    res1 = validator.validate(valid_custom, now=now)
    assert res1.is_valid

    valid_custom_upper = build_valid_vacancy(source="CUSTOM_FEED", now=now)
    res2 = validator.validate(valid_custom_upper, now=now)
    assert res2.is_valid

    invalid_telegram = build_valid_vacancy(source="telegram", now=now)
    res3 = validator.validate(invalid_telegram, now=now)
    assert not res3.is_valid
    assert any("source 'telegram' is invalid" in r for r in res3.reasons)
    assert any("custom_feed" in r for r in res3.reasons)


def test_validator_default_allowed_sources() -> None:
    validator = VacancyValidator()
    assert validator.allowed_sources == DEFAULT_ALLOWED_SOURCES


@pytest.mark.parametrize(
    "mutate_kwargs",
    [
        {"title": "A" * MIN_TITLE_LEN},
        {"title": "A" * MAX_TITLE_LEN},
        {"company": "A" * MIN_COMPANY_LEN},
        {"company": "A" * MAX_COMPANY_LEN},
        {"description": "A" * MIN_DESCRIPTION_LEN},
        {"description": "A" * MAX_DESCRIPTION_LEN},
        {"url": "https://" + "a" * (MIN_URL_LEN - 8)},
        {"url": "https://" + "a" * (MAX_URL_LEN - 8)},
    ],
)
def test_validator_boundary_lengths(mutate_kwargs: dict[str, Any]) -> None:
    now = datetime.now(UTC)
    vacancy = build_valid_vacancy(now=now, **mutate_kwargs)
    validator = VacancyValidator()
    result = validator.validate(vacancy, now=now)
    assert result.is_valid
    assert result.reasons == []


def test_validator_salary_and_location_boundaries() -> None:
    now = datetime.now(UTC)
    vacancy = build_valid_vacancy(
        salary=make_salary(
            text="A" * MIN_SALARY_LEN,
            from_=MIN_SALARY_VAL,
            to=MAX_SALARY_VAL,
            currency="EUR",
        ),
        location=LocationDTO(
            text="A" * MIN_LOC_TEXT_LEN,
            country="A" * MIN_LOC_COUNTRY_LEN,
            city="A" * MIN_LOC_CITY_LEN,
        ),
        now=now,
    )
    validator = VacancyValidator()
    res = validator.validate(vacancy, now=now)
    assert res.is_valid

    vacancy_max = build_valid_vacancy(
        salary=make_salary(
            text="A" * MAX_SALARY_LEN,
            from_=1000,
            to=1000,
            currency="RUB",
        ),
        location=LocationDTO(
            text="A" * MAX_LOC_TEXT_LEN,
            country="A" * MAX_LOC_COUNTRY_LEN,
            city="A" * MAX_LOC_CITY_LEN,
        ),
        now=now,
    )
    res_max = validator.validate(vacancy_max, now=now)
    assert res_max.is_valid


def test_validator_date_boundaries() -> None:
    now = datetime.now(UTC)
    vacancy_past_exact = build_valid_vacancy(
        published_at=now - VACANCY_VALID_UP_TO,
        parsed_at=now,
        now=now,
    )
    validator = VacancyValidator()
    assert validator.validate(vacancy_past_exact, now=now).is_valid

    vacancy_future_exact = build_valid_vacancy(
        published_at=now + MAX_FUTURE_TIME_SKEW,
        parsed_at=now + MAX_FUTURE_TIME_SKEW,
        now=now,
    )
    assert validator.validate(vacancy_future_exact, now=now).is_valid


def test_validator_invalid_types() -> None:
    now = datetime.now(UTC)

    class MockVacancy:
        def __init__(self) -> None:
            self.external_id = "ext-1"
            self.source = "hh"
            self.title = "Developer"
            self.company = 12345
            self.description = "A" * 350
            self.url = "https://hh.ru/123"
            self.grade = "junior"
            self.employment_types = [123]
            self.salary = MockVacancy.MockSalary()
            self.location = MockVacancy.MockLocation()
            self.published_at = now
            self.parsed_at = now

        class MockSalary:
            text = 123
            from_ = None
            to = None
            currency = None

        class MockLocation:
            text = 123
            country = 123
            city = 123

    mock = MockVacancy()
    validator = VacancyValidator()
    result = validator.validate(mock, now=now)
    assert not result.is_valid
    assert any("company must be a string" in r for r in result.reasons)
    assert any("employment_type '123' is invalid" in r for r in result.reasons)
    assert any("salary text must be a string" in r for r in result.reasons)
    assert any("country must be a string" in r for r in result.reasons)
    assert any("city must be a string" in r for r in result.reasons)
    assert any("location text must be a string" in r for r in result.reasons)
