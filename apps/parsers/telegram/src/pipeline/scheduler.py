import asyncio
import logging
from pathlib import Path

import yaml

from src.models.channel import ChannelsConfigFile

from .orchestrator import ETLPipeline

logger = logging.getLogger(__name__)


class ScheduledRunner:
    def __init__(
        self,
        pipeline: ETLPipeline,
        channels_config_path: Path,
        poll_interval_seconds: int = 1800,
    ) -> None:
        self.pipeline = pipeline
        self.channels_config_path = channels_config_path
        self.poll_interval = poll_interval_seconds
        self._running = False

    def load_channels(self) -> list[str]:
        if not self.channels_config_path.exists():
            logger.warning("Channels config file not found: %s", self.channels_config_path)
            return []
        with open(self.channels_config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        cfg = ChannelsConfigFile.model_validate(data)
        return [c.username for c in cfg.channels if c.enabled]

    async def run_once(self) -> None:
        channels = self.load_channels()
        logger.info("Starting extraction run for %d channels", len(channels))
        for channel in channels:
            try:
                stats = await self.pipeline.process_channel(channel)
                logger.info(
                    "Channel @%s: extracted %d, ingested %d",
                    channel,
                    stats["extracted"],
                    stats["inserted"],
                )
            except Exception:
                logger.exception("Error processing channel @%s", channel)

    async def start(self) -> None:
        self._running = True
        logger.info("Starting scheduler loop (interval %d sec)", self.poll_interval)
        while self._running:
            await self.run_once()
            logger.info("Sleeping for %d seconds...", self.poll_interval)
            await asyncio.sleep(self.poll_interval)

    def stop(self) -> None:
        self._running = False
