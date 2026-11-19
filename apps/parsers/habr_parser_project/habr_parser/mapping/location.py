"""schema.org Place -> LocationDTO."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from parsers_base.models.vacancy import LocationDTO


def build_location(raw: Any) -> LocationDTO | None:
    place = _first_place(raw)
    if place is None:
        return None

    address = place.get("address", place)
    if isinstance(address, str):
        text = address.strip()
        return LocationDTO(text=text) if text else None
    if not isinstance(address, Mapping):
        return None

    city = _text(address.get("addressLocality"))
    country = _text(address.get("addressCountry"))
    text = ", ".join(part for part in (city, country) if part)
    if not text:
        return None
    # the shared validator rejects a city without a country: keep it in `text` only
    return LocationDTO(text=text, country=country, city=city if country else None)


def _first_place(raw: Any) -> Mapping[str, Any] | None:
    if isinstance(raw, list):
        raw = next((item for item in raw if isinstance(item, Mapping)), None)
    return raw if isinstance(raw, Mapping) else None


def _text(value: Any) -> str | None:
    if isinstance(value, Mapping):
        value = value.get("name")
    if not isinstance(value, str):
        return None
    return value.strip() or None
