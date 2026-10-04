import pytest
import respx

from src.models.vacancy import CreateVacancyRequest
from src.sink.backend_api import BackendApiSink


@pytest.mark.asyncio
async def test_backend_api_sink_sends_batch_with_headers() -> None:
    backend_url = "http://backend.test/api/v1"
    api_key = "secret_parser_key"

    sample_vacancy = CreateVacancyRequest(
        external_id="forpython_101",
        source="Telegram",
        title="Senior Python Developer",
        url="https://t.me/forpython/101",
        company="FinFlow",
        salary_text="300 000 руб.",
    )

    with respx.mock(base_url=backend_url) as respx_mock:
        route = respx_mock.post("/vacancies/batch").respond(
            status_code=200,
            json={"inserted": 1, "ignored": 0},
        )

        sink = BackendApiSink(backend_url=backend_url, parser_api_key=api_key)
        resp = await sink.send_batch([sample_vacancy])

        assert resp.inserted == 1
        assert resp.ignored == 0
        assert route.called
        last_request = route.calls.last.request
        assert last_request.headers["X-Parser-Api-Key"] == api_key
        assert "vacancies" in last_request.content.decode()

        await sink.close()


@pytest.mark.asyncio
async def test_backend_api_sink_handles_empty_batch() -> None:
    sink = BackendApiSink(backend_url="http://test", parser_api_key="k")
    resp = await sink.send_batch([])
    assert resp.inserted == 0
    assert resp.ignored == 0
    await sink.close()
