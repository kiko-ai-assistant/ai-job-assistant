import argparse
import asyncio
import logging

from src.config import Settings
from src.extractor.channel_reader import TelethonChannelExtractor
from src.extractor.telethon_client import TelethonWrapper
from src.pipeline.orchestrator import ETLPipeline
from src.pipeline.scheduler import ScheduledRunner
from src.sink.backend_api import BackendApiSink
from src.storage.sqlite_store import SqliteStateStore
from src.transformer.llm_extractor import LlmExtractor
from src.transformer.post_parser import PostParser
from src.utils.logger import setup_logging
from src.validation.validator import VacancyValidator

logger = logging.getLogger("kiko.parser")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Kiko Telegram Vacancy Parser")
    parser.add_argument(
        "--run-once",
        action="store_true",
        help="Run single extraction pass across all channels and exit",
    )
    parser.add_argument(
        "--login",
        action="store_true",
        help="Interactively authorize Telegram client and save session file",
    )
    args = parser.parse_args()

    settings = Settings()
    setup_logging(settings.log_level)
    logger.info("Initializing Telegram Parser Service...")

    wrapper = TelethonWrapper(
        api_id=settings.tg_api_id,
        api_hash=settings.tg_api_hash,
        session_path=settings.tg_session_path,
    )
    if args.login:
        await wrapper.login()
        await wrapper.disconnect()
        return
    extractor = TelethonChannelExtractor(wrapper)
    llm_extractor = LlmExtractor(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model=settings.llm_model,
        timeout=settings.llm_timeout,
    )
    validator = VacancyValidator()
    transformer = PostParser(llm_extractor=llm_extractor, validator=validator)
    sink = BackendApiSink(
        backend_url=settings.backend_url,
        parser_api_key=settings.parser_api_key,
    )
    state_store = SqliteStateStore(settings.sqlite_db_path)
    await state_store.initialize()

    pipeline = ETLPipeline(
        extractor=extractor,
        transformer=transformer,
        sink=sink,
        state_store=state_store,
        batch_size=settings.batch_size,
    )

    runner = ScheduledRunner(
        pipeline=pipeline,
        channels_config_path=settings.channels_config_path,
        poll_interval_seconds=settings.poll_interval_seconds,
    )

    try:
        await extractor.start()
        if args.run_once:
            await runner.run_once()
        else:
            await runner.start()
    finally:
        await extractor.stop()
        await llm_extractor.close()
        await sink.close()
        await state_store.close()
        logger.info("Parser service stopped cleanly.")


if __name__ == "__main__":
    asyncio.run(main())
