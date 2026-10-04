import httpx

from src.models.vacancy import (
    BatchCreateVacanciesRequest,
    BatchIngestVacanciesResponse,
    CreateVacancyRequest,
)

from .base import BaseSink


class BackendApiSink(BaseSink):
    def __init__(
        self,
        backend_url: str,
        parser_api_key: str,
        timeout: float = 15.0,
    ) -> None:
        self.backend_url = backend_url.rstrip("/")
        self.client = httpx.AsyncClient(
            base_url=self.backend_url,
            headers={
                "X-Parser-Api-Key": parser_api_key,
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

    async def send_batch(
        self,
        vacancies: list[CreateVacancyRequest],
    ) -> BatchIngestVacanciesResponse:
        if not vacancies:
            return BatchIngestVacanciesResponse(inserted=0, ignored=0)

        payload = BatchCreateVacanciesRequest(vacancies=vacancies)
        response = await self.client.post(
            "/vacancies/batch",
            content=payload.model_dump_json(),
        )
        response.raise_for_status()
        data = response.json()
        return BatchIngestVacanciesResponse.model_validate(data)

    async def close(self) -> None:
        await self.client.aclose()
