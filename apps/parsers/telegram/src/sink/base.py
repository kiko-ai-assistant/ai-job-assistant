from abc import ABC, abstractmethod

from src.models.vacancy import BatchIngestVacanciesResponse, CreateVacancyRequest


class BaseSink(ABC):
    @abstractmethod
    async def send_batch(
        self,
        vacancies: list[CreateVacancyRequest],
    ) -> BatchIngestVacanciesResponse:
        """Send a batch of vacancies to the destination."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Cleanly close connections."""
        ...
