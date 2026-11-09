# Design Document: Telegram Vacancy Parser Service (`apps/parsers/telegram`)

**Date:** 2026-10-05  
**Status:** Approved  
**Author:** Pair Programming Agent & User  
**Target Path:** `apps/parsers/telegram`

---

## 1. Context & Motivation

Project **Kiko** (AI Job Assistant) aggregates job vacancies from various sources (HeadHunter, Telegram channels, career boards), calculates match scores against user profiles, generates AI summaries, and creates tailored cover letters.

The core backend is implemented in Go using Clean Architecture and Domain-Driven Design (DDD). Services interact via REST API defined in OpenAPI 3.0 contracts (`contracts/openapi/spec-files/` and `contracts/openapi/bundled/openapi.yaml`).

The Telegram Parser is a standalone Python service dedicated to scraping vacancy posts from Telegram channels, normalizing unstructured message text into typed vacancy contracts, and batch-uploading them to the Go backend through the authenticated ingestion endpoint.

---

## 2. Architecture & Design Principles

The service follows the **ETL (Extract -> Transform -> Load) Pipeline Pattern**, recognized as the industry standard for production-grade web scrapers and data ingestion agents:

1. **Extract (E):** Interacts with Telegram MTProto API via **Telethon** to fetch channel messages starting from the last known checkpoint.
2. **Transform (T):** Parses unstructured message text using deterministic heuristics and regex extractors, converting raw posts into validated `CreateVacancyRequest` objects. Posts determined to be ads, digests, or non-vacancies are filtered out.
3. **Load (L / Sink):** Ships batches of vacancies to the Go Core Backend via HTTP `POST /api/v1/vacancies/batch` with `X-Parser-Api-Key` authentication.
4. **State & Watermarking:** Persists the highest successfully ingested `last_message_id` per channel in a local SQLite database, guaranteeing at-least-once delivery without reprocessing historical messages.

### Key Architectural Boundaries
- **Strict Separation of Concerns:** Network extraction, parsing logic, state management, and HTTP transport are isolated behind abstract base classes (`ABC` / Protocols).
- **Zero Direct Database Coupling:** The parser does not touch the PostgreSQL database directly; all interactions flow through the central Go backend API, preserving service boundaries and centralized business validation.
- **Contract-First Alignment:** Schemas directly adhere to OpenAPI specifications (`BatchCreateVacanciesRequest`, `CreateVacancyRequest`, `BatchIngestVacanciesResponse`).

---

## 3. Detailed Component Architecture

### 3.1. Models & DTOs (`src/models/`)
- `raw_post.py`:
  - `RawPost`: `channel_username: str`, `message_id: int`, `text: str`, `date: datetime`, `url: str`.
- `vacancy.py`:
  - `CreateVacancyRequest`: Matching OpenAPI contract:
    - `external_id: str` (e.g. `f"{channel_username}_{message_id}"`)
    - `source: str = "Telegram"`
    - `title: str`
    - `url: str`
    - `company: str | None = None`
    - `salary_text: str | None = None`
    - `location: str | None = None`
    - `description: str | None = None`
  - `BatchCreateVacanciesRequest`: `vacancies: list[CreateVacancyRequest]`
  - `BatchIngestVacanciesResponse`: `inserted: int`, `ignored: int`
- `channel.py`:
  - `ChannelConfig`: `username: str`, `enabled: bool = True`, `tags: list[str] = []`

### 3.2. Extractor Layer (`src/extractor/`)
- `base.py`:
  - Defines `BaseExtractor(ABC)` with `fetch_posts(channel: str, since_message_id: int, limit: int) -> AsyncIterator[RawPost]`.
- `telethon_client.py`:
  - Wraps `telethon.TelegramClient` with MTProto session handling, connection pooling, and exponential backoff on `FloodWaitError`.
- `channel_reader.py`:
  - Implements pagination and reading of channel history forward from `since_message_id`.

### 3.3. Transformer Layer (`src/transformer/`)
- `base.py`:
  - Defines `BaseTransformer(ABC)` with `transform(post: RawPost) -> CreateVacancyRequest | None`.
- `heuristics.py`:
  - Modular regexes and parsers for:
    - Job title extraction (first line heuristics, keywords like `Backend Developer`, `Go`, `Python`).
    - Salary extraction (e.g. `150 000 - 250 000 руб`, `$3000-$5000`, `от 200k`).
    - Company name and location extraction (Remote, Moscow, etc.).
    - Filter rules for skipping non-vacancies (resumes, ad posts, courses, community announcements).
- `post_parser.py`:
  - Coordinates text transformation, normalization, and Pydantic validation.

### 3.4. Sink Layer (`src/sink/`)
- `base.py`:
  - Defines `BaseSink(ABC)` with `send_batch(vacancies: list[CreateVacancyRequest]) -> BatchIngestVacanciesResponse`.
- `backend_api.py`:
  - Asynchronous client powered by `httpx.AsyncClient`.
  - Sets `X-Parser-Api-Key` header from configuration.
  - Calls `POST /api/v1/vacancies/batch`.
  - Handles HTTP status codes (200 OK, 401 Unauthorized, 422 Validation Error, 5xx retry with backoff).

### 3.5. Storage & Watermarks (`src/storage/`)
- `base.py`:
  - Defines `BaseStateStore(ABC)` with `get_checkpoint(channel: str) -> int` and `commit_checkpoint(channel: str, message_id: int) -> None`.
- `sqlite_store.py`:
  - Lightweight embedded SQLite database (`data/state.sqlite`).
  - Table: `checkpoints(channel_name TEXT PRIMARY KEY, last_message_id INTEGER, updated_at TIMESTAMP)`.

### 3.6. Orchestration & Scheduling (`src/pipeline/`)
- `orchestrator.py`:
  - Executes one ETL pass across all enabled channels:
    1. Read `last_message_id` from state store.
    2. Extract new `RawPost`s.
    3. Transform to `CreateVacancyRequest`.
    4. Send batch to backend sink.
    5. On 200 response, commit new watermark to state store.
- `scheduler.py`:
  - Periodic loop runner executing the orchestrator every `POLL_INTERVAL_SECONDS` (e.g. 1800s / 30 mins) with graceful shutdown on SIGINT/SIGTERM.

---

## 4. Directory & File Structure

```text
apps/parsers/telegram/
├── pyproject.toml              # Dependencies, ruff, mypy, pytest config
├── README.md                   # Service documentation & run instructions
├── Dockerfile                  # Production container definition
├── .env.example                # Sample environment variables
│
├── config/
│   └── channels.yaml           # Monitored Telegram channels list & metadata
│
├── data/                       # Docker persistent volume mount
│   ├── .gitkeep
│   └── sessions/               # Telethon MTProto session files (*.session)
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_transformer.py # Deterministic unit tests for post parsing & heuristics
│   │   ├── test_state.py       # Checkpoint read/commit SQLite tests
│   │   └── test_sink.py        # HTTP payload & header serialization tests
│   └── fixtures/
│       └── sample_posts.json   # Real telegram post samples for testing
│
└── src/
    ├── __init__.py
    ├── __main__.py             # CLI entrypoint: python -m src
    ├── config.py               # Pydantic BaseSettings
    ├── models/
    │   ├── __init__.py
    │   ├── raw_post.py
    │   ├── vacancy.py
    │   └── channel.py
    ├── extractor/
    │   ├── __init__.py
    │   ├── base.py
    │   ├── telethon_client.py
    │   └── channel_reader.py
    ├── transformer/
    │   ├── __init__.py
    │   ├── base.py
    │   ├── heuristics.py
    │   └── post_parser.py
    ├── sink/
    │   ├── __init__.py
    │   ├── base.py
    │   └── backend_api.py
    ├── storage/
    │   ├── __init__.py
    │   ├── base.py
    │   └── sqlite_store.py
    ├── pipeline/
    │   ├── __init__.py
    │   ├── orchestrator.py
    │   └── scheduler.py
    └── utils/
        ├── __init__.py
        ├── logger.py
        └── rate_limiter.py
```

---

## 5. Tooling & Dependencies

- **Python Version:** 3.11+
- **Build & Dependency Standard:** `pyproject.toml`
- **Core Runtime:**
  - `telethon >= 1.36.0` (MTProto client)
  - `httpx >= 0.27.0` (Async HTTP client for backend ingestion)
  - `pydantic >= 2.8.0`, `pydantic-settings >= 2.4.0` (Data validation and config)
  - `aiosqlite >= 0.20.0` (Async SQLite for watermark tracking)
  - `pyyaml >= 6.0.1` (Parsing `channels.yaml`)
- **Development & Quality:**
  - `pytest >= 8.0.0`, `pytest-asyncio >= 0.24.0`
  - `ruff >= 0.6.0` (Linter and formatter)
  - `mypy >= 1.11.0` (Strict static type checker)
  - `respx >= 0.21.0` (Mocking HTTP calls for sink tests)

---

## 6. Resilience & Edge Cases

1. **FloodWait Handling:** Telethon raises `FloodWaitError` when rate-limited by Telegram servers. The extractor intercepts this, pauses execution for `error.seconds + 1`, and resumes safely.
2. **At-Least-Once Delivery:** Watermarks are updated in SQLite only **after** the Go backend responds with HTTP 200. If the service terminates or the backend is temporarily unreachable, posts are re-read and resent on next run. The backend handles deduplication via `(source, external_id)` and returns ignored counts.
3. **Data Poisoning Prevention:** Non-parseable or malformed messages are logged with warning/debug level and skipped without stalling the pipeline.
