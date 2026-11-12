"""BaseParser.run() end to end: Habr and the backend are both mocked at the HTTP level."""

import json

import httpx

from habr_parser.config import SOURCE_NAME, HttpConfig
from habr_parser.grade import Grade
from habr_parser.http_client import HabrHttpClient
from habr_parser.parser import HabrParser
from parsers_base.sink.backend_api import BackendApiSink
from parsers_base.validation.validator import VacancyValidator
from tests.builders import make_list_html, make_vacancy_html

SHORT_DESCRIPTION = "<p>too short for the contract</p>"


def habr_handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path == "/vacancies":
        page = int(request.url.params["page"])
        return httpx.Response(200, text=make_list_html([1, 2, 3] if page == 1 else []))
    if path == "/vacancies/3":
        return httpx.Response(200, text=make_vacancy_html(description=SHORT_DESCRIPTION))
    vacancy_id = path.rsplit("/", 1)[-1]
    return httpx.Response(200, text=make_vacancy_html(title=f"Dev {vacancy_id}"))


async def test_valid_vacancies_reach_the_backend_in_contract_shape():
    posted: list[httpx.Request] = []

    def backend_handler(request: httpx.Request) -> httpx.Response:
        posted.append(request)
        count = len(json.loads(request.content)["vacancies"])
        return httpx.Response(200, json={"inserted": count, "ignored": 0})

    async def no_sleep(seconds: float) -> None:
        pass

    fetcher = HabrHttpClient(
        HttpConfig(), transport=httpx.MockTransport(habr_handler), sleep=no_sleep
    )
    backend = httpx.AsyncClient(
        base_url="http://backend/api/v1",
        transport=httpx.MockTransport(backend_handler),
        headers={"Content-Type": "application/json"},
    )
    sink = BackendApiSink("http://backend/api/v1", "key", client=backend)
    parser = HabrParser(
        sink, fetcher, validator=VacancyValidator(allowed_sources={SOURCE_NAME}), batch_size=10
    )

    stats = await parser.run(grades=[Grade.MIDDLE], max_pages=2)
    await fetcher.aclose()
    await sink.close()

    # vacancy 3 has a too short description and is dropped by the shared validator
    assert (stats.extracted, stats.valid, stats.invalid, stats.inserted) == (3, 2, 1, 2)
    [request] = posted
    assert request.url.path == "/api/v1/vacancies/batch"
    items = json.loads(request.content)["vacancies"]
    assert [item["external_id"] for item in items] == ["1", "2"]
    first = items[0]
    assert first["source"] == "habr"
    assert first["grade"] == "MIDDLE"
    assert first["employment_types"] == ["REMOTE"]
    assert first["salary"]["from"] == 200_000 and first["salary"]["currency"] == "RUB"
    assert first["url"] == "https://career.habr.com/vacancies/1"
    assert {"published_at", "parsed_at", "title", "description"} <= first.keys()
