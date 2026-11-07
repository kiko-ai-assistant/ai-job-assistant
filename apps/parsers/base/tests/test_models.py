from datetime import UTC, datetime
from typing import Any

import pytest
from pydantic import ValidationError

from parsers_base.models.vacancy import (
    BatchCreateVacanciesRequest,
    BatchCreateVacanciesResponse,
    BatchIngestVacanciesResponse,
    CreateVacancyRequest,
    LocationDTO,
    SalaryDTO,
)


def test_salary_dto_defaults() -> None:
    salary = SalaryDTO()
    assert salary.text is None
    assert salary.from_ is None
    assert salary.to is None
    assert salary.currency is None
    assert salary.gross is None


def test_salary_dto_alias_from_and_serialization() -> None:
    salary_by_name = SalaryDTO.model_validate(
        {
            "from_": 5000,
            "to": 8000,
            "currency": "USD",
            "gross": True,
            "text": "$5k-$8k",
        }
    )
    assert salary_by_name.from_ == 5000
    assert salary_by_name.to == 8000
    assert salary_by_name.currency == "USD"
    assert salary_by_name.gross is True
    assert salary_by_name.text == "$5k-$8k"

    dumped_alias = salary_by_name.model_dump(by_alias=True)
    assert dumped_alias["from"] == 5000
    assert "from_" not in dumped_alias
    assert dumped_alias["gross"] is True

    dumped_json = salary_by_name.model_dump_json(by_alias=True)
    assert '"from":5000' in dumped_json or '"from": 5000' in dumped_json

    salary_by_alias = SalaryDTO.model_validate(
        {"from": 120000, "to": 150000, "currency": "RUB", "gross": False}
    )
    assert salary_by_alias.from_ == 120000
    assert salary_by_alias.to == 150000
    assert salary_by_alias.currency == "RUB"
    assert salary_by_alias.gross is False


def test_location_dto_defaults_and_serialization() -> None:
    loc_empty = LocationDTO()
    assert loc_empty.text is None
    assert loc_empty.country is None
    assert loc_empty.city is None

    loc = LocationDTO(text="Remote, Cyprus", country="Cyprus", city="Limassol")
    assert loc.text == "Remote, Cyprus"
    assert loc.country == "Cyprus"
    assert loc.city == "Limassol"

    dumped = loc.model_dump()
    assert dumped == {
        "text": "Remote, Cyprus",
        "country": "Cyprus",
        "city": "Limassol",
    }


def test_create_vacancy_request_valid_and_defaults() -> None:
    pub_time = datetime(2026, 11, 1, 10, 0, 0, tzinfo=UTC)
    parse_time = datetime(2026, 11, 1, 10, 5, 0, tzinfo=UTC)

    req = CreateVacancyRequest(
        external_id="vac_123",
        source="telegram",
        title="Senior Python Engineer",
        grade="senior",
        description="Write high performance python code in monorepo environment.",
        url="https://t.me/jobs/123",
        published_at=pub_time,
        parsed_at=parse_time,
    )
    assert req.external_id == "vac_123"
    assert req.source == "telegram"
    assert req.title == "Senior Python Engineer"
    assert req.company is None
    assert req.salary is None
    assert req.grade == "senior"
    assert req.employment_types == []
    assert req.location is None
    assert req.raw_text is None
    assert req.url == "https://t.me/jobs/123"
    assert req.published_at == pub_time
    assert req.parsed_at == parse_time


def test_create_vacancy_request_with_nested_objects() -> None:
    pub_time = datetime(2026, 11, 1, 10, 0, 0, tzinfo=UTC)
    parse_time = datetime(2026, 11, 1, 10, 5, 0, tzinfo=UTC)

    payload: dict[str, Any] = {
        "external_id": "vac_456",
        "source": "hh",
        "title": "Go Lead",
        "company": "Tech Corp",
        "salary": {"from": 300000, "to": 450000, "currency": "RUB", "gross": True},
        "grade": "lead",
        "employment_types": ["remote", "contract"],
        "location": {"city": "Moscow", "country": "Russia"},
        "description": "Leading Go backend infrastructure team.",
        "url": "https://hh.ru/vacancy/456",
        "published_at": pub_time,
        "parsed_at": parse_time,
        "raw_text": "Original raw text content",
    }

    req = CreateVacancyRequest.model_validate(payload)
    assert req.company == "Tech Corp"
    assert req.raw_text == "Original raw text content"
    assert req.employment_types == ["remote", "contract"]
    assert req.salary is not None
    assert req.salary.from_ == 300000
    assert req.salary.gross is True
    assert req.location is not None
    assert req.location.city == "Moscow"

    dumped = req.model_dump(by_alias=True)
    assert dumped["salary"]["from"] == 300000
    assert "from_" not in dumped["salary"]


@pytest.mark.parametrize(
    "missing_field",
    [
        "external_id",
        "source",
        "title",
        "grade",
        "description",
        "url",
        "published_at",
        "parsed_at",
    ],
)
def test_create_vacancy_request_required_fields(missing_field: str) -> None:
    base_data: dict[str, Any] = {
        "external_id": "ext_1",
        "source": "telegram",
        "title": "Engineer",
        "grade": "middle",
        "description": "Short description for test",
        "url": "https://example.com/1",
        "published_at": datetime.now(UTC),
        "parsed_at": datetime.now(UTC),
    }
    base_data.pop(missing_field)
    with pytest.raises(ValidationError):
        CreateVacancyRequest.model_validate(base_data)


def test_batch_create_vacancies_request_defaults_and_aliases() -> None:
    empty_req = BatchCreateVacanciesRequest()
    assert empty_req.vacancies == []

    pub_time = datetime(2026, 11, 1, 12, 0, 0, tzinfo=UTC)
    vac = CreateVacancyRequest(
        external_id="1",
        source="telegram",
        title="Dev",
        grade="junior",
        description="Desc",
        url="https://example.com",
        published_at=pub_time,
        parsed_at=pub_time,
    )

    req_by_vacancies = BatchCreateVacanciesRequest(vacancies=[vac])
    assert len(req_by_vacancies.vacancies) == 1
    assert req_by_vacancies.vacancies[0].external_id == "1"

    dumped_vac = vac.model_dump(by_alias=True)
    req_by_items = BatchCreateVacanciesRequest.model_validate({"items": [dumped_vac]})
    assert len(req_by_items.vacancies) == 1
    assert req_by_items.vacancies[0].external_id == "1"

    req_by_items_kwarg = BatchCreateVacanciesRequest.model_validate({"items": [vac]})
    assert len(req_by_items_kwarg.vacancies) == 1
    assert req_by_items_kwarg.vacancies[0].external_id == "1"


def test_batch_create_vacancies_response_and_alias() -> None:
    resp = BatchCreateVacanciesResponse(inserted=10, ignored=2)
    assert resp.inserted == 10
    assert resp.ignored == 2

    assert BatchIngestVacanciesResponse is BatchCreateVacanciesResponse
    ingest_resp = BatchIngestVacanciesResponse(inserted=5, ignored=0)
    assert isinstance(ingest_resp, BatchCreateVacanciesResponse)
    assert ingest_resp.inserted == 5
    assert ingest_resp.ignored == 0

    with pytest.raises(ValidationError):
        BatchCreateVacanciesResponse.model_validate({"inserted": 1})
