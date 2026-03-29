from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class CacheStore:
    def __init__(self, cache_path: Path) -> None:
        self.cache_path = cache_path

    def read(self) -> dict[str, Any]:
        if not self.cache_path.exists():
            return {}
        try:
            return json.loads(self.cache_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def write(self, data: dict[str, Any]) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=True), encoding="utf-8"
        )
