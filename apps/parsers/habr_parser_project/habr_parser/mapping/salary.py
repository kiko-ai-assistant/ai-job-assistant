"""schema.org MonetaryAmount -> SalaryDTO."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from parsers_base.models.vacancy import SalaryDTO

_CURRENCY_ALIASES = {"RUR": "RUB"}  # Habr still uses the old rouble code
_CURRENCY_LENGTH = 3


def build_salary(raw: Any) -> SalaryDTO | None:
    """Return a salary the shared validator will accept, or None."""
    if not isinstance(raw, Mapping):
        return None
    currency = _normalise_currency(raw.get("currency"))
    lower, upper = _bounds(raw.get("value"))
    if currency is None or (lower is None and upper is None):
        return None
    return SalaryDTO(
        text=_describe(lower, upper, currency),
        from_=lower,
        to=upper,
        currency=currency,
    )


def _bounds(value: Any) -> tuple[int | None, int | None]:
    if isinstance(value, Mapping):
        lower = _to_amount(value.get("minValue"))
        upper = _to_amount(value.get("maxValue"))
        if lower is None and upper is None:
            lower = upper = _to_amount(value.get("value"))
        return lower, upper
    fixed = _to_amount(value)
    return fixed, fixed


def _to_amount(value: Any) -> int | None:
    """Positive integer amount; zero / garbage mean 'not specified'."""
    if value is None or isinstance(value, bool):
        return None
    try:
        amount = int(float(value))
    except (TypeError, ValueError, OverflowError):
        return None
    return amount if amount > 0 else None


def _normalise_currency(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    code = value.strip().upper()
    code = _CURRENCY_ALIASES.get(code, code)
    return code if len(code) == _CURRENCY_LENGTH else None


def _describe(lower: int | None, upper: int | None, currency: str) -> str:
    if lower is not None and upper is not None:
        amount = f"{lower}" if lower == upper else f"{lower}-{upper}"
    elif lower is not None:
        amount = f"from {lower}"
    else:
        amount = f"up to {upper}"
    return f"{amount} {currency}"
