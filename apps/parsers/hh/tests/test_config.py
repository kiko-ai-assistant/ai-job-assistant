import pytest

from config import BackendConfig


@pytest.fixture(autouse=True)
def clear_backend_environment(monkeypatch):
    for name in (
        "BACKEND_URL",
        "PARSER_API_KEY",
        "BACKEND_BATCH_SIZE",
        "BACKEND_TIMEOUT_SECONDS",
    ):
        monkeypatch.delenv(name, raising=False)


@pytest.mark.parametrize("missing", ["BACKEND_URL", "PARSER_API_KEY"])
def test_backend_config_requires_credentials(monkeypatch, missing):
    monkeypatch.setenv("BACKEND_URL", "http://backend.test/api/v1")
    monkeypatch.setenv("PARSER_API_KEY", "test-parser-key")
    monkeypatch.delenv(missing)

    with pytest.raises(ValueError, match=missing):
        BackendConfig.from_env()


@pytest.mark.parametrize("empty", ["BACKEND_URL", "PARSER_API_KEY"])
def test_backend_config_rejects_empty_credentials(monkeypatch, empty):
    monkeypatch.setenv("BACKEND_URL", "http://backend.test/api/v1")
    monkeypatch.setenv("PARSER_API_KEY", "test-parser-key")
    monkeypatch.setenv(empty, "   ")

    with pytest.raises(ValueError, match=empty):
        BackendConfig.from_env()


def test_backend_config_reads_environment_at_call_time(monkeypatch):
    monkeypatch.setenv("BACKEND_URL", "http://backend.test/api/v1")
    monkeypatch.setenv("PARSER_API_KEY", "test-parser-key")

    config = BackendConfig.from_env()

    assert config.base_url == "http://backend.test/api/v1"
    assert config.api_key == "test-parser-key"
    assert config.batch_size == 50
    assert config.timeout_seconds == 15


def test_backend_config_accepts_batch_and_timeout_overrides(monkeypatch):
    monkeypatch.setenv("BACKEND_URL", "https://backend.test/api/v1/")
    monkeypatch.setenv("PARSER_API_KEY", "test-parser-key")
    monkeypatch.setenv("BACKEND_BATCH_SIZE", "7")
    monkeypatch.setenv("BACKEND_TIMEOUT_SECONDS", "2.5")

    config = BackendConfig.from_env()

    assert config.base_url == "https://backend.test/api/v1"
    assert config.batch_size == 7
    assert config.timeout_seconds == 2.5
    assert "test-parser-key" not in repr(config)


@pytest.mark.parametrize(
    "name,value",
    [
        ("BACKEND_BATCH_SIZE", "0"),
        ("BACKEND_BATCH_SIZE", "-1"),
        ("BACKEND_BATCH_SIZE", "1.5"),
        ("BACKEND_TIMEOUT_SECONDS", "0"),
        ("BACKEND_TIMEOUT_SECONDS", "-1"),
        ("BACKEND_TIMEOUT_SECONDS", "nan"),
        ("BACKEND_TIMEOUT_SECONDS", "inf"),
    ],
)
def test_backend_config_rejects_invalid_numeric_settings(monkeypatch, name, value):
    monkeypatch.setenv("BACKEND_URL", "http://backend.test/api/v1")
    monkeypatch.setenv("PARSER_API_KEY", "test-parser-key")
    monkeypatch.setenv(name, value)

    with pytest.raises(ValueError):
        BackendConfig.from_env()


@pytest.mark.parametrize(
    "url",
    [
        "backend.test/api/v1",
        "ftp://backend.test/api/v1",
        "https://user:password@backend.test/api/v1",
        "https://backend.test/api/v1?key=secret",
        "https://backend.test/api/v1#fragment",
    ],
)
def test_backend_config_rejects_invalid_base_urls(monkeypatch, url):
    monkeypatch.setenv("BACKEND_URL", url)
    monkeypatch.setenv("PARSER_API_KEY", "test-parser-key")

    with pytest.raises(ValueError, match="BACKEND_URL"):
        BackendConfig.from_env()
