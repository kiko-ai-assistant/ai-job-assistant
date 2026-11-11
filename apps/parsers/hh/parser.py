import json
import re
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

from exceptions import LayoutChangedError, ParsingError
from hh_selectors import SELECTORS
from models import Vacancy


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.replace("\xa0", " ").replace("\u202f", " ")
    return " ".join(value.split())


def get_element_text(element) -> str | None:
    if not element:
        return None
    return clean_text(element.get_all_text(separator=" ", strip=True))


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


def _job_postings(data: Any) -> Iterator[dict[str, Any]]:
    if isinstance(data, dict):
        types = data.get("@type", [])
        if isinstance(types, str):
            types = [types]
        if isinstance(types, list) and "JobPosting" in types:
            yield data
            return
        for value in data.values():
            yield from _job_postings(value)
    elif isinstance(data, list):
        for item in data:
            yield from _job_postings(item)


def extract_job_posting(page, external_id: str | None = None) -> dict[str, Any]:
    scripts = page.css('script[type="application/ld+json"]::text').getall()
    postings = []
    for script in scripts:
        try:
            data = json.loads(str(script))
        except json.JSONDecodeError:
            continue
        postings.extend(_job_postings(data))
    if external_id is not None:
        matching = []
        for posting in postings:
            identifier = posting.get("identifier")
            if isinstance(identifier, dict):
                identifier = identifier.get("value")
            url = posting.get("url")
            posting_id = extract_external_id(url) if isinstance(url, str) else None
            if str(identifier) == external_id or posting_id == external_id:
                matching.append(posting)
        if matching:
            postings = matching
        elif any("url" in posting or "identifier" in posting for posting in postings):
            return {}
    return postings[0] if len(postings) == 1 else {}


def extract_created_at(page) -> str | None:
    value = extract_job_posting(page).get("datePosted")
    return value if isinstance(value, str) else None


def extract_grade(title: str | None) -> str | None:
    labels = {
        "intern": r"\b(?:intern|стаж[её]р)\b",
        "junior": r"\b(?:junior|джуниор)\b",
        "middle": r"\b(?:middle|мидд?л)\b",
        "senior": r"\b(?:senior|сеньор)\b",
        "lead": r"\blead\b(?!\s+generation\b)",
    }
    matches = [
        grade for grade, pattern in labels.items() if re.search(pattern, title or "", re.IGNORECASE)
    ]
    return matches[0] if len(matches) == 1 else None


def extract_employment_types(page, posting: dict[str, Any]) -> list[str]:
    values = set()
    if posting.get("jobLocationType") == "TELECOMMUTE":
        values.add("remote")
    employment = posting.get("employmentType", [])
    if isinstance(employment, str):
        employment = [employment]
    if isinstance(employment, list) and "CONTRACTOR" in employment:
        values.add("contract")

    labels = {
        "удалённо": "remote",
        "удаленно": "remote",
        "удаленная работа": "remote",
        "удалённая работа": "remote",
        "remote": "remote",
        "на месте работодателя": "office",
        "в офисе": "office",
        "office": "office",
        "гибрид": "hybrid",
        "гибридный формат": "hybrid",
        "hybrid": "hybrid",
        "контракт": "contract",
        "гпх": "contract",
        "contract": "contract",
    }
    mapping = SELECTORS["vacancy"]
    for element in page.css(f"{mapping['work_format']}, {mapping['employment']}"):
        text = (get_element_text(element) or "").lower()
        text = re.sub(r"^(?:формат работы|тип занятости)\s*:\s*", "", text)
        for label in re.split(r"\s+или\s+|[,;/]", text):
            if value := labels.get(label.strip().rstrip(".")):
                values.add(value)
    return sorted(values)


def _structured_fields(vacancy: Vacancy, posting: dict[str, Any]) -> None:
    salary = posting.get("baseSalary")
    if isinstance(salary, dict):
        currency = salary.get("currency")
        value = salary.get("value")
        if isinstance(currency, str):
            vacancy.salary_currency = clean_text(currency)
        if isinstance(value, dict):
            if type(value.get("minValue")) is int:
                vacancy.salary_from = value["minValue"]
            if type(value.get("maxValue")) is int:
                vacancy.salary_to = value["maxValue"]

    location = posting.get("jobLocation")
    if isinstance(location, list):
        location = location[0] if len(location) == 1 else None
    if not isinstance(location, dict):
        return
    address = location.get("address")
    if not isinstance(address, dict):
        return
    country = address.get("addressCountry")
    if isinstance(country, dict):
        country = country.get("name")
    city = address.get("addressLocality")
    if isinstance(country, str):
        vacancy.location_country = clean_text(country)
    if isinstance(city, str):
        vacancy.location_city = clean_text(city)


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
        raise ParsingError(f"Description selector failed for vacancy {vacancy.external_id}")

    vacancy.title = title or vacancy.title
    vacancy.company = company or vacancy.company
    vacancy.salary_text = salary or vacancy.salary_text
    vacancy.location = location or vacancy.location
    vacancy.description = description
    posting = extract_job_posting(page, vacancy.external_id)
    date_posted = posting.get("datePosted")
    vacancy.created_at = date_posted if isinstance(date_posted, str) else None
    vacancy.parsed_at = datetime.now(UTC).isoformat()
    vacancy.grade = extract_grade(vacancy.title)
    vacancy.employment_types = extract_employment_types(page, posting)
    _structured_fields(vacancy, posting)

    return vacancy
