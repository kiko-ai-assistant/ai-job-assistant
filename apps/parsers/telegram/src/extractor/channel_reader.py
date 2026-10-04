import logging
from collections.abc import AsyncIterator
from datetime import UTC, datetime

from telethon import errors

from src.models.raw_post import RawPost

from .base import BaseExtractor
from .telethon_client import TelethonWrapper

logger = logging.getLogger(__name__)


class TelethonChannelExtractor(BaseExtractor):
    def __init__(self, wrapper: TelethonWrapper) -> None:
        self.wrapper = wrapper

    async def start(self) -> None:
        await self.wrapper.connect()

    async def stop(self) -> None:
        await self.wrapper.disconnect()

    async def fetch_posts(
        self,
        channel: str,
        since_message_id: int,
        limit: int = 100,
    ) -> AsyncIterator[RawPost]:
        clean_channel = channel.lstrip("@")
        try:
            entity = await self.wrapper.client.get_entity(clean_channel)
            async for message in self.wrapper.client.iter_messages(
                entity,
                min_id=since_message_id,
                limit=limit,
                reverse=True,  # Oldest to newest
            ):
                if not message.text:
                    continue
                date = message.date or datetime.now(UTC)
                yield RawPost(
                    channel_username=clean_channel,
                    message_id=message.id,
                    text=message.text,
                    date=date,
                    url=f"https://t.me/{clean_channel}/{message.id}",
                )
        except errors.FloodWaitError as err:
            logger.warning("Telegram FloodWait: %s seconds", err.seconds)
            raise
        except Exception:
            logger.exception("Failed to fetch messages for channel %s", channel)
            raise
