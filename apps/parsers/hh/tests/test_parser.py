from datetime import datetime
from pathlib import Path

import pytest
from scrapling.parser import Selector

from models import Vacancy
from parser import (
    clean_text,
    clean_vacancy_url,
    enrich_vacancy,
    extract_created_at,
    extract_employment_types,
    extract_external_id,
    extract_grade,
    extract_job_posting,
)
from transformer import to_create_vacancy


def test_clean_text_normalizes_spaces():
    value = "от\u202f100\u202f000\xa0₽   за месяц"
    assert clean_text(value) == "от 100 000 ₽ за месяц"


def test_clean_vacancy_url_removes_query():
    url = "https://hh.ru/vacancy/123?query=python&from=search"
    assert clean_vacancy_url(url) == "https://hh.ru/vacancy/123"


def test_extract_external_id():
    assert extract_external_id("https://hh.ru/vacancy/123") == "123"
    assert extract_external_id("https://hh.ru/employer/123") is None


@pytest.fixture
def detail_html():
    return (Path(__file__).parent / "fixtures" / "vacancy.html").read_text(encoding="utf-8")


def test_enriches_saved_html_and_converts_to_contract(detail_html):
    page = Selector(detail_html)
    vacancy = Vacancy(
        external_id="123",
        source="hh.ru",
        title=None,
        company=None,
        salary_text=None,
        location=None,
        description=None,
        url="https://hh.ru/vacancy/123",
        created_at=None,
        parsed_at=None,
    )

    result = enrich_vacancy(vacancy, page)
    dto = to_create_vacancy(result)

    assert dto.title == "Senior Python Developer"
    assert dto.source == "hh"
    assert dto.grade == "SENIOR"
    assert dto.employment_types == ["REMOTE"]
    assert dto.published_at == datetime.fromisoformat("2026-11-11T10:00:00+03:00")
    assert dto.parsed_at.tzinfo is not None
    assert dto.salary.from_ == 150000
    assert dto.salary.to == 200000
    assert dto.salary.currency == "RUB"
    assert dto.salary.gross is None
    assert dto.location.country == "RU"
    assert dto.location.city == "Москва"
    assert "Build and maintain Python services" in dto.description


def test_ignores_unrelated_dates_and_invalid_json(detail_html):
    page = Selector('<script type="application/ld+json">invalid</script>' + detail_html)
    assert extract_created_at(page) == "2026-11-11T10:00:00+03:00"


def test_unrelated_date_is_not_used_as_publication_time():
    page = Selector(
        '<script type="application/ld+json">'
        '{"@type":"WebPage","datePosted":"2026-11-11T10:00:00Z"}'
        "</script>"
    )
    assert extract_created_at(page) is None


def test_does_not_use_another_vacancy_metadata(detail_html):
    assert extract_job_posting(Selector(detail_html), "456") == {}


def test_ambiguous_job_postings_are_not_selected():
    page = Selector(
        '<script type="application/ld+json">'
        '[{"@type":"JobPosting","datePosted":"2026-11-11T10:00:00Z"},'
        '{"@type":"JobPosting","datePosted":"2026-11-10T10:00:00Z"}]'
        "</script>"
    )
    assert extract_job_posting(page) == {}


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("Junior Python Developer", "junior"),
        ("Python developer (Middle)", "middle"),
        ("Senior Engineer", "senior"),
        ("Lead Developer", "lead"),
        ("Intern Developer", "intern"),
        ("Стажёр-разработчик", "intern"),
        ("Senior / Lead Developer", None),
        ("Middle / Senior Developer", None),
        ("Python developer with 6 years of experience", None),
        ("Lead generation specialist", None),
        (None, None),
    ],
)
def test_extracts_only_unambiguous_explicit_grade(title, expected):
    assert extract_grade(title) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Формат работы: удалённо", ["remote"]),
        ("Формат работы: в офисе", ["office"]),
        ("Формат работы: на месте работодателя", ["office"]),
        ("Формат работы: гибрид", ["hybrid"]),
        ("Формат работы: на месте работодателя или удалённо", ["office", "remote"]),
        ("Тип занятости: контракт", ["contract"]),
        ("Полная занятость, полный день", []),
        ("Стажировка", []),
        ("Не удалённо", []),
        ("", []),
    ],
)
def test_extracts_only_explicit_work_format(text, expected):
    page = Selector(f'<div data-qa="work-formats">{text}</div>')
    assert extract_employment_types(page, {}) == expected


def test_does_not_infer_work_format_from_description():
    page = Selector('<div data-qa="vacancy-description">Удалённая работа невозможна</div>')
    assert extract_employment_types(page, {}) == []


@pytest.mark.parametrize(
    ("posting", "expected"),
    [
        ({"jobLocationType": "TELECOMMUTE"}, ["remote"]),
        ({"employmentType": "CONTRACTOR"}, ["contract"]),
        ({"employmentType": ["FULL_TIME", "CONTRACTOR"]}, ["contract"]),
        ({"employmentType": "FULL_TIME"}, []),
        ({"employmentType": "INTERN"}, []),
        ({"employmentType": None}, []),
    ],
)
def test_reads_explicit_job_posting_work_format(posting, expected):
    assert extract_employment_types(Selector("<html></html>"), posting) == expected
