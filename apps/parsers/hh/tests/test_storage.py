import json
import logging
from datetime import datetime, timedelta, timezone

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
    storage.upsert(make_vacancy(datetime.now(timezone.utc).isoformat()))
    storage.flush()

    reloaded = JsonVacancyStorage(str(path), 24, logger)
    assert reloaded.count() == 1
    assert reloaded.contains("hh.ru", "123")
    assert reloaded.should_refresh("hh.ru", "123") is False


def test_storage_refreshes_old_item(tmp_path):
    path = tmp_path / "vacancies.json"
    logger = logging.getLogger("test-storage-old")
    old = datetime.now(timezone.utc) - timedelta(hours=25)
    storage = JsonVacancyStorage(str(path), 24, logger)
    storage.upsert(make_vacancy(old.isoformat()))
    storage.flush()

    assert storage.should_refresh("hh.ru", "123") is True
