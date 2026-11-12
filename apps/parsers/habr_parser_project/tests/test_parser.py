from datetime import UTC, datetime

from habr_parser.filters import SearchFilters
from habr_parser.grade import Grade
from habr_parser.http_client import FetchError
from habr_parser.parser import HabrParser
from parsers_base.sink.base import BaseSink
from tests.builders import make_list_html, make_vacancy_html

PARSED_AT = datetime(2026, 11, 12, 12, 0, tzinfo=UTC)


class FakeFetcher:
    """Routes list pages by (qid, page) and vacancy pages by path."""

    def __init__(self, lists=None, vacancies=None):
        self.lists = lists or {}  # {(qid, page): [ids] | Exception}
        self.vacancies = vacancies or {}  # {id: html | Exception}
        self.calls: list[tuple[str, dict | None]] = []

    async def get_text(self, path, params=None):
        self.calls.append((path, params))
        if path == "/vacancies":
            result = self.lists.get((params["qid"], params["page"]), [])
            if isinstance(result, Exception):
                raise result
            return make_list_html(result)
        vacancy_id = path.rsplit("/", 1)[-1]
        result = self.vacancies.get(vacancy_id, make_vacancy_html(title=f"Dev {vacancy_id}"))
        if isinstance(result, Exception):
            raise result
        return result


class NullSink(BaseSink):
    async def send_batch(self, vacancies):
        raise AssertionError("parse() must not touch the sink")

    async def close(self):
        pass


def make_parser(fetcher):
    return HabrParser(NullSink(), fetcher, clock=lambda: PARSED_AT)


async def collect(parser, **kwargs):
    return [vacancy async for vacancy in parser.parse(**kwargs)]


async def test_all_pages_of_a_grade_are_walked_until_an_empty_page():
    fetcher = FakeFetcher(lists={(3, 1): [1, 2], (3, 2): [3], (3, 3): []})

    vacancies = await collect(make_parser(fetcher), grades=[Grade.JUNIOR])

    assert [v.external_id for v in vacancies] == ["1", "2", "3"]
    list_calls = [params["page"] for path, params in fetcher.calls if path == "/vacancies"]
    assert list_calls == [1, 2, 3]


async def test_max_pages_stops_the_walk():
    fetcher = FakeFetcher(lists={(3, 1): [1], (3, 2): [2], (3, 3): [3]})

    vacancies = await collect(make_parser(fetcher), grades=[Grade.JUNIOR], max_pages=2)

    assert [v.external_id for v in vacancies] == ["1", "2"]


async def test_vacancy_fields_come_from_the_page_the_query_and_the_clock():
    fetcher = FakeFetcher(lists={(4, 1): [1000123]})

    [vacancy] = await collect(make_parser(fetcher), grades=[Grade.MIDDLE])

    assert vacancy.external_id == "1000123"
    assert vacancy.source == "habr"
    assert vacancy.grade == "MIDDLE"
    assert vacancy.url == "https://career.habr.com/vacancies/1000123"
    assert vacancy.parsed_at == PARSED_AT
    assert vacancy.title == "Dev 1000123"


async def test_a_vacancy_listed_under_several_grades_is_fetched_once_with_the_first_grade():
    fetcher = FakeFetcher(lists={(3, 1): [1, 2], (4, 1): [2, 3]})

    vacancies = await collect(make_parser(fetcher), grades=[Grade.JUNIOR, Grade.MIDDLE])

    assert [(v.external_id, v.grade) for v in vacancies] == [
        ("1", "JUNIOR"),
        ("2", "JUNIOR"),
        ("3", "MIDDLE"),
    ]
    detail_calls = [path for path, _ in fetcher.calls if path != "/vacancies"]
    assert sorted(detail_calls) == ["/vacancies/1", "/vacancies/2", "/vacancies/3"]


async def test_all_grades_are_searched_by_default():
    fetcher = FakeFetcher()

    await collect(make_parser(fetcher))

    searched = [params["qid"] for path, params in fetcher.calls if path == "/vacancies"]
    assert searched == [grade.qid for grade in Grade]


async def test_filters_are_sent_with_every_list_request():
    fetcher = FakeFetcher()
    filters = SearchFilters(query="python", skill_ids=(7,))

    await collect(make_parser(fetcher), filters=filters, grades=[Grade.SENIOR])

    [(_, params)] = fetcher.calls
    assert params["q"] == "python"
    assert params["skill[]"] == [7]


async def test_broken_vacancies_are_skipped_and_the_rest_is_kept():
    fetcher = FakeFetcher(
        lists={(3, 1): [1, 2, 3]},
        vacancies={
            "1": FetchError("HTTP 404"),
            "2": "<html>captcha</html>",
        },
    )

    vacancies = await collect(make_parser(fetcher), grades=[Grade.JUNIOR])

    assert [v.external_id for v in vacancies] == ["3"]


async def test_a_failing_list_page_ends_only_that_grade():
    fetcher = FakeFetcher(lists={(3, 1): FetchError("HTTP 500"), (4, 1): [9]})

    vacancies = await collect(make_parser(fetcher), grades=[Grade.JUNIOR, Grade.MIDDLE])

    assert [(v.external_id, v.grade) for v in vacancies] == [("9", "MIDDLE")]
