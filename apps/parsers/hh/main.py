import argparse
import asyncio
import json
import logging
from dataclasses import replace
from pathlib import Path

from parsers_base import BackendApiSink, SinkError

from alerts import Alerter
from backend_client import HHBackendParser
from config import CONFIG, AppConfig, BackendConfig
from json_storage import JsonVacancyStorage
from logging_setup import setup_logging
from request_manager import RequestManager
from scraper import HHScraper
from unavailable_registry import UnavailableRegistry


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="HH vacancy scraper")
    parser.add_argument(
        "--groups",
        nargs="+",
        choices=("it", "management", "marketing"),
        default=None,
        help="Search groups to run",
    )
    parser.add_argument("--area", default=None, help="HH area id")
    parser.add_argument(
        "--employment",
        choices=("full", "part", "project", "volunteer", "probation"),
        default=None,
    )
    parser.add_argument("--pages", type=int, default=None)
    parser.add_argument("--refresh-hours", type=float, default=None)
    parser.add_argument("--output", default=None)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--send-only",
        action="store_true",
        help="Send pending JSON records without contacting HH",
    )
    mode.add_argument(
        "--scrape-only",
        action="store_true",
        help="Collect vacancies into JSON without contacting the backend",
    )
    args = parser.parse_args(argv)
    if args.pages is not None and args.pages <= 0:
        parser.error("--pages must be positive")
    if args.refresh_hours is not None and not (0 <= args.refresh_hours < float("inf")):
        parser.error("--refresh-hours must be finite and nonnegative")
    return args


def build_config(args: argparse.Namespace) -> AppConfig:
    search = CONFIG.search
    storage = CONFIG.storage

    if args.groups is not None:
        search = replace(search, enabled_groups=tuple(args.groups))
    if args.area is not None:
        search = replace(search, area=args.area)
    if args.employment is not None:
        search = replace(search, employment=args.employment)
    if args.pages is not None:
        search = replace(search, pages_override=args.pages)
    if args.refresh_hours is not None:
        storage = replace(storage, refresh_after_hours=args.refresh_hours)
    if args.output is not None:
        storage = replace(storage, path=args.output)

    return replace(CONFIG, search=search, storage=storage)


def collect(config: AppConfig, storage: JsonVacancyStorage, logger: logging.Logger) -> bool:
    alerter = Alerter(config.alerts, logger)
    unavailable = UnavailableRegistry(config.storage.unavailable_path)
    request_manager = RequestManager(config.request, logger)

    scraper = HHScraper(
        config,
        request_manager,
        storage,
        unavailable,
        alerter,
        logger,
    )

    stats = scraper.run()

    logger.info(
        "Run stats: %s",
        json.dumps(stats.to_dict(), ensure_ascii=False),
    )
    logger.info(
        "HTTP stats: %s",
        json.dumps(request_manager.stats.to_dict(), ensure_ascii=False),
    )
    logger.info("Total vacancies in JSON: %s", storage.count())
    return not any(
        (stats.captcha, stats.blocked, stats.layout_errors, stats.mass_failure, stats.failed)
    )


async def send_pending(
    storage: JsonVacancyStorage,
    backend: BackendConfig,
    logger: logging.Logger,
) -> bool:
    async with BackendApiSink(
        backend_url=backend.base_url,
        parser_api_key=backend.api_key,
        timeout=backend.timeout_seconds,
    ) as sink:
        parser = HHBackendParser(storage, sink, batch_size=backend.batch_size)
        stats = await parser.run()
    logger.info(
        "Delivery stats: extracted=%s valid=%s invalid=%s "
        "conversion_errors=%s inserted=%s ignored=%s",
        stats.extracted,
        stats.valid,
        stats.invalid,
        parser.conversion_errors,
        stats.inserted,
        stats.ignored,
    )
    logger.info("Pending records in JSON: %s", len(storage.pending()))
    return stats.invalid == 0 and parser.conversion_errors == 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logger = setup_logging()
    try:
        config = build_config(args)
        backend = None if args.scrape_only else BackendConfig.from_env()
        if args.send_only and not Path(config.storage.path).is_file():
            raise ValueError("Pending JSON file does not exist; check --output")
        storage = JsonVacancyStorage(
            config.storage.path,
            config.storage.refresh_after_hours,
            logger,
        )
        collected = True if args.send_only else collect(config, storage, logger)
        delivered = True if backend is None else asyncio.run(send_pending(storage, backend, logger))
        return 0 if collected and delivered else 2
    except (SinkError, ValueError, OSError) as exc:
        logger.error("Run failed; pending records remain in JSON: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
