from pathlib import Path

import aiosqlite

from .base import BaseStateStore


class SqliteStateStore(BaseStateStore):
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._db: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(self.db_path)
        await self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS checkpoints (
                channel TEXT PRIMARY KEY,
                last_message_id INTEGER NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await self._db.commit()

    async def get_checkpoint(self, channel: str) -> int:
        if not self._db:
            await self.initialize()
            assert self._db is not None

        async with self._db.execute(
            "SELECT last_message_id FROM checkpoints WHERE channel = ?",
            (channel,),
        ) as cursor:
            row = await cursor.fetchone()
            if row is None:
                return 0
            return int(row[0])

    async def commit_checkpoint(self, channel: str, message_id: int) -> None:
        if not self._db:
            await self.initialize()
            assert self._db is not None

        await self._db.execute(
            """
            INSERT INTO checkpoints (channel, last_message_id, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(channel) DO UPDATE SET
                last_message_id = MAX(checkpoints.last_message_id, excluded.last_message_id),
                updated_at = CURRENT_TIMESTAMP
            """,
            (channel, message_id),
        )
        await self._db.commit()

    async def close(self) -> None:
        if self._db:
            await self._db.close()
            self._db = None
