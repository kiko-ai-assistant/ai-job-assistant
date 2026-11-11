import json
import logging
from datetime import UTC, datetime, timedelta
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
            raise

        if not isinstance(data, list):
            raise ValueError("JSON storage must be a list; refusing to overwrite old data")

        for item in data:
            if not isinstance(item, dict):
                raise ValueError("JSON storage contains a non-object vacancy")
            source = item.get("source")
            external_id = item.get("external_id")
            if not isinstance(source, str) or not isinstance(external_id, str):
                raise ValueError("Stored vacancy must have source and external_id strings")
            vacancy_data = {
                key: value for key, value in item.items() if key != "_backend_delivered"
            }
            try:
                Vacancy(**vacancy_data)
            except TypeError as exc:
                raise ValueError("Invalid stored vacancy; refusing to overwrite old data") from exc
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
                parsed = parsed.replace(tzinfo=UTC)
        except (TypeError, ValueError):
            return True

        return datetime.now(UTC) - parsed >= self.refresh_after

    def upsert(self, vacancy: Vacancy) -> None:
        self._items[vacancy.key] = vacancy.to_dict()

    def pending(self) -> list[Vacancy]:
        return [
            Vacancy(**{key: value for key, value in item.items() if key != "_backend_delivered"})
            for item in self._items.values()
            if item.get("_backend_delivered") is not True
        ]

    def mark_delivered(self, keys: list[tuple[str, str]]) -> None:
        previous = {key: self._items[key].copy() for key in keys}
        for key in keys:
            self._items[key]["_backend_delivered"] = True
        try:
            self.flush()
        except OSError:
            self._items.update(previous)
            raise

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
