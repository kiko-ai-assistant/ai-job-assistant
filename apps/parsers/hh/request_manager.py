import logging
import random
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from config import RequestConfig
from exceptions import CaptchaDetectedError, SourceBlockedError
from models import HttpStats


def _fetch(url: str, **kwargs):
    from scrapling.fetchers import Fetcher
    return Fetcher.get(url, **kwargs)


class RequestManager:
    def __init__(self, config: RequestConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.stats = HttpStats()
        self._last_request_at: float | None = None

    def _throttle(self) -> None:
        if self._last_request_at is None:
            return

        target_delay = random.uniform(
            self.config.min_delay_seconds,
            self.config.max_delay_seconds,
        )
        elapsed = time.monotonic() - self._last_request_at
        sleep_for = max(0.0, target_delay - elapsed)

        if sleep_for > 0:
            time.sleep(sleep_for)

    @staticmethod
    def _looks_like_captcha(page) -> bool:
        url = str(page.url).lower()

        if any(marker in url for marker in (
            "/captcha",
            "captcha?",
            "account/captcha",
        )):
            return True

        # A real search page with vacancy cards is not a CAPTCHA page.
        try:
            if page.css('[data-qa="vacancy-serp__vacancy"]'):
                return False
        except Exception:
            pass

        body = page.body.decode("utf-8", errors="ignore").lower()
        markers = (
            "подтвердите, что вы не робот",
            "докажите, что вы не робот",
            "проверка безопасности",
            "пройдите проверку",
            "введите код с картинки",
            "verify you are human",
            "robot check",
        )
        return any(marker in body for marker in markers)

    @staticmethod
    def _retry_after_seconds(page) -> float | None:
        value = page.headers.get("retry-after")
        if not value:
            return None

        try:
            return max(0.0, float(value))
        except ValueError:
            pass

        try:
            target = parsedate_to_datetime(value)
            if target.tzinfo is None:
                target = target.replace(tzinfo=timezone.utc)
            return max(
                0.0,
                (target - datetime.now(timezone.utc)).total_seconds(),
            )
        except Exception:
            return None

    def _backoff(self, attempt: int) -> float:
        return min(
            self.config.max_backoff_seconds,
            self.config.backoff_base_seconds * (2 ** attempt),
        )

    def _headers(self) -> dict[str, str] | None:
        if not self.config.user_agent:
            return None
        return {"User-Agent": self.config.user_agent}

    def _count_status(self, status: int) -> None:
        if status == 200:
            self.stats.http_200 += 1
        elif status == 403:
            self.stats.http_403 += 1
        elif status in {404, 410}:
            self.stats.http_404_410 += 1
        elif status == 429:
            self.stats.http_429 += 1
        elif 500 <= status <= 599:
            self.stats.http_5xx += 1
        else:
            self.stats.other_http += 1

    def get(self, url: str):
        for attempt in range(self.config.max_retries + 1):
            self._throttle()

            try:
                page = _fetch(
                    url,
                    timeout=self.config.timeout_seconds,
                    retries=0,
                    headers=self._headers(),
                )
                self.stats.total_requests += 1
                self._count_status(page.status)
            except Exception as exc:
                self.stats.total_requests += 1
                self.stats.network_errors += 1
                self._last_request_at = time.monotonic()

                if attempt >= self.config.max_retries:
                    raise

                self.stats.retries += 1
                delay = self._backoff(attempt)
                self.logger.warning(
                    "Network error for %s: %s; retry in %.1fs",
                    url,
                    exc,
                    delay,
                )
                time.sleep(delay)
                continue

            self._last_request_at = time.monotonic()
            self.logger.info("GET %s -> %s", page.url, page.status)

            if self._looks_like_captcha(page):
                raise CaptchaDetectedError(
                    f"CAPTCHA detected at {page.url}"
                )

            if page.status == 403:
                if attempt >= self.config.max_retries:
                    raise SourceBlockedError(
                        f"Repeated 403 from {page.url}; retry budget exhausted"
                    )

                self.stats.retries += 1
                delay = self._backoff(attempt)
                self.logger.warning(
                    "403 from %s; retry in %.1fs",
                    page.url,
                    delay,
                )
                time.sleep(delay)
                continue

            if page.status == 429:
                if attempt >= self.config.max_retries:
                    raise SourceBlockedError(
                        f"Repeated 429 from {page.url}; retry budget exhausted"
                    )

                self.stats.retries += 1
                delay = self._retry_after_seconds(page)
                if delay is None:
                    delay = self._backoff(attempt)

                self.logger.warning(
                    "429 from %s; retry in %.1fs",
                    page.url,
                    delay,
                )
                time.sleep(delay)
                continue

            if page.status in {500, 502, 503, 504}:
                if attempt >= self.config.max_retries:
                    return page

                self.stats.retries += 1
                delay = self._backoff(attempt)
                self.logger.warning(
                    "HTTP %s from %s; retry in %.1fs",
                    page.status,
                    page.url,
                    delay,
                )
                time.sleep(delay)
                continue

            return page

        raise RuntimeError("Unreachable retry state")
