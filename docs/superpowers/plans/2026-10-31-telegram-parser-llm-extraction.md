# Telegram Parser LLM Extraction & Domain Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace heuristic regex guessing in the Telegram parser with OpenRouter LLM extraction, align the vacancy contract with the backend rich model, enforce strict domain validation rules with rejection logging, and update the OpenAPI contract.

**Architecture:** Contract-First OpenAPI specification (`contracts/openapi/`) is updated to define rich `CreateVacancyRequest`. The Telegram parser (`apps/parsers/telegram`) implements an OpenAI-compatible asynchronous client (`LlmExtractor`) for OpenRouter, Pydantic v2 DTOs matching the Go backend model, a dedicated `VacancyValidator` component encapsulating all Go domain invariants, and detailed structured rejection logging.

**Tech Stack:** Python 3.11+, Pydantic v2, Pydantic-Settings, HTTPX, Telethon, pytest, pytest-asyncio, respx, OpenAPI 3.0.

**Spec:** `docs/superpowers/specs/2026-10-31-telegram-parser-llm-extraction-design.md`

## Global Constraints

- Backend rich model invariants in `apps/backend/internal/domain/model/vacancy.go` are the authoritative source of truth.
- `title`: length 3..100 characters.
- `company`: optional, length 2..100 characters.
- `salary`: optional; `text` (2..150 chars); `from`/`to` (0..100,000,000, `from <= to`). Bounds require 3-letter currency code; currency requires at least one bound.
- `grade`: `intern`, `junior`, `middle`, `senior`, `lead`.
- `employment_types`: non-empty list of unique values from `remote`, `office`, `hybrid`, `contract`.
- `location`: optional; `text` (2..80 chars), `country` (2..40 chars), `city` (2..50 chars). `city` requires `country`.
- `description`: 300..2500 characters. Posts with descriptions < 300 characters are strictly rejected.
- `url`: 10..1024 characters.
- `published_at` / `parsed_at`: valid within 7 days in past, max 5 min future skew; `parsed_at >= published_at`.
- All test files must be table-driven where applicable, with no comments inside test files.
- Git commits: concise English message without a trailing period.

---

### Task 1: Update OpenAPI Contract

**Files:**
- Modify: `contracts/openapi/spec-files/models.yaml:394-426`

**Interfaces:**
- Consumes: Backend DTO in `apps/backend/internal/adapter/in/http/dto/entities.go`
- Produces: Updated OpenAPI `CreateVacancyRequest` schema matching `Salary`, `Grade`, `EmploymentType`, and `Location`

- [ ] **Step 1: Update CreateVacancyRequest in models.yaml**

Update `CreateVacancyRequest` in `contracts/openapi/spec-files/models.yaml` to reference `Salary`, `Grade`, `EmploymentType`, and `Location`, specifying string constraints (`minLength`, `maxLength`).

```yaml
    CreateVacancyRequest:
      type: object
      required:
        - external_id
        - source
        - title
        - grade
        - employment_types
        - description
        - url
        - published_at
        - parsed_at
      properties:
        external_id:
          type: string
          example: "12345678"
        source:
          type: string
          example: "telegram"
        title:
          type: string
          minLength: 3
          maxLength: 100
          example: "Junior Go Developer"
        company:
          type: string
          nullable: true
          minLength: 2
          maxLength: 100
          example: "Acme Corp"
        salary:
          $ref: "#/components/schemas/Salary"
        grade:
          $ref: "#/components/schemas/Grade"
        employment_types:
          type: array
          items:
            $ref: "#/components/schemas/EmploymentType"
        location:
          $ref: "#/components/schemas/Location"
        description:
          type: string
          minLength: 300
          maxLength: 2500
          example: "We are looking for a Junior Go Developer..."
        url:
          type: string
          minLength: 10
          maxLength: 1024
          example: "https://t.me/channel/123"
        published_at:
          type: string
          format: date-time
        parsed_at:
          type: string
          format: date-time
```

- [ ] **Step 2: Commit OpenAPI contract changes**

```bash
git add contracts/openapi/spec-files/models.yaml
git commit -m "update CreateVacancyRequest schema in OpenAPI spec"
```

---

### Task 2: Update Configuration & Parser Vacancy DTO Models

**Files:**
- Modify: `apps/parsers/telegram/src/config.py`
- Modify: `apps/parsers/telegram/src/models/vacancy.py`
- Modify: `apps/parsers/telegram/src/models/__init__.py`
- Modify: `apps/parsers/telegram/.env.example`
- Test: `apps/parsers/telegram/tests/unit/test_models.py`

**Interfaces:**
- Consumes: Environment variables (`LLM_API_KEY`, `LLM_MODEL`, `LLM_BASE_URL`, `LLM_TIMEOUT`)
- Produces: `SalaryDTO`, `LocationDTO`, `CreateVacancyRequest`, `BatchCreateVacanciesRequest`, `BatchCreateVacanciesResponse`

- [ ] **Step 1: Write failing unit test for updated Vacancy DTO models**

In `apps/parsers/telegram/tests/unit/test_models.py`, update tests to verify instantiation and JSON serialization of `CreateVacancyRequest` with nested `SalaryDTO` and `LocationDTO`.

- [ ] **Step 2: Run test to verify it fails**

Run: `apps/parsers/telegram/.venv/Scripts/pytest.exe apps/parsers/telegram/tests/unit/test_models.py`
Expected: FAIL due to missing fields / model definition.

- [ ] **Step 3: Update `src/config.py` and `src/models/vacancy.py`**

Add LLM configuration fields to `Settings`:
- `llm_api_key`: `str = Field(default="", alias="LLM_API_KEY")`
- `llm_base_url`: `str = Field(default="https://openrouter.ai/api/v1", alias="LLM_BASE_URL")`
- `llm_model`: `str = Field(default="meta-llama/llama-3.3-70b-instruct:free", alias="LLM_MODEL")`
- `llm_timeout`: `float = Field(default=30.0, alias="LLM_TIMEOUT")`

Define `SalaryDTO`, `LocationDTO`, `CreateVacancyRequest`, `BatchCreateVacanciesRequest`, `BatchCreateVacanciesResponse` in `src/models/vacancy.py`. Export all in `src/models/__init__.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `apps/parsers/telegram/.venv/Scripts/pytest.exe apps/parsers/telegram/tests/unit/test_models.py`
Expected: PASS.

- [ ] **Step 5: Commit model changes**

```bash
git add apps/parsers/telegram/src/config.py apps/parsers/telegram/src/models/ apps/parsers/telegram/.env.example apps/parsers/telegram/tests/unit/test_models.py
git commit -m "update vacancy models and config for structured LLM parsing"
```

---

### Task 3: Implement Domain Validation Layer with Detailed Rejection Logging

**Files:**
- Create: `apps/parsers/telegram/src/validation/__init__.py`
- Create: `apps/parsers/telegram/src/validation/rules.py`
- Create: `apps/parsers/telegram/src/validation/validator.py`
- Create: `apps/parsers/telegram/tests/unit/test_validator.py`

**Interfaces:**
- Consumes: `CreateVacancyRequest`
- Produces: `ValidationResult` (is_valid: bool, reasons: list[str]), `VacancyValidator.validate(vacancy: CreateVacancyRequest) -> ValidationResult`

- [ ] **Step 1: Write table-driven unit tests for VacancyValidator**

In `apps/parsers/telegram/tests/unit/test_validator.py`, write tests covering:
- Valid vacancy passes.
- Title length < 3 or > 100 fails with reason.
- Company length < 2 or > 100 fails with reason.
- Description length < 300 or > 2500 fails with reason.
- Salary bounds without currency fails.
- Currency without bounds fails.
- `from > to` fails.
- Invalid currency code length (!= 3) fails.
- City without country fails.
- Invalid grade enum fails.
- Empty or invalid employment types fails.
- Published at older than 7 days or > 5 min in future fails.
- Parsed at before published at fails.

- [ ] **Step 2: Run test to verify it fails**

Run: `apps/parsers/telegram/.venv/Scripts/pytest.exe apps/parsers/telegram/tests/unit/test_validator.py`
Expected: FAIL (module not found).

- [ ] **Step 3: Implement domain rules and VacancyValidator**

Create `src/validation/rules.py` with domain constants and allowed enum sets matching `models/vacancy.go`.
Create `src/validation/validator.py` implementing `VacancyValidator` which checks each rule and accumulates descriptive failure reasons into `ValidationResult`.

- [ ] **Step 4: Run test to verify it passes**

Run: `apps/parsers/telegram/.venv/Scripts/pytest.exe apps/parsers/telegram/tests/unit/test_validator.py`
Expected: PASS.

- [ ] **Step 5: Commit validator implementation**

```bash
git add apps/parsers/telegram/src/validation/ apps/parsers/telegram/tests/unit/test_validator.py
git commit -m "add vacancy domain rules and validator with detailed error reporting"
```

---

### Task 4: Implement LLM Extractor Client

**Files:**
- Create: `apps/parsers/telegram/src/transformer/llm_extractor.py`
- Modify: `apps/parsers/telegram/src/transformer/__init__.py`
- Create: `apps/parsers/telegram/tests/unit/test_llm_extractor.py`

**Interfaces:**
- Consumes: Raw text string from Telegram post, OpenRouter API settings
- Produces: `LlmExtractionResult` (is_vacancy: bool, reason: str | None, data: dict | None), `LlmExtractor.extract(text: str) -> LlmExtractionResult`

- [ ] **Step 1: Write unit tests for LlmExtractor using respx**

In `apps/parsers/telegram/tests/unit/test_llm_extractor.py`:
- Test successful extraction with structured JSON response.
- Test rejection when post is not a vacancy (`is_vacancy: false`, `reason: "ad for courses"`).
- Test handling of malformed JSON from LLM.
- Test handling of HTTP error / network timeout.

- [ ] **Step 2: Run test to verify it fails**

Run: `apps/parsers/telegram/.venv/Scripts/pytest.exe apps/parsers/telegram/tests/unit/test_llm_extractor.py`
Expected: FAIL (module not found).

- [ ] **Step 3: Implement LlmExtractor**

Implement `LlmExtractor` with `httpx.AsyncClient`:
- Formats request for OpenRouter `/chat/completions` with system prompt and JSON object response format.
- Handles retries on rate limits (429) or connection timeouts.
- Parses JSON payload and returns typed `LlmExtractionResult`.

- [ ] **Step 4: Run test to verify it passes**

Run: `apps/parsers/telegram/.venv/Scripts/pytest.exe apps/parsers/telegram/tests/unit/test_llm_extractor.py`
Expected: PASS.

- [ ] **Step 5: Commit LlmExtractor**

```bash
git add apps/parsers/telegram/src/transformer/llm_extractor.py apps/parsers/telegram/src/transformer/__init__.py apps/parsers/telegram/tests/unit/test_llm_extractor.py
git commit -m "implement openrouter llm extractor for vacancy extraction"
```

---

### Task 5: Transformer & Pipeline Integration with Rejection Logging

**Files:**
- Modify: `apps/parsers/telegram/src/transformer/base.py`
- Modify: `apps/parsers/telegram/src/transformer/post_parser.py`
- Modify: `apps/parsers/telegram/src/sink/backend_api.py`
- Modify: `apps/parsers/telegram/src/pipeline/orchestrator.py`
- Modify: `apps/parsers/telegram/src/__main__.py`
- Modify: `apps/parsers/telegram/tests/unit/test_transformer.py`
- Modify: `apps/parsers/telegram/tests/unit/test_sink.py`
- Modify: `apps/parsers/telegram/tests/unit/test_pipeline.py`

**Interfaces:**
- Consumes: `RawPost`, `LlmExtractor`, `VacancyValidator`
- Produces: Validated `CreateVacancyRequest | None`, detailed logs with post URL and reasons on rejection

- [ ] **Step 1: Update unit tests for PostParser, Sink, and Pipeline**

Update `test_transformer.py`, `test_sink.py`, and `test_pipeline.py` to reflect asynchronous transformation, structured vacancy payloads, and detailed logging of rejected posts.

- [ ] **Step 2: Run tests to verify failure**

Run: `apps/parsers/telegram/.venv/Scripts/pytest.exe apps/parsers/telegram/tests/`
Expected: FAIL due to interface changes.

- [ ] **Step 3: Implement PostParser with LlmExtractor and VacancyValidator**

- Update `BaseTransformer.transform` to be an async method: `async def transform(self, post: RawPost) -> CreateVacancyRequest | None:`.
- `PostParser.transform(post)`:
  1. Calls `await self.llm_extractor.extract(post.text)`.
  2. If `not result.is_vacancy`, logs info: `Post url=%s rejected: not a vacancy (%s)`.
  3. If extracted, constructs `CreateVacancyRequest` draft using post date as `published_at` and `now` as `parsed_at`.
  4. Runs `self.validator.validate(vacancy)`.
  5. If invalid, logs warning: `Vacancy validation rejected for url=%s. Reasons: %s`.
  6. Returns valid vacancy or `None`.
- Update `ETLPipeline.process_channel` to `await self.transformer.transform(post)`.
- Update `BackendApiSink` to use `BatchCreateVacanciesRequest` and `BatchCreateVacanciesResponse`.
- Update `src/__main__.py` to initialize `LlmExtractor`, `VacancyValidator`, and `PostParser`.

- [ ] **Step 4: Run all unit tests to verify they pass**

Run: `apps/parsers/telegram/.venv/Scripts/pytest.exe apps/parsers/telegram/tests/`
Expected: ALL PASS.

- [ ] **Step 5: Commit transformer and pipeline changes**

```bash
git add apps/parsers/telegram/src/ apps/parsers/telegram/tests/
git commit -m "integrate llm extractor and validator into etl pipeline"
```

---

### Task 6: Full Verification & Code Hygiene

**Files:**
- Entire repository

**Interfaces:**
- Consumes: All tests and linters
- Produces: Clean test pass, clean linter output

- [ ] **Step 1: Run complete pytest suite**

Run: `apps/parsers/telegram/.venv/Scripts/pytest.exe apps/parsers/telegram/tests/ -v`
Expected: All tests pass with zero errors.

- [ ] **Step 2: Run ruff check on telegram parser**

Run: `apps/parsers/telegram/.venv/Scripts/ruff.exe check apps/parsers/telegram/src apps/parsers/telegram/tests`
Expected: Clean check or auto-fixed.

- [ ] **Step 3: Run project linter standard**

Check `.golangci.yml` in root and run:
`go run github.com/golangci/golangci-lint/v2/cmd/golangci-lint@latest run --fix`
Expected: Clean pass.

- [ ] **Step 4: Commit any remaining fixes**

```bash
git commit -m "finalize telegram parser llm extraction and validation"
```
