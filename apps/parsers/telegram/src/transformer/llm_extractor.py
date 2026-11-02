import json
import logging
from dataclasses import dataclass
from types import TracebackType
from typing import Any, Self

import httpx

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a strict IT vacancy extractor from Telegram channel posts. "
    "Your job is to extract vacancy data into JSON format strictly based on the text. "
    "Do not hallucinate or guess details.\n"
    "If the post is NOT a job vacancy (e.g. ad for courses, channel promo, meetup announcement, "
    "news, digest of links, resume/candidate profile), return:\n"
    '{"is_vacancy": false, "reason": "<short reason>"}\n\n'
    "If it is a job vacancy, return:\n"
    "{\n"
    '  "is_vacancy": true,\n'
    '  "title": "concise role title (3-100 characters)",\n'
    '  "company": "company name or null",\n'
    '  "salary": {\n'
    '    "text": "raw salary text or null",\n'
    '    "from": integer or null,\n'
    '    "to": integer or null,\n'
    '    "currency": "3-letter currency code (e.g. RUB, USD, EUR) or null"\n'
    "  } or null,\n"
    '  "grade": "intern" | "junior" | "middle" | "senior" | "lead",\n'
    '  "employment_types": ["remote" | "office" | "hybrid" | "contract"],\n'
    '  "location": {\n'
    '    "text": "location string or null",\n'
    '    "country": "country or null",\n'
    '    "city": "city or null"\n'
    "  } or null,\n"
    '  "description": "full job description including responsibilities, requirements, and '
    'conditions from the post"\n'
    "}"
)


@dataclass
class LlmExtractionResult:
    is_vacancy: bool
    reason: str | None = None
    data: dict[str, Any] | None = None


class LlmExtractor:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout: float = 30.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._client = client or httpx.AsyncClient(timeout=timeout)
        self._own_client = client is None

    async def close(self) -> None:
        if self._own_client:
            await self._client.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()

    async def extract(self, text: str) -> LlmExtractionResult:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = await self._client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
        except (httpx.HTTPError, Exception) as err:
            logger.warning("LLM request failed: %s", err)
            return LlmExtractionResult(is_vacancy=False, reason=f"LLM request error: {err}")

        try:
            body = response.json()
            content = body["choices"][0]["message"]["content"]
            if not isinstance(content, str):
                return LlmExtractionResult(
                    is_vacancy=False,
                    reason="Failed to parse LLM JSON response",
                )
            cleaned = content.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            data = json.loads(cleaned)
            if not isinstance(data, dict):
                return LlmExtractionResult(
                    is_vacancy=False,
                    reason="Failed to parse LLM JSON response",
                )
        except (KeyError, IndexError, TypeError, json.JSONDecodeError, AttributeError):
            return LlmExtractionResult(
                is_vacancy=False,
                reason="Failed to parse LLM JSON response",
            )

        if not data.get("is_vacancy", False):
            reason = data.get("reason") or "Not a vacancy"
            return LlmExtractionResult(is_vacancy=False, reason=str(reason))

        return LlmExtractionResult(is_vacancy=True, data=data)
