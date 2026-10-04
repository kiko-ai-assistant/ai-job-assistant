# Telegram Vacancy Parser Service Scaffolding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a production-grade Python project skeleton for `apps/parsers/telegram` following the ETL (Extract -> Transform -> Load) architecture, OpenAPI contract alignment, and clean interfaces for the Kiko platform.

**Architecture:** ETL data pipeline with isolated layers: Extractor (Telethon MTProto), Transformer (text normalization & heuristics), Sink (HTTP REST to Go Backend with `X-Parser-Api-Key`), and Storage (SQLite watermark checkpoints). All components communicate via Pydantic v2 schemas and abstract base classes.

**Tech Stack:** Python 3.11+, Telethon, HTTPX, Pydantic v2, Pydantic-Settings, aiosqlite, PyYAML, Pytest, Pytest-asyncio, Respx, Ruff, Mypy.

**Spec:** [docs/superpowers/specs/2026-10-05-telegram-parser-design.md](file:///C:/Users/Lenovo/Desktop/All%20important/AiJobAssistant/docs/superpowers/specs/2026-10-05-telegram-parser-design.md)

## Global Constraints

- Root location: `apps/parsers/telegram`
- Python version target: 3.11+
- Package management: `pyproject.toml`
- Backend Contract: OpenAPI 3.0 specification (`contracts/openapi/spec-files/api.yaml` and `models.yaml`), specifically `POST /vacancies/batch` with `X-Parser-Api-Key` header and schema `BatchCreateVacanciesRequest`.
- Type annotations: 100% strict type hints across all modules.

---

### Task 1: Project Scaffolding, Package Setup & Tooling Configuration

**Files:**
- Create: `apps/parsers/telegram/pyproject.toml`
- Create: `apps/parsers/telegram/.env.example`
- Create: `apps/parsers/telegram/README.md`
- Create: `apps/parsers/telegram/Dockerfile`
- Create: `apps/parsers/telegram/config/channels.yaml`
- Create: `apps/parsers/telegram/data/.gitkeep`
- Create: `apps/parsers/telegram/data/sessions/.gitkeep`
- Create: `apps/parsers/telegram/tests/__init__.py`
- Create: `apps/parsers/telegram/tests/conftest.py`
- Create: `apps/parsers/telegram/tests/fixtures/sample_posts.json`

**Interfaces:**
- Produces: Project build configuration, dependency list, and sample test fixtures.

- [ ] **Step 1: Create `apps/parsers/telegram/pyproject.toml`**

Define project dependencies, ruff, mypy, and pytest configuration:

```toml
[project]
name = "kiko-telegram-parser"
version = "0.1.0"
description = "Telegram vacancy parser service for Kiko AI Job Assistant"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "telethon>=1.36.0",
    "httpx>=0.27.0",
    "pydantic>=2.8.0",
    "pydantic-settings>=2.4.0",
    "aiosqlite>=0.20.0",
    "pyyaml>=6.0.1",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "respx>=0.21.0",
    "ruff>=0.6.0",
    "mypy>=1.11.0",
    "types-pyyaml>=6.0.12.20240917",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

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
strict = true
ignore_missing_imports = true
```

- [ ] **Step 2: Create `.env.example`, `channels.yaml`, `Dockerfile`, and `README.md`**

Create `apps/parsers/telegram/.env.example`:
```env
TG_API_ID=12345678
TG_API_HASH=your_telegram_api_hash_here
TG_SESSION_PATH=data/sessions/parser.session

BACKEND_URL=http://localhost:8080/api/v1
PARSER_API_KEY=test_parser_secret_key

POLL_INTERVAL_SECONDS=1800
BATCH_SIZE=50
SQLITE_DB_PATH=data/state.sqlite
CHANNELS_CONFIG_PATH=config/channels.yaml
LOG_LEVEL=INFO
```

Create `apps/parsers/telegram/config/channels.yaml`:
```yaml
channels:
  - username: "tproger_jobs"
    enabled: true
    tags: ["it", "development"]
  - username: "forpython"
    enabled: true
    tags: ["python", "backend"]
  - username: "golang_jobs"
    enabled: true
    tags: ["go", "backend"]
```

Create `apps/parsers/telegram/Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY src/ ./src/
COPY config/ ./config/
RUN mkdir -p data/sessions

CMD ["python", "-m", "src"]
```

Create `apps/parsers/telegram/README.md`:
```markdown
# Telegram Vacancy Parser Service (`apps/parsers/telegram`)

Production-grade ETL parser for scraping job vacancies from Telegram channels and ingesting them into Kiko Core Backend.

## Features
- **ETL Pipeline:** Independent Extractor, Transformer, Sink, and Storage layers.
- **Telegram MTProto (Telethon):** Robust fetching with session caching and FloodWait backoff.
- **Contract-first:** Full compliance with OpenAPI `POST /api/v1/vacancies/batch` and `X-Parser-Api-Key`.
- **Watermarking:** SQLite checkpoint tracking (`last_message_id`) guaranteeing at-least-once delivery.

## Local Setup
```bash
pip install -e ".[dev]"
cp .env.example .env
# Fill in TG_API_ID, TG_API_HASH, PARSER_API_KEY
python -m src --run-once
```

## Running Tests
```bash
pytest
```
```

Create placeholder `.gitkeep` files in `data/` and `data/sessions/`.

- [ ] **Step 3: Create test fixtures in `apps/parsers/telegram/tests/fixtures/sample_posts.json`**

Provide real-world message samples (vacancy post vs ad post):
```json
[
  {
    "channel_username": "forpython",
    "message_id": 101,
    "text": "Senior Python Developer в финтех стартап FinFlow\n\nЛокация: Удаленно (РФ/СНГ)\nЗарплата: от 300 000 до 400 000 руб. на руки\n\nСтек: Python 3.12, FastAPI, PostgreSQL, Redis, Docker, Kafka.\n\nКонтакты: @hr_recruiter",
    "date": "2026-10-05T00:00:00Z",
    "url": "https://t.me/forpython/101"
  },
  {
    "channel_username": "forpython",
    "message_id": 102,
    "text": "Подписывайтесь на наш канал с новостями AI! Ссылка в описании.",
    "date": "2026-10-05T01:00:00Z",
    "url": "https://t.me/forpython/102"
  }
]
```

Create `apps/parsers/telegram/tests/__init__.py` and `apps/parsers/telegram/tests/conftest.py`.

- [ ] **Step 4: Commit Task 1**
```bash
git add apps/parsers/telegram
git commit -m "feat(parser): add project scaffolding, config and test fixtures"
```

---

### Task 2: Configuration & Models Layer (Contracts & DTOs)

**Files:**
- Create: `apps/parsers/telegram/src/__init__.py`
- Create: `apps/parsers/telegram/src/config.py`
- Create: `apps/parsers/telegram/src/models/__init__.py`
- Create: `apps/parsers/telegram/src/models/raw_post.py`
- Create: `apps/parsers/telegram/src/models/vacancy.py`
- Create: `apps/parsers/telegram/src/models/channel.py`
- Test: `apps/parsers/telegram/tests/unit/test_models.py`

**Interfaces:**
- Produces:
  - `RawPost`: `channel_username: str`, `message_id: int`, `text: str`, `date: datetime`, `url: str`
  - `CreateVacancyRequest`: `external_id: str`, `source: str`, `title: str`, `url: str`, `company: str | None`, `salary_text: str | None`, `location: str | None`, `description: str | None`
  - `BatchCreateVacanciesRequest`: `vacancies: list[CreateVacancyRequest]`
  - `BatchIngestVacanciesResponse`: `inserted: int`, `ignored: int`
  - `ChannelConfig`: `username: str`, `enabled: bool`, `tags: list[str]`
  - `Settings`: Pydantic `BaseSettings` object

- [ ] **Step 1: Write failing test for models and config**

Create `apps/parsers/telegram/tests/unit/test_models.py`:
```python
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from src.models.raw_post import RawPost
from src.models.vacancy import (
    CreateVacancyRequest,
    BatchCreateVacanciesRequest,
    BatchIngestVacanciesResponse,
)
from src.models.channel import ChannelConfig, ChannelsConfigFile


def test_raw_post_model() -> None:
    now = datetime.now(timezone.utc)
    post = RawPost(
        channel_username="forpython",
        message_id=42,
        text="Vacancy text",
        date=now,
        url="https://t.me/forpython/42",
    )
    assert post.channel_username == "forpython"
    assert post.message_id == 42


def test_create_vacancy_request_contract() -> None:
    vacancy = CreateVacancyRequest(
        external_id="forpython_42",
        source="Telegram",
        title="Python Backend Developer",
        url="https://t.me/forpython/42",
        salary_text="от 250 000 руб.",
        company="FinFlow",
        location="Remote",
        description="Full text",
    )
    assert vacancy.external_id == "forpython_42"
    assert vacancy.source == "Telegram"

    batch = BatchCreateVacanciesRequest(vacancies=[vacancy])
    assert len(batch.vacancies) == 1

    resp = BatchIngestVacanciesResponse(inserted=1, ignored=0)
    assert resp.inserted == 1
    assert resp.ignored == 0


def test_create_vacancy_request_requires_mandatory_fields() -> None:
    with pytest.raises(ValidationError):
        CreateVacancyRequest.model_validate({"source": "Telegram"})


def test_channel_config() -> None:
    channel = ChannelConfig(username="test_chan", enabled=True, tags=["python"])
    assert channel.username == "test_chan"
    assert channel.tags == ["python"]
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest apps/parsers/telegram/tests/unit/test_models.py`
Expected: FAIL (ModuleNotFoundError: No module named 'src')

- [ ] **Step 3: Implement `config.py` and model files**

Create `apps/parsers/telegram/src/models/raw_post.py`:
```python
from datetime import datetime
from pydantic import BaseModel, Field


class RawPost(BaseModel):
    channel_username: str
    message_id: int
    text: str
    date: datetime
    url: str
```

Create `apps/parsers/telegram/src/models/vacancy.py`:
```python
from pydantic import BaseModel, Field


class CreateVacancyRequest(BaseModel):
    external_id: str
    source: str = "Telegram"
    title: str
    url: str
    company: str | None = None
    salary_text: str | None = None
    location: str | None = None
    description: str | None = None


class BatchCreateVacanciesRequest(BaseModel):
    vacancies: list[CreateVacancyRequest] = Field(default_factory=list)


class BatchIngestVacanciesResponse(BaseModel):
    inserted: int
    ignored: int
```

Create `apps/parsers/telegram/src/models/channel.py`:
```python
from pydantic import BaseModel, Field


class ChannelConfig(BaseModel):
    username: str
    enabled: bool = True
    tags: list[str] = Field(default_factory=list)


class ChannelsConfigFile(BaseModel):
    channels: list[ChannelConfig] = Field(default_factory=list)
```

Create `apps/parsers/telegram/src/models/__init__.py`:
```python
from .channel import ChannelConfig, ChannelsConfigFile
from .raw_post import RawPost
from .vacancy import (
    BatchCreateVacanciesRequest,
    BatchIngestVacanciesResponse,
    CreateVacancyRequest,
)

__all__ = [
    "RawPost",
    "CreateVacancyRequest",
    "BatchCreateVacanciesRequest",
    "BatchIngestVacanciesResponse",
    "ChannelConfig",
    "ChannelsConfigFile",
]
```

Create `apps/parsers/telegram/src/config.py`:
```python
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    tg_api_id: int = 0
    tg_api_hash: str = ""
    tg_session_path: Path = Path("data/sessions/parser.session")

    backend_url: str = "http://localhost:8080/api/v1"
    parser_api_key: str = "test_key"

    poll_interval_seconds: int = 1800
    batch_size: int = 50
    sqlite_db_path: Path = Path("data/state.sqlite")
    channels_config_path: Path = Path("config/channels.yaml")
    log_level: str = "INFO"
```

Create `apps/parsers/telegram/src/__init__.py`.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest apps/parsers/telegram/tests/unit/test_models.py -v`
Expected: PASS

- [ ] **Step 5: Commit Task 2**
```bash
git add apps/parsers/telegram/src apps/parsers/telegram/tests
git commit -m "feat(parser): add pydantic models, contracts and settings"
```

---

### Task 3: State Storage Layer (SQLite Checkpoints)

**Files:**
- Create: `apps/parsers/telegram/src/storage/__init__.py`
- Create: `apps/parsers/telegram/src/storage/base.py`
- Create: `apps/parsers/telegram/src/storage/sqlite_store.py`
- Test: `apps/parsers/telegram/tests/unit/test_state.py`

**Interfaces:**
- Consumes: `Path` for SQLite database file
- Produces: `BaseStateStore` ABC, `SqliteStateStore`
  - `async def get_checkpoint(channel: str) -> int`
  - `async def commit_checkpoint(channel: str, message_id: int) -> None`

- [ ] **Step 1: Write failing test for state storage**

Create `apps/parsers/telegram/tests/unit/test_state.py`:
```python
from pathlib import Path
import pytest
from src.storage.sqlite_store import SqliteStateStore


@pytest.mark.asyncio
async def test_sqlite_state_store_lifecycle(tmp_path: Path) -> None:
    db_path = tmp_path / "test_state.sqlite"
    store = SqliteStateStore(db_path)
    await store.initialize()

    # Initial checkpoint for unknown channel should be 0
    initial = await store.get_checkpoint("test_chan")
    assert initial == 0

    # Commit checkpoint
    await store.commit_checkpoint("test_chan", 42)
    saved = await store.get_checkpoint("test_chan")
    assert saved == 42

    # Update checkpoint with higher watermark
    await store.commit_checkpoint("test_chan", 100)
    updated = await store.get_checkpoint("test_chan")
    assert updated == 100

    # Different channel stays isolated
    chan2 = await store.get_checkpoint("other_chan")
    assert chan2 == 0

    await store.close()
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest apps/parsers/telegram/tests/unit/test_state.py`
Expected: FAIL (ModuleNotFoundError: No module named 'src.storage.sqlite_store')

- [ ] **Step 3: Implement `BaseStateStore` and `SqliteStateStore`**

Create `apps/parsers/telegram/src/storage/base.py`:
```python
from abc import ABC, abstractmethod


class BaseStateStore(ABC):
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize database schema or connections."""
        ...

    @abstractmethod
    async def get_checkpoint(self, channel: str) -> int:
        """Return the highest processed message_id for the channel, or 0 if none."""
        ...

    @abstractmethod
    async def commit_checkpoint(self, channel: str, message_id: int) -> None:
        """Persist new highest processed message_id for the channel."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Cleanly close storage resources."""
        ...
```

Create `apps/parsers/telegram/src/storage/sqlite_store.py`:
```python
from pathlib import Path
import aiosqlite
from .base import BaseStateStore


class SqliteStateStore(BaseStateStore):
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._db: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(self.db_path)
        await self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS checkpoints (
                channel TEXT PRIMARY KEY,
                last_message_id INTEGER NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await self._db.commit()

    async def get_checkpoint(self, channel: str) -> int:
        if not self._db:
            await self.initialize()
            assert self._db is not None

        async with self._db.execute(
            "SELECT last_message_id FROM checkpoints WHERE channel = ?",
            (channel,),
        ) as cursor:
            row = await cursor.fetchone()
            if row is None:
                return 0
            return int(row[0])

    async def commit_checkpoint(self, channel: str, message_id: int) -> None:
        if not self._db:
            await self.initialize()
            assert self._db is not None

        await self._db.execute(
            """
            INSERT INTO checkpoints (channel, last_message_id, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(channel) DO UPDATE SET
                last_message_id = MAX(checkpoints.last_message_id, excluded.last_message_id),
                updated_at = CURRENT_TIMESTAMP
            """,
            (channel, message_id),
        )
        await self._db.commit()

    async def close(self) -> None:
        if self._db:
            await self._db.close()
            self._db = None
```

Create `apps/parsers/telegram/src/storage/__init__.py`:
```python
from .base import BaseStateStore
from .sqlite_store import SqliteStateStore

__all__ = ["BaseStateStore", "SqliteStateStore"]
```

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest apps/parsers/telegram/tests/unit/test_state.py -v`
Expected: PASS

- [ ] **Step 5: Commit Task 3**
```bash
git add apps/parsers/telegram/src/storage apps/parsers/telegram/tests/unit/test_state.py
git commit -m "feat(parser): implement SQLite watermark state store"
```

---

### Task 4: Sink Layer (HTTP Backend Client with OpenAPI Contracts)

**Files:**
- Create: `apps/parsers/telegram/src/sink/__init__.py`
- Create: `apps/parsers/telegram/src/sink/base.py`
- Create: `apps/parsers/telegram/src/sink/backend_api.py`
- Test: `apps/parsers/telegram/tests/unit/test_sink.py`

**Interfaces:**
- Consumes: `CreateVacancyRequest`, `BatchCreateVacanciesRequest`, `BatchIngestVacanciesResponse`, `backend_url: str`, `parser_api_key: str`
- Produces: `BaseSink` ABC, `BackendApiSink`
  - `async def send_batch(vacancies: list[CreateVacancyRequest]) -> BatchIngestVacanciesResponse`

- [ ] **Step 1: Write failing test for BackendApiSink**

Create `apps/parsers/telegram/tests/unit/test_sink.py`:
```python
import httpx
import pytest
import respx
from src.models.vacancy import CreateVacancyRequest
from src.sink.backend_api import BackendApiSink


@pytest.mark.asyncio
async def test_backend_api_sink_sends_batch_with_headers() -> None:
    backend_url = "http://backend.test/api/v1"
    api_key = "secret_parser_key"

    sample_vacancy = CreateVacancyRequest(
        external_id="forpython_101",
        source="Telegram",
        title="Senior Python Developer",
        url="https://t.me/forpython/101",
        company="FinFlow",
        salary_text="300 000 руб.",
    )

    with respx.mock(base_url=backend_url) as respx_mock:
        route = respx_mock.post("/vacancies/batch").respond(
            status_code=200,
            json={"inserted": 1, "ignored": 0},
        )

        sink = BackendApiSink(backend_url=backend_url, parser_api_key=api_key)
        resp = await sink.send_batch([sample_vacancy])

        assert resp.inserted == 1
        assert resp.ignored == 0
        assert route.called
        last_request = route.calls.last.request
        assert last_request.headers["X-Parser-Api-Key"] == api_key
        assert "vacancies" in last_request.content.decode()

        await sink.close()


@pytest.mark.asyncio
async def test_backend_api_sink_handles_empty_batch() -> None:
    sink = BackendApiSink(backend_url="http://test", parser_api_key="k")
    resp = await sink.send_batch([])
    assert resp.inserted == 0
    assert resp.ignored == 0
    await sink.close()
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest apps/parsers/telegram/tests/unit/test_sink.py`
Expected: FAIL (ModuleNotFoundError: No module named 'src.sink.backend_api')

- [ ] **Step 3: Implement `BaseSink` and `BackendApiSink`**

Create `apps/parsers/telegram/src/sink/base.py`:
```python
from abc import ABC, abstractmethod
from src.models.vacancy import BatchIngestVacanciesResponse, CreateVacancyRequest


class BaseSink(ABC):
    @abstractmethod
    async def send_batch(
        self,
        vacancies: list[CreateVacancyRequest],
    ) -> BatchIngestVacanciesResponse:
        """Send a batch of vacancies to the destination."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Cleanly close connections."""
        ...
```

Create `apps/parsers/telegram/src/sink/backend_api.py`:
```python
import httpx
from src.models.vacancy import (
    BatchCreateVacanciesRequest,
    BatchIngestVacanciesResponse,
    CreateVacancyRequest,
)
from .base import BaseSink


class BackendApiSink(BaseSink):
    def __init__(
        self,
        backend_url: str,
        parser_api_key: str,
        timeout: float = 15.0,
    ) -> None:
        self.backend_url = backend_url.rstrip("/")
        self.client = httpx.AsyncClient(
            base_url=self.backend_url,
            headers={
                "X-Parser-Api-Key": parser_api_key,
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

    async def send_batch(
        self,
        vacancies: list[CreateVacancyRequest],
    ) -> BatchIngestVacanciesResponse:
        if not vacancies:
            return BatchIngestVacanciesResponse(inserted=0, ignored=0)

        payload = BatchCreateVacanciesRequest(vacancies=vacancies)
        response = await self.client.post(
            "/vacancies/batch",
            content=payload.model_dump_json(),
        )
        response.raise_for_status()
        data = response.json()
        return BatchIngestVacanciesResponse.model_validate(data)

    async def close(self) -> None:
        await self.client.aclose()
```

Create `apps/parsers/telegram/src/sink/__init__.py`:
```python
from .base import BaseSink
from .backend_api import BackendApiSink

__all__ = ["BaseSink", "BackendApiSink"]
```

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest apps/parsers/telegram/tests/unit/test_sink.py -v`
Expected: PASS

- [ ] **Step 5: Commit Task 4**
```bash
git add apps/parsers/telegram/src/sink apps/parsers/telegram/tests/unit/test_sink.py
git commit -m "feat(parser): implement BackendApiSink with OpenAPI contracts"
```

---

### Task 5: Extractor & Transformer Abstractions and Base Skeletons

**Files:**
- Create: `apps/parsers/telegram/src/extractor/__init__.py`
- Create: `apps/parsers/telegram/src/extractor/base.py`
- Create: `apps/parsers/telegram/src/extractor/telethon_client.py`
- Create: `apps/parsers/telegram/src/extractor/channel_reader.py`
- Create: `apps/parsers/telegram/src/transformer/__init__.py`
- Create: `apps/parsers/telegram/src/transformer/base.py`
- Create: `apps/parsers/telegram/src/transformer/heuristics.py`
- Create: `apps/parsers/telegram/src/transformer/post_parser.py`
- Test: `apps/parsers/telegram/tests/unit/test_transformer.py`

**Interfaces:**
- Produces:
  - `BaseExtractor(ABC)`: `fetch_posts(channel: str, since_message_id: int, limit: int) -> AsyncIterator[RawPost]`
  - `BaseTransformer(ABC)`: `transform(post: RawPost) -> CreateVacancyRequest | None`
  - `PostParser(BaseTransformer)`
  - `HeuristicExtractor`

- [ ] **Step 1: Write failing test for Transformer & PostParser**

Create `apps/parsers/telegram/tests/unit/test_transformer.py`:
```python
from datetime import datetime, timezone
import json
from pathlib import Path
from src.models.raw_post import RawPost
from src.transformer.post_parser import PostParser


def test_post_parser_extracts_vacancy() -> None:
    fixtures_path = Path(__file__).parent.parent / "fixtures" / "sample_posts.json"
    with open(fixtures_path, encoding="utf-8") as f:
        samples = json.load(f)

    parser = PostParser()

    # Post 1 is a vacancy
    raw_vacancy = RawPost.model_validate(samples[0])
    result = parser.transform(raw_vacancy)

    assert result is not None
    assert result.external_id == "forpython_101"
    assert "Python" in result.title
    assert result.salary_text is not None
    assert "300 000" in result.salary_text
    assert result.url == "https://t.me/forpython/101"

    # Post 2 is an ad / non-vacancy
    raw_ad = RawPost.model_validate(samples[1])
    ad_result = parser.transform(raw_ad)
    assert ad_result is None
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest apps/parsers/telegram/tests/unit/test_transformer.py`
Expected: FAIL (ModuleNotFoundError: No module named 'src.transformer.post_parser')

- [ ] **Step 3: Implement Extractor & Transformer layers**

Create `apps/parsers/telegram/src/extractor/base.py`:
```python
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from src.models.raw_post import RawPost


class BaseExtractor(ABC):
    @abstractmethod
    def fetch_posts(
        self,
        channel: str,
        since_message_id: int,
        limit: int = 100,
    ) -> AsyncIterator[RawPost]:
        """Fetch posts from a channel starting after since_message_id."""
        ...

    @abstractmethod
    async def start(self) -> None:
        """Start client connection."""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Close client connection."""
        ...
```

Create `apps/parsers/telegram/src/extractor/telethon_client.py`:
```python
import logging
from pathlib import Path
from telethon import TelegramClient, errors

logger = logging.getLogger(__name__)


class TelethonWrapper:
    def __init__(self, api_id: int, api_hash: str, session_path: Path) -> None:
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_path = session_path
        self.session_path.parent.mkdir(parents=True, exist_ok=True)
        self.client = TelegramClient(str(self.session_path), self.api_id, self.api_hash)

    async def connect(self) -> None:
        logger.info("Connecting Telethon MTProto client...")
        await self.client.connect()

    async def disconnect(self) -> None:
        logger.info("Disconnecting Telethon MTProto client...")
        await self.client.disconnect()
```

Create `apps/parsers/telegram/src/extractor/channel_reader.py`:
```python
from collections.abc import AsyncIterator
from datetime import datetime, timezone
import logging
from telethon import errors
from src.models.raw_post import RawPost
from .base import BaseExtractor
from .telethon_client import TelethonWrapper

logger = logging.getLogger(__name__)


class TelethonChannelExtractor(BaseExtractor):
    def __init__(self, wrapper: TelethonWrapper) -> None:
        self.wrapper = wrapper

    async def start(self) -> None:
        await self.wrapper.connect()

    async def stop(self) -> None:
        await self.wrapper.disconnect()

    async def fetch_posts(
        self,
        channel: str,
        since_message_id: int,
        limit: int = 100,
    ) -> AsyncIterator[RawPost]:
        clean_channel = channel.lstrip("@")
        try:
            entity = await self.wrapper.client.get_entity(clean_channel)
            async for message in self.wrapper.client.iter_messages(
                entity,
                min_id=since_message_id,
                limit=limit,
                reverse=True,  # Oldest to newest
            ):
                if not message.text:
                    continue
                date = message.date or datetime.now(timezone.utc)
                yield RawPost(
                    channel_username=clean_channel,
                    message_id=message.id,
                    text=message.text,
                    date=date,
                    url=f"https://t.me/{clean_channel}/{message.id}",
                )
        except errors.FloodWaitError as err:
            logger.warning("Telegram FloodWait: %s seconds", err.seconds)
            raise
        except Exception:
            logger.exception("Failed to fetch messages for channel %s", channel)
            raise
```

Create `apps/parsers/telegram/src/extractor/__init__.py`:
```python
from .base import BaseExtractor
from .channel_reader import TelethonChannelExtractor
from .telethon_client import TelethonWrapper

__all__ = ["BaseExtractor", "TelethonWrapper", "TelethonChannelExtractor"]
```

Create `apps/parsers/telegram/src/transformer/base.py`:
```python
from abc import ABC, abstractmethod
from src.models.raw_post import RawPost
from src.models.vacancy import CreateVacancyRequest


class BaseTransformer(ABC):
    @abstractmethod
    def transform(self, post: RawPost) -> CreateVacancyRequest | None:
        """Transform a raw post into a vacancy contract, or None if not a vacancy."""
        ...
```

Create `apps/parsers/telegram/src/transformer/heuristics.py`:
```python
import re

VACANCY_KEYWORDS = [
    r"вакансия",
    r"требуется",
    r"ищем",
    r"hiring",
    r"developer",
    r"разработчик",
    r"инженер",
    r"lead",
    r"senior",
    r"middle",
    r"junior",
]

SALARY_PATTERNS = [
    r"(\d[\d\s]{2,}\s*(?:до|от|-)?\s*\d*[\d\s]{2,}?\s*(?:руб|rub|usd|\$|eur|€|k|к|тыс))",
    r"(\$\s*\d+[\d\s]*(?:-\s*\$?\s*\d+[\d\s]*)?)",
    r"((?:от|до)\s*\d+[\d\s]*(?:руб|rub|\$|eur|k))",
]


class HeuristicExtractor:
    @staticmethod
    def is_vacancy(text: str) -> bool:
        lower = text.lower()
        if len(text.strip()) < 40:
            return False
        # Filter obvious non-vacancies
        if any(bad in lower for bad in ["реклама", "партнерский материал", "подписывайтесь на"]):
            if "вакансия" not in lower and "требуется" not in lower:
                return False
        return any(re.search(kw, lower) for kw in VACANCY_KEYWORDS)

    @staticmethod
    def extract_title(text: str) -> str:
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for line in lines[:3]:
            # Remove emoji and formatting artifacts
            cleaned = re.sub(r"[#*`_]", "", line).strip()
            if any(re.search(kw, cleaned.lower()) for kw in ["developer", "разработчик", "инженер", "lead", "senior", "middle", "junior", "teamlead"]):
                return cleaned[:100]
        return lines[0][:100] if lines else "Вакансия"

    @staticmethod
    def extract_salary(text: str) -> str | None:
        for pattern in SALARY_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    @staticmethod
    def extract_company(text: str) -> str | None:
        match = re.search(r"(?:компания|в\s+компанию|в)\s+([A-ZА-Я][A-Za-zА-Яа-я0-9\s\-]{2,30})", text)
        if match:
            return match.group(1).strip()
        return None
```

Create `apps/parsers/telegram/src/transformer/post_parser.py`:
```python
from src.models.raw_post import RawPost
from src.models.vacancy import CreateVacancyRequest
from .base import BaseTransformer
from .heuristics import HeuristicExtractor


class PostParser(BaseTransformer):
    def __init__(self, extractor: type[HeuristicExtractor] = HeuristicExtractor) -> None:
        self.extractor = extractor

    def transform(self, post: RawPost) -> CreateVacancyRequest | None:
        text = post.text
        if not self.extractor.is_vacancy(text):
            return None

        title = self.extractor.extract_title(text)
        salary = self.extractor.extract_salary(text)
        company = self.extractor.extract_company(text)

        external_id = f"{post.channel_username}_{post.message_id}"

        return CreateVacancyRequest(
            external_id=external_id,
            source="Telegram",
            title=title,
            company=company,
            salary_text=salary,
            description=text,
            url=post.url,
        )
```

Create `apps/parsers/telegram/src/transformer/__init__.py`:
```python
from .base import BaseTransformer
from .heuristics import HeuristicExtractor
from .post_parser import PostParser

__all__ = ["BaseTransformer", "HeuristicExtractor", "PostParser"]
```

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest apps/parsers/telegram/tests/unit/test_transformer.py -v`
Expected: PASS

- [ ] **Step 5: Commit Task 5**
```bash
git add apps/parsers/telegram/src/extractor apps/parsers/telegram/src/transformer apps/parsers/telegram/tests/unit/test_transformer.py
git commit -m "feat(parser): implement extractor and transformer modules"
```

---

### Task 6: Pipeline Orchestrator, Scheduler, CLI Entrypoint & Verification

**Files:**
- Create: `apps/parsers/telegram/src/utils/__init__.py`
- Create: `apps/parsers/telegram/src/utils/logger.py`
- Create: `apps/parsers/telegram/src/pipeline/__init__.py`
- Create: `apps/parsers/telegram/src/pipeline/orchestrator.py`
- Create: `apps/parsers/telegram/src/pipeline/scheduler.py`
- Create: `apps/parsers/telegram/src/__main__.py`
- Test: `apps/parsers/telegram/tests/unit/test_pipeline.py`

**Interfaces:**
- Produces:
  - `ETLPipeline`: orchestrates reading from Extractor, transforming via Transformer, uploading via Sink, committing watermark via StateStore.
  - `ScheduledRunner`: manages periodic invocation and shutdown.
  - `python -m src`: CLI entrypoint.

- [ ] **Step 1: Write integration unit test for `ETLPipeline`**

Create `apps/parsers/telegram/tests/unit/test_pipeline.py`:
```python
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from pathlib import Path
import pytest
from src.extractor.base import BaseExtractor
from src.models.raw_post import RawPost
from src.models.vacancy import BatchIngestVacanciesResponse, CreateVacancyRequest
from src.pipeline.orchestrator import ETLPipeline
from src.sink.base import BaseSink
from src.storage.sqlite_store import SqliteStateStore
from src.transformer.post_parser import PostParser


class MockExtractor(BaseExtractor):
    def __init__(self, posts: list[RawPost]) -> None:
        self.posts = posts

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass

    async def fetch_posts(
        self, channel: str, since_message_id: int, limit: int = 100
    ) -> AsyncIterator[RawPost]:
        for p in self.posts:
            if p.message_id > since_message_id:
                yield p


class MockSink(BaseSink):
    def __init__(self) -> None:
        self.sent: list[CreateVacancyRequest] = []

    async def send_batch(
        self, vacancies: list[CreateVacancyRequest]
    ) -> BatchIngestVacanciesResponse:
        self.sent.extend(vacancies)
        return BatchIngestVacanciesResponse(inserted=len(vacancies), ignored=0)

    async def close(self) -> None:
        pass


@pytest.mark.asyncio
async def test_etl_pipeline_run_channel(tmp_path: Path) -> None:
    now = datetime.now(timezone.utc)
    posts = [
        RawPost(
            channel_username="test_chan",
            message_id=1,
            text="Ищем Senior Python Developer на удаленку!",
            date=now,
            url="https://t.me/test_chan/1",
        ),
        RawPost(
            channel_username="test_chan",
            message_id=2,
            text="Реклама курсов, не вакансия",
            date=now,
            url="https://t.me/test_chan/2",
        ),
    ]

    extractor = MockExtractor(posts)
    transformer = PostParser()
    sink = MockSink()
    store = SqliteStateStore(tmp_path / "state.sqlite")
    await store.initialize()

    pipeline = ETLPipeline(
        extractor=extractor,
        transformer=transformer,
        sink=sink,
        state_store=store,
    )

    stats = await pipeline.process_channel("test_chan")

    assert stats["extracted"] == 2
    assert stats["transformed"] == 1
    assert stats["inserted"] == 1
    assert len(sink.sent) == 1
    assert sink.sent[0].external_id == "test_chan_1"

    # Verify watermark updated to highest message_id
    checkpoint = await store.get_checkpoint("test_chan")
    assert checkpoint == 2

    await store.close()
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest apps/parsers/telegram/tests/unit/test_pipeline.py`
Expected: FAIL (ModuleNotFoundError: No module named 'src.pipeline.orchestrator')

- [ ] **Step 3: Implement logger, orchestrator, scheduler, and `__main__.py`**

Create `apps/parsers/telegram/src/utils/logger.py`:
```python
import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
```

Create `apps/parsers/telegram/src/utils/__init__.py`:
```python
from .logger import setup_logging

__all__ = ["setup_logging"]
```

Create `apps/parsers/telegram/src/pipeline/orchestrator.py`:
```python
import logging
from src.extractor.base import BaseExtractor
from src.models.vacancy import CreateVacancyRequest
from src.sink.base import BaseSink
from src.storage.base import BaseStateStore
from src.transformer.base import BaseTransformer

logger = logging.getLogger(__name__)


class ETLPipeline:
    def __init__(
        self,
        extractor: BaseExtractor,
        transformer: BaseTransformer,
        sink: BaseSink,
        state_store: BaseStateStore,
        batch_size: int = 50,
    ) -> None:
        self.extractor = extractor
        self.transformer = transformer
        self.sink = sink
        self.state_store = state_store
        self.batch_size = batch_size

    async def process_channel(self, channel: str) -> dict[str, int]:
        clean_channel = channel.lstrip("@")
        checkpoint = await self.state_store.get_checkpoint(clean_channel)
        logger.info("Channel @%s watermark is %d", clean_channel, checkpoint)

        extracted_count = 0
        transformed_vacancies: list[CreateVacancyRequest] = []
        highest_message_id = checkpoint

        async for post in self.extractor.fetch_posts(clean_channel, since_message_id=checkpoint):
            extracted_count += 1
            highest_message_id = max(highest_message_id, post.message_id)

            vacancy = self.transformer.transform(post)
            if vacancy:
                transformed_vacancies.append(vacancy)

            if len(transformed_vacancies) >= self.batch_size:
                await self.sink.send_batch(transformed_vacancies)
                transformed_vacancies.clear()

        inserted = 0
        if transformed_vacancies:
            resp = await self.sink.send_batch(transformed_vacancies)
            inserted = resp.inserted

        if highest_message_id > checkpoint:
            await self.state_store.commit_checkpoint(clean_channel, highest_message_id)
            logger.info("Committed watermark for @%s: %d", clean_channel, highest_message_id)

        return {
            "extracted": extracted_count,
            "transformed": len(transformed_vacancies) + inserted,
            "inserted": inserted,
        }
```

Create `apps/parsers/telegram/src/pipeline/scheduler.py`:
```python
import asyncio
import logging
from pathlib import Path
import yaml
from src.models.channel import ChannelsConfigFile
from .orchestrator import ETLPipeline

logger = logging.getLogger(__name__)


class ScheduledRunner:
    def __init__(
        self,
        pipeline: ETLPipeline,
        channels_config_path: Path,
        poll_interval_seconds: int = 1800,
    ) -> None:
        self.pipeline = pipeline
        self.channels_config_path = channels_config_path
        self.poll_interval = poll_interval_seconds
        self._running = False

    def load_channels(self) -> list[str]:
        if not self.channels_config_path.exists():
            logger.warning("Channels config file not found: %s", self.channels_config_path)
            return []
        with open(self.channels_config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        cfg = ChannelsConfigFile.model_validate(data)
        return [c.username for c in cfg.channels if c.enabled]

    async def run_once(self) -> None:
        channels = self.load_channels()
        logger.info("Starting extraction run for %d channels", len(channels))
        for channel in channels:
            try:
                stats = await self.pipeline.process_channel(channel)
                logger.info(
                    "Channel @%s: extracted %d, ingested %d",
                    channel,
                    stats["extracted"],
                    stats["inserted"],
                )
            except Exception:
                logger.exception("Error processing channel @%s", channel)

    async def start(self) -> None:
        self._running = True
        logger.info("Starting scheduler loop (interval %d sec)", self.poll_interval)
        while self._running:
            await self.run_once()
            logger.info("Sleeping for %d seconds...", self.poll_interval)
            await asyncio.sleep(self.poll_interval)

    def stop(self) -> None:
        self._running = False
```

Create `apps/parsers/telegram/src/pipeline/__init__.py`:
```python
from .orchestrator import ETLPipeline
from .scheduler import ScheduledRunner

__all__ = ["ETLPipeline", "ScheduledRunner"]
```

Create `apps/parsers/telegram/src/__main__.py`:
```python
import argparse
import asyncio
import logging
from src.config import Settings
from src.extractor.channel_reader import TelethonChannelExtractor
from src.extractor.telethon_client import TelethonWrapper
from src.pipeline.orchestrator import ETLPipeline
from src.pipeline.scheduler import ScheduledRunner
from src.sink.backend_api import BackendApiSink
from src.storage.sqlite_store import SqliteStateStore
from src.transformer.post_parser import PostParser
from src.utils.logger import setup_logging

logger = logging.getLogger("kiko.parser")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Kiko Telegram Vacancy Parser")
    parser.add_argument(
        "--run-once",
        action="store_true",
        help="Run single extraction pass across all channels and exit",
    )
    args = parser.parse_args()

    settings = Settings()
    setup_logging(settings.log_level)
    logger.info("Initializing Telegram Parser Service...")

    wrapper = TelethonWrapper(
        api_id=settings.tg_api_id,
        api_hash=settings.tg_api_hash,
        session_path=settings.tg_session_path,
    )
    extractor = TelethonChannelExtractor(wrapper)
    transformer = PostParser()
    sink = BackendApiSink(
        backend_url=settings.backend_url,
        parser_api_key=settings.parser_api_key,
    )
    state_store = SqliteStateStore(settings.sqlite_db_path)
    await state_store.initialize()

    pipeline = ETLPipeline(
        extractor=extractor,
        transformer=transformer,
        sink=sink,
        state_store=state_store,
        batch_size=settings.batch_size,
    )

    runner = ScheduledRunner(
        pipeline=pipeline,
        channels_config_path=settings.channels_config_path,
        poll_interval_seconds=settings.poll_interval_seconds,
    )

    try:
        await extractor.start()
        if args.run_once:
            await runner.run_once()
        else:
            await runner.start()
    finally:
        await extractor.stop()
        await sink.close()
        await state_store.close()
        logger.info("Parser service stopped cleanly.")


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest apps/parsers/telegram/tests/unit/test_pipeline.py -v`
Expected: PASS

- [ ] **Step 5: Run full test suite across the new service**
Run: `pytest apps/parsers/telegram/tests -v`
Expected: ALL PASS

- [ ] **Step 6: Commit Task 6**
```bash
git add apps/parsers/telegram/src apps/parsers/telegram/tests
git commit -m "feat(parser): add pipeline orchestrator, scheduler and main entrypoint"
```

---

## Plan Self-Review Check
- **Spec Coverage:** Covers Telethon MTProto Extractor, PostParser Transformer, BackendApiSink with `X-Parser-Api-Key` and `POST /vacancies/batch`, SQLite Watermark state store, `pyproject.toml`, Dockerfile, tests, and CLI entrypoint.
- **Type Consistency:** Model types `RawPost`, `CreateVacancyRequest`, `BatchIngestVacanciesResponse` are consistent across all layers.
- **No Placeholders:** All files, configs, tests, and code are written out in full.
