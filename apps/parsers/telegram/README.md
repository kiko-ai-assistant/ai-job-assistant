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
