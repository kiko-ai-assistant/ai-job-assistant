import asyncpg
import logging
from pathlib import Path
from src.config import BASE_DIR
from src.services.logs.logger import AppLogger


class BaseRepository:
    def __init__(self, pool: asyncpg.Pool, logger: AppLogger):
        self._pool = pool
        self._logger = logger

        self._queries_path = Path(BASE_DIR) / "src" / "services" / "database" / "queries"
        self._queries_path.mkdir(parents=True, exist_ok=True)

    def _get_query(self, entity: str, query_name: str) -> str:
        """Read SQL file and returns the query as a string object"""
        filepath = self._queries_path / entity / f"{query_name}.sql"
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            self._logger.error(f"SQL file not found: {filepath}")
            raise
        except Exception as e:
            self._logger.critical(f"Failed to read SQL file: {e}")
            raise
