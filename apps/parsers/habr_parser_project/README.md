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
| `cli.py`, `__main__.py` | options and composition root |
