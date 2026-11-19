"""Vacancy grades: the values of the Kiko API enum and Habr's `qid` filter."""

from __future__ import annotations

from enum import StrEnum


class Grade(StrEnum):
    INTERN = "INTERN"
    JUNIOR = "JUNIOR"
    MIDDLE = "MIDDLE"
    SENIOR = "SENIOR"
    LEAD = "LEAD"

    @property
    def qid(self) -> int:
        """Habr's `qid` (qualification) query parameter for this grade."""
        return _QID_BY_GRADE[self]


# Verify against the filter links on career.habr.com/vacancies.
_QID_BY_GRADE: dict[Grade, int] = {
    Grade.INTERN: 1,
    Grade.JUNIOR: 3,
    Grade.MIDDLE: 4,
    Grade.SENIOR: 5,
    Grade.LEAD: 6,
}
