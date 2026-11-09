# Parsers Shared Base & Reusable Validation Refactoring Design

**Date:** 2026-11-03  
**Status:** Approved  
**Scope:** `apps/parsers/base`, `apps/parsers/telegram`, `apps/parsers/AGENTS.md`

## 1. Context & Motivation

The `apps/parsers` domain collects job vacancies across multiple sources (Telegram, HH.ru, Habr Career, corporate websites, etc.) and forwards them to the Go backend service via `POST /vacancies/batch`.

Previously, models, validation rules, HTTP sink logic, and ingestion buffering were coupled directly inside `apps/parsers/telegram`. This posed several challenges:
- **Code Duplication**: Every subsequent scraper/crawler would need to copy-paste OpenAPI DTOs (`CreateVacancyRequest`, `SalaryDTO`, etc.), validation rules (`rules.py`, `validator.py`), and HTTP ingestion logic (`BackendApiSink`).
- **Inconsistent Invariants**: Bug fixes or schema changes in one parser could lead to drift between parser implementations.
- **Boilerplate Overhead**: Developing new scrapers required writing redundant batching, validation filtering, and error handling loops instead of focusing purely on source-specific HTML/API extraction.

Because all current and future parsers share the Python runtime (Python 3.12+), an isolated, reusable local package `kiko-parsers-base` in `apps/parsers/base` establishes a clean, shared foundation across all scraper services.

---

## 2. Architecture & Design Decisions

### 2.1 Shared Local Monorepo Package (`kiko-parsers-base`)
- Located in `apps/parsers/base/` with its own `pyproject.toml` managed by `hatchling`.
- Consumed by concrete parser services (such as `apps/parsers/telegram`) as a local editable path dependency:
  ```toml
  dependencies = [
      "kiko-parsers-base",
  ]
  ```
- Lightweight dependency footprint: only relies on `pydantic>=2.8.0` and `httpx>=0.27.0`.

### 2.2 Template Method Lifecycle (`BaseParser`)
Concrete parsers implement a clean generator interface:
```python
async def parse(self, **kwargs) -> AsyncIterator[CreateVacancyRequest]:
    ...
```
The abstract `BaseParser` encapsulates the standard lifecycle:
1. **Streaming**: Iterates over vacancies yielded by `parse()`.
2. **Deterministic Validation**: Passes each vacancy through `VacancyValidator`.
3. **Structured Filtering**: Drops invalid items, logs warning with field-level rejection reasons, and tracks metrics.
4. **Batch Accumulation**: Buffers valid vacancies up to `batch_size`.
5. **Ingestion**: Dispatches batches to `BaseSink.send_batch()`.
6. **Extensible Hooking**: Calls `await self.on_batch_sent(batch, response)` to allow subclasses to commit source watermarks, offsets, or database states.
7. **Telemetry**: Returns structured `ParserStats` (extracted, valid, invalid, inserted, ignored).

### 2.3 Strict Domain Invariants & Contract Compliance
- Directly mirrors OpenAPI schemas (`contracts/openapi/`) and backend domain model invariants (`apps/backend/internal/domain/model/vacancy.go`).
- Enforces strict constraints: title lengths, optional company, structured salary validation (currency matching, from <= to), grade and employment type enums, location hierarchy (city requires country), description character limits (300..2500), and source whitelist.
- `VacancyValidator` allows customizable source lists for scrapers targeting new platforms.

---

## 3. Package Structure

```
apps/parsers/
├── base/
│   ├── pyproject.toml
│   ├── README.md
│   ├── parsers_base/
│   │   ├── __init__.py              # Public exports (BaseParser, VacancyValidator, etc.)
│   │   ├── py.typed
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── vacancy.py           # DTOs: CreateVacancyRequest, SalaryDTO, LocationDTO, Batch*
│   │   ├── validation/
│   │   │   ├── __init__.py
│   │   │   ├── rules.py             # Domain constraints and enums
│   │   │   └── validator.py         # VacancyValidator and ValidationResult
│   │   ├── sink/
│   │   │   ├── __init__.py
│   │   │   ├── base.py              # BaseSink ABC and SinkError
│   │   │   └── backend_api.py       # BackendApiSink with HTTP retry and auth
│   │   └── parser/
│   │       ├── __init__.py
│   │       ├── base.py              # BaseParser abstract lifecycle class
│   │       └── stats.py             # ParserStats dataclass
│   └── tests/
│       ├── test_validator.py        # Domain validation test suite
│       ├── test_sink.py             # Sink HTTP and error handling tests
│       └── test_base_parser.py      # BaseParser streaming and lifecycle tests
├── telegram/                        # Refactored to consume parsers_base
└── AGENTS.md                        # Documentation updated for new parsers
```

---

## 4. Component Interfaces

### 4.1 Models (`parsers_base.models.vacancy`)
- `SalaryDTO`: `from_`, `to`, `currency`, `gross`, `text`.
- `LocationDTO`: `country`, `city`, `text`.
- `CreateVacancyRequest`: `external_id`, `source`, `url`, `title`, `company`, `salary`, `grade`, `employment_types`, `location`, `description`, `raw_text`, `published_at`, `parsed_at`.
- `BatchCreateVacanciesRequest`: `items: list[CreateVacancyRequest]`.
- `BatchCreateVacanciesResponse`: `inserted: int`, `ignored: int`.

### 4.2 Validation (`parsers_base.validation`)
- `ValidationResult`: dataclass with `is_valid: bool` and `reasons: list[str]`.
- `VacancyValidator`: validates domain invariants, text boundaries, dates, and source whitelisting.

### 4.3 Sink (`parsers_base.sink`)
- `BaseSink`: abstract base class defining `async def send_batch(self, vacancies: list[CreateVacancyRequest]) -> BatchCreateVacanciesResponse` and `async def close(self) -> None`.
- `BackendApiSink`: HTTP client wrapping `httpx.AsyncClient`, passing `X-Parser-Api-Key` header, executing requests with retry backoff, and raising `SinkError` on fatal failures.

### 4.4 Base Parser (`parsers_base.parser`)
- `ParserStats`: counters for `extracted`, `valid`, `invalid`, `inserted`, `ignored`.
- `BaseParser`: abstract template method class coordinating stream iteration, validator execution, batch buffering, sink delivery, and `on_batch_sent` hook callback.

---

## 5. Migration of Telegram Parser

1. Add `kiko-parsers-base` dependency to `apps/parsers/telegram/pyproject.toml`.
2. Refactor `apps/parsers/telegram`:
   - Replace local `src/models/vacancy.py` with imports from `parsers_base.models.vacancy` (or provide backward-compatibility re-exports during transition).
   - Update `src/sink/` to use `parsers_base.sink`.
   - Update `src/validation/` to use `parsers_base.validation`.
   - Connect or adapt `src/pipeline/orchestrator.py` to leverage `parsers_base` abstractions while preserving channel watermarks stored in `SQLiteStore`.
3. Verify that all existing unit tests in `apps/parsers/telegram/tests/` continue passing.

---

## 6. Testing Strategy

1. **`apps/parsers/base/tests`**:
   - Comprehensive unit tests for `VacancyValidator` covering boundary conditions, missing fields, invalid salary/location formats, and source constraints.
   - Mocked HTTP tests for `BackendApiSink` validating payload serialization, auth headers, and retry behavior.
   - Asynchronous stream tests for `BaseParser` validating item consumption, error dropping, batch size limits, hook callbacks, and metrics aggregation.
2. **`apps/parsers/telegram/tests`**:
   - Execute all 105 existing tests to ensure zero regressions after switching imports to `parsers_base`.
