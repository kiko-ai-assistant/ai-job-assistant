from abc import ABC, abstractmethod

from parsers_base.models.vacancy import BatchCreateVacanciesResponse, CreateVacancyRequest


class SinkError(Exception):
    pass


class BaseSink(ABC):
    @abstractmethod
    async def send_batch(
        self,
        vacancies: list[CreateVacancyRequest],
    ) -> BatchCreateVacanciesResponse:
        ...

    @abstractmethod
    async def close(self) -> None:
        ...
