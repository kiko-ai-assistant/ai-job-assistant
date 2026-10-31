from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from .rules import (
    MAX_COMPANY_LEN,
    MAX_DESCRIPTION_LEN,
    MAX_FUTURE_TIME_SKEW,
    MAX_LOC_CITY_LEN,
    MAX_LOC_COUNTRY_LEN,
    MAX_LOC_TEXT_LEN,
    MAX_SALARY_LEN,
    MAX_SALARY_VAL,
    MAX_TITLE_LEN,
    MAX_URL_LEN,
    MIN_COMPANY_LEN,
    MIN_CURRENCY_LEN,
    MIN_DESCRIPTION_LEN,
    MIN_LOC_CITY_LEN,
    MIN_LOC_COUNTRY_LEN,
    MIN_LOC_TEXT_LEN,
    MIN_SALARY_LEN,
    MIN_SALARY_VAL,
    MIN_TITLE_LEN,
    MIN_URL_LEN,
    VACANCY_VALID_UP_TO,
    VALID_EMPLOYMENT_TYPES,
    VALID_GRADES,
    VALID_SOURCES,
)

if TYPE_CHECKING:
    from src.models.vacancy import CreateVacancyRequest


@dataclass
class ValidationResult:
    is_valid: bool
    reasons: list[str] = field(default_factory=list)


class VacancyValidator:
    def validate(
        self,
        vacancy: "CreateVacancyRequest | Any",
        now: datetime | None = None,
    ) -> ValidationResult:
        reasons: list[str] = []

        if now is None:
            now = datetime.now(UTC)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=UTC)

        external_id = getattr(vacancy, "external_id", None)
        if not external_id or not isinstance(external_id, str) or not external_id.strip():
            reasons.append("external_id is required")

        source = getattr(vacancy, "source", None)
        if not source or not isinstance(source, str) or not source.strip():
            reasons.append("source is required")
        elif source.strip().lower() not in VALID_SOURCES:
            reasons.append(
                f"source '{source}' is invalid, must be one of {sorted(VALID_SOURCES)}"
            )

        title = getattr(vacancy, "title", None)
        if not title or not isinstance(title, str) or not title.strip():
            reasons.append("title is required")
        else:
            trimmed_title = title.strip()
            if not (MIN_TITLE_LEN <= len(trimmed_title) <= MAX_TITLE_LEN):
                reasons.append(
                    f"title length {len(trimmed_title)} is out of bounds "
                    f"[{MIN_TITLE_LEN}, {MAX_TITLE_LEN}]"
                )

        company = getattr(vacancy, "company", None)
        if company is not None:
            if not isinstance(company, str):
                reasons.append("company must be a string")
            else:
                trimmed_company = company.strip()
                if not (MIN_COMPANY_LEN <= len(trimmed_company) <= MAX_COMPANY_LEN):
                    reasons.append(
                        f"company length {len(trimmed_company)} is out of bounds "
                        f"[{MIN_COMPANY_LEN}, {MAX_COMPANY_LEN}]"
                    )

        description = getattr(vacancy, "description", None)
        if not description or not isinstance(description, str) or not description.strip():
            reasons.append("description is required")
        else:
            trimmed_desc = description.strip()
            if not (MIN_DESCRIPTION_LEN <= len(trimmed_desc) <= MAX_DESCRIPTION_LEN):
                reasons.append(
                    f"description length {len(trimmed_desc)} is out of bounds "
                    f"[{MIN_DESCRIPTION_LEN}, {MAX_DESCRIPTION_LEN}]"
                )

        url = getattr(vacancy, "url", None)
        if not url or not isinstance(url, str) or not url.strip():
            reasons.append("url is required")
        else:
            trimmed_url = url.strip()
            if not (MIN_URL_LEN <= len(trimmed_url) <= MAX_URL_LEN):
                reasons.append(
                    f"url length {len(trimmed_url)} is out of bounds "
                    f"[{MIN_URL_LEN}, {MAX_URL_LEN}]"
                )

        grade = getattr(vacancy, "grade", None)
        if not grade or not isinstance(grade, str) or not grade.strip():
            reasons.append("grade is required")
        elif grade.strip().lower() not in VALID_GRADES:
            reasons.append(f"grade '{grade}' is invalid, must be one of {sorted(VALID_GRADES)}")

        employment_types = getattr(vacancy, "employment_types", None)
        if not employment_types:
            reasons.append("employment_types is required")
        else:
            for et in employment_types:
                if not isinstance(et, str) or et.strip().lower() not in VALID_EMPLOYMENT_TYPES:
                    reasons.append(
                        f"employment_type '{et}' is invalid, must be one of "
                        f"{sorted(VALID_EMPLOYMENT_TYPES)}"
                    )

        salary = getattr(vacancy, "salary", None)
        if salary is not None:
            self._validate_salary(salary, reasons)

        location = getattr(vacancy, "location", None)
        if location is not None:
            self._validate_location(location, reasons)

        self._validate_dates(vacancy, now, reasons)

        return ValidationResult(is_valid=len(reasons) == 0, reasons=reasons)

    def _validate_salary(self, salary: Any, reasons: list[str]) -> None:
        salary_text = getattr(salary, "text", None)
        salary_from = getattr(salary, "from_", None)
        if salary_from is None:
            salary_from = getattr(salary, "from", None)
        salary_to = getattr(salary, "to", None)
        salary_currency = getattr(salary, "currency", None)

        if salary_text is not None:
            if not isinstance(salary_text, str):
                reasons.append("salary text must be a string")
            else:
                trimmed_text = salary_text.strip()
                if not (MIN_SALARY_LEN <= len(trimmed_text) <= MAX_SALARY_LEN):
                    reasons.append(
                        f"salary text length {len(trimmed_text)} is out of bounds "
                        f"[{MIN_SALARY_LEN}, {MAX_SALARY_LEN}]"
                    )

        if salary_from is not None:
            if not (MIN_SALARY_VAL <= salary_from <= MAX_SALARY_VAL):
                reasons.append(
                    f"salary_from {salary_from} is out of bounds "
                    f"[{MIN_SALARY_VAL}, {MAX_SALARY_VAL}]"
                )

        if salary_to is not None:
            if not (MIN_SALARY_VAL <= salary_to <= MAX_SALARY_VAL):
                reasons.append(
                    f"salary_to {salary_to} is out of bounds "
                    f"[{MIN_SALARY_VAL}, {MAX_SALARY_VAL}]"
                )

        if salary_from is not None and salary_to is not None and salary_from > salary_to:
            reasons.append("salary_from cannot be greater than salary_to")

        has_bounds = salary_from is not None or salary_to is not None
        has_currency = (
            salary_currency is not None
            and isinstance(salary_currency, str)
            and len(salary_currency.strip()) > 0
        )

        if has_bounds and not has_currency:
            reasons.append("currency is required when salary bounds are specified")
        elif not has_bounds and has_currency:
            reasons.append("currency cannot be specified without salary bounds")

        if has_currency:
            trimmed_curr = salary_currency.strip()  # type: ignore[union-attr]
            if len(trimmed_curr) != MIN_CURRENCY_LEN:
                reasons.append(
                    f"currency '{salary_currency}' length must be {MIN_CURRENCY_LEN}"
                )

    def _validate_location(self, location: Any, reasons: list[str]) -> None:
        loc_text = getattr(location, "text", None)
        loc_country = getattr(location, "country", None)
        loc_city = getattr(location, "city", None)

        has_city = loc_city is not None and isinstance(loc_city, str) and len(loc_city.strip()) > 0
        has_country = (
            loc_country is not None
            and isinstance(loc_country, str)
            and len(loc_country.strip()) > 0
        )

        if has_city and not has_country:
            reasons.append("city cannot be specified without country")
        elif loc_city is not None and loc_country is None:
            reasons.append("city cannot be specified without country")

        if loc_country is not None:
            if not isinstance(loc_country, str):
                reasons.append("country must be a string")
            else:
                trimmed_country = loc_country.strip()
                if not (MIN_LOC_COUNTRY_LEN <= len(trimmed_country) <= MAX_LOC_COUNTRY_LEN):
                    reasons.append(
                        f"country length {len(trimmed_country)} is out of bounds "
                        f"[{MIN_LOC_COUNTRY_LEN}, {MAX_LOC_COUNTRY_LEN}]"
                    )

        if loc_city is not None:
            if not isinstance(loc_city, str):
                reasons.append("city must be a string")
            else:
                trimmed_city = loc_city.strip()
                if not (MIN_LOC_CITY_LEN <= len(trimmed_city) <= MAX_LOC_CITY_LEN):
                    reasons.append(
                        f"city length {len(trimmed_city)} is out of bounds "
                        f"[{MIN_LOC_CITY_LEN}, {MAX_LOC_CITY_LEN}]"
                    )

        if loc_text is not None:
            if not isinstance(loc_text, str):
                reasons.append("location text must be a string")
            else:
                trimmed_text = loc_text.strip()
                if not (MIN_LOC_TEXT_LEN <= len(trimmed_text) <= MAX_LOC_TEXT_LEN):
                    reasons.append(
                        f"location text length {len(trimmed_text)} is out of bounds "
                        f"[{MIN_LOC_TEXT_LEN}, {MAX_LOC_TEXT_LEN}]"
                    )

    def _validate_dates(
        self,
        vacancy: Any,
        now: datetime,
        reasons: list[str],
    ) -> None:
        pub = getattr(vacancy, "published_at", None)
        if pub is None:
            reasons.append("published_at is required")
        else:
            if pub.tzinfo is None:
                pub = pub.replace(tzinfo=UTC)
            if pub < (now - VACANCY_VALID_UP_TO) or pub > (now + MAX_FUTURE_TIME_SKEW):
                reasons.append(
                    "published_at must not be earlier than 7 days ago or later than "
                    "5 minutes in future"
                )

        parsed = getattr(vacancy, "parsed_at", None)
        if parsed is None:
            reasons.append("parsed_at is required")
        else:
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=UTC)
            if pub is not None and (parsed < pub or parsed > (now + MAX_FUTURE_TIME_SKEW)):
                reasons.append(
                    "parsed_at must be >= published_at and not later than 5 minutes in future"
                )
