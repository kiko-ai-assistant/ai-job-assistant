import json
from datetime import UTC, datetime

import httpx
import pytest
import respx

from parsers_base.models.vacancy import CreateVacancyRequest, LocationDTO, SalaryDTO
from parsers_base.sink import BackendApiSink, BaseSink, SinkError


def _create_sample_vacancy() -> CreateVacancyRequest:
    now = datetime.now(UTC)
    return CreateVacancyRequest(
        external_id="job_123",
        source="telegram",
        title="Backend Developer",
        company="TechCorp",
        salary=SalaryDTO.model_validate(
            {
                "text": "200k",
                "from": 200000,
                "to": 250000,
                "currency": "RUB",
            }
        ),
        grade="middle",
        employment_types=["remote"],
        location=LocationDTO(text="Remote", country="Russia", city="Moscow"),
        description="Senior backend engineer responsibilities..." * 10,
        url="https://t.me/job_channel/123",
        published_at=now,
        parsed_at=now,
    )


@pytest.mark.asyncio
async def test_backend_api_sink_implements_base_sink() -> None:
    sink = BackendApiSink(backend_url="http://localhost:8080", parser_api_key="test_key")
    assert isinstance(sink, BaseSink)
    await sink.close()


@pytest.mark.asyncio
async def test_backend_api_sink_handles_empty_batch() -> None:
    sink = BackendApiSink(backend_url="http://localhost:8080", parser_api_key="test_key")
    resp = await sink.send_batch([])
    assert resp.inserted == 0
    assert resp.ignored == 0
    await sink.close()


@pytest.mark.asyncio
async def test_backend_api_sink_sends_batch_with_headers_and_payload() -> None:
    backend_url = "http://backend.local/api/v1"
    api_key = "secret_key"
    vacancy = _create_sample_vacancy()
    vacancy.raw_text = "Internal collection data"
    assert vacancy.salary is not None
    vacancy.salary.gross = True

    with respx.mock(base_url=backend_url) as respx_mock:
        route = respx_mock.post("/vacancies/batch").respond(
            status_code=200,
            json={"inserted": 1, "ignored": 0},
        )

        sink = BackendApiSink(backend_url=backend_url, parser_api_key=api_key)
        resp = await sink.send_batch([vacancy])

        assert resp.inserted == 1
        assert resp.ignored == 0
        assert route.called

        last_request = route.calls.last.request
        assert last_request.headers["X-Parser-Api-Key"] == api_key
        assert last_request.headers["Content-Type"] == "application/json"

        body = last_request.content.decode()
        serialized = json.loads(body)["vacancies"][0]
        assert "raw_text" not in serialized
        assert "gross" not in serialized["salary"]
        assert "job_123" in body
        assert '"from":200000' in body or '"from": 200000' in body

        await sink.close()


@pytest.mark.asyncio
async def test_backend_api_sink_omits_absent_optional_objects() -> None:
    vacancy = _create_sample_vacancy()
    vacancy.salary = None
    vacancy.location = None
    with respx.mock as mock:
        route = mock.post("http://backend.local/api/v1/vacancies/batch").respond(
            200, json={"inserted": 1, "ignored": 0}
        )
        async with BackendApiSink("http://backend.local/api/v1", "key") as sink:
            await sink.send_batch([vacancy])
    serialized = json.loads(route.calls.last.request.content)["vacancies"][0]
    assert "salary" not in serialized
    assert "location" not in serialized
    assert "raw_text" not in serialized


@pytest.mark.asyncio
async def test_backend_api_sink_raises_sink_error_on_500() -> None:
    backend_url = "http://backend.local/api/v1"
    vacancy = _create_sample_vacancy()

    with respx.mock(base_url=backend_url) as respx_mock:
        respx_mock.post("/vacancies/batch").respond(
            status_code=500,
            text="Internal Server Error",
        )

        sink = BackendApiSink(backend_url=backend_url, parser_api_key="key")
        with pytest.raises(SinkError) as exc_info:
            await sink.send_batch([vacancy])

        assert "500" in str(exc_info.value)
        await sink.close()


@pytest.mark.asyncio
async def test_backend_api_sink_raises_sink_error_on_4xx() -> None:
    backend_url = "http://backend.local/api/v1"
    vacancy = _create_sample_vacancy()

    with respx.mock(base_url=backend_url) as respx_mock:
        respx_mock.post("/vacancies/batch").respond(
            status_code=401,
            text="Unauthorized",
        )

        sink = BackendApiSink(backend_url=backend_url, parser_api_key="wrong_key")
        with pytest.raises(SinkError) as exc_info:
            await sink.send_batch([vacancy])

        assert "401" in str(exc_info.value)
        await sink.close()


@pytest.mark.asyncio
async def test_backend_api_sink_raises_sink_error_on_connection_failure() -> None:
    backend_url = "http://backend.local/api/v1"
    vacancy = _create_sample_vacancy()

    with respx.mock(base_url=backend_url) as respx_mock:
        respx_mock.post("/vacancies/batch").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        sink = BackendApiSink(backend_url=backend_url, parser_api_key="key")
        with pytest.raises(SinkError) as exc_info:
            await sink.send_batch([vacancy])

        err_msg = str(exc_info.value)
        assert "Connection refused" in err_msg or "request failed" in err_msg
        await sink.close()


@pytest.mark.asyncio
async def test_backend_api_sink_context_manager() -> None:
    backend_url = "http://backend.local/api/v1"

    async with BackendApiSink(backend_url=backend_url, parser_api_key="key") as sink:
        resp = await sink.send_batch([])
        assert resp.inserted == 0
        assert resp.ignored == 0

    assert sink.client.is_closed
