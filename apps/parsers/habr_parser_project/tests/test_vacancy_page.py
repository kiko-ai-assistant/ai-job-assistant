from datetime import UTC, datetime

import pytest

from habr_parser.vacancy_page import VacancyPageError, parse_vacancy_page
from tests.builders import ld_script, make_job_posting, make_vacancy_html, page_with_scripts


def test_job_posting_fields_are_extracted():
    page = parse_vacancy_page(make_vacancy_html(datePosted="2026-11-10T09:15:00+03:00"))

    assert page.title == "Python-разработчик"
    assert page.company == "Acme"
    assert page.published_at == datetime(2026, 11, 10, 6, 15, tzinfo=UTC)
    assert page.job_location_type == "TELECOMMUTE"
    assert page.employment_type == "FULL_TIME"
    assert page.base_salary["currency"] == "RUR"
    assert page.job_location["address"]["addressLocality"] == "Москва"
    assert "Писать код" in page.description_html


def test_optional_fields_may_be_absent():
    page = parse_vacancy_page(
        make_vacancy_html(hiringOrganization=None, baseSalary=None, jobLocation=None)
    )

    assert page.company is None
    assert page.base_salary is None
    assert page.job_location is None


def test_unrelated_json_ld_blocks_are_skipped():
    organisation = ld_script({"@type": "Organization", "name": "Habr"})
    broken = '<script type="application/ld+json">{not json</script>'
    html = page_with_scripts(organisation, broken, ld_script(make_job_posting()))

    assert parse_vacancy_page(html).title == "Python-разработчик"


@pytest.mark.parametrize("wrap", [lambda p: [p], lambda p: {"@graph": [{"@type": "WebPage"}, p]}])
def test_job_posting_is_found_in_lists_and_graphs(wrap):
    html = page_with_scripts(ld_script(wrap(make_job_posting())))

    assert parse_vacancy_page(html).company == "Acme"


def test_raw_control_characters_inside_json_strings_are_tolerated():
    script = (
        '<script type="application/ld+json">'
        '{"@type":"JobPosting","title":"Dev\nops","description":"<p>text</p>",'
        '"datePosted":"2026-11-10"}</script>'
    )

    assert parse_vacancy_page(page_with_scripts(script)).title == "Dev\nops"


def test_page_without_job_posting_is_rejected():
    with pytest.raises(VacancyPageError, match="JobPosting"):
        parse_vacancy_page("<html><body>captcha</body></html>")


@pytest.mark.parametrize("missing", ["title", "description", "datePosted"])
def test_required_fields_must_be_present(missing):
    with pytest.raises(VacancyPageError, match=missing):
        parse_vacancy_page(make_vacancy_html(**{missing: None}))


def test_unparseable_publication_date_is_rejected():
    with pytest.raises(VacancyPageError, match="datePosted"):
        parse_vacancy_page(make_vacancy_html(datePosted="yesterday"))
