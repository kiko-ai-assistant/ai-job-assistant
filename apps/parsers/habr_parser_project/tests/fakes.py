"""Test doubles shared by several test modules."""

from parsers_base.sink.base import BaseSink
from .builders import make_list_html, make_vacancy_html


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
        result = self.vacancies.get(
            vacancy_id, make_vacancy_html(title=f"Dev {vacancy_id}")
        )
        if isinstance(result, Exception):
            raise result
        return result


class FakeHabrClient(FakeFetcher):
    """FakeFetcher that can stand in for HabrHttpClient (async context manager)."""

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return None


class NullSink(BaseSink):
    async def send_batch(self, vacancies):
        raise AssertionError("parse() must not touch the sink")

    async def close(self):
        pass
