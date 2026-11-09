import logging

from src.extractor.base import BaseExtractor
from src.models.vacancy import CreateVacancyRequest
from src.sink.base import BaseSink
from src.storage.base import BaseStateStore
from src.transformer.base import BaseTransformer

logger = logging.getLogger(__name__)


class ETLPipeline:
    def __init__(
        self,
        extractor: BaseExtractor,
        transformer: BaseTransformer,
        sink: BaseSink,
        state_store: BaseStateStore,
        batch_size: int = 50,
    ) -> None:
        self.extractor = extractor
        self.transformer = transformer
        self.sink = sink
        self.state_store = state_store
        self.batch_size = batch_size

    async def process_channel(self, channel: str) -> dict[str, int]:
        clean_channel = channel.lstrip("@")
        checkpoint = await self.state_store.get_checkpoint(clean_channel)
        logger.info("Channel @%s watermark is %d", clean_channel, checkpoint)

        extracted_count = 0
        transformed_count = 0
        transformed_vacancies: list[CreateVacancyRequest] = []
        highest_message_id = checkpoint
        total_inserted = 0

        async for post in self.extractor.fetch_posts(clean_channel, since_message_id=checkpoint):
            extracted_count += 1
            highest_message_id = max(highest_message_id, post.message_id)

            vacancy = await self.transformer.transform(post)
            if vacancy:
                transformed_vacancies.append(vacancy)
                transformed_count += 1

            if len(transformed_vacancies) >= self.batch_size:
                resp = await self.sink.send_batch(transformed_vacancies)
                total_inserted += resp.inserted
                transformed_vacancies.clear()

        if transformed_vacancies:
            resp = await self.sink.send_batch(transformed_vacancies)
            total_inserted += resp.inserted
            transformed_vacancies.clear()

        if highest_message_id > checkpoint:
            await self.state_store.commit_checkpoint(clean_channel, highest_message_id)
            logger.info("Committed watermark for @%s: %d", clean_channel, highest_message_id)

        return {
            "extracted": extracted_count,
            "transformed": transformed_count,
            "inserted": total_inserted,
        }
