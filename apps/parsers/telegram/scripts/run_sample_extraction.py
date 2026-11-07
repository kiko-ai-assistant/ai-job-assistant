import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import yaml  # noqa: E402

from src.config import Settings  # noqa: E402
from src.transformer.llm_extractor import LlmExtractionResult, LlmExtractor  # noqa: E402

FIXTURES_PATH = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "mock_posts.yaml"


def load_fixtures() -> list[dict[str, Any]]:
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        return list(yaml.safe_load(f))


async def extract_with_retry(
    extractor: LlmExtractor, text: str, max_retries: int = 3
) -> LlmExtractionResult:
    for attempt in range(1, max_retries + 1):
        result = await extractor.extract(text)
        if result.is_vacancy or not result.reason or "429" not in result.reason:
            return result
        if attempt < max_retries:
            wait_time = attempt * 3.0
            print(
                f"   [Rate limited (429), waiting {wait_time:.1f}s before retry {attempt + 1}...]"
            )
            await asyncio.sleep(wait_time)
    return result


async def run_extraction(model: str | None = None) -> None:
    settings = Settings()
    active_model = model or settings.llm_model
    if not settings.llm_api_key:
        raise ValueError(
            "No LLM API key found. Set OPENROUTER_API_KEY or LLM_API_KEY in environment or .env"
        )

    print("=== Running Live LLM Extraction ===")
    print(f"Model: {active_model}")
    print(f"Base URL: {settings.llm_base_url}")
    print(f"Loaded fixtures: {FIXTURES_PATH.name}\n")

    cases = load_fixtures()

    async with LlmExtractor(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model=active_model,
        timeout=60.0,
    ) as extractor:
        for idx, case in enumerate(cases, start=1):
            case_id = case.get("id", f"case_{idx}")
            expected = case.get("expected_is_vacancy")
            text = case.get("text", "").strip()

            print(f"[{idx}/{len(cases)}] Case: '{case_id}' (Expected vacancy: {expected})")
            print("--- Input Text Snippet ---")
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            preview = "\n".join(lines[:3])
            print(f"{preview}\n...")

            print("--- Sending to LLM... ---")
            result = await extract_with_retry(extractor, text)
            print(f"-> is_vacancy: {result.is_vacancy}")
            if result.reason:
                print(f"-> reason: {result.reason}")
            if result.data:
                print("-> extracted data:")
                print(json.dumps(result.data, indent=2, ensure_ascii=False))

            print("-" * 60 + "\n")
            if idx < len(cases):
                await asyncio.sleep(2.0)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run LLM vacancy extraction on mock fixtures")
    parser.add_argument(
        "--model",
        type=str,
        default="openrouter/free",
        help="OpenRouter model identifier",
    )
    args = parser.parse_args()
    asyncio.run(run_extraction(model=args.model))


if __name__ == "__main__":
    main()
