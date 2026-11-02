from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from src.models.vacancy import CreateVacancyRequest, LocationDTO, SalaryDTO
from src.validation.rules import (
    MAX_COMPANY_LEN,
    MAX_DESCRIPTION_LEN,
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
    MIN_TITLE_LEN,
    MIN_URL_LEN,
)
from src.validation.validator import VacancyValidator


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
        "salary": SalaryDTO(
            text="от 2000 до 3000 USD",
            from_=2000,
            to=3000,
            currency="USD",
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
            SalaryDTO(from_=5000, to=3000, currency="USD"),
            "salary_from cannot be greater than salary_to",
        ),
        (
            SalaryDTO(from_=2000, to=None, currency=None),
            "currency is required when salary bounds are specified",
        ),
        (
            SalaryDTO(from_=None, to=4000, currency=None),
            "currency is required when salary bounds are specified",
        ),
        (
            SalaryDTO(from_=None, to=None, currency="USD"),
            "currency cannot be specified without salary bounds",
        ),
        (
            SalaryDTO(from_=1000, to=2000, currency="US"),
            "currency",
        ),
        (
            SalaryDTO(from_=1000, to=2000, currency="USDD"),
            "currency",
        ),
        (
            SalaryDTO(from_=-1, to=2000, currency="USD"),
            "salary_from",
        ),
        (
            SalaryDTO(from_=MAX_SALARY_VAL + 1, to=None, currency="USD"),
            "salary_from",
        ),
        (
            SalaryDTO(from_=None, to=-1, currency="USD"),
            "salary_to",
        ),
        (
            SalaryDTO(from_=None, to=MAX_SALARY_VAL + 1, currency="USD"),
            "salary_to",
        ),
        (
            SalaryDTO(text="A" * (MIN_SALARY_LEN - 1)),
            "salary",
        ),
        (
            SalaryDTO(text="A" * (MAX_SALARY_LEN + 1)),
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
