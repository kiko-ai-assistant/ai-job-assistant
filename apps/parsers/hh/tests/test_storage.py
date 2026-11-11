import json
import logging
from datetime import UTC, datetime, timedelta

import pytest

from json_storage import JsonVacancyStorage
from models import Vacancy


def make_vacancy(parsed_at: str) -> Vacancy:
    return Vacancy(
        external_id="123",
        source="hh.ru",
        title="Python Developer",
        company="Test",
        salary_text=None,
        location="Moscow",
        description="Description",
        url="https://hh.ru/vacancy/123",
        created_at=None,
        parsed_at=parsed_at,
    )


def test_storage_upsert_and_reload(tmp_path):
    path = tmp_path / "vacancies.json"
    logger = logging.getLogger("test-storage")
    storage = JsonVacancyStorage(str(path), 24, logger)
    storage.upsert(make_vacancy(datetime.now(UTC).isoformat()))
    storage.flush()

    reloaded = JsonVacancyStorage(str(path), 24, logger)
    assert reloaded.count() == 1
    assert reloaded.contains("hh.ru", "123")
    assert reloaded.should_refresh("hh.ru", "123") is False


def test_storage_refreshes_old_item(tmp_path):
    path = tmp_path / "vacancies.json"
    logger = logging.getLogger("test-storage-old")
    old = datetime.now(UTC) - timedelta(hours=25)
    storage = JsonVacancyStorage(str(path), 24, logger)
    storage.upsert(make_vacancy(old.isoformat()))
    storage.flush()

    assert storage.should_refresh("hh.ru", "123") is True


def test_legacy_json_records_are_pending(tmp_path):
    path = tmp_path / "vacancies.json"
    vacancy = make_vacancy(datetime.now(UTC).isoformat())
    legacy = vacancy.to_dict()
    for field in (
        "grade",
        "employment_types",
        "salary_from",
        "salary_to",
        "salary_currency",
        "location_country",
        "location_city",
    ):
        del legacy[field]
    path.write_text(json.dumps([legacy]), encoding="utf-8")

    storage = JsonVacancyStorage(str(path), 24, logging.getLogger("test-legacy"))

    assert storage.pending() == [vacancy]


def test_acknowledgement_survives_reload_and_upsert_makes_record_pending(tmp_path):
    path = tmp_path / "vacancies.json"
    logger = logging.getLogger("test-acknowledgement")
    vacancy = make_vacancy(datetime.now(UTC).isoformat())
    storage = JsonVacancyStorage(str(path), 24, logger)
    storage.upsert(vacancy)
    storage.flush()
    storage.mark_delivered([vacancy.key])

    reloaded = JsonVacancyStorage(str(path), 24, logger)
    assert reloaded.pending() == []
    assert reloaded.count() == 1

    reloaded.upsert(vacancy)
    reloaded.flush()
    assert JsonVacancyStorage(str(path), 24, logger).pending() == [vacancy]


@pytest.mark.parametrize("payload", ["{broken-json", "{}", '[{"source": "hh.ru"}]'])
def test_corrupted_storage_is_reported_without_overwriting(tmp_path, payload):
    path = tmp_path / "vacancies.json"
    path.write_text(payload, encoding="utf-8")

    with pytest.raises(ValueError):
        JsonVacancyStorage(str(path), 24, logging.getLogger("test-corrupt"))

    assert path.read_text(encoding="utf-8") == payload


def test_failed_acknowledgement_write_preserves_pending_record(tmp_path, monkeypatch):
    path = tmp_path / "vacancies.json"
    logger = logging.getLogger("test-acknowledgement-failure")
    vacancy = make_vacancy(datetime.now(UTC).isoformat())
    storage = JsonVacancyStorage(str(path), 24, logger)
    storage.upsert(vacancy)
    storage.flush()
    original = path.read_bytes()

    def fail_flush():
        raise OSError("Simulated storage write failure")

    monkeypatch.setattr(storage, "flush", fail_flush)
    with pytest.raises(OSError, match="storage write failure"):
        storage.mark_delivered([vacancy.key])

    assert storage.pending() == [vacancy]
    assert path.read_bytes() == original
    assert JsonVacancyStorage(str(path), 24, logger).pending() == [vacancy]
