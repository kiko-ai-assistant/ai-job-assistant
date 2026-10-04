from .channel import ChannelConfig, ChannelsConfigFile
from .raw_post import RawPost
from .vacancy import (
    BatchCreateVacanciesRequest,
    BatchIngestVacanciesResponse,
    CreateVacancyRequest,
)

__all__ = [
    "RawPost",
    "CreateVacancyRequest",
    "BatchCreateVacanciesRequest",
    "BatchIngestVacanciesResponse",
    "ChannelConfig",
    "ChannelsConfigFile",
]
