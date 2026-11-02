from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from src.extractor import BaseExtractor, TelethonChannelExtractor, TelethonWrapper
from src.models.raw_post import RawPost
from src.transformer import (
    BaseTransformer,
    HeuristicExtractor,
    LlmExtractionResult,
    LlmExtractor,
    PostParser,
)


@pytest.mark.asyncio
async def test_post_parser_extracts_vacancy() -> None:
    now = datetime.now(UTC)
    raw_post = RawPost(
        channel_username="forpython",
        message_id=101,
        text="Senior Python Developer в FinFlow. Зарплата 300 000 руб. Удаленно.",
        date=now - timedelta(hours=2),
        url="https://t.me/forpython/101",
    )

    desc = (
        "We are seeking an experienced Senior Python Developer to build backend "
        "services and high load systems." * 4
    )
    mock_llm = AsyncMock(spec=LlmExtractor)
    mock_llm.extract.return_value = LlmExtractionResult(
        is_vacancy=True,
        data={
            "title": "Senior Python Developer",
            "company": "FinFlow",
            "salary": {
                "text": "300 000 руб.",
                "from": 300000,
                "to": 400000,
                "currency": "RUB",
            },
            "grade": "senior",
            "employment_types": ["remote"],
            "location": {
                "text": "Moscow",
                "country": "Russia",
                "city": "Moscow",
            },
            "description": desc,
        },
    )

    parser = PostParser(llm_extractor=mock_llm)
    result = await parser.transform(raw_post)

    assert result is not None
    assert result.external_id == "forpython_101"
    assert result.source == "telegram"
    assert result.title == "Senior Python Developer"
    assert result.company == "FinFlow"
    assert result.salary is not None
    assert result.salary.from_ == 300000
    assert result.salary.to == 400000
    assert result.salary.currency == "RUB"
    assert result.grade == "senior"
    assert result.employment_types == ["remote"]
    assert result.location is not None
    assert result.location.city == "Moscow"
    assert result.url == "https://t.me/forpython/101"
    assert result.published_at == raw_post.date


scenario_desc = (
    "We are seeking an experienced Senior Python Developer to join our team and build services."
    * 5
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("extract_result", "expected_valid"),
    [
        (
            LlmExtractionResult(
                is_vacancy=True,
                data={
                    "title": "Senior Python Developer",
                    "company": "FinFlow",
                    "salary": {
                        "text": "300 000 руб.",
                        "from": 300000,
                        "to": 400000,
                        "currency": "RUB",
                    },
                    "grade": "senior",
                    "employment_types": ["remote"],
                    "location": {"text": "Moscow", "country": "Russia", "city": "Moscow"},
                    "description": scenario_desc,
                },
            ),
            True,
        ),
        (
            LlmExtractionResult(
                is_vacancy=False,
                reason="Promo post",
                data=None,
            ),
            False,
        ),
        (
            LlmExtractionResult(
                is_vacancy=True,
                data={
                    "title": "Senior Python Developer",
                    "company": "FinFlow",
                    "grade": "unknown_grade",
                    "description": "Short",
                },
            ),
            False,
        ),
    ],
)
async def test_post_parser_scenarios(
    extract_result: LlmExtractionResult,
    expected_valid: bool,
) -> None:
    now = datetime.now(UTC)
    raw_post = RawPost(
        channel_username="forpython",
        message_id=102,
        text="Sample post text",
        date=now - timedelta(hours=1),
        url="https://t.me/forpython/102",
    )

    mock_llm = AsyncMock(spec=LlmExtractor)
    mock_llm.extract.return_value = extract_result

    parser = PostParser(llm_extractor=mock_llm)
    result = await parser.transform(raw_post)

    if expected_valid:
        assert result is not None
        assert result.external_id == "forpython_102"
    else:
        assert result is None


@pytest.mark.asyncio
async def test_post_parser_handles_extractor_exception() -> None:
    now = datetime.now(UTC)
    raw_post = RawPost(
        channel_username="forpython",
        message_id=103,
        text="Sample post text",
        date=now - timedelta(hours=1),
        url="https://t.me/forpython/103",
    )

    mock_llm = AsyncMock(spec=LlmExtractor)
    mock_llm.extract.side_effect = RuntimeError("LLM connection failed")

    parser = PostParser(llm_extractor=mock_llm)
    result = await parser.transform(raw_post)

    assert result is None


@pytest.mark.asyncio
async def test_post_parser_custom_source() -> None:
    now = datetime.now(UTC)
    raw_post = RawPost(
        channel_username="forpython",
        message_id=104,
        text="Senior Python Developer в FinFlow.",
        date=now - timedelta(hours=1),
        url="https://t.me/forpython/104",
    )

    mock_llm = AsyncMock(spec=LlmExtractor)
    mock_llm.extract.return_value = LlmExtractionResult(
        is_vacancy=True,
        data={
            "title": "Senior Python Developer",
            "company": "FinFlow",
            "grade": "senior",
            "employment_types": ["remote"],
            "description": scenario_desc,
        },
    )

    parser = PostParser(llm_extractor=mock_llm, default_source="telegram")
    result = await parser.transform(raw_post)

    assert result is not None
    assert result.source == "telegram"


@pytest.mark.asyncio
async def test_post_parser_skips_outdated_posts_before_llm() -> None:
    now = datetime.now(UTC)
    raw_post = RawPost(
        channel_username="forpython",
        message_id=105,
        text="Senior Python Developer в FinFlow.",
        date=now - timedelta(days=8),
        url="https://t.me/forpython/105",
    )

    mock_llm = AsyncMock(spec=LlmExtractor)
    parser = PostParser(llm_extractor=mock_llm)
    result = await parser.transform(raw_post)

    assert result is None
    mock_llm.extract.assert_not_called()


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
