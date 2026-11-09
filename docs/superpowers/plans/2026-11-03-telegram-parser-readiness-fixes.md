# Telegram Parser Readiness Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix deployment path configuration, eliminate cold-start LLM token waste on historical posts, add Telethon interactive session login CLI, and fix static typing in tests.

**Architecture:** 
1. Fix path mismatches in Dockerfile and `.env.example` to point to `data/config/channels.yaml`.
2. Implement pre-LLM date validation in `PostParser` to discard posts older than 7 days before making LLM requests while allowing watermarks to advance past obsolete messages.
3. Add `--login` CLI argument and `TelethonWrapper.login()` for first-time interactive MTProto session creation.
4. Enable `pydantic.mypy` plugin and fix type annotations in unit test files to ensure clean `mypy` passing.

**Tech Stack:** Python 3.11+, Telethon, Pydantic v2, pytest, pytest-asyncio, respx, mypy, Docker.

## Global Constraints
- Pure technical English for code, commits, and docs.
- No unsolicited code comments.
- Conventional commits: `<prefix>: <short imperative description without trailing period>`.
- Preserves all contract rules (`contracts/openapi/`) and domain model validation.

---

### Task 1: Fix Dockerfile and `.env.example` Configuration Paths

**Files:**
- Modify: `apps/parsers/telegram/Dockerfile:11-13`
- Modify: `apps/parsers/telegram/.env.example:17`

**Interfaces:**
- Consumes: `data/config/channels.yaml`
- Produces: Correct container image filesystem layout and valid environment template

- [ ] **Step 1: Update Dockerfile**
In `apps/parsers/telegram/Dockerfile`:
Replace:
```dockerfile
COPY src/ ./src/
COPY config/ ./config/
RUN mkdir -p data/sessions
```
With:
```dockerfile
COPY src/ ./src/
COPY data/ ./data/
RUN mkdir -p data/sessions
```

- [ ] **Step 2: Update `.env.example`**
In `apps/parsers/telegram/.env.example`:
Change line 17 from `CHANNELS_CONFIG_PATH=config/channels.yaml` to `CHANNELS_CONFIG_PATH=data/config/channels.yaml`.

- [ ] **Step 3: Verify path resolution**
Run Python command to verify `Settings().channels_config_path` resolves to an existing file.

- [ ] **Step 4: Commit changes**
```bash
git add apps/parsers/telegram/Dockerfile apps/parsers/telegram/.env.example
git commit -m "fix: align config paths in Dockerfile and environment template"
```

---

### Task 2: Implement Pre-LLM Date Filtering in PostParser

**Files:**
- Modify: `apps/parsers/telegram/src/transformer/post_parser.py`
- Test: `apps/parsers/telegram/tests/unit/test_transformer.py`

**Interfaces:**
- Consumes: `RawPost.date`, `VACANCY_VALID_UP_TO = timedelta(days=7)` from `src.validation.rules`
- Produces: Discards posts older than 7 days immediately before calling LLM extractor

- [ ] **Step 1: Write failing unit test for pre-LLM date filter**
In `apps/parsers/telegram/tests/unit/test_transformer.py`:
Add a test asserting that if `raw_post.date` is 8 days ago, `PostParser.transform(post)` returns `None` and `mock_llm.extract` is never called.

- [ ] **Step 2: Run test to verify it fails**
Run: `apps/parsers/telegram/.venv/Scripts/pytest.exe apps/parsers/telegram/tests/unit/test_transformer.py -k test_post_parser_skips_outdated_posts_before_llm`
Expected: FAIL because `mock_llm.extract` is currently called.

- [ ] **Step 3: Implement pre-LLM date check in `PostParser.transform`**
In `apps/parsers/telegram/src/transformer/post_parser.py`:
Import `VACANCY_VALID_UP_TO` from `src.validation.rules`.
At the start of `transform(self, post: RawPost)`:
```python
post_date = post.date if post.date.tzinfo is not None else post.date.replace(tzinfo=UTC)
if post_date < (datetime.now(UTC) - VACANCY_VALID_UP_TO):
    logger.info("Post url=%s skipped: published_at older than valid window", post.url)
    return None
```

- [ ] **Step 4: Run test to verify it passes**
Run: `apps/parsers/telegram/.venv/Scripts/pytest.exe apps/parsers/telegram/tests/unit/test_transformer.py`
Expected: PASS.

- [ ] **Step 5: Commit changes**
```bash
git add apps/parsers/telegram/src/transformer/post_parser.py apps/parsers/telegram/tests/unit/test_transformer.py
git commit -m "feat: skip outdated posts before llm extraction"
```

---

### Task 3: Add Telethon Interactive Login CLI Mode

**Files:**
- Modify: `apps/parsers/telegram/src/extractor/telethon_client.py`
- Modify: `apps/parsers/telegram/src/__main__.py`

**Interfaces:**
- Consumes: CLI flag `--login`
- Produces: Interactive login flow and persisted `.session` file via `client.start()`

- [ ] **Step 1: Add `login()` method to `TelethonWrapper`**
In `apps/parsers/telegram/src/extractor/telethon_client.py`:
Add method:
```python
async def login(self) -> None:
    logger.info("Starting interactive Telethon authentication...")
    await self.client.start()
    me = await self.client.get_me()
    username = getattr(me, "username", None) or getattr(me, "first_name", "User")
    logger.info("Successfully authenticated as: %s", username)
```

- [ ] **Step 2: Add `--login` argument in `src/__main__.py`**
In `apps/parsers/telegram/src/__main__.py`:
Add `--login` argument to `argparse.ArgumentParser`.
If `args.login`:
Execute:
```python
await wrapper.login()
await wrapper.disconnect()
return
```

- [ ] **Step 3: Run existing unit tests to verify no regressions**
Run: `apps/parsers/telegram/.venv/Scripts/pytest.exe apps/parsers/telegram/tests/`
Expected: PASS.

- [ ] **Step 4: Commit changes**
```bash
git add apps/parsers/telegram/src/extractor/telethon_client.py apps/parsers/telegram/src/__main__.py
git commit -m "feat: add interactive login CLI mode for telethon session"
```

---

### Task 4: Fix Static Typing & Mypy Errors in Test Suite

**Files:**
- Modify: `apps/parsers/telegram/pyproject.toml`
- Modify: `apps/parsers/telegram/tests/unit/test_validator.py`
- Modify: `apps/parsers/telegram/tests/unit/test_pipeline.py`
- Modify: `apps/parsers/telegram/tests/unit/test_sink.py`

**Interfaces:**
- Consumes: Mypy 1.11+, Pydantic plugin
- Produces: 0 errors across `src/` and `tests/`

- [ ] **Step 1: Configure `pydantic.mypy` plugin in `pyproject.toml`**
In `apps/parsers/telegram/pyproject.toml`:
Add `plugins = ["pydantic.mypy"]` under `[tool.mypy]`.

- [ ] **Step 2: Fix signature and annotations in test files**
- In `tests/unit/test_pipeline.py`: add `wait_time: float = 3` to `MockExtractor.fetch_posts`.
- In `tests/unit/test_validator.py`: add type annotations for `build_valid_vacancy(**kwargs: Any) -> CreateVacancyRequest` and return types `-> None` for test functions.
- In `tests/unit/test_sink.py`: verify `SalaryDTO(from_=...)` is recognized by `pydantic.mypy`.

- [ ] **Step 3: Run mypy and pytest**
Run: `apps/parsers/telegram/.venv/Scripts/mypy.exe src tests`
Expected: Success: no issues found.
Run: `apps/parsers/telegram/.venv/Scripts/pytest.exe`
Expected: 100% PASS.

- [ ] **Step 4: Commit typing fixes**
```bash
git add apps/parsers/telegram/pyproject.toml apps/parsers/telegram/tests/
git commit -m "fix: resolve mypy typing errors in test suite"
```
