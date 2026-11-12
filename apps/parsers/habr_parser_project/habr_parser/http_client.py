"""The only module that talks to Habr: polite, bounded and retrying HTTP."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Mapping
from types import TracebackType
from typing import Any, Protocol

import httpx

from .config import HttpConfig

_RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})


class FetchError(Exception):
    """A page could not be fetched (after retries, or because retrying is pointless)."""


class HtmlFetcher(Protocol):
    async def get_text(self, path: str, params: Mapping[str, Any] | None = None) -> str: ...


class HabrHttpClient:
    def __init__(
        self,
        config: HttpConfig | None = None,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self._config = config or HttpConfig()
        self._sleep = sleep
        self._slots = asyncio.Semaphore(self._config.concurrency)
        self._client = httpx.AsyncClient(
            base_url=self._config.base_url,
            headers={"User-Agent": self._config.user_agent, "Accept-Language": "ru,en;q=0.8"},
            timeout=self._config.timeout,
            follow_redirects=True,
            transport=transport,
        )

    async def get_text(self, path: str, params: Mapping[str, Any] | None = None) -> str:
        async with self._slots:
            try:
                return await self._get_with_retries(path, params)
            finally:
                await self._sleep(self._config.request_delay)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> HabrHttpClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def _get_with_retries(self, path: str, params: Mapping[str, Any] | None) -> str:
        attempts = self._config.max_retries + 1
        last_problem = "no attempt made"
        for attempt in range(attempts):
            if attempt:
                await self._sleep(self._config.request_delay * 2**attempt)
            try:
                response = await self._client.get(path, params=params)
            except httpx.TransportError as exc:
                last_problem = f"{type(exc).__name__}: {exc}"
                continue
            if response.status_code in _RETRY_STATUSES:
                last_problem = f"HTTP {response.status_code}"
                continue
            if response.is_error:
                raise FetchError(f"{path}: HTTP {response.status_code}")
            return response.text
        raise FetchError(f"{path}: gave up after {attempts} attempts ({last_problem})")
