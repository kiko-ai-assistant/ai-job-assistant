import json
from datetime import datetime, timezone
from pathlib import Path


class UnavailableRegistry:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._items: dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return
        if isinstance(data, list):
            for item in data:
                key = f"{item.get('source')}:{item.get('external_id')}"
                self._items[key] = item

    def mark(self, source: str, external_id: str, url: str, status: int) -> None:
        key = f"{source}:{external_id}"
        self._items[key] = {
            "source": source,
            "external_id": external_id,
            "url": url,
            "http_status": status,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    def flush(self) -> None:
        temp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        temp_path.write_text(
            json.dumps(list(self._items.values()), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp_path.replace(self.path)
