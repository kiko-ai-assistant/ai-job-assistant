from typing import Optional

import asyncpg

from src.config import load_db_config
from src.services.database.repositories.user_repository import UserRepository
from src.services.database.repositories.user_settings_repository import UserSettingsRepository
from src.services.logs.logger import AppLogger, db_logger

class Database:
    def __init__(self, dsn: str = load_db_config(), logger: AppLogger = db_logger):
        self.dsn = dsn
        self.__pool = None

        # Repositories
        self.users: Optional[UserRepository] = None
        self.user_settings: Optional[UserSettingsRepository] = None

        # Logger
        self._logger = logger

    @property
    def pool(self) -> asyncpg.Pool:
        return self.__pool

    async def connect(self) -> None:
        """Creates connection pool and initializes repositories"""
        self.__pool = await asyncpg.create_pool(dsn=self.dsn, max_size=15)
        self.users = UserRepository(self.__pool, self._logger)
        self.user_settings = UserSettingsRepository(self.__pool, self._logger)

    async def disconnect(self) -> None:
        """Closes connection pool if it exists"""
        if self.__pool:
            await self.__pool.close()
