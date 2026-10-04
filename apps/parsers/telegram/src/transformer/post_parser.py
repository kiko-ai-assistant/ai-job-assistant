from src.models.raw_post import RawPost
from src.models.vacancy import CreateVacancyRequest

from .base import BaseTransformer
from .heuristics import HeuristicExtractor


class PostParser(BaseTransformer):
    def __init__(self, extractor: type[HeuristicExtractor] = HeuristicExtractor) -> None:
        self.extractor = extractor

    def transform(self, post: RawPost) -> CreateVacancyRequest | None:
        text = post.text
        if not self.extractor.is_vacancy(text):
            return None

        title = self.extractor.extract_title(text)
        salary = self.extractor.extract_salary(text)
        company = self.extractor.extract_company(text)

        external_id = f"{post.channel_username}_{post.message_id}"

        return CreateVacancyRequest(
            external_id=external_id,
            source="Telegram",
            title=title,
            company=company,
            salary_text=salary,
            description=text,
            url=post.url,
        )
