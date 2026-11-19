"""Composition root: `python -m habr_parser`.

stdout carries data only (vacancies in --dry-run mode); logs and the final stats go to stderr.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from collections.abc import Sequence
from dataclasses import asdict

from parsers_base.sink.backend_api import BackendApiSink
from parsers_base.sink.base import BaseSink

from ..app import run_app
from .cli import RunOptions, parse_cli
from ..transport.http_client import HabrHttpClient
from ..sinks.jsonl_sink import JsonlSink
from ..outcome import exit_code_for


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"environment variable {name} is not set")
    return value


def _build_sink(options: RunOptions) -> BaseSink:
    if options.dry_run:
        return JsonlSink(sys.stdout)
    return BackendApiSink(_require_env("BACKEND_URL"), _require_env("PARSER_API_KEY"))


async def _run(options: RunOptions) -> int:
    sink = _build_sink(options)
    try:
        async with HabrHttpClient(options.http) as fetcher:
            stats = await run_app(options, sink, fetcher)
    finally:
        await sink.close()
    print(json.dumps(asdict(stats)), file=sys.stderr)
    return exit_code_for(stats)


def main(argv: Sequence[str] | None = None) -> int:
    options = parse_cli(argv)
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    return asyncio.run(_run(options))


if __name__ == "__main__":
    raise SystemExit(main())
