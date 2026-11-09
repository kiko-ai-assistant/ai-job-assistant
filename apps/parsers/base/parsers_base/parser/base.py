from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from parsers_base.models.vacancy import BatchCreateVacanciesResponse, CreateVacancyRequest
from parsers_base.parser.stats import ParserStats
from parsers_base.sink.base import BaseSink
from parsers_base.validation.validator import VacancyValidator

logger = logging.getLogger(__name__)


class BaseParser(ABC):
    def __init__(
        self,
        sink: BaseSink,
        validator: VacancyValidator | None = None,
        batch_size: int = 50,
    ) -> None:
        if batch_size <= 0:
            raise ValueError("batch_size must be greater than 0")
        self.sink = sink
        self.validator = validator
        self.batch_size = batch_size

    @abstractmethod
    async def parse(self, **kwargs: Any) -> AsyncIterator[CreateVacancyRequest]:
        if False:
            yield

    async def on_batch_sent(  # noqa: B027
        self,
        batch: list[CreateVacancyRequest],
        response: BatchCreateVacanciesResponse,
    ) -> None:
        pass

    async def _send_batch(
        self,
        batch: list[CreateVacancyRequest],
        stats: ParserStats,
    ) -> None:
        if not batch:
            return
        response = await self.sink.send_batch(batch)
        await self.on_batch_sent(batch, response)
        stats.inserted += response.inserted
        stats.ignored += response.ignored

    async def run(self, **kwargs: Any) -> ParserStats:
        stats = ParserStats()
        buffer: list[CreateVacancyRequest] = []

        async for item in self.parse(**kwargs):
            stats.extracted += 1

            if self.validator is not None:
                validation_result = self.validator.validate(item)
                is_valid = (
                    validation_result.is_valid
                    if hasattr(validation_result, "is_valid")
                    else bool(validation_result)
                )
                if not is_valid:
                    reasons = getattr(validation_result, "reasons", [])
                    logger.warning(
                        "Dropping invalid vacancy %s: %s",
                        getattr(item, "external_id", item),
                        reasons,
                    )
                    stats.invalid += 1
                    continue

            stats.valid += 1
            buffer.append(item)

            if len(buffer) >= self.batch_size:
                batch = buffer[:]
                buffer.clear()
                await self._send_batch(batch, stats)

        if buffer:
            batch = buffer[:]
            buffer.clear()
            await self._send_batch(batch, stats)

        return stats
