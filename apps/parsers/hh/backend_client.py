import logging
from collections.abc import AsyncIterator
from typing import Any

from parsers_base import (
    BaseParser,
    BaseSink,
    BatchCreateVacanciesResponse,
    CreateVacancyRequest,
    SinkError,
    VacancyValidator,
)

from json_storage import JsonVacancyStorage
from transformer import to_create_vacancy

logger = logging.getLogger(__name__)


class HHBackendParser(BaseParser):
    def __init__(
        self,
        storage: JsonVacancyStorage,
        sink: BaseSink,
        batch_size: int = 50,
    ) -> None:
        super().__init__(sink, VacancyValidator(allowed_sources={"hh"}), batch_size)
        self.storage = storage
        self.conversion_errors = 0
        self._raw_keys: dict[int, tuple[str, str]] = {}

    async def parse(self, **kwargs: Any) -> AsyncIterator[CreateVacancyRequest]:
        self.conversion_errors = 0
        self._raw_keys.clear()
        for vacancy in self.storage.pending():
            try:
                item = to_create_vacancy(vacancy)
            except ValueError as exc:
                self.conversion_errors += 1
                logger.warning("Keeping vacancy %s pending: %s", vacancy.external_id, exc)
                continue
            self._raw_keys[id(item)] = vacancy.key
            yield item

    async def on_batch_sent(
        self,
        batch: list[CreateVacancyRequest],
        response: BatchCreateVacanciesResponse,
    ) -> None:
        if (
            response.inserted < 0
            or response.ignored < 0
            or response.inserted + response.ignored != len(batch)
        ):
            raise SinkError("Backend batch counters do not acknowledge the complete batch")
        keys = [self._raw_keys[id(vacancy)] for vacancy in batch]
        self.storage.mark_delivered(keys)
        for vacancy in batch:
            del self._raw_keys[id(vacancy)]
