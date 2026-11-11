# HH parser and backend delivery

Collect HH vacancies into a durable local JSON queue and send validated batches to the Kiko backend through `kiko-parsers-base`

## Install

Run from the repository root with Python 3.12+ and the existing `.venv`

```powershell
.venv/Scripts/python.exe -m pip install -e apps/parsers/base -r apps/parsers/hh/requirements.txt
```

Install the shared package and HH dependencies together so pip resolves `kiko-parsers-base` from this checkout rather than a public registry

For development checks, install the existing base development extras

```powershell
.venv/Scripts/python.exe -m pip install -e "apps/parsers/base[dev]"
```

The static Scrapling `Fetcher` does not require browser installation

## Configure

Set environment variables in the shell or in the PyCharm run configuration
`.env.example` documents the variables; `.env` files are not loaded automatically

```powershell
$env:BACKEND_URL = "http://localhost:8080/api/v1"
$env:PARSER_API_KEY = "<your-parser-key>"
$env:BACKEND_BATCH_SIZE = "50"
$env:BACKEND_TIMEOUT_SECONDS = "15"
```

`BACKEND_URL` must include the API prefix `/api/v1`
The parser sends `X-Parser-Api-Key`, not Bearer authentication
Batch size and timeout are optional, positive settings with defaults of 50 records and 15 seconds
The key is required for delivery and is never stored in JSON

## Run

Collect and send from the repository root

```powershell
.venv/Scripts/python.exe apps/parsers/hh/main.py --groups it --area 1 --pages 2
```

Retry pending records without requesting any HH pages

```powershell
.venv/Scripts/python.exe apps/parsers/hh/main.py --send-only
```

Collect locally without backend configuration

```powershell
.venv/Scripts/python.exe apps/parsers/hh/main.py --scrape-only --groups it --pages 1
```

Other supported options include `--groups it management marketing`, `--employment full`, `--refresh-hours 6`, and `--output <json-path>`
`--send-only` and `--scrape-only` are mutually exclusive
`--employment` filters HH search results; it does not assign a backend work format

In PyCharm select the repository `.venv` interpreter, set the script to `apps/parsers/hh/main.py`, and configure the same environment variables and arguments
Default data and log paths are anchored to the HH script directory, independent of the working directory
An explicit relative `--output` path is resolved against the working directory

## Transformation and validation

| Field | Mapping and missing-data policy |
| --- | --- |
| `source` | Normalize the HH source `hh.ru` to `hh` |
| `published_at` | Use `datePosted` from the matching JSON-LD `JobPosting`; require an explicit timezone and time; never substitute the collection time |
| `parsed_at` | Use the actual detail-page parsing time, retained unchanged during replay |
| `grade` | Recognize an unambiguous explicit title label: intern, junior, middle, senior, lead, and supported Russian equivalents; never infer it from years of experience |
| `employment_types` | Use explicit work-format labels or structured `TELECOMMUTE`/`CONTRACTOR` metadata; never turn full-time into office work |
| `salary` | Send only when original text, integer lower and upper bounds, and currency are all available; take structured values from JSON-LD without estimating bounds |
| `location` | Send only when original text, country and city are available; take country and city from structured address metadata without assuming a country |

The wire format uses uppercase `grade` and `employment_types` enums required by OpenAPI
The current contract permits omitting `salary` and `location`, but requires all their nested fields when supplied
Incomplete optional objects are therefore omitted from requests while their original text and available structured data remain in local JSON
The shared HTTP sink omits absent optional values and Python-only `raw_text`/`gross` fields

`HHBackendParser` inherits `BaseParser` and uses `VacancyValidator` with the `hh` source whitelist, followed by `BackendApiSink`
Missing required fields or failed domain validation leave the original record pending and log the reason
Descriptions are not padded or truncated: the existing 300–2500 character limit applies
The shared validator also requires publication within seven days, no more than five minutes into the future, and `parsed_at >= published_at`
Long-delayed retries can fail these existing rules; dates are never rewritten to bypass them
Legacy JSON without the new grade/work-format metadata can require a new scrape with `--refresh-hours 0`

## Durable delivery and replay

Default files

```text
apps/parsers/hh/output/vacancies.json
apps/parsers/hh/output/unavailable.json
apps/parsers/hh/logs/hh_scraper.log
```

Every successfully parsed vacancy is written atomically to JSON before delivery
Backend requests use `POST /api/v1/vacancies/batch` with `{"vacancies": [...]}`
A successful response must acknowledge the complete batch through nonnegative `inserted` and `ignored` counts
Only then is `_backend_delivered: true` written atomically for those records
Delivery failures, malformed responses and failed acknowledgement writes keep records pending
Confirmed earlier batches remain confirmed if a later batch fails

Use `--send-only` with the same `--output` file after fixing connectivity, authentication or backend failures
The backend contract deduplicates by `(source, external_id)` and counts repeated records as `ignored`, allowing replay after a lost response
Backend delivery performs one attempt per run; automatic retry/backoff belongs to the existing HH fetcher, not the shared backend sink
Refreshing a raw record resets its delivery acknowledgement
The contract ignores existing vacancies rather than updating them

Use a single writer per JSON file: concurrent parser processes are not supported
Invalid or unreadable queue files cause an error instead of being silently overwritten

Exit codes: `0` for successful completion, `1` for configuration/storage/backend failure, `2` for retained invalid records or an incomplete scrape

## Source request behavior

The existing scraper retains search groups, pagination, TTL refresh, deduplication, random request delays, bounded retry/backoff, `Retry-After`, CAPTCHA detection and layout/error thresholds
Automatic CAPTCHA solving and proxy rotation are not enabled
Optional external alert variables remain `ALERT_WEBHOOK_URL`, or `TELEGRAM_BOT_TOKEN` with `TELEGRAM_CHAT_ID`
Set `HH_SCRAPER_USER_AGENT` only when a fixed User-Agent is needed

## Checks

```powershell
.venv/Scripts/python.exe -m pytest -c apps/parsers/hh/pyproject.toml apps/parsers/hh/tests -q
.venv/Scripts/python.exe -m pytest -c apps/parsers/base/pyproject.toml apps/parsers/base/tests -q
.venv/Scripts/python.exe -m ruff check apps/parsers/hh
.venv/Scripts/python.exe -m ruff format --check apps/parsers/hh
```

Tests use saved synthetic HTML and mocked HTTP, including failures and replay after reopening JSON storage
They do not contact HH, the real backend or PostgreSQL
Live HH selectors, deployed authentication, persistence and database deduplication require a separate integration check

## Backend issues outside this change

- The Go domain normalizes grade/employment enums to lowercase, while the PostgreSQL enum definitions require uppercase; the current mapper passes them through unchanged, so real ingestion may fail
- The current Go router does not enforce the parser API key described by OpenAPI
- OpenAPI requires complete salary/location objects, while shared Python and Go DTOs allow missing nested values; this parser omits incomplete objects
- Go error responses do not match the structured error envelope in OpenAPI

Backend code, contracts and migrations are not changed by this integration
