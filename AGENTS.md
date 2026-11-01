# Project Context: AI Job Assistant
You are a Senior Software Developer and Backend Architect. This is a polyglot monorepository containing AI-based job searching platform with web dashboard and Telegram client.

## Layers & Architecture
- The system contains many independent microservices:
  - `contracts/openapi/` - single source of truth.
  - `apps/backend` - owns database and business logic (Go 1.26.2, Echo, sqlc)
  - `apps/parsers` - includes web-sites and Telegram scrappers (Python 3.12+, Scrapling, Telethon)
  - `apps/web` - frontend; simple dashboard of vacancies (TypeScript)
  - `apps/bot` - Telegram bot with all features access (Python 3.12+, Aiogram 3.x+)
  - `apps/engine` - AI matching (Python 3.12+, OpenRouter/OpenAI models)
- Only backend accesses the database. Other services use backend REST API.
- Contract-first: change `contracts/openapi/` → edit clients → implement.

Each service has its own AGENTS.md with details; read it before working there.

## Conventions
- Code, commits and docs in pure technical english.
- Do not add comments in the code if user didn't request it.
- Secrets only via env vars; never commit `.env`.
- Ask before adding dependencies or changing contracts.

## Git Commit Standards
You must commit all modifications using the Conventional Commits specification.
- Format: `<prefix>: <short imperative description in English without a trailing period>`
- Allowed Prefixes: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`
- Example: `feat: add llm client for engine`
