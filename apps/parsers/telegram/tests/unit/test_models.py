from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from src.config import Settings
from src.models.channel import ChannelConfig, ChannelsConfigFile
from src.models.raw_post import RawPost
from src.models.vacancy import (
    BatchCreateVacanciesRequest,
    BatchCreateVacanciesResponse,
    BatchIngestVacanciesResponse,
    CreateVacancyRequest,
    LocationDTO,
    SalaryDTO,
)


@pytest.mark.parametrize(
    ("input_data", "expected_from", "expected_to", "expected_currency", "expected_text"),
    [
        (
            {"text": "100k-150k", "from_": 100000, "to": 150000, "currency": "USD"},
            100000,
            150000,
            "USD",
            "100k-150k",
        ),
        (
            {"from_": 200000},
            200000,
            None,
            None,
            None,
        ),
        (
            {"to": 300000, "currency": "RUB"},
            None,
            300000,
            "RUB",
            None,
        ),
        (
            {},
            None,
            None,
            None,
            None,
        ),
    ],
)
def test_salary_dto_instantiation_and_dump(
    input_data: dict[str, Any],
    expected_from: int | None,
    expected_to: int | None,
    expected_currency: str | None,
    expected_text: str | None,
) -> None:
    salary = SalaryDTO(**input_data)
    assert salary.from_ == expected_from
    assert salary.to == expected_to
    assert salary.currency == expected_currency
    assert salary.text == expected_text

    dumped = salary.model_dump(by_alias=True)
    assert dumped["from"] == expected_from
    assert "from_" not in dumped

    dumped_json = salary.model_dump_json(by_alias=True)
    if expected_from is not None:
        assert f'"from":{expected_from}' in dumped_json or f'"from": {expected_from}' in dumped_json


@pytest.mark.parametrize(
    ("payload", "expected_from", "expected_to", "expected_currency"),
    [
        (
            {"text": "от 5000$", "from": 5000, "to": 7000, "currency": "USD"},
            5000,
            7000,
            "USD",
        ),
        (
            {"from": 120000},
            120000,
            None,
            None,
        ),
        (
            {"from_": 80000, "currency": "EUR"},
            80000,
            None,
            "EUR",
        ),
    ],
)
def test_salary_dto_deserialization(
    payload: dict[str, Any],
    expected_from: int | None,
    expected_to: int | None,
    expected_currency: str | None,
) -> None:
    salary = SalaryDTO.model_validate(payload)
    assert salary.from_ == expected_from
    assert salary.to == expected_to
    assert salary.currency == expected_currency


@pytest.mark.parametrize(
    ("payload", "expected_text", "expected_country", "expected_city"),
    [
        (
            {"text": "Remote, Cyprus", "country": "Cyprus", "city": "Limassol"},
            "Remote, Cyprus",
            "Cyprus",
            "Limassol",
        ),
        (
            {"text": "Remote"},
            "Remote",
            None,
            None,
        ),
        (
            {"country": "Germany", "city": "Berlin"},
            None,
            "Germany",
            "Berlin",
        ),
        (
            {},
            None,
            None,
            None,
        ),
    ],
)
def test_location_dto(
    payload: dict[str, Any],
    expected_text: str | None,
    expected_country: str | None,
    expected_city: str | None,
) -> None:
    location = LocationDTO.model_validate(payload)
    assert location.text == expected_text
    assert location.country == expected_country
    assert location.city == expected_city


@pytest.mark.parametrize(
    ("payload", "expected_source", "expected_grade", "expected_salary_from", "expected_city"),
    [
        (
            {
                "external_id": "job_1",
                "title": "Senior Go Developer",
                "grade": "Senior",
                "description": "Full vacancy description",
                "url": "https://t.me/jobs/1",
                "published_at": datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
                "parsed_at": datetime(2026, 1, 1, 12, 5, tzinfo=UTC),
                "salary": {"from": 3000, "to": 5000, "currency": "USD"},
                "location": {"city": "Berlin", "country": "Germany"},
                "employment_types": ["remote", "full-time"],
                "company": "Tech Corp",
            },
            "telegram",
            "Senior",
            3000,
            "Berlin",
        ),
        (
            {
                "external_id": "job_2",
                "source": "custom_channel",
                "title": "Junior Python Dev",
                "grade": "Junior",
                "description": "Desc",
                "url": "https://t.me/jobs/2",
                "published_at": datetime(2026, 1, 2, 8, 0, tzinfo=UTC),
                "parsed_at": datetime(2026, 1, 2, 8, 1, tzinfo=UTC),
            },
            "custom_channel",
            "Junior",
            None,
            None,
        ),
    ],
)
def test_create_vacancy_request_valid(
    payload: dict[str, Any],
    expected_source: str,
    expected_grade: str,
    expected_salary_from: int | None,
    expected_city: str | None,
) -> None:
    vacancy = CreateVacancyRequest.model_validate(payload)
    assert vacancy.external_id == payload["external_id"]
    assert vacancy.source == expected_source
    assert vacancy.grade == expected_grade
    assert vacancy.title == payload["title"]
    if vacancy.salary:
        assert vacancy.salary.from_ == expected_salary_from
    if vacancy.location:
        assert vacancy.location.city == expected_city

    dumped = vacancy.model_dump(by_alias=True)
    if vacancy.salary:
        assert dumped["salary"]["from"] == expected_salary_from
        assert "from_" not in dumped["salary"]


@pytest.mark.parametrize(
    "missing_field",
    [
        "external_id",
        "title",
        "grade",
        "description",
        "url",
        "published_at",
        "parsed_at",
    ],
)
def test_create_vacancy_request_validation_errors(missing_field: str) -> None:
    valid_data: dict[str, Any] = {
        "external_id": "valid_id",
        "title": "Backend Developer",
        "grade": "Middle",
        "description": "Some description",
        "url": "https://t.me/jobs/10",
        "published_at": datetime.now(UTC),
        "parsed_at": datetime.now(UTC),
    }
    valid_data.pop(missing_field)
    with pytest.raises(ValidationError):
        CreateVacancyRequest.model_validate(valid_data)


@pytest.mark.parametrize(
    ("vacancy_count", "inserted", "ignored"),
    [
        (0, 0, 0),
        (2, 2, 0),
        (1, 0, 1),
    ],
)
def test_batch_create_vacancies(
    vacancy_count: int,
    inserted: int,
    ignored: int,
) -> None:
    now = datetime.now(UTC)
    vacancies = [
        CreateVacancyRequest(
            external_id=f"ext_{idx}",
            title="Engineer",
            grade="Middle",
            description="Work",
            url=f"https://t.me/jobs/{idx}",
            published_at=now,
            parsed_at=now,
        )
        for idx in range(vacancy_count)
    ]
    batch_req = BatchCreateVacanciesRequest(vacancies=vacancies)
    assert len(batch_req.vacancies) == vacancy_count

    resp = BatchCreateVacanciesResponse(inserted=inserted, ignored=ignored)
    assert resp.inserted == inserted
    assert resp.ignored == ignored

    ingest_resp = BatchIngestVacanciesResponse(inserted=inserted, ignored=ignored)
    assert isinstance(ingest_resp, BatchCreateVacanciesResponse)
    assert ingest_resp.inserted == inserted
    assert ingest_resp.ignored == ignored


@pytest.mark.parametrize(
    ("username", "enabled", "tags"),
    [
        ("python_jobs", True, ["python", "backend"]),
        ("empty_channel", False, []),
    ],
)
def test_channel_config(username: str, enabled: bool, tags: list[str]) -> None:
    config = ChannelConfig(username=username, enabled=enabled, tags=tags)
    assert config.username == username
    assert config.enabled is enabled
    assert config.tags == tags


def test_channels_config_file() -> None:
    file_cfg = ChannelsConfigFile(
        channels=[
            ChannelConfig(username="chan_1", enabled=True, tags=["go"]),
            ChannelConfig(username="chan_2", enabled=False),
        ]
    )
    assert len(file_cfg.channels) == 2
    assert file_cfg.channels[0].username == "chan_1"
    assert file_cfg.channels[1].tags == []


def test_raw_post() -> None:
    now = datetime.now(UTC)
    post = RawPost(
        channel_username="channel_test",
        message_id=123,
        text="Sample vacancy post",
        date=now,
        url="https://t.me/channel_test/123",
    )
    assert post.channel_username == "channel_test"
    assert post.message_id == 123
    assert post.text == "Sample vacancy post"
    assert post.date == now
    assert post.url == "https://t.me/channel_test/123"


@pytest.mark.parametrize(
    ("init_kwargs", "expected_backend_key", "expected_db_path", "expected_llm_model"),
    [
        (
            {},
            "",
            Path("data/state.sqlite"),
            "meta-llama/llama-3.3-70b-instruct:free",
        ),
        (
            {
                "backend_api_key": "backend_secret",
                "state_storage_path": Path("custom/state.sqlite"),
                "llm_model": "custom/model",
            },
            "backend_secret",
            Path("custom/state.sqlite"),
            "custom/model",
        ),
        (
            {
                "parser_api_key": "parser_secret",
                "sqlite_db_path": Path("storage/sqlite.db"),
            },
            "parser_secret",
            Path("storage/sqlite.db"),
            "meta-llama/llama-3.3-70b-instruct:free",
        ),
    ],
)
def test_settings_configuration(
    init_kwargs: dict[str, Any],
    expected_backend_key: str,
    expected_db_path: Path,
    expected_llm_model: str,
) -> None:
    settings = Settings(**init_kwargs)
    assert settings.backend_api_key == expected_backend_key
    assert settings.parser_api_key == expected_backend_key
    assert settings.state_storage_path == expected_db_path
    assert settings.sqlite_db_path == expected_db_path
    assert settings.llm_model == expected_llm_model
    assert settings.backend_url == "http://localhost:8080/api/v1"
    assert settings.poll_interval_seconds == 1800
    assert settings.batch_size == 50
    assert settings.llm_timeout == 30.0
    assert settings.llm_base_url == "https://openrouter.ai/api/v1"
