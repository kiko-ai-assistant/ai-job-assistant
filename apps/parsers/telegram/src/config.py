from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    tg_api_id: int = Field(default=0, alias="TG_API_ID")
    tg_api_hash: str = Field(default="", alias="TG_API_HASH")
    tg_phone: str | None = Field(default=None, alias="TG_PHONE")
    tg_session_path: Path | None = Field(default=None, alias="TG_SESSION_PATH")

    backend_url: str = Field(default="http://localhost:8080/api/v1", alias="BACKEND_URL")
    backend_api_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "BACKEND_API_KEY",
            "PARSER_API_KEY",
            "backend_api_key",
            "parser_api_key",
        ),
    )

    poll_interval_seconds: int = Field(
        default=1800,
        validation_alias=AliasChoices(
            "POLL_INTERVAL_SECONDS",
            "POLL_INTERVAL",
            "poll_interval_seconds",
        ),
    )
    batch_size: int = Field(default=50, alias="BATCH_SIZE")
    state_storage_path: Path = Field(
        default=Path("data/state.sqlite"),
        validation_alias=AliasChoices(
            "STATE_STORAGE",
            "SQLITE_DB_PATH",
            "state_storage_path",
            "sqlite_db_path",
        ),
    )
    channels_config_path: Path = Field(
        default=Path("data/config/channels.yaml"),
        validation_alias=AliasChoices(
            "CHANNELS_CONFIG_PATH",
            "CHANNELS_CONFIG",
            "channels_config_path",
        ),
    )
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    llm_api_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "LLM_API_KEY",
            "OPENROUTER_API_KEY",
            "llm_api_key",
            "openrouter_api_key",
        ),
    )
    llm_base_url: str = Field(default="https://openrouter.ai/api/v1", alias="LLM_BASE_URL")
    llm_model: str = Field(default="meta-llama/llama-3.3-70b-instruct:free", alias="LLM_MODEL")
    llm_timeout: float = Field(default=30.0, alias="LLM_TIMEOUT")

    @property
    def parser_api_key(self) -> str:
        return self.backend_api_key

    @property
    def resolved_session_path(self) -> Path:
        base_dir = Path(__file__).resolve().parent.parent
        if self.tg_session_path is not None:
            if self.tg_session_path.is_absolute():
                return self.tg_session_path
            return (base_dir / self.tg_session_path).resolve()
        return (base_dir / "data" / "sessions" / "parser.session").resolve()

    @property
    def sqlite_db_path(self) -> Path:
        return self.state_storage_path
