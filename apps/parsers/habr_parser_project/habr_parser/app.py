"""Use case: run the Habr parser with the given options, sink and fetcher."""

from __future__ import annotations

from parsers_base.parser.stats import ParserStats
from parsers_base.sink.base import BaseSink
from parsers_base.validation.validator import VacancyValidator

from .cli.cli import RunOptions
from .config import SOURCE_NAME
from .transport.http_client import HtmlFetcher
from .parser import HabrParser


async def run_app(
    options: RunOptions, sink: BaseSink, fetcher: HtmlFetcher
) -> ParserStats:
    parser = HabrParser(
        sink,
        fetcher,
        validator=VacancyValidator(allowed_sources={SOURCE_NAME}),
        batch_size=options.batch_size,
    )
    return await parser.run(
        filters=options.filters,
        grades=options.grades,
        max_pages=options.max_pages,
    )
