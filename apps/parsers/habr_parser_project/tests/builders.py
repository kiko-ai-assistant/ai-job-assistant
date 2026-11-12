"""Builders for synthetic Habr pages. Each test overrides only what it cares about.

NOTE: these pages follow the schema.org JobPosting shape the parser expects;
they are NOT copies of real Habr HTML.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

SENTENCE = "Мы ищем разработчика для работы над высоконагруженным сервисом. "
DESCRIPTION_HTML = (
    "<p>Обязанности:</p><ul><li>Писать код</li></ul>"
    "<p>Требования:</p><ul><li>Python</li></ul>"
    f"<p>{SENTENCE * 6}</p>"
)


def recent_iso(hours_ago: int = 2) -> str:
    return (datetime.now(UTC) - timedelta(hours=hours_ago)).isoformat()


def make_job_posting(**overrides: Any) -> dict[str, Any]:
    """A valid JobPosting. Pass `key=None` to remove a key."""
    posting: dict[str, Any] = {
        "@context": "https://schema.org/",
        "@type": "JobPosting",
        "title": "Python-разработчик",
        "datePosted": recent_iso(),
        "description": DESCRIPTION_HTML,
        "hiringOrganization": {"@type": "Organization", "name": "Acme"},
        "jobLocationType": "TELECOMMUTE",
        "employmentType": "FULL_TIME",
        "baseSalary": {
            "@type": "MonetaryAmount",
            "currency": "RUR",
            "value": {
                "@type": "QuantitativeValue",
                "minValue": 200000,
                "maxValue": 300000,
                "unitText": "MONTH",
            },
        },
        "jobLocation": {
            "@type": "Place",
            "address": {
                "@type": "PostalAddress",
                "addressLocality": "Москва",
                "addressCountry": "RU",
            },
        },
    }
    posting.update(overrides)
    return {key: value for key, value in posting.items() if value is not None}


def ld_script(payload: Any) -> str:
    body = json.dumps(payload, ensure_ascii=False)
    return f'<script type="application/ld+json">{body}</script>'


def page_with_scripts(*scripts: str) -> str:
    return f"<html><head>{''.join(scripts)}</head><body><h1>Vacancy</h1></body></html>"


def make_vacancy_html(**overrides: Any) -> str:
    return page_with_scripts(ld_script(make_job_posting(**overrides)))


def make_list_html(ids: list[int | str]) -> str:
    cards = "".join(
        f'<div class="vacancy-card"><a class="vacancy-card__title-link" '
        f'href="/vacancies/{vacancy_id}">Vacancy {vacancy_id}</a></div>'
        for vacancy_id in ids
    )
    return f'<html><body><a href="/vacancies?page=2">next</a>{cards}</body></html>'
