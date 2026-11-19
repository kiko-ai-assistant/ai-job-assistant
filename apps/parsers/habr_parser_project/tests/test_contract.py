"""The parser's wire format against contracts/openapi.yaml (the backend's contract)."""

import json
from datetime import UTC, datetime
from urllib.parse import urlparse

import httpx
import pytest

from habr_parser.domain.employment import (
    EmploymentType,
)
from habr_parser.domain.grade import Grade
from habr_parser.mapping.mapper import (
    to_create_request,
)
from habr_parser.site.vacancy_page import (
    parse_vacancy_page,
)
from parsers_base.sink.backend_api import BackendApiSink
from parsers_base.validation import rules
from tests.builders import make_vacancy_html
from tests.contract_support import load_spec, request_body_schema, schema_errors

BATCH_PATH = "/vacancies/batch"


@pytest.fixture(scope="module")
def spec():
    return load_spec()


def make_vacancy(**overrides):
    page = parse_vacancy_page(make_vacancy_html(**overrides))
    return to_create_request(
        page,
        vacancy_id="1000123",
        grade=Grade.MIDDLE,
        url="https://career.habr.com/vacancies/1000123",
        parsed_at=datetime.now(UTC),
    )


async def send_through_real_sink(vacancies) -> httpx.Request:
    """Run vacancies through the real BackendApiSink and capture what goes on the wire."""
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json={"inserted": len(vacancies), "ignored": 0})

    sink = BackendApiSink("http://backend/api/v1", "secret-key")
    headers = dict(sink.client.headers)
    await sink.client.aclose()
    sink.client = httpx.AsyncClient(
        base_url=sink.backend_url,
        headers=headers,
        transport=httpx.MockTransport(handler),
    )
    await sink.send_batch(vacancies)
    await sink.close()
    return captured[0]


async def test_sink_calls_the_documented_endpoint_with_the_documented_credentials(spec):
    request = await send_through_real_sink([make_vacancy()])

    operation = spec["paths"][BATCH_PATH]["post"]
    server_prefix = urlparse(spec["servers"][0]["url"]).path
    assert request.method == "POST"
    assert request.url.path == server_prefix + BATCH_PATH
    assert operation["security"] == [{"ParserApiKey": []}]
    scheme = spec["components"]["securitySchemes"]["ParserApiKey"]
    assert scheme["in"] == "header"
    assert request.headers[scheme["name"]] == "secret-key"


async def test_a_fully_populated_vacancy_matches_the_batch_request_schema(spec):
    request = await send_through_real_sink([make_vacancy()])

    schema = request_body_schema(spec, BATCH_PATH, "post")
    assert schema_errors(schema, json.loads(request.content)) == []


# BackendApiSink serialises absent values as JSON null, but the contract declares `salary`,
# `location` and their members as required and NOT nullable. Until the backend contract or the
# sink changes, every scenario with a missing optional block is a known deviation. strict=True
# makes the suite fail as soon as the deviation disappears, so the marker cannot rot.
KNOWN_NULL_DEVIATION = pytest.mark.xfail(
    strict=True, reason="sink sends null for a field the contract declares non-nullable"
)

SPARSE_SCENARIOS = [
    pytest.param(
        {"hiringOrganization": None}, id="no company"
    ),  # company is nullable: OK
    pytest.param({"baseSalary": None}, marks=KNOWN_NULL_DEVIATION, id="no salary"),
    pytest.param({"jobLocation": None}, marks=KNOWN_NULL_DEVIATION, id="no location"),
    pytest.param(
        {"baseSalary": {"currency": "RUR", "value": {"minValue": 100000}}},
        marks=KNOWN_NULL_DEVIATION,
        id="salary with a lower bound only",
    ),
    pytest.param(
        {"jobLocation": {"address": {"addressCountry": "Беларусь"}}},
        marks=KNOWN_NULL_DEVIATION,
        id="location with a country only",
    ),
]


@pytest.mark.parametrize("overrides", SPARSE_SCENARIOS)
async def test_vacancies_with_missing_optional_data_match_the_request_schema(
    spec, overrides
):
    request = await send_through_real_sink([make_vacancy(**overrides)])

    schema = request_body_schema(spec, BATCH_PATH, "post")
    assert schema_errors(schema, json.loads(request.content)) == []


def test_our_enums_equal_the_contract_enums(spec):
    schemas = spec["components"]["schemas"]

    assert [g.value for g in Grade] == schemas["Grade"]["enum"]
    assert [t.value for t in EmploymentType] == schemas["EmploymentType"]["enum"]


@pytest.mark.parametrize(
    ("field", "min_len", "max_len"),
    [
        ("title", rules.MIN_TITLE_LEN, rules.MAX_TITLE_LEN),
        ("company", rules.MIN_COMPANY_LEN, rules.MAX_COMPANY_LEN),
        ("description", rules.MIN_DESCRIPTION_LEN, rules.MAX_DESCRIPTION_LEN),
        ("url", rules.MIN_URL_LEN, rules.MAX_URL_LEN),
    ],
)
def test_validator_length_rules_equal_the_contract_limits(
    spec, field, min_len, max_len
):
    properties = spec["components"]["schemas"]["CreateVacancyRequest"]["properties"]

    assert (properties[field]["minLength"], properties[field]["maxLength"]) == (
        min_len,
        max_len,
    )


def test_the_contract_helper_really_detects_violations(spec):
    """Guards the guard: a bad payload must produce errors."""
    schema = request_body_schema(spec, BATCH_PATH, "post")
    broken = {"vacancies": [{"external_id": "1", "grade": "WIZARD"}]}

    errors = schema_errors(schema, broken)

    assert any("WIZARD" in e for e in errors)
    assert any("required" in e for e in errors)
