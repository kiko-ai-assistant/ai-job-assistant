"""A sink that writes vacancies as JSON Lines instead of sending them to the backend."""

from __future__ import annotations

from typing import TextIO

from parsers_base.models.vacancy import BatchCreateVacanciesResponse, CreateVacancyRequest
from parsers_base.sink.base import BaseSink


class JsonlSink(BaseSink):
    """Dry-run sink: one vacancy per line, in the exact wire format of the backend API.

    The stream is owned by the caller; `close()` only flushes it.
    """

    def __init__(self, stream: TextIO) -> None:
        self._stream = stream

    async def send_batch(
        self,
        vacancies: list[CreateVacancyRequest],
    ) -> BatchCreateVacanciesResponse:
        for vacancy in vacancies:
            self._stream.write(vacancy.model_dump_json(by_alias=True) + "\n")
        self._stream.flush()
        return BatchCreateVacanciesResponse(inserted=len(vacancies), ignored=0)

    async def close(self) -> None:
        self._stream.flush()
