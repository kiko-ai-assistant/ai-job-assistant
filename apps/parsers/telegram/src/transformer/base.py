from abc import ABC, abstractmethod

from src.models.raw_post import RawPost
from src.models.vacancy import CreateVacancyRequest


class BaseTransformer(ABC):
    @abstractmethod
    def transform(self, post: RawPost) -> CreateVacancyRequest | None:
        """Transform a raw post into a vacancy contract, or None if not a vacancy."""
        ...
