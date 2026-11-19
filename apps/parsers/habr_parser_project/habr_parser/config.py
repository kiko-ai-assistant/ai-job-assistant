"""Static settings of the Habr parser."""

from __future__ import annotations

from dataclasses import dataclass

SOURCE_NAME = "habr"
BASE_URL = "https://career.habr.com"
DEFAULT_USER_AGENT = "Mozilla/5.0 (compatible; kiko-habr-parser/0.1)"


@dataclass(frozen=True)
class HttpConfig:
    """How politely and how persistently we talk to Habr."""

    base_url: str = BASE_URL
    request_delay: float = 1.0  # pause (s) after every request, also the backoff base
    max_retries: int = 3
    timeout: float = 20.0
    concurrency: int = 3  # simultaneous requests
    user_agent: str = DEFAULT_USER_AGENT
