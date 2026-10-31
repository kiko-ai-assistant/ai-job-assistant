import logging
from datetime import UTC, datetime

from src.models.raw_post import RawPost
from src.models.vacancy import CreateVacancyRequest, LocationDTO, SalaryDTO
from src.transformer.base import BaseTransformer
from src.transformer.llm_extractor import LlmExtractor
from src.validation.validator import VacancyValidator

logger = logging.getLogger(__name__)


class PostParser(BaseTransformer):
    def __init__(
        self,
        llm_extractor: LlmExtractor | None = None,
        validator: VacancyValidator | None = None,
        default_source: str = "telegram",
    ) -> None:
        self.llm_extractor = llm_extractor if llm_extractor is not None else LlmExtractor()
        self.validator = validator if validator is not None else VacancyValidator()
        self.default_source = default_source

    async def transform(self, post: RawPost) -> CreateVacancyRequest | None:
        try:
            result = await self.llm_extractor.extract(post.text)
            if not result.is_vacancy:
                logger.info("Post url=%s rejected: not a vacancy (%s)", post.url, result.reason)
                return None

            data = result.data or {}
            raw_salary = data.get("salary")
            salary = SalaryDTO.model_validate(raw_salary) if raw_salary else None

            raw_location = data.get("location")
            location = LocationDTO.model_validate(raw_location) if raw_location else None

            vacancy = CreateVacancyRequest(
                external_id=f"{post.channel_username}_{post.message_id}",
                source=self.default_source,
                title=data.get("title") or "",
                company=data.get("company"),
                salary=salary,
                grade=data.get("grade") or "",
                employment_types=data.get("employment_types") or [],
                location=location,
                description=data.get("description") or post.text,
                url=post.url,
                published_at=post.date,
                parsed_at=datetime.now(UTC),
            )

            val_result = self.validator.validate(vacancy)
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
