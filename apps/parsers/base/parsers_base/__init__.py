from parsers_base.models.vacancy import (
    BatchCreateVacanciesRequest,
    BatchCreateVacanciesResponse,
    BatchIngestVacanciesResponse,
    CreateVacancyRequest,
    LocationDTO,
    SalaryDTO,
)
from parsers_base.parser.base import BaseParser
from parsers_base.parser.stats import ParserStats
from parsers_base.sink.backend_api import BackendApiSink
from parsers_base.sink.base import BaseSink, SinkError
from parsers_base.validation.validator import VacancyValidator, ValidationResult

__all__ = [
    "BackendApiSink",
    "BaseParser",
    "BaseSink",
    "BatchCreateVacanciesRequest",
    "BatchCreateVacanciesResponse",
    "BatchIngestVacanciesResponse",
    "CreateVacancyRequest",
    "LocationDTO",
    "ParserStats",
    "SalaryDTO",
    "SinkError",
    "VacancyValidator",
    "ValidationResult",
]
