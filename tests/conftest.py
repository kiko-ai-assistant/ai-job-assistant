import pytest
import asyncio
import asyncpg

from yoyo import read_migrations, get_backend

from src.config import load_db_test_config, MIGRATIONS_DIR


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def db_pool():
    dsn = load_db_test_config()

    backend = get_backend(dsn)
    migrations = read_migrations(str(MIGRATIONS_DIR))

    with backend.lock():
        backend.apply_migrations(backend.to_apply(migrations=migrations))

    pool = await asyncpg.create_pool(dsn=dsn, min_size=1, max_size=5)

    yield pool
    await pool.close()
