from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    tg_api_id: int = 0
    tg_api_hash: str = ""
    tg_session_path: Path = Path("data/sessions/parser.session")

    backend_url: str = "http://localhost:8080/api/v1"
    parser_api_key: str = "test_key"

    poll_interval_seconds: int = 1800
    batch_size: int = 50
    sqlite_db_path: Path = Path("data/state.sqlite")
    channels_config_path: Path = Path("config/channels.yaml")
    log_level: str = "INFO"
