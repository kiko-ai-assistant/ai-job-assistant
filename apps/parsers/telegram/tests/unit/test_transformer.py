import json
from pathlib import Path

from src.extractor import BaseExtractor, TelethonChannelExtractor, TelethonWrapper
from src.models.raw_post import RawPost
from src.transformer import BaseTransformer, HeuristicExtractor, PostParser


def test_post_parser_extracts_vacancy() -> None:
    fixtures_path = Path(__file__).parent.parent / "fixtures" / "sample_posts.json"
    with open(fixtures_path, encoding="utf-8") as f:
        samples = json.load(f)

    parser = PostParser()

    # Post 1 is a vacancy
    raw_vacancy = RawPost.model_validate(samples[0])
    result = parser.transform(raw_vacancy)

    assert result is not None
    assert result.external_id == "forpython_101"
    assert "Python" in result.title
    assert result.salary_text is not None
    assert "300 000" in result.salary_text
    assert result.url == "https://t.me/forpython/101"

    # Post 2 is an ad / non-vacancy
    raw_ad = RawPost.model_validate(samples[1])
    ad_result = parser.transform(raw_ad)
    assert ad_result is None


def test_heuristic_extractor_edge_cases() -> None:
    assert not HeuristicExtractor.is_vacancy("Short text")
    assert not HeuristicExtractor.is_vacancy(
        "Реклама сервиса подписывайтесь на нас прямо сейчас без вакансий"
    )
    assert HeuristicExtractor.extract_title("") == "Вакансия"
    assert HeuristicExtractor.extract_salary("Без указания вилки") is None
    assert HeuristicExtractor.extract_company("Без указания компании") is None


def test_extractor_and_transformer_interfaces() -> None:
    assert issubclass(TelethonChannelExtractor, BaseExtractor)
    assert issubclass(PostParser, BaseTransformer)
    assert TelethonWrapper is not None
