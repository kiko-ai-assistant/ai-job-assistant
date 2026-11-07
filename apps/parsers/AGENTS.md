# Parsers

Collects vacancies from many sources (HH.ru, career websites, Telegram channels, etc.) and sends them to the backend REST API.
Stack: Python 3.12+, Scrapling, Telethon, Pydantic v2, HTTPX.

## Shared Package: `kiko-parsers-base` (`apps/parsers/base`)
All parsers consume the monorepo package `kiko-parsers-base` (`parsers_base`), which provides shared domain building blocks:
- **Models (`parsers_base.models.vacancy`)**: OpenAPI-compliant DTOs (`CreateVacancyRequest`, `SalaryDTO`, `LocationDTO`, `BatchCreateVacanciesRequest`, `BatchCreateVacanciesResponse`, `BatchIngestVacanciesResponse`).
- **Validation (`parsers_base.validation`)**: `VacancyValidator` and `ValidationResult` enforcing domain invariants (title, company, description lengths, salary bounds, location hierarchy, date skew/window, allowed sources whitelist).
- **Sink (`parsers_base.sink`)**: `BaseSink` abstraction, `BackendApiSink` HTTP client with retry backoff and auth header (`X-Parser-Api-Key`) sending to `POST /vacancies/batch`, and `SinkError`.
- **Parser Lifecycle (`parsers_base.parser`)**: `BaseParser` template method abstract base class coordinating async streaming, validation, batch buffering, sink delivery, lifecycle hooks (`on_batch_sent`), and `ParserStats` collection.

## Rules
- Parsers never access the database directly. Send results to backend REST API only, using the models from `contracts/openapi/` and `kiko-parsers-base`.
- If the contract has to change, stop and ask first.
- Use the `scrapling-official` skill for any Scrapling code. Do not guess the API; follow the skill's references.
- Choose the lightest fetcher that works: static first, then dynamic, stealthy only when blocked.
- Respect target sites: rate limits, retries with backoff, no aggressive concurrency.

## Structure
- `apps/parsers/base/` — `kiko-parsers-base` shared monorepo package for all scrapers.
- `apps/parsers/<source>/` — concrete parser per source (e.g. `hh/`, `telegram/`).
- A new parser must follow clean architecture agreements and yield normalized `CreateVacancyRequest` objects; never invent fields outside the contract.

## Adding a parser
1. Add `kiko-parsers-base` to dependencies (`apps/parsers/<source>/pyproject.toml`).
2. Create `apps/parsers/<source>/` with its own entrypoint.
3. Inherit from `parsers_base.BaseParser` and implement the abstract generator `async def parse(self, **kwargs) -> AsyncIterator[CreateVacancyRequest]`.
4. Configure `BackendApiSink` and optional custom `VacancyValidator` source whitelist.
5. Execute via `await parser.run()` to handle validation, batching, and sink dispatch automatically.
6. Add unit tests with saved HTML/JSON fixtures; tests must not hit real sites.
7. Add a nested AGENTS.md only if the source has special auth, anti-bot logic or fragile selectors.

## Commands
- Install base package: `pip install -e apps/parsers/base`
- Browsers for Scrapling: `scrapling install`
- Run a parser: `<command>`
- Tests / lint: `<command>`

## Secrets
Telegram API credentials, sessions, and proxies come only from env vars. Never commit `.session` files or `.env`.
