import json
from typing import Any

import httpx
import pytest
from respx import MockRouter

from src.transformer import LlmExtractor

VACANCY_PAYLOAD = {
    "is_vacancy": True,
    "title": "Senior Python Developer",
    "company": "Tech Corp",
    "salary": {
        "text": "300 000 - 400 000 RUB",
        "from": 300000,
        "to": 400000,
        "currency": "RUB",
    },
    "grade": "senior",
    "employment_types": ["remote"],
    "location": {
        "text": "Moscow, Russia",
        "country": "Russia",
        "city": "Moscow",
    },
    "description": "We are looking for an experienced Python developer to join our team.",
}

TEST_CASES = [
    (
        "success_valid_vacancy",
        200,
        {"choices": [{"message": {"content": json.dumps(VACANCY_PAYLOAD)}}]},
        None,
        True,
        None,
        VACANCY_PAYLOAD,
    ),
    (
        "success_with_markdown_fence",
        200,
        {"choices": [{"message": {"content": f"```json\n{json.dumps(VACANCY_PAYLOAD)}\n```"}}]},
        None,
        True,
        None,
        VACANCY_PAYLOAD,
    ),
    (
        "rejected_not_a_vacancy_with_reason",
        200,
        {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({"is_vacancy": False, "reason": "Ad for courses"})
                    }
                }
            ]
        },
        None,
        False,
        "Ad for courses",
        None,
    ),
    (
        "rejected_not_a_vacancy_without_reason",
        200,
        {"choices": [{"message": {"content": json.dumps({"is_vacancy": False})}}]},
        None,
        False,
        "Not a vacancy",
        None,
    ),
    (
        "error_malformed_json_syntax",
        200,
        {"choices": [{"message": {"content": "{ invalid json "}}]},
        None,
        False,
        "Failed to parse LLM JSON response",
        None,
    ),
    (
        "error_non_json_response",
        200,
        {"choices": [{"message": {"content": "I am an AI and this is plain text."}}]},
        None,
        False,
        "Failed to parse LLM JSON response",
        None,
    ),
    (
        "error_non_dict_json",
        200,
        {"choices": [{"message": {"content": "[1, 2, 3]"}}]},
        None,
        False,
        "Failed to parse LLM JSON response",
        None,
    ),
    (
        "error_missing_choices_field",
        200,
        {"error": "something"},
        None,
        False,
        "Failed to parse LLM JSON response",
        None,
    ),
    (
        "error_http_500",
        500,
        {"error": "Internal Server Error"},
        None,
        False,
        "LLM request error:",
        None,
    ),
    (
        "error_network_timeout",
        None,
        None,
        httpx.ConnectTimeout("Connection timeout to OpenRouter"),
        False,
        "LLM request error:",
        None,
    ),
]


@pytest.mark.parametrize(
    (
        "case_name",
        "status_code",
        "json_body",
        "side_effect",
        "expected_is_vacancy",
        "expected_reason_substr",
        "expected_data",
    ),
    TEST_CASES,
)
async def test_llm_extractor_table_driven(
    respx_mock: MockRouter,
    case_name: str,
    status_code: int | None,
    json_body: dict[str, Any] | None,
    side_effect: Exception | None,
    expected_is_vacancy: bool,
    expected_reason_substr: str | None,
    expected_data: dict[str, Any] | None,
) -> None:
    api_url = "https://openrouter.ai/api/v1/chat/completions"
    if side_effect is not None:
        route = respx_mock.post(api_url).mock(side_effect=side_effect)
    else:
        assert status_code is not None
        route = respx_mock.post(api_url).mock(
            return_value=httpx.Response(status_code=status_code, json=json_body)
        )

    extractor = LlmExtractor(api_key="test-api-key")
    result = await extractor.extract("Looking for Senior Python Developer")
    await extractor.close()

    assert route.called
    assert result.is_vacancy == expected_is_vacancy
    if expected_reason_substr is not None:
        assert result.reason is not None
        assert expected_reason_substr in result.reason
    if expected_data is not None:
        assert result.data == expected_data
    else:
        assert result.data is None


async def test_llm_extractor_request_payload_and_headers(respx_mock: MockRouter) -> None:
    api_url = "https://openrouter.ai/api/v1/chat/completions"
    route = respx_mock.post(api_url).mock(
        return_value=httpx.Response(
            status_code=200,
            json={"choices": [{"message": {"content": json.dumps(VACANCY_PAYLOAD)}}]},
        )
    )

    async with LlmExtractor(
        api_key="secret-key",
        model="custom-model",
    ) as extractor:
        result = await extractor.extract("Sample post text")

    assert result.is_vacancy is True
    assert route.called
    sent_request = route.calls.last.request
    assert sent_request.headers["Authorization"] == "Bearer secret-key"
    assert sent_request.headers["Content-Type"] == "application/json"
    sent_json = json.loads(sent_request.content.decode("utf-8"))
    assert sent_json["model"] == "custom-model"
    assert sent_json["messages"][1]["content"] == "Sample post text"
    assert sent_json["response_format"] == {"type": "json_object"}


async def test_llm_extractor_external_client_lifecycle(respx_mock: MockRouter) -> None:
    api_url = "https://openrouter.ai/api/v1/chat/completions"
    respx_mock.post(api_url).mock(
        return_value=httpx.Response(
            status_code=200,
            json={"choices": [{"message": {"content": json.dumps(VACANCY_PAYLOAD)}}]},
        )
    )

    external_client = httpx.AsyncClient()
    extractor = LlmExtractor(api_key="test-key", client=external_client)
    result = await extractor.extract("Sample post text")
    assert result.is_vacancy is True

    await extractor.close()
    assert not external_client.is_closed
    await external_client.aclose()
    assert external_client.is_closed
