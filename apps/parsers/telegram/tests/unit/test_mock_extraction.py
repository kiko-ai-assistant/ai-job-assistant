import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import pytest
import yaml
from respx import MockRouter

from src.models.raw_post import RawPost
from src.transformer.llm_extractor import LlmExtractionResult, LlmExtractor
from src.transformer.post_parser import PostParser

FIXTURES_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "mock_posts.yaml"


def load_mock_posts() -> list[dict[str, Any]]:
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return list(data)


MOCK_CASES = load_mock_posts()

MOCK_LLM_RESPONSES: dict[str, dict[str, Any]] = {
    "senior_python": {
        "is_vacancy": True,
        "title": "Senior Python Developer",
        "company": "PayCore",
        "salary": {
            "text": "от 350 000 до 450 000 руб. на руки",
            "from": 350000,
            "to": 450000,
            "currency": "RUB",
        },
        "grade": "senior",
        "employment_types": ["remote", "office"],
        "location": {
            "text": "Москва, РФ",
            "country": "Russia",
            "city": "Moscow",
        },
        "description": (
            "PayCore is looking for a Senior Python Developer. "
            "Responsibilities: design high-load backend services using FastAPI and asyncio. "
            "Optimize PostgreSQL queries and Redis cache. "
            "Configure inter-service communication via Apache Kafka. "
            "Requirements: 4+ years of Python experience, deep knowledge of FastAPI, "
            "PostgreSQL, SQLAlchemy, Kafka, Docker, Kubernetes, CI/CD pipelines."
        ),
    },
    "middle_devops": {
        "is_vacancy": True,
        "title": "Middle DevOps Engineer",
        "company": "CloudScale Solutions",
        "salary": {
            "text": "$3,000 - $4,500 net",
            "from": 3000,
            "to": 4500,
            "currency": "USD",
        },
        "grade": "middle",
        "employment_types": ["hybrid", "remote"],
        "location": {
            "text": "Limassol, Cyprus",
            "country": "Cyprus",
            "city": "Limassol",
        },
        "description": (
            "CloudScale Solutions is hiring a Middle DevOps Engineer in Limassol, Cyprus. "
            "Maintain and improve multi-region Kubernetes clusters on EKS and GKE. "
            "Automate CI/CD pipelines using GitHub Actions and ArgoCD. "
            "Implement Infrastructure as Code with Terraform and Terragrunt. "
            "Setup Prometheus, Grafana, VictoriaMetrics, and OpenTelemetry. "
            "Requires 2+ years of DevOps experience, Linux, Docker, K8s, AWS, and B2+ English."
        ),
    },
    "junior_frontend": {
        "is_vacancy": True,
        "title": "Junior Frontend Developer",
        "company": "EdTech Nova",
        "salary": None,
        "grade": "junior",
        "employment_types": ["office"],
        "location": {
            "text": "Москва, м. Белорусская",
            "country": "Russia",
            "city": "Moscow",
        },
        "description": (
            "EdTech Nova is seeking a Junior Frontend Developer (React / TypeScript). "
            "Develop interactive UI components for an educational platform. "
            "Slice responsive layouts according to Figma designs. "
            "Integrate REST APIs and WebSocket connections. Write unit tests with Vitest. "
            "Requirements: JavaScript ES6+, TypeScript, React 18+, HTML5, CSS3, Tailwind, Git."
        ),
    },
    "course_promo": {
        "is_vacancy": False,
        "reason": "Promotional post for online education course",
    },
    "candidate_resume": {
        "is_vacancy": False,
        "reason": "Candidate resume / job seeker profile",
    },
    "meetup_announcement": {
        "is_vacancy": False,
        "reason": "Tech meetup announcement",
    },
}


@pytest.mark.parametrize("case", MOCK_CASES, ids=lambda c: str(c["id"]))
async def test_llm_extraction_result_with_mock_posts(
    respx_mock: MockRouter, case: dict[str, Any]
) -> None:
    case_id = case["id"]
    expected_is_vacancy = case["expected_is_vacancy"]
    llm_payload = MOCK_LLM_RESPONSES[case_id]

    base_url = "https://llm.example.com/v1"
    api_url = f"{base_url}/chat/completions"

    respx_mock.post(api_url).mock(
        return_value=httpx.Response(
            status_code=200,
            json={"choices": [{"message": {"content": json.dumps(llm_payload)}}]},
        )
    )

    async with LlmExtractor(
        api_key="mock-api-key",
        base_url=base_url,
        model="meta-llama/llama-3.3-70b-instruct:free",
    ) as extractor:
        result: LlmExtractionResult = await extractor.extract(case["text"])

    assert result.is_vacancy is expected_is_vacancy

    if expected_is_vacancy:
        assert result.reason is None
        assert result.data is not None
        assert result.data["title"] == llm_payload["title"]
        assert result.data["grade"] == llm_payload["grade"]
        assert result.data["employment_types"] == llm_payload["employment_types"]
        if llm_payload["salary"] is not None:
            assert result.data["salary"]["currency"] == llm_payload["salary"]["currency"]
    else:
        assert result.data is None
        assert result.reason is not None
        assert len(result.reason) > 0


@pytest.mark.parametrize(
    "case",
    [c for c in MOCK_CASES if c["expected_is_vacancy"]],
    ids=lambda c: str(c["id"]),
)
async def test_post_parser_transform_with_mock_posts(
    respx_mock: MockRouter, case: dict[str, Any]
) -> None:
    case_id = case["id"]
    llm_payload = MOCK_LLM_RESPONSES[case_id]

    base_url = "https://llm.example.com/v1"
    api_url = f"{base_url}/chat/completions"

    respx_mock.post(api_url).mock(
        return_value=httpx.Response(
            status_code=200,
            json={"choices": [{"message": {"content": json.dumps(llm_payload)}}]},
        )
    )

    async with LlmExtractor(
        api_key="mock-api-key",
        base_url=base_url,
        model="meta-llama/llama-3.3-70b-instruct:free",
    ) as extractor:
        parser = PostParser(llm_extractor=extractor)
        raw_post = RawPost(
            channel_username=case["channel_username"],
            message_id=case["message_id"],
            text=case["text"],
            date=datetime.now(UTC),
            url=f"https://t.me/{case['channel_username']}/{case['message_id']}",
        )
        vacancy = await parser.transform(raw_post)

    assert vacancy is not None
    assert vacancy.external_id == f"{case['channel_username']}_{case['message_id']}"
    assert vacancy.title == llm_payload["title"]
    assert vacancy.grade == llm_payload["grade"]
    assert len(vacancy.description) >= 300
