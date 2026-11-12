"""Command line options."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import dataclass

from .config import HttpConfig
from .filters import SearchFilters
from .grade import Grade
from .parser import DEFAULT_MAX_PAGES


@dataclass(frozen=True)
class RunOptions:
    filters: SearchFilters
    grades: tuple[Grade, ...]
    max_pages: int
    batch_size: int
    http: HttpConfig


def _grade(value: str) -> Grade:
    return Grade(value.upper())


def parse_cli(argv: Sequence[str] | None = None) -> RunOptions:
    parser = argparse.ArgumentParser(
        prog="habr_parser",
        description="Parse Habr Career vacancies and send them to the Kiko backend.",
        epilog="Environment: BACKEND_URL, PARSER_API_KEY.",
    )
    parser.add_argument("--query", help="free-text search (q)")
    parser.add_argument("--min-salary", type=int, help="minimum salary (salary)")
    parser.add_argument("--skill", type=int, action="append", default=[], help="skill id (skill[])")
    parser.add_argument(
        "--location", type=int, action="append", default=[], help="location id (location_id[])"
    )
    parser.add_argument(
        "--grade",
        type=_grade,
        action="append",
        default=[],
        metavar="{" + ",".join(g.lower() for g in Grade) + "}",
        help="grade to search (repeatable); default: all",
    )
    parser.add_argument(
        "--max-pages", type=int, default=DEFAULT_MAX_PAGES, help="list pages per grade"
    )
    parser.add_argument("--batch-size", type=int, default=50, help="vacancies per backend request")
    parser.add_argument(
        "--delay", type=float, default=HttpConfig().request_delay, help="seconds between requests"
    )
    args = parser.parse_args(argv)

    return RunOptions(
        filters=SearchFilters(
            query=args.query,
            min_salary=args.min_salary,
            skill_ids=tuple(args.skill),
            location_ids=tuple(args.location),
        ),
        grades=tuple(args.grade) or tuple(Grade),
        max_pages=args.max_pages,
        batch_size=args.batch_size,
        http=HttpConfig(request_delay=args.delay),
    )
