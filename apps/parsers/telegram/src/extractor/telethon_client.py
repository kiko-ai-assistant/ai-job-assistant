import logging
from pathlib import Path

from telethon import TelegramClient

logger = logging.getLogger(__name__)


class TelethonWrapper:
    def __init__(self, api_id: int, api_hash: str, session_path: Path | None) -> None:
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_path = session_path
        session: str | None = None
        if self.session_path is not None:
            self.session_path.parent.mkdir(parents=True, exist_ok=True)
            session = str(self.session_path)
        self.client = TelegramClient(session, self.api_id, self.api_hash)

    async def connect(self) -> None:
        logger.info("Connecting Telethon MTProto client...")
        await self.client.connect()

    async def login(self, phone: str | None = None) -> None:
        logger.info("Starting interactive Telethon authentication...")
        if phone:
            await self.client.start(phone=phone)
        else:
            await self.client.start()
        me = await self.client.get_me()
        username = getattr(me, "username", None) or getattr(me, "first_name", "User")
        logger.info("Successfully authenticated as: %s", username)

    async def disconnect(self) -> None:
        logger.info("Disconnecting Telethon MTProto client...")
        await self.client.disconnect()
