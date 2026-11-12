from datetime import UTC, datetime

from habr_parser.config import SOURCE_NAME
from habr_parser.grade import Grade
from habr_parser.mapper import to_create_request
from habr_parser.vacancy_page import parse_vacancy_page
from parsers_base.validation.rules import MAX_DESCRIPTION_LEN
from parsers_base.validation.validator import VacancyValidator
from tests.builders import SENTENCE, make_vacancy_html

URL = "https://career.habr.com/vacancies/1000123"


def map_page(grade=Grade.MIDDLE, **overrides):
    page = parse_vacancy_page(make_vacancy_html(**overrides))
    return to_create_request(
        page,
        vacancy_id="1000123",
        grade=grade,
        url=URL,
        parsed_at=datetime.now(UTC),
    )


def test_all_contract_fields_are_filled():
    vacancy = map_page(datePosted="2026-11-10T09:15:00+03:00")

    assert vacancy.external_id == "1000123"
    assert vacancy.source == SOURCE_NAME == "habr"
    assert vacancy.title == "Python-разработчик"
    assert vacancy.company == "Acme"
    assert vacancy.grade == "MIDDLE"
    assert vacancy.employment_types == ["REMOTE"]
    assert vacancy.url == URL
    assert vacancy.published_at == datetime(2026, 11, 10, 6, 15, tzinfo=UTC)
    assert (vacancy.salary.from_, vacancy.salary.to, vacancy.salary.currency) == (
        200_000,
        300_000,
        "RUB",
    )
    assert (vacancy.location.city, vacancy.location.country) == ("Москва", "RU")
    assert vacancy.description.startswith("Обязанности:\n• Писать код")
    assert "Требования:" in vacancy.description


def test_a_typical_vacancy_passes_the_shared_validator():
    result = VacancyValidator(allowed_sources={SOURCE_NAME}).validate(map_page())

    assert result.is_valid, result.reasons


def test_description_is_truncated_to_the_contract_limit():
    vacancy = map_page(description=f"<p>{SENTENCE * 100}</p>")

    assert len(vacancy.description) <= MAX_DESCRIPTION_LEN


def test_missing_optional_blocks_stay_empty():
    vacancy = map_page(
        hiringOrganization=None, baseSalary=None, jobLocation=None, jobLocationType=None
    )

    assert vacancy.company is None
    assert vacancy.salary is None
    assert vacancy.location is None
    assert vacancy.employment_types == ["OFFICE"]


def test_grade_is_taken_from_the_argument():
    assert map_page(grade=Grade.LEAD).grade == "LEAD"
