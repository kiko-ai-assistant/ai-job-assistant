import logging
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

import pytest

from parsers_base.models.vacancy import (
    BatchCreateVacanciesResponse,
    CreateVacancyRequest,
    LocationDTO,
    SalaryDTO,
)
from parsers_base.parser import BaseParser, ParserStats
from parsers_base.sink.base import BaseSink
from parsers_base.validation import VacancyValidator, ValidationResult


def _make_vacancy(
    external_id: str,
    title: str = "Senior Backend Engineer",
    description: str | None = None,
) -> CreateVacancyRequest:
    now = datetime.now(UTC)
    desc = (
        description
        if description is not None
        else (
            "We are looking for a backend engineer. "
            "Responsibilities include building scalable services. "
        )
        * 5
    )
    return CreateVacancyRequest(
        external_id=external_id,
        source="telegram",
        title=title,
        company="TechCorp Inc",
        salary=SalaryDTO(
            text="200k",
            from_=200000,
            to=250000,
            currency="RUB",
        ),
        grade="middle",
        employment_types=["remote"],
        location=LocationDTO(text="Remote", country="Russia", city="Moscow"),
        description=desc,
        url=f"https://t.me/jobs/{external_id}",
        published_at=now,
        parsed_at=now,
    )


class MockSink(BaseSink):
    def __init__(self, inserted: int = 1, ignored: int = 0) -> None:
        self.sent_batches: list[list[CreateVacancyRequest]] = []
        self.inserted = inserted
        self.ignored = ignored
        self.closed = False

    async def send_batch(
        self,
        vacancies: list[CreateVacancyRequest],
    ) -> BatchCreateVacanciesResponse:
        self.sent_batches.append(list(vacancies))
        return BatchCreateVacanciesResponse(
            inserted=len(vacancies) if self.inserted == 1 else self.inserted,
            ignored=self.ignored,
        )

    async def close(self) -> None:
        self.closed = True


class StreamingParser(BaseParser):
    def __init__(
        self,
        items: list[CreateVacancyRequest],
        sink: BaseSink,
        validator: VacancyValidator | None = None,
        batch_size: int = 50,
    ) -> None:
        super().__init__(sink=sink, validator=validator, batch_size=batch_size)
        self.items = items
        self.received_kwargs: dict[str, Any] = {}
        self.sent_hook_batches: list[list[CreateVacancyRequest]] = []
        self.sent_hook_responses: list[BatchCreateVacanciesResponse] = []

    async def parse(self, **kwargs: Any) -> AsyncIterator[CreateVacancyRequest]:
        self.received_kwargs = kwargs
        for item in self.items:
            yield item

    async def on_batch_sent(
        self,
        batch: list[CreateVacancyRequest],
        response: BatchCreateVacanciesResponse,
    ) -> None:
        self.sent_hook_batches.append(list(batch))
        self.sent_hook_responses.append(response)


@pytest.mark.asyncio
async def test_base_parser_full_streaming_lifecycle() -> None:
    items = [_make_vacancy(f"id_{i}") for i in range(5)]
    sink = MockSink()
    parser = StreamingParser(items=items, sink=sink, batch_size=10)

    stats = await parser.run(category="backend")

    assert isinstance(stats, ParserStats)
    assert stats.extracted == 5
    assert stats.valid == 5
    assert stats.invalid == 0
    assert stats.inserted == 5
    assert stats.ignored == 0
    assert len(sink.sent_batches) == 1
    assert len(sink.sent_batches[0]) == 5
    assert parser.received_kwargs == {"category": "backend"}


@pytest.mark.asyncio
async def test_base_parser_invalid_item_dropping(caplog: pytest.LogCaptureFixture) -> None:
    items = [
        _make_vacancy("valid_1"),
        _make_vacancy("invalid_1"),
        _make_vacancy("valid_2"),
    ]
    sink = MockSink()

    class RejectingValidator(VacancyValidator):
        def validate(
            self,
            vacancy: CreateVacancyRequest | Any,
            now: datetime | None = None,
        ) -> ValidationResult:
            if vacancy.external_id == "invalid_1":
                return ValidationResult(is_valid=False, reasons=["blacklisted id"])
            return ValidationResult(is_valid=True)

    parser = StreamingParser(
        items=items,
        sink=sink,
        validator=RejectingValidator(),
        batch_size=10,
    )

    with caplog.at_level(logging.WARNING):
        stats = await parser.run()

    assert stats.extracted == 3
    assert stats.valid == 2
    assert stats.invalid == 1
    assert stats.inserted == 2
    assert len(sink.sent_batches) == 1
    assert [v.external_id for v in sink.sent_batches[0]] == ["valid_1", "valid_2"]
    assert "Dropping invalid vacancy invalid_1: ['blacklisted id']" in caplog.text


@pytest.mark.asyncio
async def test_base_parser_batch_chunking_and_flush() -> None:
    items = [_make_vacancy(f"id_{i}") for i in range(7)]
    sink = MockSink()
    parser = StreamingParser(items=items, sink=sink, batch_size=3)

    stats = await parser.run()

    assert stats.extracted == 7
    assert stats.valid == 7
    assert len(sink.sent_batches) == 3
    assert len(sink.sent_batches[0]) == 3
    assert len(sink.sent_batches[1]) == 3
    assert len(sink.sent_batches[2]) == 1


@pytest.mark.asyncio
async def test_base_parser_hook_invocation() -> None:
    items = [_make_vacancy(f"id_{i}") for i in range(4)]
    sink = MockSink()
    parser = StreamingParser(items=items, sink=sink, batch_size=2)

    await parser.run()

    assert len(parser.sent_hook_batches) == 2
    assert len(parser.sent_hook_batches[0]) == 2
    assert len(parser.sent_hook_batches[1]) == 2
    assert len(parser.sent_hook_responses) == 2


@pytest.mark.asyncio
async def test_base_parser_default_hook() -> None:
    class DefaultHookParser(BaseParser):
        def __init__(self, sink: BaseSink) -> None:
            super().__init__(sink=sink, batch_size=2)

        async def parse(self, **kwargs: Any) -> AsyncIterator[CreateVacancyRequest]:
            yield _make_vacancy("item_1")

    sink = MockSink()
    parser = DefaultHookParser(sink=sink)
    stats = await parser.run()

    assert stats.extracted == 1
    assert stats.valid == 1
    assert stats.inserted == 1


@pytest.mark.asyncio
async def test_base_parser_empty_stream() -> None:
    sink = MockSink()
    parser = StreamingParser(items=[], sink=sink, batch_size=5)

    stats = await parser.run()

    assert stats == ParserStats(extracted=0, valid=0, invalid=0, inserted=0, ignored=0)
    assert len(sink.sent_batches) == 0


def test_base_parser_invalid_batch_size() -> None:
    sink = MockSink()
    with pytest.raises(ValueError, match="batch_size must be greater than 0"):
        StreamingParser(items=[], sink=sink, batch_size=0)

    with pytest.raises(ValueError, match="batch_size must be greater than 0"):
        StreamingParser(items=[], sink=sink, batch_size=-5)


@pytest.mark.asyncio
async def test_base_parser_with_real_vacancy_validator() -> None:
    valid_item = _make_vacancy("valid_real")
    invalid_item = _make_vacancy("invalid_short_desc", description="Too short")
    sink = MockSink()

    parser = StreamingParser(
        items=[valid_item, invalid_item],
        sink=sink,
        validator=VacancyValidator(),
        batch_size=10,
    )

    stats = await parser.run()

    assert stats.extracted == 2
    assert stats.valid == 1
    assert stats.invalid == 1
    assert stats.inserted == 1
    assert len(sink.sent_batches) == 1
    assert sink.sent_batches[0][0].external_id == "valid_real"


@pytest.mark.asyncio
async def test_base_parser_stats_accumulates_inserted_and_ignored() -> None:
    items = [_make_vacancy(f"id_{i}") for i in range(6)]

    class SplitSink(BaseSink):
        async def send_batch(
            self,
            vacancies: list[CreateVacancyRequest],
        ) -> BatchCreateVacanciesResponse:
            return BatchCreateVacanciesResponse(
                inserted=len(vacancies) - 1,
                ignored=1,
            )

        async def close(self) -> None:
            pass

    sink = SplitSink()
    parser = StreamingParser(items=items, sink=sink, batch_size=2)
    stats = await parser.run()

    assert stats.extracted == 6
    assert stats.valid == 6
    assert stats.invalid == 0
    assert stats.inserted == 3
    assert stats.ignored == 3

