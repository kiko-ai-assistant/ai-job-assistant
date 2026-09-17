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
