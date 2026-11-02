# Parsers

Collects vacancies from many source (HH.ru, career websites, Telegram channels etc.) and sends them to the backend.
Stack: Python 3.12+, Scrapling, Telethon.

## Rules
- Parsers never access the database. Send results to backend REST API only, using the models from `contracts/openapi/`.
- If the contract has to change, stop and ask first.
- Use the `scrapling-official` skill for any Scrapling code. Do not guess the API; follow the skill's references.
- Choose the lightest fetcher that works: static first, then dynamic, stealthy only when blocked.
- Respect target sites: rate limits, retries with backoff, no aggressive concurrency.

## Structure
- `apps/parsers/<source>/` — one parser per source (e.g. `hh/`, `telegram/`).
- A new parser must follow clean architecture agreements and return the normalized vacancy model; never invent fields outside the contract.

## Adding a parser
1. Create `apps/parsers/<source>/` with its own entrypoint.
2. Add tests with saved HTML/JSON fixtures; tests must not hit real sites.
3. Add a nested AGENTS.md only if the source has special auth, anti-bot logic or fragile selectors.

## Commands
- Install: <command>
- Browsers for Scrapling: `scrapling install`
- Run a parser: <command>
- Tests / lint: <command>

## Secrets
Telegram API credentials, sessions and proxies come only from env vars. Never commit `.session` files or `.env`.