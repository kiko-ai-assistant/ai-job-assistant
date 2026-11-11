import math
import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

APP_DIR = Path(__file__).resolve().parent


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
    path: str = str(APP_DIR / "output/vacancies.json")
    unavailable_path: str = str(APP_DIR / "output/unavailable.json")
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


@dataclass(frozen=True)
class BackendConfig:
    base_url: str
    api_key: str = field(repr=False)
    batch_size: int = 50
    timeout_seconds: float = 15.0

    @classmethod
    def from_env(cls) -> "BackendConfig":
        base_url = os.environ.get("BACKEND_URL", "").strip()
        api_key = os.environ.get("PARSER_API_KEY", "").strip()
        if not base_url or not api_key:
            raise ValueError("BACKEND_URL and PARSER_API_KEY must be set")
        parsed = urlsplit(base_url)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("BACKEND_URL must be an HTTP(S) API base URL without credentials")
        batch_size = int(os.environ.get("BACKEND_BATCH_SIZE", "50"))
        timeout = float(os.environ.get("BACKEND_TIMEOUT_SECONDS", "15"))
        if batch_size <= 0 or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("Backend batch size and timeout must be positive")
        return cls(base_url.rstrip("/"), api_key, batch_size, timeout)


CONFIG = AppConfig()
