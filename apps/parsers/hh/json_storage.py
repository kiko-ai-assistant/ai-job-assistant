import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from models import Vacancy


class JsonVacancyStorage:
    def __init__(
        self,
        path: str,
        refresh_after_hours: float,
        logger: logging.Logger,
    ):
        self.path = Path(path)
        self.refresh_after = timedelta(hours=refresh_after_hours)
        self.logger = logger
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._items: dict[tuple[str, str], dict] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return

        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            self.logger.exception("Could not read JSON storage %s", self.path)
            return

        if not isinstance(data, list):
            self.logger.warning("JSON storage is not a list; ignoring old data")
            return

        for item in data:
            source = item.get("source")
            external_id = item.get("external_id")
            if source and external_id:
                self._items[(source, external_id)] = item

        self.logger.info("Loaded %s vacancies from %s", len(self._items), self.path)

    def contains(self, source: str, external_id: str) -> bool:
        return (source, external_id) in self._items

    def should_refresh(self, source: str, external_id: str) -> bool:
        item = self._items.get((source, external_id))
        if item is None:
            return True

        parsed_at = item.get("parsed_at")
        if not parsed_at:
            return True

        try:
            parsed = datetime.fromisoformat(parsed_at)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
        except (TypeError, ValueError):
            return True

        return datetime.now(timezone.utc) - parsed >= self.refresh_after

    def upsert(self, vacancy: Vacancy) -> None:
        self._items[vacancy.key] = vacancy.to_dict()

    def flush(self) -> None:
        temp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        payload = list(self._items.values())
        temp_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp_path.replace(self.path)

    def count(self) -> int:
        return len(self._items)
