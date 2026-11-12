"""schema.org employment hints -> the Kiko EmploymentType enum."""

from __future__ import annotations

from enum import StrEnum
from typing import Any


class EmploymentType(StrEnum):
    REMOTE = "REMOTE"
    OFFICE = "OFFICE"
    HYBRID = "HYBRID"
    CONTRACT = "CONTRACT"


def map_employment_types(job_location_type: Any, employment_type: Any) -> list[str]:
    """Never empty: the contract requires at least one employment type.

    schema.org cannot express HYBRID, and a vacancy with no remote/contract
    hint is assumed to be OFFICE.
    """
    types: list[EmploymentType] = []
    if "TELECOMMUTE" in _upper_values(job_location_type):
        types.append(EmploymentType.REMOTE)
    if "CONTRACTOR" in _upper_values(employment_type):
        types.append(EmploymentType.CONTRACT)
    return [t.value for t in types] or [EmploymentType.OFFICE.value]


def _upper_values(value: Any) -> set[str]:
    values = value if isinstance(value, list) else [value]
    return {item.strip().upper() for item in values if isinstance(item, str)}
