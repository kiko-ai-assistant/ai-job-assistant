import json
import logging
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
import respx

import main as cli
from json_storage import JsonVacancyStorage
from models import RunStats, Vacancy

BACKEND_URL = "http://backend.test/api/v1"
ENDPOINT = f"{BACKEND_URL}/vacancies/batch"


@pytest.fixture(autouse=True)
def isolated_cli(monkeypatch, tmp_path):
    logger = logging.getLogger("test-main")
    monkeypatch.setattr(cli, "setup_logging", lambda: logger)
    monkeypatch.setenv("BACKEND_URL", BACKEND_URL)
    monkeypatch.setenv("PARSER_API_KEY", "test-parser-key")
    monkeypatch.delenv("BACKEND_BATCH_SIZE", raising=False)
    monkeypatch.delenv("BACKEND_TIMEOUT_SECONDS", raising=False)
    storage = replace(
        cli.CONFIG.storage,
        path=str(tmp_path / "vacancies.json"),
        unavailable_path=str(tmp_path / "unavailable.json"),
    )
    monkeypatch.setattr(cli, "CONFIG", replace(cli.CONFIG, storage=storage))


def make_vacancy(**changes):
    now = datetime.now(UTC)
    values = {
        "external_id": "123",
        "source": "hh.ru",
        "title": "Senior Python Developer",
        "company": "Test Company",
        "salary_text": None,
        "location": None,
        "description": "Build and maintain reliable Python backend services. " * 10,
        "url": "https://hh.ru/vacancy/123",
        "created_at": (now - timedelta(hours=1)).isoformat(),
        "parsed_at": now.isoformat(),
        "grade": "senior",
        "employment_types": ["remote"],
    }
    values.update(changes)
    return Vacancy(**values)


def storage():
    return JsonVacancyStorage(
        cli.CONFIG.storage.path,
        cli.CONFIG.storage.refresh_after_hours,
        logging.getLogger("test-main"),
    )


def save_vacancy(vacancy):
    queue = storage()
    queue.upsert(vacancy)
    queue.flush()


def forbid_collection(*args):
    pytest.fail("Send-only mode must not contact HH")


def test_default_mode_sends_just_collected_records(monkeypatch):
    vacancy = make_vacancy()

    def fake_run(scraper):
        scraper.storage.upsert(vacancy)
        scraper.storage.flush()
        return RunStats(parsed=1)

    monkeypatch.setattr(cli.HHScraper, "run", fake_run)

    with respx.mock as mock:
        route = mock.post(ENDPOINT).respond(200, json={"inserted": 1, "ignored": 0})
        result = cli.main(["--groups", "it", "--pages", "1"])

    assert result == 0
    assert route.call_count == 1
    payload = json.loads(route.calls.last.request.content)
    assert payload["vacancies"][0]["external_id"] == vacancy.external_id
    assert storage().pending() == []


def test_send_only_retries_saved_records_after_backend_failure(monkeypatch):
    vacancy = make_vacancy()
    save_vacancy(vacancy)
    monkeypatch.setattr(cli, "collect", forbid_collection)

    with respx.mock as mock:
        failed = mock.post(ENDPOINT).respond(500, json={"error": "Temporary outage"})
        assert cli.main(["--send-only"]) == 1

    assert storage().pending() == [vacancy]

    with respx.mock as mock:
        retried = mock.post(ENDPOINT).respond(200, json={"inserted": 0, "ignored": 1})
        assert cli.main(["--send-only"]) == 0

    assert json.loads(failed.calls.last.request.content) == json.loads(
        retried.calls.last.request.content
    )
    assert storage().pending() == []


def test_scrape_only_does_not_require_backend_credentials_or_send(monkeypatch):
    monkeypatch.delenv("BACKEND_URL")
    monkeypatch.delenv("PARSER_API_KEY")
    vacancy = make_vacancy()

    def fake_run(scraper):
        scraper.storage.upsert(vacancy)
        scraper.storage.flush()
        return RunStats(parsed=1)

    monkeypatch.setattr(cli.HHScraper, "run", fake_run)

    with respx.mock as mock:
        result = cli.main(["--scrape-only"])
        assert len(mock.calls) == 0

    assert result == 0
    assert storage().pending() == [vacancy]


def test_missing_backend_credentials_fails_before_collection(monkeypatch):
    monkeypatch.delenv("PARSER_API_KEY")
    monkeypatch.setattr(cli, "collect", forbid_collection)

    with respx.mock as mock:
        assert cli.main([]) == 1
        assert len(mock.calls) == 0


def test_send_only_requires_existing_json_file(monkeypatch, tmp_path):
    path = tmp_path / "missing.json"
    monkeypatch.setattr(cli, "collect", forbid_collection)

    with respx.mock as mock:
        assert cli.main(["--send-only", "--output", str(path)]) == 1
        assert len(mock.calls) == 0

    assert not path.exists()


def test_send_only_returns_incomplete_status_for_retained_invalid_record(monkeypatch):
    vacancy = make_vacancy(created_at=None)
    save_vacancy(vacancy)
    monkeypatch.setattr(cli, "collect", forbid_collection)

    with respx.mock as mock:
        assert cli.main(["--send-only"]) == 2
        assert len(mock.calls) == 0

    assert storage().pending() == [vacancy]


def test_incomplete_collection_still_delivers_saved_records(monkeypatch):
    vacancy = make_vacancy()

    def fake_run(scraper):
        scraper.storage.upsert(vacancy)
        scraper.storage.flush()
        return RunStats(parsed=1, failed=1)

    monkeypatch.setattr(cli.HHScraper, "run", fake_run)

    with respx.mock as mock:
        route = mock.post(ENDPOINT).respond(200, json={"inserted": 1, "ignored": 0})
        assert cli.main([]) == 2

    assert route.call_count == 1
    assert storage().pending() == []


def test_search_http_failure_returns_incomplete_status(monkeypatch):
    monkeypatch.setattr(
        cli.RequestManager,
        "get",
        lambda self, url: SimpleNamespace(status=500),
    )
    with respx.mock as mock:
        assert cli.main(["--scrape-only", "--groups", "it", "--pages", "1"]) == 2
        assert len(mock.calls) == 0


def test_corrupt_send_only_input_is_reported_without_overwriting(monkeypatch, tmp_path):
    path = tmp_path / "corrupt.json"
    path.write_text("{invalid", encoding="utf-8")
    monkeypatch.setattr(cli, "collect", forbid_collection)

    with respx.mock as mock:
        assert cli.main(["--send-only", "--output", str(path)]) == 1
        assert len(mock.calls) == 0

    assert path.read_text(encoding="utf-8") == "{invalid"


def test_cli_overrides_search_and_storage_settings(tmp_path):
    path = tmp_path / "custom.json"
    args = cli.parse_args(
        [
            "--groups",
            "it",
            "management",
            "--area",
            "2",
            "--employment",
            "part",
            "--pages",
            "2",
            "--refresh-hours",
            "0",
            "--output",
            str(path),
        ]
    )

    config = cli.build_config(args)

    assert config.search.enabled_groups == ("it", "management")
    assert config.search.area == "2"
    assert config.search.employment == "part"
    assert config.search.pages_override == 2
    assert config.storage.refresh_after_hours == 0
    assert config.storage.path == str(path)


@pytest.mark.parametrize(
    "args",
    [
        ["--pages", "0"],
        ["--pages", "-1"],
        ["--refresh-hours", "-1"],
        ["--refresh-hours", "nan"],
        ["--refresh-hours", "inf"],
        ["--send-only", "--scrape-only"],
    ],
)
def test_invalid_cli_options_exit_with_usage_error(args):
    with pytest.raises(SystemExit) as exc_info:
        cli.parse_args(args)

    assert exc_info.value.code == 2
