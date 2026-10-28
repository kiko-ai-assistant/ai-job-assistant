import json
from datetime import datetime, timezone
from urllib.parse import urlparse

from exceptions import LayoutChangedError, ParsingError
from models import Vacancy
from hh_selectors import SELECTORS


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.replace("\xa0", " ").replace("\u202f", " ")
    return " ".join(value.split())


def get_element_text(element) -> str | None:
    if not element:
        return None
    return clean_text(
        element.get_all_text(separator=" ", strip=True)
    )


def clean_vacancy_url(url: str | None) -> str | None:
    if not url:
        return None
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"


def extract_external_id(url: str | None) -> str | None:
    if not url:
        return None
    parts = urlparse(url).path.strip("/").split("/")
    if len(parts) >= 2 and parts[0] == "vacancy":
        return parts[1]
    return None


def find_date_posted(data) -> str | None:
    if isinstance(data, dict):
        if isinstance(data.get("datePosted"), str):
            return data["datePosted"]
        for value in data.values():
            result = find_date_posted(value)
            if result:
                return result
    elif isinstance(data, list):
        for item in data:
            result = find_date_posted(item)
            if result:
                return result
    return None


def extract_created_at(page) -> str | None:
    scripts = page.css('script[type="application/ld+json"]::text').getall()
    for script in scripts:
        try:
            data = json.loads(str(script))
        except json.JSONDecodeError:
            continue
        result = find_date_posted(data)
        if result:
            return result
    return None


def parse_search_page(page) -> list[Vacancy]:
    cards = page.css(SELECTORS["search"]["card"])

    if not cards:
        results_container = page.css(SELECTORS["search"]["results"])
        body = page.body.decode("utf-8", errors="ignore").lower()
        no_results_markers = (
            "по вашему запросу ничего не найдено",
            "ничего не найдено",
            "вакансии не найдены",
        )

        if results_container or any(marker in body for marker in no_results_markers):
            return []

        raise LayoutChangedError(
            "Search page has neither vacancy cards nor the expected results container"
        )

    vacancies: list[Vacancy] = []

    for card in cards:
        title_element = card.css(SELECTORS["search"]["title"]).first
        if not title_element:
            continue

        raw_url = title_element.attrib.get("href")
        url = clean_vacancy_url(raw_url)
        external_id = extract_external_id(url)
        if not url or not external_id:
            continue

        employer_element = card.css(SELECTORS["search"]["company"]).first
        salary_element = card.css(SELECTORS["search"]["salary"]).first
        location_element = card.css(SELECTORS["search"]["location"]).first

        vacancies.append(
            Vacancy(
                external_id=external_id,
                source="hh.ru",
                title=get_element_text(title_element),
                company=get_element_text(employer_element),
                salary_text=get_element_text(salary_element),
                location=get_element_text(location_element),
                description=None,
                url=url,
                created_at=None,
                parsed_at=None,
            )
        )

    return vacancies


def enrich_vacancy(vacancy: Vacancy, page) -> Vacancy:
    mapping = SELECTORS["vacancy"]

    title = get_element_text(page.css(mapping["title"]).first)
    company = get_element_text(page.css(mapping["company"]).first)
    salary = get_element_text(page.css(mapping["salary"]).first)
    location = get_element_text(page.css(mapping["location"]).first)
    description = get_element_text(page.css(mapping["description"]).first)

    if description is None:
        raise ParsingError(
            f"Description selector failed for vacancy {vacancy.external_id}"
        )

    vacancy.title = title or vacancy.title
    vacancy.company = company or vacancy.company
    vacancy.salary_text = salary or vacancy.salary_text
    vacancy.location = location or vacancy.location
    vacancy.description = description
    vacancy.created_at = extract_created_at(page)
    vacancy.parsed_at = datetime.now(timezone.utc).isoformat()

    return vacancy
