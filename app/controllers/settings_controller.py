from __future__ import annotations

import os
from pathlib import Path

from core.models import AppSettings
from core.utils.logger import configure_logger
from storage.cache_store import CacheStore
from storage.settings_store import SettingsStore


class SettingsController:
    def __init__(self) -> None:
        self.base_dir = self._resolve_base_dir()
        self.store = SettingsStore(self.base_dir / "settings.json")
        self.cache_store = CacheStore(self.base_dir / "cache.json")
        configure_logger(self.base_dir / "logs" / "repopulse.log")
        self.settings = self.store.load()

    def save(self) -> None:
        self.store.save(self.settings)

    def update(self, settings: AppSettings) -> AppSettings:
        self.settings = settings
        self.save()
        return self.settings

    def clear_last_repo(self) -> None:
        self.settings.last_repo_path = None
        self.save()

    def _resolve_base_dir(self) -> Path:
        xdg_config = os.getenv("XDG_CONFIG_HOME")
        if xdg_config:
            return Path(xdg_config) / "repopulse"
        return Path.home() / ".config" / "repopulse"
