# Parsers Shared Base Refactoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a reusable monorepo package `kiko-parsers-base` in `apps/parsers/base` containing shared OpenAPI models, domain validation rules, HTTP ingestion sink, and an abstract streaming `BaseParser` lifecycle, then refactor `apps/parsers/telegram` to consume it.

**Architecture:** Monorepo local package `kiko-parsers-base` managed by hatchling, defining shared DTOs matching the OpenAPI spec, an extensible `VacancyValidator` with customizable source whitelists, an async `BackendApiSink` for batching, and a template method `BaseParser` coordinating parsing, validation, batch accumulation, sink delivery, and metrics tracking.

**Tech Stack:** Python 3.11+, Pydantic v2, HTTPX, Pytest, Pytest-Asyncio, Respx, Hatchling, Mypy, Ruff.

**Spec:** `docs/superpowers/specs/2026-11-03-parsers-base-refactoring-design.md`

## Global Constraints
- Pure technical English for code, commits, and documentation.
- No unsolicited code comments.
- Conventional commits: `<prefix>: <short imperative description without trailing period>`.
- Invariants match backend `apps/backend/internal/domain/model/vacancy.go` and `contracts/openapi/`.
- Lightweight dependencies for `kiko-parsers-base`: `pydantic>=2.8.0`, `httpx>=0.27.0`.

---

### Task 1: Scaffolding `apps/parsers/base` Monorepo Package

**Files:**
- Create: `apps/parsers/base/pyproject.toml`
- Create: `apps/parsers/base/README.md`
- Create: `apps/parsers/base/parsers_base/__init__.py`
- Create: `apps/parsers/base/parsers_base/py.typed`

**Interfaces:**
- Produces: Installable Python package `kiko-parsers-base` with strict typing markers.

- [ ] **Step 1: Create package pyproject.toml and README.md**

```toml
[project]
name = "kiko-parsers-base"
version = "0.1.0"
description = "Shared base models, validation, sink, and parser abstractions for Kiko job scrapers"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.8.0",
    "httpx>=0.27.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "respx>=0.21.0",
    "ruff>=0.6.0",
    "mypy>=1.11.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["parsers_base"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
pythonpath = ["."]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "B", "C4"]

[tool.mypy]
python_version = "3.11"
plugins = ["pydantic.mypy"]
strict = true
ignore_missing_imports = true
```

- [ ] **Step 2: Create package directory markers**

Create `apps/parsers/base/parsers_base/__init__.py` and empty `apps/parsers/base/parsers_base/py.typed`.

- [ ] **Step 3: Commit**

```bash
git add apps/parsers/base
git commit -m "chore: scaffold kiko-parsers-base package"
```

---

### Task 2: Implement Shared Models (`parsers_base.models.vacancy`)

**Files:**
- Create: `apps/parsers/base/parsers_base/models/__init__.py`
- Create: `apps/parsers/base/parsers_base/models/vacancy.py`
- Create: `apps/parsers/base/tests/test_models.py`

**Interfaces:**
- Produces: `SalaryDTO`, `LocationDTO`, `CreateVacancyRequest`, `BatchCreateVacanciesRequest`, `BatchCreateVacanciesResponse`, `BatchIngestVacanciesResponse`.

- [ ] **Step 1: Write test for models serialization and aliases**

Test that `SalaryDTO` accepts `from` as alias for `from_`, `CreateVacancyRequest` serializes correctly with aliases, and `BatchCreateVacanciesRequest` supports `vacancies`.

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py` -> verify `ModuleNotFoundError`.

- [ ] **Step 3: Implement models in `parsers_base/models/vacancy.py`**

```python
from datetime import datetime
from pydantic import AliasChoices, BaseModel, ConfigDict, Field

class SalaryDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    text: str | None = None
    from_: int | None = Field(default=None, alias="from")
    to: int | None = None
    currency: str | None = None
    gross: bool | None = None

class LocationDTO(BaseModel):
    text: str | None = None
    country: str | None = None
    city: str | None = None

class CreateVacancyRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    external_id: str
    source: str
    title: str
    company: str | None = None
    salary: SalaryDTO | None = None
    grade: str
    employment_types: list[str] = Field(default_factory=list)
    location: LocationDTO | None = None
    description: str
    url: str
    published_at: datetime
    parsed_at: datetime
    raw_text: str | None = None

class BatchCreateVacanciesRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    vacancies: list[CreateVacancyRequest] = Field(
        default_factory=list,
        validation_alias=AliasChoices("vacancies", "items"),
    )

class BatchCreateVacanciesResponse(BaseModel):
    inserted: int
    ignored: int

BatchIngestVacanciesResponse = BatchCreateVacanciesResponse
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_models.py` -> PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/parsers/base/parsers_base/models apps/parsers/base/tests/test_models.py
git commit -m "feat: implement shared vacancy models in parsers_base"
```

---

### Task 3: Implement Domain Rules and Validator (`parsers_base.validation`)

**Files:**
- Create: `apps/parsers/base/parsers_base/validation/__init__.py`
- Create: `apps/parsers/base/parsers_base/validation/rules.py`
- Create: `apps/parsers/base/parsers_base/validation/validator.py`
- Create: `apps/parsers/base/tests/test_validator.py`

**Interfaces:**
- Produces: `ValidationResult`, `VacancyValidator`, validation constants (`MIN_TITLE_LEN`, `MAX_DESCRIPTION_LEN`, etc.).
- `VacancyValidator(allowed_sources=None)` accepts optional custom allowed sources set.

- [ ] **Step 1: Write comprehensive validator unit tests**

Test title length, company length, description length (300..2500), salary invariants (from <= to, currency required if from/to present, currency bounds), location hierarchy (city requires country), date bounds (past 7 days, max future skew 5 min, parsed_at >= published_at), and source whitelisting.

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement rules.py and validator.py**

Port and generalize `VacancyValidator` to support configurable `allowed_sources: set[str] | None = None` while preserving all Go backend invariants.

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

```bash
git add apps/parsers/base/parsers_base/validation apps/parsers/base/tests/test_validator.py
git commit -m "feat: implement domain validation and rules in parsers_base"
```

---

### Task 4: Implement Sinks (`parsers_base.sink`)

**Files:**
- Create: `apps/parsers/base/parsers_base/sink/__init__.py`
- Create: `apps/parsers/base/parsers_base/sink/base.py`
- Create: `apps/parsers/base/parsers_base/sink/backend_api.py`
- Create: `apps/parsers/base/tests/test_sink.py`

**Interfaces:**
- Produces: `BaseSink`, `SinkError`, `BackendApiSink`.
- `send_batch(vacancies: list[CreateVacancyRequest]) -> BatchCreateVacanciesResponse`.

- [ ] **Step 1: Write sink unit tests using respx**

Test empty batch returns `inserted=0, ignored=0`, test successful HTTP batch delivery with `X-Parser-Api-Key` and `POST /vacancies/batch`, and test HTTP 4xx/5xx raises `SinkError` with context.

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement `BaseSink`, `SinkError`, and `BackendApiSink`**

```python
class SinkError(Exception):
    pass
```
Implement retry logic on connection errors and clean `aclose()`.

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

```bash
git add apps/parsers/base/parsers_base/sink apps/parsers/base/tests/test_sink.py
git commit -m "feat: implement sink abstractions and backend api sink in parsers_base"
```

---

### Task 5: Implement `ParserStats` and `BaseParser` Lifecycle (`parsers_base.parser`)

**Files:**
- Create: `apps/parsers/base/parsers_base/parser/__init__.py`
- Create: `apps/parsers/base/parsers_base/parser/stats.py`
- Create: `apps/parsers/base/parsers_base/parser/base.py`
- Create: `apps/parsers/base/tests/test_base_parser.py`

**Interfaces:**
- Produces: `ParserStats`, `BaseParser`.
- Abstract method: `async def parse(self, **kwargs) -> AsyncIterator[CreateVacancyRequest]`.
- Lifecycle method: `async def run(self, **kwargs) -> ParserStats`.
- Hook: `async def on_batch_sent(self, batch: list[CreateVacancyRequest], response: BatchCreateVacanciesResponse) -> None`.

- [ ] **Step 1: Write tests for BaseParser lifecycle**

Test streaming consumption from `parse()`, validation filtering (invalid discarded with log warnings), batch accumulation up to `batch_size`, dispatching remaining vacancies on generator completion, calling `on_batch_sent()` hook after each batch, and returning accurate `ParserStats`.

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement `ParserStats` dataclass and `BaseParser` abstract class**

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

```bash
git add apps/parsers/base/parsers_base/parser apps/parsers/base/tests/test_base_parser.py
git commit -m "feat: implement BaseParser template method lifecycle and stats in parsers_base"
```

---

### Task 6: Expose Public API & Verify Base Package

**Files:**
- Modify: `apps/parsers/base/parsers_base/__init__.py`
- Modify: `apps/parsers/AGENTS.md`

**Interfaces:**
- Produces: Top-level exports:
  - `CreateVacancyRequest`, `SalaryDTO`, `LocationDTO`, `BatchCreateVacanciesResponse`, `BatchCreateVacanciesRequest`
  - `VacancyValidator`, `ValidationResult`
  - `BaseSink`, `BackendApiSink`, `SinkError`
  - `BaseParser`, `ParserStats`

- [ ] **Step 1: Populate `parsers_base/__init__.py` with `__all__`**
- [ ] **Step 2: Run ruff and mypy across `apps/parsers/base`**
- [ ] **Step 3: Run pytest across `apps/parsers/base`**
- [ ] **Step 4: Commit**

```bash
git add apps/parsers/base apps/parsers/AGENTS.md
git commit -m "feat: finalize public exports for kiko-parsers-base"
```

---

### Task 7: Integrate `kiko-parsers-base` into `apps/parsers/telegram`

**Files:**
- Modify: `apps/parsers/telegram/pyproject.toml`
- Modify: `apps/parsers/telegram/src/models/vacancy.py` (re-export from `parsers_base.models.vacancy`)
- Modify: `apps/parsers/telegram/src/validation/` (re-export or use `parsers_base.validation`)
- Modify: `apps/parsers/telegram/src/sink/` (re-export or use `parsers_base.sink`)

**Interfaces:**
- Ensures complete backward compatibility for Telegram parser while removing duplicated domain logic.

- [x] **Step 1: Add editable local path dependency in `apps/parsers/telegram/pyproject.toml`**

Add `kiko-parsers-base` to dependencies:
```toml
dependencies = [
    "kiko-parsers-base",
    ...
]
```

- [x] **Step 2: Install local editable package in telegram parser venv**

Run: `pip install -e ../base`

- [x] **Step 3: Update `src/models/vacancy.py`, `src/validation/`, and `src/sink/` to delegate to `parsers_base`**

- [x] **Step 4: Run all 114 unit tests in `apps/parsers/telegram` to verify zero regressions**

Run: `pytest` -> 114 passed.

- [x] **Step 5: Run ruff check and mypy on `apps/parsers/telegram`**

- [x] **Step 6: Commit**

```bash
git add apps/parsers/telegram
git commit -m "refactor: migrate telegram parser to use shared kiko-parsers-base"
```
