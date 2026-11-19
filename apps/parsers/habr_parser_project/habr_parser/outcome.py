"""What a finished run means for the process that launched it (cron, Kubernetes, CI)."""

from __future__ import annotations

from enum import IntEnum

from parsers_base.parser.stats import ParserStats


class ExitCode(IntEnum):
    """1 (unhandled exception) and 2 (usage error) are reserved by Python and argparse."""

    OK = 0
    NOTHING_EXTRACTED = 3


def exit_code_for(stats: ParserStats) -> ExitCode:
    """Zero extracted vacancies means Habr changed, blocked us or the filters match nothing.

    Either way a scheduler must not see such a run as a success.
    """
    return ExitCode.NOTHING_EXTRACTED if stats.extracted == 0 else ExitCode.OK
