from __future__ import annotations

import json
from pathlib import Path

from core.models import AppSettings


class SettingsStore:
    def __init__(self, settings_path: Path) -> None:
        self.settings_path = settings_path

    def load(self) -> AppSettings:
        if not self.settings_path.exists():
            return AppSettings()
        try:
            data = json.loads(self.settings_path.read_text(encoding="utf-8"))
            return AppSettings.from_dict(data)
        except (json.JSONDecodeError, OSError, TypeError, ValueError):
            return AppSettings()

    def save(self, settings: AppSettings) -> None:
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        self.settings_path.write_text(
            json.dumps(settings.to_dict(), indent=2, ensure_ascii=True),
            encoding="utf-8",
        )
