import pytest

from src.services.database.repositories.user_repository import UserRepository
from src.services.database.repositories.user_settings_repository import UserSettingsRepository
from src.services.logs.logger import db_logger


@pytest.fixture
async def user_repo(db_pool):
    await db_pool.execute("TRUNCATE TABLE users CASCADE")
    repo = UserRepository(db_pool, db_logger)
    return repo

@pytest.fixture
async def user_settings_repo(db_pool):
    await db_pool.execute("TRUNCATE TABLE user_settings CASCADE")
    repo = UserSettingsRepository(db_pool, db_logger)
    return repo
