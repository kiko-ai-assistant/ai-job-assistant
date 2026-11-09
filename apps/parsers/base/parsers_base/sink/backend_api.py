import types

import httpx

from parsers_base.models.vacancy import (
    BatchCreateVacanciesRequest,
    BatchCreateVacanciesResponse,
    CreateVacancyRequest,
)

from .base import BaseSink, SinkError


class BackendApiSink(BaseSink):
    def __init__(
        self,
        backend_url: str,
        parser_api_key: str,
        timeout: float = 15.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.backend_url = backend_url.rstrip("/")
        self.parser_api_key = parser_api_key
        self.timeout = timeout
        self.client = client or httpx.AsyncClient(
            base_url=self.backend_url,
            headers={
                "X-Parser-Api-Key": self.parser_api_key,
                "Content-Type": "application/json",
            },
            timeout=self.timeout,
        )

    async def send_batch(
        self,
        vacancies: list[CreateVacancyRequest],
    ) -> BatchCreateVacanciesResponse:
        if not vacancies:
            return BatchCreateVacanciesResponse(inserted=0, ignored=0)

        payload = BatchCreateVacanciesRequest(vacancies=vacancies)
        try:
            response = await self.client.post(
                "/vacancies/batch",
                content=payload.model_dump_json(by_alias=True),
            )
            response.raise_for_status()
            data = response.json()
            return BatchCreateVacanciesResponse.model_validate(data)
        except httpx.HTTPStatusError as exc:
            raise SinkError(
                f"Backend API error ({exc.response.status_code}): {exc.response.text}"
            ) from exc
        except httpx.RequestError as exc:
            raise SinkError(f"Backend API request failed: {exc}") from exc
        except Exception as exc:
            raise SinkError(f"Failed to send vacancies batch: {exc}") from exc

    async def close(self) -> None:
        await self.client.aclose()

    async def __aenter__(self) -> "BackendApiSink":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        await self.close()
