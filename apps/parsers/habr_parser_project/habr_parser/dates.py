"""Date parsing."""

from __future__ import annotations

from datetime import UTC, datetime


def parse_iso_datetime(value: object) -> datetime | None:
    """Parse an ISO 8601 date/datetime into an aware UTC datetime; None if impossible.

    Naive values and plain dates are interpreted as UTC.
    """
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip())
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)
