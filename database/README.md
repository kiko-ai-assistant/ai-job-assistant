# Database Layer

This directory is the single source of truth for the database schema, migrations, and database administration scripts for the Kiko project.

## Structure

- `migrations/`: Pure SQL migrations (`.up.sql` and `.down.sql`).
  - `0001_create_users`: Core `users` table and `user_settings` table.
  - `0002_vacancies`: Global vacancies scraped across all sources.
  - `0003_user_vacancies`: Relation table linking users to vacancies with `match_score`, `ai_summary`, and `cover_letter`.
- `scripts/`: Migration execution scripts (`migrate.py`, `loader.py`).
