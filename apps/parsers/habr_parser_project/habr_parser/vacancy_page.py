"""Habr vacancy page -> VacancyPage (the schema.org JobPosting embedded as JSON-LD)."""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from bs4 import BeautifulSoup

from .dates import parse_iso_datetime


class VacancyPageError(ValueError):
    """The page does not hold a usable vacancy (captcha, removed, markup changed...)."""


@dataclass(frozen=True)
class VacancyPage:
    title: str
    description_html: str
    published_at: datetime
    company: str | None = None
    base_salary: Mapping[str, Any] | None = None
    job_location: Any = None
    job_location_type: str | None = None
    employment_type: str | list[str] | None = None


def parse_vacancy_page(html: str) -> VacancyPage:
    posting = _find_job_posting(html)
    if posting is None:
        raise VacancyPageError("no JobPosting JSON-LD found on the page")

    published_at = parse_iso_datetime(posting.get("datePosted"))
    if published_at is None:
        raise VacancyPageError("JobPosting has a missing or unparseable 'datePosted'")

    return VacancyPage(
        title=_required_text(posting, "title"),
        description_html=_required_text(posting, "description"),
        published_at=published_at,
        company=_company_name(posting.get("hiringOrganization")),
        base_salary=posting.get("baseSalary"),
        job_location=posting.get("jobLocation"),
        job_location_type=posting.get("jobLocationType"),
        employment_type=posting.get("employmentType"),
    )


def _find_job_posting(html: str) -> Mapping[str, Any] | None:
    soup = BeautifulSoup(html, "html.parser")
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "", strict=False)
        except json.JSONDecodeError:
            continue
        for node in _iter_nodes(data):
            if _is_job_posting(node):
                return node
    return None


def _iter_nodes(data: Any) -> Iterator[Mapping[str, Any]]:
    if isinstance(data, list):
        for item in data:
            yield from _iter_nodes(item)
    elif isinstance(data, dict):
        yield data
        yield from _iter_nodes(data.get("@graph", []))


def _is_job_posting(node: Mapping[str, Any]) -> bool:
    node_type = node.get("@type")
    return node_type == "JobPosting" or (isinstance(node_type, list) and "JobPosting" in node_type)


def _required_text(posting: Mapping[str, Any], key: str) -> str:
    value = posting.get(key)
    if not isinstance(value, str) or not value.strip():
        raise VacancyPageError(f"JobPosting is missing required field '{key}'")
    return value.strip()


def _company_name(organization: Any) -> str | None:
    name = organization.get("name") if isinstance(organization, Mapping) else organization
    if not isinstance(name, str):
        return None
    return name.strip() or None
