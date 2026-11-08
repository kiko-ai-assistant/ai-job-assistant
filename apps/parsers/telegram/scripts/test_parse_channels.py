import argparse
import asyncio
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from telethon import TelegramClient, errors

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import Settings
from src.models.raw_post import RawPost
from src.models.vacancy import BatchCreateVacanciesRequest, CreateVacancyRequest
from src.transformer.llm_extractor import LlmExtractionResult, LlmExtractor
from src.transformer.post_parser import PostParser
from src.validation.rules import VALID_EMPLOYMENT_TYPES, VALID_GRADES
from src.validation.validator import VacancyValidator

DEFAULT_CHANNELS = [
    "https://t.me/godevjob",
    "https://t.me/backend_frontend_jobs",
    "https://t.me/GolangJobsit",
]

AUTH_STATE_FILE = PROJECT_ROOT / "data" / "sessions" / ".auth_pending.json"


def normalize_channel_name(url_or_name: str) -> str:
    cleaned = url_or_name.strip()
    if "t.me/" in cleaned:
        cleaned = cleaned.split("t.me/")[-1]
    cleaned = cleaned.strip("/@")
    return cleaned


class ResilientLlmExtractor(LlmExtractor):
    async def extract(self, text: str, max_retries: int = 3) -> LlmExtractionResult:
        for attempt in range(1, max_retries + 1):
            result = await super().extract(text)
            if result.is_vacancy or not result.reason or "429" not in result.reason:
                return result
            if attempt < max_retries:
                wait_time = attempt * 3.5
                print(f"      [LLM Rate-limited (429), waiting {wait_time:.1f}s before retry {attempt + 1}...]")
                await asyncio.sleep(wait_time)
        return result


def assert_vacancy_contract(vacancy: CreateVacancyRequest) -> None:
    assert isinstance(vacancy, CreateVacancyRequest), "Result must be CreateVacancyRequest"
    assert vacancy.external_id and len(vacancy.external_id.strip()) > 0, "external_id cannot be empty"
    assert vacancy.source == "telegram", f"source must be 'telegram', got '{vacancy.source}'"
    assert 3 <= len(vacancy.title.strip()) <= 100, f"title length ({len(vacancy.title)}) out of bounds [3, 100]"
    assert vacancy.grade in VALID_GRADES, f"invalid grade '{vacancy.grade}', must be one of {sorted(VALID_GRADES)}"
    assert len(vacancy.employment_types) > 0, "employment_types cannot be empty"
    for et in vacancy.employment_types:
        assert et in VALID_EMPLOYMENT_TYPES, f"invalid employment_type '{et}'"
    assert 10 <= len(vacancy.url) <= 1024, f"url length ({len(vacancy.url)}) out of bounds [10, 1024]"
    assert vacancy.url.startswith("https://t.me/"), f"url must start with https://t.me/, got '{vacancy.url}'"
    assert len(vacancy.description.strip()) > 0, "description cannot be empty"
    assert vacancy.published_at is not None, "published_at cannot be None"
    assert vacancy.parsed_at is not None, "parsed_at cannot be None"

    if vacancy.company:
        assert 2 <= len(vacancy.company.strip()) <= 100, f"company length ({len(vacancy.company)}) out of bounds"

    if vacancy.salary:
        if vacancy.salary.from_ is not None and vacancy.salary.to is not None:
            assert vacancy.salary.from_ <= vacancy.salary.to, "salary from must be <= to"
        if vacancy.salary.from_ is not None or vacancy.salary.to is not None:
            assert vacancy.salary.currency is not None and len(vacancy.salary.currency.strip()) == 3, (
                "currency must be 3 characters when bounds are set"
            )

    if vacancy.location:
        if vacancy.location.city:
            assert vacancy.location.country, "city specified without country"


async def handle_send_code(client: TelegramClient, phone: str) -> None:
    await client.connect()
    try:
        if await client.is_user_authorized():
            me = await client.get_me()
            username = getattr(me, "username", None) or getattr(me, "first_name", "User")
            print(f"[AUTH] Session is already authorized as: {username}")
            return

        print(f"[AUTH] Requesting verification code for {phone}...")
        sent_code = await client.send_code_request(phone)
        AUTH_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        AUTH_STATE_FILE.write_text(
            json.dumps({"phone": phone, "phone_code_hash": sent_code.phone_code_hash}),
            encoding="utf-8",
        )
        print(f"[AUTH] Code successfully requested! Telegram sent a code to {phone}.")
        print("[AUTH] Please pass the received code using: --verify-code <CODE>")
    finally:
        await client.disconnect()


async def handle_verify_code(client: TelegramClient, code: str, password: str | None = None) -> None:
    if not AUTH_STATE_FILE.exists():
        raise RuntimeError("No pending auth request found. Please run with --send-code first.")
    auth_data = json.loads(AUTH_STATE_FILE.read_text(encoding="utf-8"))
    phone = auth_data["phone"]
    phone_code_hash = auth_data["phone_code_hash"]

    await client.connect()
    try:
        try:
            await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
        except errors.SessionPasswordNeededError:
            if not password:
                raise RuntimeError("Two-step verification (2FA) is active. Pass --password <2FA_PASSWORD>")
            await client.sign_in(password=password)

        me = await client.get_me()
        username = getattr(me, "username", None) or getattr(me, "first_name", "User")
        print(f"[AUTH] Successfully authorized as: {username} (ID: {me.id})")
        if AUTH_STATE_FILE.exists():
            AUTH_STATE_FILE.unlink()
    finally:
        await client.disconnect()


async def handle_status(client: TelegramClient) -> None:
    await client.connect()
    try:
        is_auth = await client.is_user_authorized()
        if is_auth:
            me = await client.get_me()
            username = getattr(me, "username", None) or getattr(me, "first_name", "User")
            print(f"[AUTH STATUS] Authorized: Yes | User: {username} (ID: {me.id})")
        else:
            print("[AUTH STATUS] Authorized: No")
    finally:
        await client.disconnect()


async def run_parsing(
    channels: list[str],
    limit_per_channel: int,
    output_path: Path,
) -> None:
    settings = Settings()
    session_file = settings.resolved_session_path

    if not settings.tg_api_id or not settings.tg_api_hash:
        raise ValueError("TG_API_ID and TG_API_HASH must be configured in environment or .env")

    client = TelegramClient(str(session_file), settings.tg_api_id, settings.tg_api_hash)
    await client.connect()
    if not await client.is_user_authorized():
        await client.disconnect()
        raise RuntimeError(
            f"Telegram client session is not authorized at {session_file}. "
            f"Run with --send-code or --login first."
        )

    llm_key = settings.llm_api_key
    if not llm_key:
        await client.disconnect()
        raise ValueError("LLM_API_KEY / OPENROUTER_API_KEY is not set.")

    validator = VacancyValidator()
    llm_extractor = ResilientLlmExtractor(
        api_key=llm_key,
        base_url=settings.llm_base_url,
        model=settings.llm_model,
        timeout=settings.llm_timeout,
    )
    post_parser = PostParser(
        llm_extractor=llm_extractor,
        validator=validator,
        default_source="telegram",
        ignore_date_window=True,
    )

    all_extracted_vacancies: list[CreateVacancyRequest] = []
    stats: dict[str, dict[str, Any]] = {}

    print(f"\n{'='*70}")
    print(f"Starting Telegram parsing run:")
    print(f"Channels: {channels}")
    print(f"Limit per channel: {limit_per_channel}")
    print(f"LLM Model: {settings.llm_model}")
    print(f"{'='*70}\n")

    try:
        for channel_input in channels:
            channel_name = normalize_channel_name(channel_input)
            print(f"--> Processing channel @{channel_name}...")
            channel_stats = {
                "fetched": 0,
                "vacancies": 0,
                "non_vacancies": 0,
                "validation_errors": 0,
            }
            stats[channel_name] = channel_stats

            try:
                entity = await client.get_entity(channel_name)
            except Exception as err:
                print(f"    [ERROR] Could not resolve channel entity @{channel_name}: {err}")
                continue

            channel_posts: list[RawPost] = []
            async for msg in client.iter_messages(entity=entity, limit=limit_per_channel):
                if not msg.text:
                    continue
                date = msg.date or datetime.now(UTC)
                channel_posts.append(
                    RawPost(
                        channel_username=channel_name,
                        message_id=msg.id,
                        text=msg.text,
                        date=date,
                        url=f"https://t.me/{channel_name}/{msg.id}",
                    )
                )

            channel_stats["fetched"] = len(channel_posts)
            print(f"    Fetched {len(channel_posts)} posts with text from @{channel_name}")

            for idx, post in enumerate(channel_posts, start=1):
                preview = " ".join(post.text.split())[:60]
                print(f"    [{idx}/{len(channel_posts)}] Post #{post.message_id}: \"{preview}...\"")
                
                vacancy = await post_parser.transform(post)
                if vacancy is None:
                    channel_stats["non_vacancies"] += 1
                    print(f"        -> Rejected (Not a vacancy or invalid)")
                else:
                    try:
                        assert_vacancy_contract(vacancy)
                        channel_stats["vacancies"] += 1
                        all_extracted_vacancies.append(vacancy)
                        salary_info = f"{vacancy.salary.from_ or ''}-{vacancy.salary.to or ''} {vacancy.salary.currency or ''}" if vacancy.salary else "not specified"
                        loc_info = vacancy.location.city if vacancy.location and vacancy.location.city else (vacancy.location.text if vacancy.location else "not specified")
                        print(f"        -> [OK] Title: '{vacancy.title}' | Grade: {vacancy.grade} | Employment: {vacancy.employment_types} | Salary: {salary_info} | Loc: {loc_info}")
                    except AssertionError as err:
                        channel_stats["validation_errors"] += 1
                        print(f"        -> [ASSERTION FAILED]: {err}")

                await asyncio.sleep(1.5)

            print(f"    Summary @{channel_name}: Fetched={channel_stats['fetched']}, Vacancies={channel_stats['vacancies']}, Non-vacancies={channel_stats['non_vacancies']}, Errors={channel_stats['validation_errors']}\n")

    finally:
        await client.disconnect()
        await llm_extractor.close()

    batch_request = BatchCreateVacanciesRequest(vacancies=all_extracted_vacancies)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    serialized_json = batch_request.model_dump(mode="json", by_alias=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(serialized_json, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*70}")
    print(f"RUN SUMMARY")
    print(f"{'='*70}")
    total_fetched = sum(s["fetched"] for s in stats.values())
    total_vacancies = sum(s["vacancies"] for s in stats.values())
    total_non_vacancies = sum(s["non_vacancies"] for s in stats.values())
    total_errors = sum(s["validation_errors"] for s in stats.values())

    print(f"Total posts fetched: {total_fetched}")
    print(f"Total valid vacancies parsed: {total_vacancies}")
    print(f"Total non-vacancies / rejected: {total_non_vacancies}")
    print(f"Total assertion/validation errors: {total_errors}")
    print(f"Output saved to: {output_path.resolve()}")
    print(f"{'='*70}\n")


async def main() -> None:
    logging.basicConfig(level=logging.WARNING)
    parser = argparse.ArgumentParser(description="Test Telegram channel parser and output BatchCreateVacanciesRequest JSON")
    parser.add_argument("--send-code", action="store_true", help="Send verification code to TG_PHONE")
    parser.add_argument("--verify-code", type=str, default=None, help="Submit verification code")
    parser.add_argument("--password", type=str, default=None, help="2FA password if enabled")
    parser.add_argument("--status", action="store_true", help="Check Telegram authorization status")
    parser.add_argument("--login", action="store_true", help="Interactive terminal login")
    parser.add_argument("--limit", type=int, default=10, help="Posts per channel (default: 10)")
    parser.add_argument(
        "--channels",
        nargs="+",
        default=DEFAULT_CHANNELS,
        help="Channels to parse",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "data" / "output" / "test_vacancies.json",
        help="Path for output JSON file",
    )
    args = parser.parse_args()

    settings = Settings()
    session_file = settings.resolved_session_path
    client = TelegramClient(str(session_file), settings.tg_api_id, settings.tg_api_hash)

    if args.send_code:
        phone = settings.tg_phone or "+79137908254"
        await handle_send_code(client, phone)
        return

    if args.verify_code:
        await handle_verify_code(client, args.verify_code, args.password)
        return

    if args.status:
        await handle_status(client)
        return

    if args.login:
        await client.connect()
        phone = settings.tg_phone or "+79137908254"
        await client.start(phone=phone)
        me = await client.get_me()
        username = getattr(me, "username", None) or getattr(me, "first_name", "User")
        print(f"[AUTH] Successfully authorized as: {username}")
        await client.disconnect()
        return

    await run_parsing(
        channels=args.channels,
        limit_per_channel=args.limit,
        output_path=args.output,
    )


if __name__ == "__main__":
    asyncio.run(main())
