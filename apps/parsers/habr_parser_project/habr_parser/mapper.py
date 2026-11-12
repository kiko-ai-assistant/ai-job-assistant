"""VacancyPage -> CreateVacancyRequest (the parsers_base / OpenAPI contract)."""

from __future__ import annotations

from datetime import datetime

from parsers_base.models.vacancy import CreateVacancyRequest
from parsers_base.validation.rules import MAX_DESCRIPTION_LEN

from .config import SOURCE_NAME
from .description import html_to_text, truncate_text
from .employment import map_employment_types
from .grade import Grade
from .location import build_location
from .salary import build_salary
from .vacancy_page import VacancyPage


def to_create_request(
    page: VacancyPage,
    *,
    vacancy_id: str,
    grade: Grade,
    url: str,
    parsed_at: datetime,
) -> CreateVacancyRequest:
    return CreateVacancyRequest(
        external_id=vacancy_id,
        source=SOURCE_NAME,
        title=page.title,
        company=page.company,
        salary=build_salary(page.base_salary),
        grade=grade.value,
        employment_types=map_employment_types(page.job_location_type, page.employment_type),
        location=build_location(page.job_location),
        description=truncate_text(html_to_text(page.description_html), MAX_DESCRIPTION_LEN),
        url=url,
        published_at=page.published_at,
        parsed_at=parsed_at,
    )
