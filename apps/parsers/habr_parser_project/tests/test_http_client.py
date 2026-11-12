import asyncio

import httpx
import pytest

from habr_parser.config import HttpConfig
from habr_parser.http_client import FetchError, HabrHttpClient


def make_client(handler, **config):
    sleeps: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)

    config.setdefault("request_delay", 0.5)
    config.setdefault("max_retries", 2)
    client = HabrHttpClient(
        HttpConfig(**config),
        transport=httpx.MockTransport(handler),
        sleep=fake_sleep,
    )
    return client, sleeps


async def test_returns_body_and_sends_params_and_user_agent():
    seen: list[httpx.Request] = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, text="<html>ok</html>")

    client, _ = make_client(handler, user_agent="test-agent")

    body = await client.get_text("/vacancies", {"page": 2, "skill[]": [1, 2]})

    assert body == "<html>ok</html>"
    request = seen[0]
    assert request.url.host == "career.habr.com"
    assert request.url.path == "/vacancies"
    assert request.url.params.get_list("skill[]") == ["1", "2"]
    assert request.url.params["page"] == "2"
    assert request.headers["user-agent"] == "test-agent"


async def test_pauses_after_every_request():
    client, sleeps = make_client(lambda request: httpx.Response(200, text="x"))

    await client.get_text("/vacancies")

    assert sleeps == [0.5]


async def test_retries_server_errors_with_exponential_backoff():
    statuses = iter([503, 429, 200])

    def handler(request):
        status = next(statuses)
        return httpx.Response(status, text="done" if status == 200 else "")

    client, sleeps = make_client(handler)

    assert await client.get_text("/vacancies") == "done"
    assert sleeps == [1.0, 2.0, 0.5]  # backoff 0.5*2, 0.5*4, then the normal pause


async def test_retries_transport_errors():
    attempts = []

    def handler(request):
        attempts.append(1)
        if len(attempts) == 1:
            raise httpx.ConnectError("boom")
        return httpx.Response(200, text="recovered")

    client, _ = make_client(handler)

    assert await client.get_text("/vacancies") == "recovered"
    assert len(attempts) == 2


async def test_gives_up_after_max_retries():
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(503)

    client, _ = make_client(handler, max_retries=2)

    with pytest.raises(FetchError, match="/vacancies"):
        await client.get_text("/vacancies")
    assert len(calls) == 3  # first try + 2 retries


async def test_client_errors_are_not_retried():
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(404)

    client, _ = make_client(handler)

    with pytest.raises(FetchError, match="404"):
        await client.get_text("/vacancies/1")
    assert len(calls) == 1


async def test_concurrency_is_limited():
    running = peak = 0

    async def handler(request):
        nonlocal running, peak
        running += 1
        peak = max(peak, running)
        await asyncio.sleep(0)
        running -= 1
        return httpx.Response(200, text="x")

    client, _ = make_client(handler, concurrency=2)

    await asyncio.gather(*(client.get_text(f"/vacancies/{i}") for i in range(6)))

    assert peak == 2
