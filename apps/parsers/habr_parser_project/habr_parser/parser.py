"""HabrParser: the BaseParser implementation that wires the other modules together."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator, Callable, Iterable
from datetime import UTC, datetime

from parsers_base.models.vacancy import CreateVacancyRequest
from parsers_base.parser.base import BaseParser
from parsers_base.sink.base import BaseSink
from parsers_base.validation.validator import VacancyValidator

from .config import BASE_URL
from .filters import SearchFilters
from .grade import Grade
from .http_client import FetchError, HtmlFetcher
from .list_page import extract_vacancy_ids
from .mapper import to_create_request
from .vacancy_page import VacancyPageError, parse_vacancy_page

logger = logging.getLogger(__name__)

LIST_PATH = "/vacancies"
DEFAULT_MAX_PAGES = 5


def _utc_now() -> datetime:
    return datetime.now(UTC)


class HabrParser(BaseParser):
    """Walks Habr's vacancy lists grade by grade and yields contract-shaped vacancies.

    The grade of a vacancy is the grade of the `qid` query that found it; a vacancy
    listed under several grades is fetched once and keeps the first one.
    """

    def __init__(
        self,
        sink: BaseSink,
        fetcher: HtmlFetcher,
        validator: VacancyValidator | None = None,
        batch_size: int = 50,
        clock: Callable[[], datetime] = _utc_now,
    ) -> None:
        super().__init__(sink, validator, batch_size)
        self._fetcher = fetcher
        self._clock = clock

    async def parse(  # type: ignore[override]
        self,
        *,
        filters: SearchFilters | None = None,
        grades: Iterable[Grade] = tuple(Grade),
        max_pages: int = DEFAULT_MAX_PAGES,
    ) -> AsyncIterator[CreateVacancyRequest]:
        filters = filters or SearchFilters()
        seen_ids: set[str] = set()
        for grade in grades:
            async for ids in self._iter_id_pages(filters, grade, max_pages, seen_ids):
                loaded = await asyncio.gather(*(self._load_vacancy(i, grade) for i in ids))
                for vacancy in loaded:
                    if vacancy is not None:
                        yield vacancy

    async def _iter_id_pages(
        self,
        filters: SearchFilters,
        grade: Grade,
        max_pages: int,
        seen_ids: set[str],
    ) -> AsyncIterator[list[str]]:
        """Yield the not yet seen vacancy ids of every list page, until the results end."""
        for page in range(1, max_pages + 1):
            try:
                html = await self._fetcher.get_text(LIST_PATH, filters.to_params(grade, page))
            except FetchError as exc:
                logger.warning("Stopping %s search on page %d: %s", grade, page, exc)
                return
            ids = extract_vacancy_ids(html)
            if page == 1 and not ids:
                logger.warning("No vacancies found for %s on the first page", grade)
            new_ids = [vacancy_id for vacancy_id in ids if vacancy_id not in seen_ids]
            if not new_ids:
                return
            seen_ids.update(new_ids)
            yield new_ids

    async def _load_vacancy(self, vacancy_id: str, grade: Grade) -> CreateVacancyRequest | None:
        path = f"{LIST_PATH}/{vacancy_id}"
        try:
            page = parse_vacancy_page(await self._fetcher.get_text(path))
        except (FetchError, VacancyPageError) as exc:
            logger.warning("Skipping vacancy %s: %s", vacancy_id, exc)
            return None
        return to_create_request(
            page,
            vacancy_id=vacancy_id,
            grade=grade,
            url=f"{BASE_URL}{path}",
            parsed_at=self._clock(),
        )
