"""Composition root: `python -m habr_parser`."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from collections.abc import Sequence
from dataclasses import asdict

from parsers_base.sink.backend_api import BackendApiSink
from parsers_base.validation.validator import VacancyValidator

from .cli import RunOptions, parse_cli
from .config import SOURCE_NAME
from .http_client import HabrHttpClient
from .parser import HabrParser


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"environment variable {name} is not set")
    return value


async def run(options: RunOptions, backend_url: str, api_key: str) -> dict[str, int]:
    async with BackendApiSink(backend_url, api_key) as sink, HabrHttpClient(options.http) as http:
        parser = HabrParser(
            sink,
            http,
            validator=VacancyValidator(allowed_sources={SOURCE_NAME}),
            batch_size=options.batch_size,
        )
        stats = await parser.run(
            filters=options.filters, grades=options.grades, max_pages=options.max_pages
        )
    return asdict(stats)


def main(argv: Sequence[str] | None = None) -> int:
    options = parse_cli(argv)
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    stats = asyncio.run(run(options, _require_env("BACKEND_URL"), _require_env("PARSER_API_KEY")))
    print(json.dumps(stats))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
