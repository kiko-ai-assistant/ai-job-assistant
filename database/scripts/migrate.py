import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BOT_DIR = PROJECT_ROOT / "apps" / "bot"

for p in (PROJECT_ROOT, BOT_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from yoyo import read_migrations, get_backend
from src.config import MIGRATIONS_DIR, load_db_config


def run_migrations():
    dsn = load_db_config()

    backend = get_backend(dsn)
    migrations = read_migrations(str(MIGRATIONS_DIR))

    with backend.lock():
        backend.apply_migrations(backend.to_apply(migrations=migrations))


if __name__ == "__main__":
    run_migrations()
