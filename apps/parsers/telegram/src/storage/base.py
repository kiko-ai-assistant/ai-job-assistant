from abc import ABC, abstractmethod


class BaseStateStore(ABC):
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize database schema or connections."""
        ...

    @abstractmethod
    async def get_checkpoint(self, channel: str) -> int:
        """Return the highest processed message_id for the channel, or 0 if none."""
        ...

    @abstractmethod
    async def commit_checkpoint(self, channel: str, message_id: int) -> None:
        """Persist new highest processed message_id for the channel."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Cleanly close storage resources."""
        ...
