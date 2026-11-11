from datetime import datetime

from parsers_base import CreateVacancyRequest, LocationDTO, SalaryDTO
from parsers_base.validation.rules import VALID_EMPLOYMENT_TYPES, VALID_GRADES

from models import Vacancy


def _required_text(value: str | None, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} is missing")
    return value.strip()


def _optional_text(value: str | None) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _timestamp(value: str | None, field: str) -> datetime:
    raw = _required_text(value, field)
    try:
        result = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO date-time with a timezone") from exc
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError(f"{field} must include a time and timezone")
    return result


def to_create_vacancy(vacancy: Vacancy) -> CreateVacancyRequest:
    if vacancy.source not in {"hh", "hh.ru"}:
        raise ValueError(f"Unsupported HH source: {vacancy.source}")

    grade = _required_text(vacancy.grade, "grade").lower()
    if grade not in VALID_GRADES:
        raise ValueError(f"Unsupported grade: {vacancy.grade}")
    if not isinstance(vacancy.employment_types, list) or not vacancy.employment_types:
        raise ValueError("employment_types are missing")
    employment_types = []
    for item in vacancy.employment_types:
        employment_type = _required_text(item, "employment_types").lower()
        if employment_type not in VALID_EMPLOYMENT_TYPES:
            raise ValueError(f"Unsupported employment_types value: {item}")
        if employment_type.upper() not in employment_types:
            employment_types.append(employment_type.upper())

    salary = None
    salary_text = _optional_text(vacancy.salary_text)
    currency = _optional_text(vacancy.salary_currency)
    if (
        salary_text is not None
        and type(vacancy.salary_from) is int
        and type(vacancy.salary_to) is int
        and currency is not None
    ):
        salary = SalaryDTO.model_validate(
            {
                "text": salary_text,
                "from": vacancy.salary_from,
                "to": vacancy.salary_to,
                "currency": currency,
            }
        )

    location = None
    location_text = _optional_text(vacancy.location)
    country = _optional_text(vacancy.location_country)
    city = _optional_text(vacancy.location_city)
    if location_text is not None and country is not None and city is not None:
        location = LocationDTO(text=location_text, country=country, city=city)

    return CreateVacancyRequest(
        external_id=_required_text(vacancy.external_id, "external_id"),
        source="hh",
        title=_required_text(vacancy.title, "title"),
        company=_optional_text(vacancy.company),
        salary=salary,
        grade=grade.upper(),
        employment_types=employment_types,
        location=location,
        description=_required_text(vacancy.description, "description"),
        url=_required_text(vacancy.url, "url"),
        published_at=_timestamp(vacancy.created_at, "published_at"),
        parsed_at=_timestamp(vacancy.parsed_at, "parsed_at"),
    )
