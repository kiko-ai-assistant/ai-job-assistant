import logging
from pathlib import Path

from telethon import TelegramClient

logger = logging.getLogger(__name__)


class TelethonWrapper:
    def __init__(self, api_id: int, api_hash: str, session_path: Path) -> None:
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_path = session_path
        self.session_path.parent.mkdir(parents=True, exist_ok=True)
        self.client = TelegramClient(str(self.session_path), self.api_id, self.api_hash)

    async def connect(self) -> None:
        logger.info("Connecting Telethon MTProto client...")
        await self.client.connect()

    async def disconnect(self) -> None:
        logger.info("Disconnecting Telethon MTProto client...")
        await self.client.disconnect()
