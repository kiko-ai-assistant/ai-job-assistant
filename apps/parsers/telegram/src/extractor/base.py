from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from src.models.raw_post import RawPost


class BaseExtractor(ABC):
    @abstractmethod
    def fetch_posts(
        self,
        channel: str,
        since_message_id: int,
        limit: int = 100,
        wait_time: float = 3,
    ) -> AsyncIterator[RawPost]:
        """Fetch posts from a channel starting after since_message_id."""
        ...

    @abstractmethod
    async def start(self) -> None:
        """Start client connection."""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Close client connection."""
        ...
