import parsers_base as pb
from parsers_base import (
    BackendApiSink,
    BaseParser,
    BaseSink,
    BatchCreateVacanciesRequest,
    BatchCreateVacanciesResponse,
    BatchIngestVacanciesResponse,
    CreateVacancyRequest,
    LocationDTO,
    ParserStats,
    SalaryDTO,
    SinkError,
    VacancyValidator,
    ValidationResult,
)


def test_public_exports_all() -> None:
    expected_exports = {
        "CreateVacancyRequest",
        "SalaryDTO",
        "LocationDTO",
        "BatchCreateVacanciesRequest",
        "BatchCreateVacanciesResponse",
        "BatchIngestVacanciesResponse",
        "VacancyValidator",
        "ValidationResult",
        "BaseSink",
        "BackendApiSink",
        "SinkError",
        "BaseParser",
        "ParserStats",
    }
    assert set(pb.__all__) == expected_exports
    for export_name in expected_exports:
        assert hasattr(pb, export_name)
        assert getattr(pb, export_name) is not None


def test_public_exports_identities() -> None:
    assert pb.CreateVacancyRequest is CreateVacancyRequest
    assert pb.SalaryDTO is SalaryDTO
    assert pb.LocationDTO is LocationDTO
    assert pb.BatchCreateVacanciesRequest is BatchCreateVacanciesRequest
    assert pb.BatchCreateVacanciesResponse is BatchCreateVacanciesResponse
    assert pb.BatchIngestVacanciesResponse is BatchIngestVacanciesResponse
    assert pb.VacancyValidator is VacancyValidator
    assert pb.ValidationResult is ValidationResult
    assert pb.BaseSink is BaseSink
    assert pb.BackendApiSink is BackendApiSink
    assert pb.SinkError is SinkError
    assert pb.BaseParser is BaseParser
    assert pb.ParserStats is ParserStats
