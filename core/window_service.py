from __future__ import annotations

from pathlib import Path

import flet as ft

from core.models import AppSettings


class WindowService:
    def apply_base_window(self, page: ft.Page, settings: AppSettings) -> None:
        page.title = "RepoPulse"
        page.padding = 0
        page.spacing = 0
        page.bgcolor = "#081221"
        page.theme_mode = ft.ThemeMode.DARK
        page.window.resizable = True
        page.window.minimizable = True
        page.window.maximizable = False
        page.window.prevent_close = False
        page.window.always_on_top = (
            settings.window.always_on_top if settings.remember_window_geometry else settings.always_on_top_default
        )
        page.window.width = max(settings.window.width, 480)
        page.window.height = max(settings.window.height, 680)
        page.window.min_width = 430
        page.window.min_height = 640
        self.restore_geometry(page, settings)

    def restore_geometry(self, page: ft.Page, settings: AppSettings) -> None:
        if settings.remember_window_geometry and settings.window.left is not None and settings.window.top is not None:
            try:
                page.window.left = settings.window.left
                page.window.top = settings.window.top
                return
            except Exception:
                pass
        self.apply_default_anchor(page)

    def apply_default_anchor(self, page: ft.Page) -> None:
        platform = str(page.platform).lower()
        page.window.top = 48
        if "macos" in platform:
            page.window.left = 980
        else:
            page.window.left = 40

    def capture_geometry(self, page: ft.Page, settings: AppSettings) -> AppSettings:
        settings.window.width = int(page.window.width or settings.window.width)
        settings.window.height = int(page.window.height or settings.window.height)
        settings.window.left = int(page.window.left) if page.window.left is not None else settings.window.left
        settings.window.top = int(page.window.top) if page.window.top is not None else settings.window.top
        settings.window.always_on_top = bool(page.window.always_on_top)
        return settings

    def reset_geometry(self, page: ft.Page, settings: AppSettings) -> AppSettings:
        settings.window.width = 520
        settings.window.height = 880
        settings.window.left = None
        settings.window.top = None
        self.apply_base_window(page, settings)
        return settings
