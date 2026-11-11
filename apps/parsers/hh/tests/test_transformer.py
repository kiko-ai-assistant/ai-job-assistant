from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from parsers_base import VacancyValidator

from models import Vacancy
from transformer import to_create_vacancy


@pytest.fixture
def vacancy():
    now = datetime.now(UTC)
    return Vacancy(
        external_id="123",
        source="hh.ru",
        title="Senior Python Developer",
        company="Example Company",
        salary_text="от 150 000 до 200 000 ₽ за месяц",
        location="Москва",
        description="Build and maintain reliable Python services for our customers. " * 6,
        url="https://hh.ru/vacancy/123",
        created_at=(now - timedelta(hours=1)).isoformat(),
        parsed_at=now.isoformat(),
        grade="senior",
        employment_types=["remote"],
    )


def test_maps_contract_fields_without_inventing_optional_data(vacancy):
    dto = to_create_vacancy(vacancy)

    assert dto.external_id == "123"
    assert dto.source == "hh"
    assert dto.title == vacancy.title
    assert dto.company == vacancy.company
    assert dto.grade == "SENIOR"
    assert dto.employment_types == ["REMOTE"]
    assert dto.published_at == datetime.fromisoformat(vacancy.created_at)
    assert dto.parsed_at == datetime.fromisoformat(vacancy.parsed_at)
    assert dto.salary is None
    assert dto.location is None
    assert VacancyValidator(allowed_sources={"hh"}).validate(dto).is_valid
    assert vacancy.salary_text == "от 150 000 до 200 000 ₽ за месяц"
    assert vacancy.location == "Москва"


def test_maps_complete_salary_and_location(vacancy):
    vacancy = replace(
        vacancy,
        salary_from=150000,
        salary_to=200000,
        salary_currency="RUB",
        location_country="RU",
        location_city="Москва",
    )
    dto = to_create_vacancy(vacancy)

    assert dto.salary.model_dump(by_alias=True, exclude_none=True) == {
        "text": vacancy.salary_text,
        "from": 150000,
        "to": 200000,
        "currency": "RUB",
    }
    assert dto.location.model_dump() == {
        "text": "Москва",
        "country": "RU",
        "city": "Москва",
    }
    assert VacancyValidator().validate(dto).is_valid


@pytest.mark.parametrize(
    "changes",
    [
        {"salary_text": None},
        {"salary_text": "  "},
        {"salary_from": 150000, "salary_currency": "RUB"},
        {"salary_to": 200000, "salary_currency": "RUB"},
        {"salary_from": 150000, "salary_to": 200000},
        {"salary_from": False, "salary_to": 200000, "salary_currency": "RUB"},
    ],
)
def test_incomplete_salary_is_omitted(vacancy, changes):
    assert to_create_vacancy(replace(vacancy, **changes)).salary is None


@pytest.mark.parametrize(
    "changes",
    [
        {"location": None},
        {"location_city": "Москва"},
        {"location_country": "RU"},
        {"location_country": " ", "location_city": "Москва"},
    ],
)
def test_incomplete_location_is_omitted(vacancy, changes):
    assert to_create_vacancy(replace(vacancy, **changes)).location is None


@pytest.mark.parametrize("grade", ["intern", "junior", "middle", "senior", "lead"])
def test_preserves_explicit_grade_in_contract_case(vacancy, grade):
    assert to_create_vacancy(replace(vacancy, grade=grade)).grade == grade.upper()


def test_normalizes_and_deduplicates_explicit_employment_types(vacancy):
    vacancy.employment_types = ["remote", "REMOTE", "office", "hybrid", "contract"]
    assert to_create_vacancy(vacancy).employment_types == [
        "REMOTE",
        "OFFICE",
        "HYBRID",
        "CONTRACT",
    ]


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("source", "telegram", "source"),
        ("external_id", "", "external_id"),
        ("title", None, "title"),
        ("description", " ", "description"),
        ("url", "", "url"),
        ("grade", None, "grade"),
        ("grade", "unknown", "grade"),
        ("employment_types", [], "employment_types"),
        ("employment_types", ["full"], "employment_types"),
        ("created_at", None, "published_at"),
        ("created_at", "2026-11-11", "published_at"),
        ("created_at", "2026-11-11T10:00:00", "published_at"),
        ("created_at", "not-a-date", "published_at"),
        ("parsed_at", None, "parsed_at"),
        ("parsed_at", "2026-11-11T10:00:00", "parsed_at"),
    ],
)
def test_rejects_missing_or_unsupported_required_data(vacancy, field, value, message):
    with pytest.raises(ValueError, match=message):
        to_create_vacancy(replace(vacancy, **{field: value}))


def test_preserves_published_timezone_and_accepts_normalized_source(vacancy):
    vacancy.source = "hh"
    vacancy.created_at = "2026-11-11T10:00:00+03:00"
    assert to_create_vacancy(vacancy).published_at.isoformat() == vacancy.created_at


def test_keeps_long_description_for_shared_validator(vacancy):
    vacancy.description = "x" * 2501
    dto = to_create_vacancy(vacancy)
    assert dto.description == vacancy.description
    assert not VacancyValidator().validate(dto).is_valid


def test_keeps_invalid_complete_salary_for_shared_validator(vacancy):
    vacancy.salary_from = 200000
    vacancy.salary_to = 100000
    vacancy.salary_currency = "RUB"
    dto = to_create_vacancy(vacancy)
    assert dto.salary.from_ == 200000
    assert not VacancyValidator().validate(dto).is_valid
