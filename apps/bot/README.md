# Telegram Bot Client (apps/bot)

Telegram client frontend for Kiko — AI Job Assistant.

## Technology
- Python 3.12
- aiogram 3.x
- asyncpg (PostgreSQL client)

## Local Development

```bash
# 1. Navigate to bot directory
cd apps/bot

# 2. Install dependencies (virtual environment recommended)
pip install -r requirements.txt

# 3. Run bot
python run.py
```

## Structure
- `src/bot/handlers`: Telegram command and inline keyboard message handlers.
- `src/bot/keyboard`: Inline and reply keyboard builders.
- `src/bot/middlewares`: Chat cleaning and user context middleware.
- `src/bot/state`: FSM (Finite State Machine) states for user setup.
- `src/locales`: Localization strings (multilingual support).
- `src/services`: Database repositories and loggers.
