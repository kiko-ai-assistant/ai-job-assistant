from dataclasses import FrozenInstanceError

import pytest

from habr_parser.filters import SearchFilters
from habr_parser.grade import Grade


def test_default_filters_only_send_paging_and_grade():
    params = SearchFilters().to_params(Grade.JUNIOR, page=1)

    assert params == {"type": "all", "page": 1, "qid": Grade.JUNIOR.qid}


def test_every_filter_is_mapped_to_its_habr_query_parameter():
    filters = SearchFilters(
        query="python",
        min_salary=150_000,
        skill_ids=(1, 2),
        location_ids=(678,),
    )

    assert filters.to_params(Grade.SENIOR, page=3) == {
        "type": "all",
        "page": 3,
        "qid": Grade.SENIOR.qid,
        "q": "python",
        "salary": 150_000,
        "skill[]": [1, 2],
        "location_id[]": [678],
    }


def test_filters_are_immutable():
    with pytest.raises(FrozenInstanceError):
        SearchFilters().query = "go"  # type: ignore[misc]
