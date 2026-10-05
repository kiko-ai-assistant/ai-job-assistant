from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from src.config import Settings
from src.models.channel import ChannelConfig, ChannelsConfigFile
from src.models.raw_post import RawPost
from src.models.vacancy import (
    BatchCreateVacanciesRequest,
    BatchIngestVacanciesResponse,
    CreateVacancyRequest,
)


def test_raw_post_model() -> None:
    now = datetime.now(UTC)
    post = RawPost(
        channel_username="forpython",
        message_id=42,
        text="Vacancy text",
        date=now,
        url="https://t.me/forpython/42",
    )
    assert post.channel_username == "forpython"
    assert post.message_id == 42


def test_create_vacancy_request_contract() -> None:
    vacancy = CreateVacancyRequest(
        external_id="forpython_42",
        source="Telegram",
        title="Python Backend Developer",
        url="https://t.me/forpython/42",
        salary_text="от 250 000 руб.",
        company="FinFlow",
        location="Remote",
        description="Full text",
    )
    assert vacancy.external_id == "forpython_42"
    assert vacancy.source == "Telegram"

    batch = BatchCreateVacanciesRequest(vacancies=[vacancy])
    assert len(batch.vacancies) == 1

    resp = BatchIngestVacanciesResponse(inserted=1, ignored=0)
    assert resp.inserted == 1
    assert resp.ignored == 0


def test_create_vacancy_request_requires_mandatory_fields() -> None:
    with pytest.raises(ValidationError):
        CreateVacancyRequest.model_validate({"source": "Telegram"})


def test_channel_config() -> None:
    channel = ChannelConfig(
        username="test_chan",
        enabled=True,
        tags=["python"],
    )
    assert channel.username == "test_chan"
    assert channel.tags == ["python"]


def test_channels_config_file() -> None:
    config_file = ChannelsConfigFile(
        channels=[
            ChannelConfig(username="test_chan", enabled=True, tags=["python"]),
            ChannelConfig(username="other_chan", enabled=False),
        ]
    )
    assert len(config_file.channels) == 2
    assert config_file.channels[1].enabled is False
    assert config_file.channels[1].tags == []


def test_settings_defaults() -> None:
    settings = Settings()
    assert settings.poll_interval_seconds == 1800
    assert settings.batch_size == 50
    assert settings.backend_url == "http://localhost:8080/api/v1"
    assert settings.parser_api_key == "test_key"
