import logging

from alerts import Alerter
from config import AppConfig
from exceptions import (
    CaptchaDetectedError,
    LayoutChangedError,
    MassFailureError,
    ParsingError,
    SourceBlockedError,
)
from json_storage import JsonVacancyStorage
from models import RunStats
from parser import enrich_vacancy, parse_search_page
from request_manager import RequestManager
from roles import enabled_targets
from search_urls import build_search_url
from unavailable_registry import UnavailableRegistry


class HHScraper:
    def __init__(
        self,
        config: AppConfig,
        request_manager: RequestManager,
        storage: JsonVacancyStorage,
        unavailable: UnavailableRegistry,
        alerter: Alerter,
        logger: logging.Logger,
    ):
        self.config = config
        self.requests = request_manager
        self.storage = storage
        self.unavailable = unavailable
        self.alerter = alerter
        self.logger = logger
        self._detail_attempts = 0
        self._detail_failures = 0
        self._consecutive_detail_errors = 0

    def _check_mass_failures(self, stats: RunStats) -> None:
        policy = self.config.failures

        if self._consecutive_detail_errors >= policy.max_consecutive_detail_errors:
            raise MassFailureError(
                f"{self._consecutive_detail_errors} consecutive detail-page errors"
            )

        if self._detail_attempts >= policy.min_detail_samples_for_rate:
            rate = self._detail_failures / self._detail_attempts
            if rate >= policy.max_detail_error_rate:
                raise MassFailureError(
                    f"Detail-page error rate is {rate:.1%} "
                    f"({self._detail_failures}/{self._detail_attempts})"
                )

    def _register_detail_failure(self, stats: RunStats) -> None:
        stats.failed += 1
        self._detail_failures += 1
        self._consecutive_detail_errors += 1
        self._check_mass_failures(stats)

    def _register_detail_success(self) -> None:
        self._consecutive_detail_errors = 0

    def run(self) -> RunStats:
        stats = RunStats()
        seen: set[tuple[str, str]] = set()

        try:
            targets = enabled_targets(self.config.search.enabled_groups)

            for target in targets:
                stats.targets_started += 1
                max_pages = self.config.search.pages_override or target.max_pages
                self.logger.info(
                    "Starting target %s (%s), max_pages=%s",
                    target.name,
                    target.group,
                    max_pages,
                )

                for page_number in range(max_pages):
                    stats.pages_requested += 1
                    url = build_search_url(
                        self.config.hh_base_url,
                        target,
                        page_number,
                        self.config.search,
                    )

                    page = self.requests.get(url)

                    if page.status != 200:
                        self.logger.error(
                            "Search target %s page %s returned HTTP %s",
                            target.name,
                            page_number,
                            page.status,
                        )
                        break

                    cards = parse_search_page(page)
                    stats.cards_found += len(cards)

                    if not cards:
                        self.logger.info(
                            "No cards for target %s on page %s; target finished",
                            target.name,
                            page_number,
                        )
                        break

                    self.logger.info(
                        "Found %s cards for %s page %s",
                        len(cards),
                        target.name,
                        page_number,
                    )

                    for vacancy in cards:
                        if vacancy.key in seen:
                            stats.duplicates_skipped += 1
                            continue
                        seen.add(vacancy.key)

                        existed = self.storage.contains(
                            vacancy.source,
                            vacancy.external_id,
                        )

                        if existed and not self.storage.should_refresh(
                            vacancy.source,
                            vacancy.external_id,
                        ):
                            stats.fresh_skipped += 1
                            continue

                        self._detail_attempts += 1

                        try:
                            detail_page = self.requests.get(vacancy.url)

                            if detail_page.status in {404, 410}:
                                stats.unavailable += 1
                                self.unavailable.mark(
                                    vacancy.source,
                                    vacancy.external_id,
                                    vacancy.url,
                                    detail_page.status,
                                )
                                self.unavailable.flush()
                                self._register_detail_success()
                                continue

                            if detail_page.status != 200:
                                self.logger.warning(
                                    "Vacancy %s returned HTTP %s",
                                    vacancy.external_id,
                                    detail_page.status,
                                )
                                self._register_detail_failure(stats)
                                continue

                            vacancy = enrich_vacancy(vacancy, detail_page)
                            self.storage.upsert(vacancy)
                            self.storage.flush()

                            if existed:
                                stats.refreshed += 1
                            else:
                                stats.parsed += 1

                            self._register_detail_success()

                            self.logger.info(
                                "Stored vacancy %s | %s",
                                vacancy.external_id,
                                vacancy.title,
                            )

                        except ParsingError:
                            self.logger.exception(
                                "Parsing failed for vacancy %s",
                                vacancy.external_id,
                            )
                            self._register_detail_failure(stats)

        except CaptchaDetectedError as exc:
            stats.captcha += 1
            self.alerter.send(
                "captcha",
                str(exc),
                context=stats.to_dict(),
            )

        except SourceBlockedError as exc:
            stats.blocked += 1
            self.alerter.send(
                "source_blocked",
                str(exc),
                context={
                    **stats.to_dict(),
                    **self.requests.stats.to_dict(),
                },
            )

        except LayoutChangedError as exc:
            stats.layout_errors += 1
            self.alerter.send(
                "layout_changed",
                str(exc),
                context=stats.to_dict(),
            )

        except MassFailureError as exc:
            stats.mass_failure += 1
            self.alerter.send(
                "mass_failure",
                str(exc),
                context={
                    **stats.to_dict(),
                    **self.requests.stats.to_dict(),
                },
            )

        finally:
            self.storage.flush()
            self.unavailable.flush()

        return stats
