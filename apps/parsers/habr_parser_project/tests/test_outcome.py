import pytest

from habr_parser.outcome import ExitCode, exit_code_for
from parsers_base.parser.stats import ParserStats


def test_exit_codes_do_not_collide_with_python_or_argparse_codes():
    assert {code.value for code in ExitCode}.isdisjoint({1, 2})


def test_nothing_extracted_is_a_failure():
    assert exit_code_for(ParserStats(extracted=0)) is ExitCode.NOTHING_EXTRACTED


@pytest.mark.parametrize(
    "stats",
    [
        ParserStats(extracted=5, valid=5, inserted=5),
        ParserStats(extracted=5, valid=3, invalid=2, inserted=1, ignored=2),
        ParserStats(extracted=2, invalid=2),  # parsed, but everything was filtered out
    ],
)
def test_anything_extracted_counts_as_success(stats):
    assert exit_code_for(stats) is ExitCode.OK
