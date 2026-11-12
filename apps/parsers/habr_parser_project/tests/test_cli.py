import pytest

from habr_parser.cli import parse_cli
from habr_parser.filters import SearchFilters
from habr_parser.grade import Grade


def test_defaults_search_all_grades_without_filters():
    options = parse_cli([])

    assert options.filters == SearchFilters()
    assert options.grades == tuple(Grade)
    assert options.max_pages == 5
    assert options.batch_size == 50


def test_arguments_are_mapped_to_options():
    options = parse_cli(
        [
            "--query",
            "python",
            "--min-salary",
            "150000",
            "--skill",
            "1",
            "--skill",
            "2",
            "--location",
            "678",
            "--grade",
            "junior",
            "--grade",
            "middle",
            "--max-pages",
            "2",
            "--batch-size",
            "10",
            "--delay",
            "2.5",
        ]
    )

    assert options.filters == SearchFilters("python", 150_000, (1, 2), (678,))
    assert options.grades == (Grade.JUNIOR, Grade.MIDDLE)
    assert options.max_pages == 2
    assert options.batch_size == 10
    assert options.http.request_delay == 2.5


def test_unknown_grade_is_rejected():
    with pytest.raises(SystemExit):
        parse_cli(["--grade", "wizard"])
