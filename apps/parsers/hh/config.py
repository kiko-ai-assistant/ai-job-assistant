from dataclasses import dataclass, field
import os


@dataclass(frozen=True)
class RequestConfig:
    timeout_seconds: float = 20.0
    min_delay_seconds: float = 1.5
    max_delay_seconds: float = 3.5
    max_retries: int = 3
    backoff_base_seconds: float = 2.0
    max_backoff_seconds: float = 60.0
    user_agent: str | None = os.getenv("HH_SCRAPER_USER_AGENT") or None


@dataclass(frozen=True)
class SearchConfig:
    area: str | None = "1"
    employment: str | None = None
    enabled_groups: tuple[str, ...] = ("it", "management", "marketing")
    pages_override: int | None = None


@dataclass(frozen=True)
class StorageConfig:
    path: str = "output/vacancies.json"
    unavailable_path: str = "output/unavailable.json"
    refresh_after_hours: float = 24.0


@dataclass(frozen=True)
class FailurePolicyConfig:
    max_consecutive_detail_errors: int = 5
    max_detail_error_rate: float = 0.35
    min_detail_samples_for_rate: int = 10


@dataclass(frozen=True)
class AlertConfig:
    webhook_url: str | None = os.getenv("ALERT_WEBHOOK_URL") or None
    telegram_bot_token: str | None = os.getenv("TELEGRAM_BOT_TOKEN") or None
    telegram_chat_id: str | None = os.getenv("TELEGRAM_CHAT_ID") or None


@dataclass(frozen=True)
class AppConfig:
    hh_base_url: str = "https://hh.ru"
    request: RequestConfig = field(default_factory=RequestConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    failures: FailurePolicyConfig = field(default_factory=FailurePolicyConfig)
    alerts: AlertConfig = field(default_factory=AlertConfig)


CONFIG = AppConfig()
