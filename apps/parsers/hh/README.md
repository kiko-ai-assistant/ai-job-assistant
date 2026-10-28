# HH Scraper v2 — JSON mode

Autonomous HH vacancy scraper. Backend integration is intentionally not included yet; output is stored in JSON.

## Implemented

- Search by narrow groups: `it`, `management`, `marketing`
- Current HH `professional_role` filters for IT/tech management
- Narrow marketing keyword searches without guessing unknown role IDs
- Pagination
- Location and employment filters
- Vacancy detail enrichment
- Full description and `datePosted`
- Deduplication by `(source, external_id)`
- Configurable random throttling
- Exponential backoff for 403, 429, network errors and 5xx
- `Retry-After` support for 429
- CAPTCHA detection -> stop + log + optional external alert
- Mass-error detector
- Layout-change detector
- HTTP/run statistics
- Atomic JSON writes
- Partial progress preserved after every successful vacancy
- TTL refresh of existing vacancies
- Separate registry for 404/410 vacancies
- Centralized selectors
- Optional webhook or Telegram alerts
- Optional fixed User-Agent

Automatic CAPTCHA solving, proxy/IP rotation and anti-bot evasion are intentionally not implemented.

## Install

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

`Fetcher` does not require `scrapling install`.

## Run

All enabled groups from config:

```bash
python main.py
```

Only IT, Moscow, first 2 pages per target:

```bash
python main.py --groups it --area 1 --pages 2
```

Full-time only:

```bash
python main.py --groups it management --employment full
```

Refresh already stored vacancies after 6 hours:

```bash
python main.py --refresh-hours 6
```

## Output

```text
output/vacancies.json
output/unavailable.json
logs/hh_scraper.log
```

## Alerts

Set environment variables if needed:

```text
ALERT_WEBHOOK_URL=https://...
```

or Telegram:

```text
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

Alerts are sent for:

- CAPTCHA
- repeated 403/429 block
- likely layout change
- mass detail-page failures

## User-Agent

A fixed User-Agent can be supplied through `HH_SCRAPER_USER_AGENT`. Automatic User-Agent rotation is not used.

## Tests

```bash
pytest -q
```
