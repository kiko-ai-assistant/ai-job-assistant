from dataclasses import asdict, dataclass


@dataclass
class Vacancy:
    external_id: str
    source: str
    title: str | None
    company: str | None
    salary_text: str | None
    location: str | None
    description: str | None
    url: str
    created_at: str | None
    parsed_at: str | None

    @property
    def key(self) -> tuple[str, str]:
        return self.source, self.external_id

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RunStats:
    targets_started: int = 0
    pages_requested: int = 0
    cards_found: int = 0
    duplicates_skipped: int = 0
    fresh_skipped: int = 0
    parsed: int = 0
    refreshed: int = 0
    unavailable: int = 0
    failed: int = 0
    layout_errors: int = 0
    blocked: int = 0
    captcha: int = 0
    mass_failure: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class HttpStats:
    total_requests: int = 0
    http_200: int = 0
    http_403: int = 0
    http_404_410: int = 0
    http_429: int = 0
    http_5xx: int = 0
    other_http: int = 0
    network_errors: int = 0
    retries: int = 0

    def to_dict(self) -> dict:
        return asdict(self)
