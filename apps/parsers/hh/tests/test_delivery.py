import json
import logging
from datetime import UTC, datetime, timedelta

import httpx
import pytest
import respx
from parsers_base import BackendApiSink, SinkError

from backend_client import HHBackendParser
from json_storage import JsonVacancyStorage
from models import Vacancy

BACKEND_URL = "http://backend.test/api/v1"
ENDPOINT = f"{BACKEND_URL}/vacancies/batch"
API_KEY = "test-parser-key"


def make_vacancy(external_id="123", **changes):
    now = datetime.now(UTC)
    values = {
        "external_id": external_id,
        "source": "hh.ru",
        "title": "Senior Python Developer",
        "company": "Test Company",
        "salary_text": None,
        "location": None,
        "description": "Build and maintain reliable Python backend services. " * 10,
        "url": f"https://hh.ru/vacancy/{external_id}",
        "created_at": (now - timedelta(hours=1)).isoformat(),
        "parsed_at": now.isoformat(),
        "grade": "senior",
        "employment_types": ["remote"],
    }
    values.update(changes)
    return Vacancy(**values)


def open_storage(path):
    return JsonVacancyStorage(str(path), 24, logging.getLogger("test-delivery"))


def save_vacancies(path, vacancies):
    storage = open_storage(path)
    for vacancy in vacancies:
        storage.upsert(vacancy)
    storage.flush()
    return storage


async def deliver(storage, batch_size=50):
    async with BackendApiSink(BACKEND_URL, API_KEY) as sink:
        parser = HHBackendParser(storage, sink, batch_size=batch_size)
        return await parser.run()


@pytest.mark.asyncio
async def test_delivery_sends_contract_payload_and_acknowledges_raw_key(tmp_path):
    path = tmp_path / "vacancies.json"
    vacancy = make_vacancy()
    storage = save_vacancies(path, [vacancy])

    with respx.mock as mock:
        route = mock.post(ENDPOINT).respond(200, json={"inserted": 1, "ignored": 0})
        stats = await deliver(storage)

    request = route.calls.last.request
    body = json.loads(request.content)
    assert request.headers["X-Parser-Api-Key"] == API_KEY
    assert request.headers["Content-Type"] == "application/json"
    assert "Authorization" not in request.headers
    assert set(body) == {"vacancies"}
    assert len(body["vacancies"]) == 1
    payload = body["vacancies"][0]
    assert payload["source"] == "hh"
    assert payload["external_id"] == vacancy.external_id
    assert payload["grade"] == "SENIOR"
    assert payload["employment_types"] == ["REMOTE"]
    assert datetime.fromisoformat(payload["published_at"]) == datetime.fromisoformat(
        vacancy.created_at
    )
    assert datetime.fromisoformat(payload["parsed_at"]) == datetime.fromisoformat(vacancy.parsed_at)
    assert "salary" not in payload
    assert "location" not in payload
    assert "created_at" not in payload
    assert stats.inserted == 1
    assert stats.ignored == 0
    assert open_storage(path).pending() == []
    stored = json.loads(path.read_text(encoding="utf-8"))[0]
    assert stored["source"] == "hh.ru"
    assert stored["_backend_delivered"] is True


@pytest.mark.asyncio
async def test_empty_queue_does_not_send_http(tmp_path):
    with respx.mock as mock:
        stats = await deliver(open_storage(tmp_path / "vacancies.json"))
        assert len(mock.calls) == 0
    assert stats.extracted == 0


@pytest.mark.asyncio
async def test_delivery_chunks_pending_records(tmp_path):
    path = tmp_path / "vacancies.json"
    storage = save_vacancies(path, [make_vacancy(str(index)) for index in range(5)])

    def accept(request):
        count = len(json.loads(request.content)["vacancies"])
        return httpx.Response(200, json={"inserted": count, "ignored": 0})

    with respx.mock as mock:
        route = mock.post(ENDPOINT).mock(side_effect=accept)
        stats = await deliver(storage, batch_size=2)

    batches = [json.loads(call.request.content)["vacancies"] for call in route.calls]
    assert [len(batch) for batch in batches] == [2, 2, 1]
    assert [item["external_id"] for batch in batches for item in batch] == [
        str(index) for index in range(5)
    ]
    assert stats.inserted == 5
    assert open_storage(path).pending() == []


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", [401, 422, 500, "timeout", "invalid_json", "bad_schema"])
async def test_failed_delivery_survives_reload_and_can_be_retried(tmp_path, failure):
    path = tmp_path / "vacancies.json"
    vacancy = make_vacancy()
    storage = save_vacancies(path, [vacancy])

    with respx.mock as mock:
        route = mock.post(ENDPOINT)
        if failure == "timeout":
            route.mock(side_effect=httpx.ReadTimeout("Simulated backend timeout"))
        elif failure == "invalid_json":
            route.respond(200, text="not json")
        elif failure == "bad_schema":
            route.respond(200, json={"inserted": 1})
        else:
            route.respond(failure, json={"error": "Simulated backend refusal"})
        with pytest.raises(SinkError):
            await deliver(storage)

    reloaded = open_storage(path)
    assert [item.key for item in reloaded.pending()] == [vacancy.key]
    assert reloaded.should_refresh(*vacancy.key) is False

    with respx.mock as mock:
        retry = mock.post(ENDPOINT).respond(200, json={"inserted": 0, "ignored": 1})
        stats = await deliver(reloaded)

    assert json.loads(route.calls.last.request.content) == json.loads(
        retry.calls.last.request.content
    )
    assert stats.ignored == 1
    assert open_storage(path).pending() == []


@pytest.mark.asyncio
async def test_partial_run_keeps_only_unacknowledged_batches_pending(tmp_path):
    path = tmp_path / "vacancies.json"
    storage = save_vacancies(path, [make_vacancy(str(index)) for index in range(3)])

    with respx.mock as mock:
        route = mock.post(ENDPOINT).mock(
            side_effect=[
                httpx.Response(200, json={"inserted": 1, "ignored": 1}),
                httpx.Response(500, json={"error": "Temporary backend outage"}),
            ]
        )
        with pytest.raises(SinkError):
            await deliver(storage, batch_size=2)

    assert route.call_count == 2
    assert [item.external_id for item in open_storage(path).pending()] == ["2"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "counts",
    [
        {"inserted": 0, "ignored": 0},
        {"inserted": 2, "ignored": 0},
        {"inserted": -1, "ignored": 2},
        {"inserted": 2, "ignored": -1},
        {"inserted": True, "ignored": False},
        {"inserted": "1", "ignored": "0"},
        {"inserted": 1.0, "ignored": 0.0},
    ],
)
async def test_inconsistent_acknowledgement_keeps_records_pending(tmp_path, counts):
    path = tmp_path / "vacancies.json"
    storage = save_vacancies(path, [make_vacancy()])

    with respx.mock as mock:
        mock.post(ENDPOINT).respond(200, json=counts)
        with pytest.raises(SinkError):
            await deliver(storage)

    assert len(open_storage(path).pending()) == 1


@pytest.mark.asyncio
async def test_invalid_records_are_retained_and_valid_records_still_send(tmp_path):
    path = tmp_path / "vacancies.json"
    storage = save_vacancies(
        path,
        [
            make_vacancy("missing-date", created_at=None),
            make_vacancy("short-description", description="Too short"),
            make_vacancy("valid"),
        ],
    )

    with respx.mock as mock:
        route = mock.post(ENDPOINT).respond(200, json={"inserted": 1, "ignored": 0})
        async with BackendApiSink(BACKEND_URL, API_KEY) as sink:
            parser = HHBackendParser(storage, sink)
            stats = await parser.run()

    assert parser.conversion_errors == 1
    assert stats.invalid == 1
    assert stats.inserted == 1
    assert [
        item["external_id"] for item in json.loads(route.calls.last.request.content)["vacancies"]
    ] == ["valid"]
    assert {item.external_id for item in open_storage(path).pending()} == {
        "missing-date",
        "short-description",
    }


@pytest.mark.asyncio
async def test_source_alias_does_not_acknowledge_invalid_record(tmp_path):
    path = tmp_path / "vacancies.json"
    storage = save_vacancies(
        path,
        [
            make_vacancy("123", source="hh.ru"),
            make_vacancy("123", source="hh", description="Too short"),
            make_vacancy("456"),
        ],
    )

    with respx.mock as mock:
        route = mock.post(ENDPOINT).respond(200, json={"inserted": 2, "ignored": 0})
        stats = await deliver(storage, batch_size=2)

    payload = json.loads(route.calls.last.request.content)["vacancies"]
    assert [item["external_id"] for item in payload] == ["123", "456"]
    assert stats.inserted == 2
    assert stats.invalid == 1
    assert [item.key for item in open_storage(path).pending()] == [("hh", "123")]
