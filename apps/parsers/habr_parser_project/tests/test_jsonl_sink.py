import io
import json
from datetime import UTC, datetime

from habr_parser.sinks.jsonl_sink import JsonlSink
from parsers_base.models.vacancy import CreateVacancyRequest, SalaryDTO


def make_vacancy(external_id="1", **overrides):
    fields = {
        "external_id": external_id,
        "source": "habr",
        "title": "Python-разработчик",
        "grade": "MIDDLE",
        "employment_types": ["REMOTE"],
        "description": "d" * 300,
        "url": f"https://career.habr.com/vacancies/{external_id}",
        "published_at": datetime(2026, 11, 10, tzinfo=UTC),
        "parsed_at": datetime(2026, 11, 11, tzinfo=UTC),
    }
    return CreateVacancyRequest(**{**fields, **overrides})


async def test_writes_one_json_line_per_vacancy_and_counts_them_as_inserted():
    buffer = io.StringIO()
    sink = JsonlSink(buffer)

    response = await sink.send_batch([make_vacancy("1"), make_vacancy("2")])

    lines = buffer.getvalue().splitlines()
    assert [json.loads(line)["external_id"] for line in lines] == ["1", "2"]
    assert (response.inserted, response.ignored) == (2, 0)


async def test_lines_use_the_wire_format_of_the_backend_api():
    buffer = io.StringIO()
    vacancy = make_vacancy(
        salary=SalaryDTO(text="100 RUB", from_=100, to=200, currency="RUB")
    )

    await JsonlSink(buffer).send_batch([vacancy])

    payload = json.loads(buffer.getvalue())
    assert payload["salary"]["from"] == 100  # alias, exactly what BackendApiSink sends
    assert "from_" not in payload["salary"]
    assert payload["title"] == "Python-разработчик"  # not escaped to \uXXXX
    assert "Python-разработчик" in buffer.getvalue()


async def test_lines_can_be_read_back_as_vacancies():
    buffer = io.StringIO()
    vacancy = make_vacancy()

    await JsonlSink(buffer).send_batch([vacancy])

    assert CreateVacancyRequest.model_validate_json(buffer.getvalue()) == vacancy


async def test_empty_batch_writes_nothing():
    buffer = io.StringIO()

    response = await JsonlSink(buffer).send_batch([])

    assert buffer.getvalue() == ""
    assert (response.inserted, response.ignored) == (0, 0)


async def test_close_flushes_but_leaves_the_stream_open():
    buffer = io.StringIO()
    sink = JsonlSink(buffer)

    await sink.close()

    assert not buffer.closed
