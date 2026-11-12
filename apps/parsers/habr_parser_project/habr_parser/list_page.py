"""Habr list page -> vacancy ids."""

from __future__ import annotations

import re
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

_VACANCY_PATH = re.compile(r"^/vacancies/(\d+)(?:/|$)")


def extract_vacancy_ids(html: str) -> list[str]:
    """Ids of all vacancies linked from the page, in page order, without duplicates."""
    soup = BeautifulSoup(html, "html.parser")
    ids: dict[str, None] = {}
    for link in soup.find_all("a", href=True):
        match = _VACANCY_PATH.match(urlsplit(link["href"]).path)
        if match:
            ids[match.group(1)] = None
    return list(ids)
