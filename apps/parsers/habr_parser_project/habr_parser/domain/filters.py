"""User-facing search filters and their translation into Habr query parameters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .grade import Grade


@dataclass(frozen=True)
class SearchFilters:
    query: str | None = None
    min_salary: int | None = None
    skill_ids: tuple[int, ...] = ()
    location_ids: tuple[int, ...] = ()

    def to_params(self, grade: Grade, page: int) -> dict[str, Any]:
        params: dict[str, Any] = {"type": "all", "page": page, "qid": grade.qid}
        if self.query:
            params["q"] = self.query
        if self.min_salary:
            params["salary"] = self.min_salary
        if self.skill_ids:
            params["skill[]"] = list(self.skill_ids)
        if self.location_ids:
            params["location_id[]"] = list(self.location_ids)
        return params
