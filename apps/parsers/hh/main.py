import argparse
import json
from dataclasses import replace

from alerts import Alerter
from config import CONFIG
from json_storage import JsonVacancyStorage
from logging_setup import setup_logging
from request_manager import RequestManager
from scraper import HHScraper
from unavailable_registry import UnavailableRegistry


def parse_args() -> argparse.Namespace:
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
    return parser.parse_args()


def build_config(args: argparse.Namespace):
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


def main() -> None:
    args = parse_args()
    config = build_config(args)
    logger = setup_logging()

    alerter = Alerter(config.alerts, logger)
    storage = JsonVacancyStorage(
        config.storage.path,
        config.storage.refresh_after_hours,
        logger,
    )
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


if __name__ == "__main__":
    main()
