import logging

import pytest

import request_manager as module
from config import RequestConfig
from exceptions import CaptchaDetectedError
from request_manager import RequestManager


class FakePage:
    def __init__(self, status=200, url="https://hh.ru/test", body=b"", headers=None):
        self.status = status
        self.url = url
        self.body = body
        self.headers = headers or {}

    def css(self, selector):
        return []


def make_manager():
    return RequestManager(
        RequestConfig(
            min_delay_seconds=0,
            max_delay_seconds=0,
            max_retries=3,
            backoff_base_seconds=0,
            max_backoff_seconds=0,
        ),
        logging.getLogger("test-request-manager"),
    )


def test_403_retries_then_success(monkeypatch):
    responses = [FakePage(403), FakePage(403), FakePage(200)]
    monkeypatch.setattr(module, "_fetch", lambda *a, **k: responses.pop(0))
    monkeypatch.setattr(module.time, "sleep", lambda _: None)

    manager = make_manager()
    page = manager.get("https://hh.ru/test")

    assert page.status == 200
    assert manager.stats.http_403 == 2
    assert manager.stats.http_200 == 1
    assert manager.stats.retries == 2


def test_429_respects_retry_path(monkeypatch):
    responses = [
        FakePage(429, headers={"retry-after": "0"}),
        FakePage(200),
    ]
    monkeypatch.setattr(module, "_fetch", lambda *a, **k: responses.pop(0))
    monkeypatch.setattr(module.time, "sleep", lambda _: None)

    manager = make_manager()
    page = manager.get("https://hh.ru/test")

    assert page.status == 200
    assert manager.stats.http_429 == 1
    assert manager.stats.retries == 1


def test_captcha_detection(monkeypatch):
    response = FakePage(
        200,
        body="Подтвердите, что вы не робот".encode("utf-8"),
    )
    monkeypatch.setattr(module, "_fetch", lambda *a, **k: response)

    manager = make_manager()

    with pytest.raises(CaptchaDetectedError):
        manager.get("https://hh.ru/test")
