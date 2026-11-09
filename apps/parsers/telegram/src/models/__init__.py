from .channel import ChannelConfig, ChannelsConfigFile
from .raw_post import RawPost
from .vacancy import (
    BatchCreateVacanciesRequest,
    BatchCreateVacanciesResponse,
    BatchIngestVacanciesResponse,
    CreateVacancyRequest,
    LocationDTO,
    SalaryDTO,
)

__all__ = [
    "BatchCreateVacanciesRequest",
    "BatchCreateVacanciesResponse",
    "BatchIngestVacanciesResponse",
    "ChannelConfig",
    "ChannelsConfigFile",
    "CreateVacancyRequest",
    "LocationDTO",
    "RawPost",
    "SalaryDTO",
]
