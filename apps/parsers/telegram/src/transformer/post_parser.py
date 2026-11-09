import logging
from datetime import UTC, datetime

from src.models.raw_post import RawPost
from src.models.vacancy import CreateVacancyRequest, LocationDTO, SalaryDTO
from src.transformer.base import BaseTransformer
from src.transformer.llm_extractor import LlmExtractor
from src.validation.rules import VACANCY_VALID_UP_TO
from src.validation.validator import VacancyValidator

logger = logging.getLogger(__name__)


class PostParser(BaseTransformer):
    def __init__(
        self,
        llm_extractor: LlmExtractor,
        validator: VacancyValidator | None = None,
        default_source: str = "telegram",
        ignore_date_window: bool = False,
    ) -> None:
        self.llm_extractor = llm_extractor
        self.validator = validator if validator is not None else VacancyValidator()
        self.default_source = default_source
        self.ignore_date_window = ignore_date_window

    async def transform(self, post: RawPost) -> CreateVacancyRequest | None:
        try:
            post_date = (
                post.date if post.date.tzinfo is not None else post.date.replace(tzinfo=UTC)
            )
            if not self.ignore_date_window and post_date < (datetime.now(UTC) - VACANCY_VALID_UP_TO):
                logger.info("Post url=%s skipped: published_at older than valid window", post.url)
                return None

            result = await self.llm_extractor.extract(post.text)
            if not result.is_vacancy:
                logger.info("Post url=%s rejected: not a vacancy (%s)", post.url, result.reason)
                return None

            data = result.data or {}
            raw_salary = data.get("salary")
            salary = SalaryDTO.model_validate(raw_salary) if raw_salary else None
            if salary and (salary.from_ is not None or salary.to is not None):
                curr = (salary.currency or "RUB").strip()
                if curr in {"₽", "руб", "руб.", "RUR", "rur"}:
                    curr = "RUB"
                elif curr in {"$", "usd"}:
                    curr = "USD"
                elif curr in {"€", "eur"}:
                    curr = "EUR"
                salary.currency = curr

            raw_location = data.get("location")
            location = LocationDTO.model_validate(raw_location) if raw_location else None
            if location and location.city and not location.country:
                location.country = "Russia"

            description = (data.get("description") or post.text).strip()
            if len(description) < 300 and len(post.text.strip()) >= 300:
                description = post.text.strip()
            if len(description) > 2500:
                description = description[:2500].rstrip()

            grade = (data.get("grade") or "").strip().lower()
            if grade.endswith("+"):
                grade = grade[:-1].strip()

            employment_types = [
                et.lower().strip() for et in (data.get("employment_types") or [])
            ]

            parsed_at = post.date if self.ignore_date_window else datetime.now(UTC)

            vacancy = CreateVacancyRequest(
                external_id=f"{post.channel_username}_{post.message_id}",
                source=self.default_source,
                title=data.get("title") or "",
                company=data.get("company"),
                salary=salary,
                grade=grade,
                employment_types=employment_types,
                location=location,
                description=description,
                url=post.url,
                published_at=post.date,
                parsed_at=parsed_at,
            )

            validation_now = post_date if self.ignore_date_window else None
            val_result = self.validator.validate(vacancy, now=validation_now)
            if not val_result.is_valid:
                logger.warning(
                    "Vacancy validation failed for url=%s. Reasons: %s",
                    post.url,
                    "; ".join(val_result.reasons),
                )
                return None

            return vacancy
        except Exception as err:
            logger.warning("Failed to transform post url=%s: %s", post.url, err)
            return None
