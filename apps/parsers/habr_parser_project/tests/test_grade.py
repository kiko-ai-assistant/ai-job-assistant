import pytest

from habr_parser.grade import Grade


def test_values_match_the_openapi_grade_enum():
    assert [g.value for g in Grade] == ["INTERN", "JUNIOR", "MIDDLE", "SENIOR", "LEAD"]


@pytest.mark.parametrize(
    ("grade", "qid"),
    [
        (Grade.INTERN, 1),
        (Grade.JUNIOR, 3),
        (Grade.MIDDLE, 4),
        (Grade.SENIOR, 5),
        (Grade.LEAD, 6),
    ],
)
def test_each_grade_has_its_habr_qid(grade, qid):
    assert grade.qid == qid


def test_grade_is_a_plain_string_for_the_vacancy_model():
    assert Grade.MIDDLE == "MIDDLE"
