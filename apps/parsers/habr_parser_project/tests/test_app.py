import io
import json

from habr_parser.app import run_app
from habr_parser.cli.cli import parse_cli
from habr_parser.sinks.jsonl_sink import JsonlSink
from .builders import SENTENCE, make_vacancy_html
from .fakes import FakeFetcher


async def test_vacancies_are_validated_and_sent_to_the_given_sink():
    options = parse_cli(["--grade", "junior", "--max-pages", "1"])
    buffer = io.StringIO()
    fetcher = FakeFetcher(
        lists={(3, 1): [1, 2, 3]},
        vacancies={"3": make_vacancy_html(description="<p>too short</p>")},
    )

    stats = await run_app(options, JsonlSink(buffer), fetcher)

    assert (stats.extracted, stats.valid, stats.invalid, stats.inserted) == (3, 2, 1, 2)
    ids = [json.loads(line)["external_id"] for line in buffer.getvalue().splitlines()]
    assert ids == ["1", "2"]


async def test_options_reach_the_parser():
    options = parse_cli(
        ["--query", "go", "--skill", "7", "--grade", "lead", "--max-pages", "1"]
    )
    fetcher = FakeFetcher()

    await run_app(options, JsonlSink(io.StringIO()), fetcher)

    [(_, params)] = fetcher.calls
    assert (params["q"], params["skill[]"], params["qid"]) == ("go", [7], 6)


async def test_batch_size_controls_how_often_the_sink_is_called():
    options = parse_cli(["--grade", "junior", "--max-pages", "1", "--batch-size", "2"])
    batches: list[int] = []

    class CountingSink(JsonlSink):
        async def send_batch(self, vacancies):
            batches.append(len(vacancies))
            return await super().send_batch(vacancies)

    fetcher = FakeFetcher(
        lists={(3, 1): [1, 2, 3]},
        vacancies={
            str(i): make_vacancy_html(description=f"<p>{SENTENCE * 6}</p>")
            for i in (1, 2, 3)
        },
    )

    await run_app(options, CountingSink(io.StringIO()), fetcher)

    assert batches == [2, 1]
