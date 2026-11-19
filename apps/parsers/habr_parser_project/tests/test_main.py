import json

import pytest

from habr_parser.cli import __main__ as entrypoint
from habr_parser.outcome import ExitCode
from tests.fakes import FakeHabrClient

ARGS = ["--grade", "junior", "--max-pages", "1"]


@pytest.fixture(autouse=True)
def no_backend_credentials(monkeypatch):
    monkeypatch.delenv("BACKEND_URL", raising=False)
    monkeypatch.delenv("PARSER_API_KEY", raising=False)


def test_dry_run_prints_vacancies_to_stdout_and_stats_to_stderr(monkeypatch, capsys):
    monkeypatch.setattr(
        entrypoint,
        "HabrHttpClient",
        lambda config: FakeHabrClient(lists={(3, 1): [1, 2]}),
    )

    code = entrypoint.main(["--dry-run", *ARGS])

    captured = capsys.readouterr()
    assert code == ExitCode.OK == 0
    assert [json.loads(line)["external_id"] for line in captured.out.splitlines()] == [
        "1",
        "2",
    ]
    assert json.loads(captured.err.splitlines()[-1])["extracted"] == 2


def test_nothing_extracted_gives_a_failing_exit_code(monkeypatch, capsys):
    monkeypatch.setattr(entrypoint, "HabrHttpClient", lambda config: FakeHabrClient())

    code = entrypoint.main(["--dry-run", *ARGS])

    assert code == ExitCode.NOTHING_EXTRACTED
    assert capsys.readouterr().out == ""


def test_real_mode_requires_backend_credentials():
    with pytest.raises(SystemExit, match="BACKEND_URL"):
        entrypoint.main(ARGS)


def test_real_mode_with_credentials_is_wired_up(monkeypatch):
    monkeypatch.setenv("BACKEND_URL", "http://backend.invalid/api/v1")
    monkeypatch.setenv("PARSER_API_KEY", "key")
    monkeypatch.setattr(entrypoint, "HabrHttpClient", lambda config: FakeHabrClient())

    # nothing is extracted, so the backend is never contacted
    assert entrypoint.main(ARGS) == ExitCode.NOTHING_EXTRACTED
