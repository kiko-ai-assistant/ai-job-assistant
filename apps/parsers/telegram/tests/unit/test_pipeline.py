from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path

import pytest

from src.extractor.base import BaseExtractor
from src.models.raw_post import RawPost
from src.models.vacancy import BatchIngestVacanciesResponse, CreateVacancyRequest
from src.pipeline.orchestrator import ETLPipeline
from src.pipeline.scheduler import ScheduledRunner
from src.sink.base import BaseSink
from src.storage.sqlite_store import SqliteStateStore
from src.transformer.post_parser import PostParser


class MockExtractor(BaseExtractor):
    def __init__(self, posts: list[RawPost]) -> None:
        self.posts = posts

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass

    async def fetch_posts(
        self, channel: str, since_message_id: int, limit: int = 100
    ) -> AsyncIterator[RawPost]:
        for p in self.posts:
            if p.message_id > since_message_id:
                yield p


class MockSink(BaseSink):
    def __init__(self) -> None:
        self.sent: list[CreateVacancyRequest] = []

    async def send_batch(
        self, vacancies: list[CreateVacancyRequest]
    ) -> BatchIngestVacanciesResponse:
        self.sent.extend(vacancies)
        return BatchIngestVacanciesResponse(inserted=len(vacancies), ignored=0)

    async def close(self) -> None:
        pass


@pytest.mark.asyncio
async def test_etl_pipeline_run_channel(tmp_path: Path) -> None:
    now = datetime.now(UTC)
    posts = [
        RawPost(
            channel_username="test_chan",
            message_id=1,
            text="Ищем Senior Python Developer на удаленку!",
            date=now,
            url="https://t.me/test_chan/1",
        ),
        RawPost(
            channel_username="test_chan",
            message_id=2,
            text="Реклама курсов, не вакансия",
            date=now,
            url="https://t.me/test_chan/2",
        ),
    ]

    extractor = MockExtractor(posts)
    transformer = PostParser()
    sink = MockSink()
    store = SqliteStateStore(tmp_path / "state.sqlite")
    await store.initialize()

    pipeline = ETLPipeline(
        extractor=extractor,
        transformer=transformer,
        sink=sink,
        state_store=store,
    )

    stats = await pipeline.process_channel("test_chan")

    assert stats["extracted"] == 2
    assert stats["transformed"] == 1
    assert stats["inserted"] == 1
    assert len(sink.sent) == 1
    assert sink.sent[0].external_id == "test_chan_1"

    # Verify watermark updated to highest message_id
    checkpoint = await store.get_checkpoint("test_chan")
    assert checkpoint == 2

    await store.close()


@pytest.mark.asyncio
async def test_scheduled_runner(tmp_path: Path) -> None:
    config_file = tmp_path / "channels.yaml"
    config_file.write_text(
        """
channels:
  - username: "chan1"
    enabled: true
  - username: "chan2"
    enabled: false
""",
        encoding="utf-8",
    )

    now = datetime.now(UTC)
    posts = [
        RawPost(
            channel_username="chan1",
            message_id=10,
            text="Вакансия: Ищем Senior Python Backend Developer в компанию Kiko",
            date=now,
            url="https://t.me/chan1/10",
        )
    ]
    extractor = MockExtractor(posts)
    transformer = PostParser()
    sink = MockSink()
    store = SqliteStateStore(tmp_path / "state.sqlite")
    await store.initialize()

    pipeline = ETLPipeline(
        extractor=extractor,
        transformer=transformer,
        sink=sink,
        state_store=store,
    )

    runner = ScheduledRunner(
        pipeline=pipeline,
        channels_config_path=config_file,
        poll_interval_seconds=10,
    )

    channels = runner.load_channels()
    assert channels == ["chan1"]

    await runner.run_once()
    assert len(sink.sent) == 1
    assert sink.sent[0].external_id == "chan1_10"

    runner.stop()
    assert not runner._running

    await store.close()
