# habr_parser

Habr Career vacancy parser for the Kiko backend, built on `parsers_base`
(`BaseParser` -> `BaseSink` -> `POST /vacancies/batch`).

```bash
pip install -e ".[dev]"          # parsers_base must be importable
pytest

export BACKEND_URL=http://localhost:8080/api/v1 PARSER_API_KEY=...
python -m habr_parser --query python --grade junior --grade middle \
    --skill 123 --location 678 --min-salary 150000 --max-pages 3
```

Dry run (no backend, no key needed): vacancies go to stdout as JSON Lines in the exact
wire format of `POST /vacancies/batch`; logs and final stats go to stderr.

```bash
python -m habr_parser --dry-run --grade junior --max-pages 1 > vacancies.jsonl
```

Exit codes: `0` ok, `1` unhandled error, `2` bad arguments, `3` nothing extracted
(Habr changed its markup, blocked us, or the filters match nothing) - alert on non-zero.

Contract tests read `contracts/openapi.yaml`; keep it in sync with the backend repository
(or set `OPENAPI_SPEC=/path/to/openapi.yaml`). Four scenarios are marked `xfail(strict=True)`:
the sink sends `null` where the contract declares non-nullable fields (see test_contract.py).

| Module | Responsibility |
|---|---|
| `config.py` | `HttpConfig`, `SOURCE_NAME`, `BASE_URL` |
| `grade.py` | `Grade` enum (API values) + Habr `qid` |
| `filters.py` | `SearchFilters` -> query parameters |
| `http_client.py` | `HabrHttpClient` (delay, retries, concurrency), `FetchError`, `HtmlFetcher` |
| `list_page.py` | list HTML -> vacancy ids |
| `vacancy_page.py` | vacancy HTML -> `VacancyPage` (JSON-LD `JobPosting`) |
| `salary.py`, `location.py`, `employment.py`, `dates.py`, `description.py` | field-level conversions |
| `mapper.py` | `VacancyPage` -> `CreateVacancyRequest` |
| `parser.py` | `HabrParser(BaseParser)` orchestration |
| `jsonl_sink.py` | `JsonlSink`: dry-run sink writing JSON Lines |
| `outcome.py` | `ExitCode`, `exit_code_for(stats)` |
| `app.py` | `run_app`: options + sink + fetcher -> stats |
| `cli.py`, `__main__.py` | options and composition root |
