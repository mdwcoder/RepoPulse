from __future__ import annotations

from collections.abc import Callable

import flet as ft

from app.ui import theme
from core.enums import ScanState
from core.utils.path_utils import shorten_path

_TAB_LABELS = ["Overview", "Hotspots", "Git", "Ignore", "Files"]


class HeaderBar:
    def __init__(
        self,
        on_open_repo: Callable[[], None],
        on_refresh: Callable[[], None],
        on_toggle_pin: Callable[[], None],
        on_settings: Callable[[], None],
        on_minimize: Callable[[], None],
        on_tab_change: Callable[[int], None] | None = None,
    ) -> None:
        self.on_open_repo = on_open_repo
        self.on_refresh = on_refresh
        self.on_toggle_pin = on_toggle_pin
        self.on_settings = on_settings
        self.on_minimize = on_minimize
        self.on_tab_change = on_tab_change

        self._active_tab = 0
        self.scan_chip = theme.badge("idle", muted=True)

        self.pin_button = ft.IconButton(
            icon=ft.Icons.PUSH_PIN_OUTLINED,
            icon_color=theme.MUTED,
            on_click=lambda _: self.on_toggle_pin(),
            tooltip="Pin window",
        )

        self._tab_controls: list[ft.Container] = []
        self._tab_texts: list[ft.Text] = []

        for i, label in enumerate(_TAB_LABELS):
            txt = ft.Text(
                label,
                size=13,
                weight=ft.FontWeight.W_600,
                color=theme.TEAL if i == 0 else theme.MUTED,
            )
            self._tab_texts.append(txt)
            tab_btn = ft.Container(
                padding=ft.padding.symmetric(horizontal=14, vertical=8),
                border=ft.border.only(bottom=ft.BorderSide(2, theme.TEAL)) if i == 0 else None,
                ink=True,
                on_click=lambda _, idx=i: self._handle_tab_click(idx),
                content=txt,
            )
            self._tab_controls.append(tab_btn)

        self.root = ft.Container(
            padding=ft.padding.symmetric(horizontal=18, vertical=6),
            bgcolor="#081426",
            border=ft.border.only(bottom=ft.BorderSide(1, theme.STROKE)),
            content=ft.Row(
                [
                    # Left: logo + scan chip
                    ft.Row(
                        [
                            ft.Text("RepoPulse", size=16, weight=ft.FontWeight.W_700, color=theme.TEXT),
                            self.scan_chip,
                        ],
                        spacing=10,
                    ),
                    # Center: tab buttons
                    ft.Row(
                        self._tab_controls,
                        spacing=0,
                        expand=True,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    # Right: icon-only action buttons
                    ft.Row(
                        [
                            ft.IconButton(
                                icon=ft.Icons.FOLDER_OPEN_ROUNDED,
                                icon_color=theme.MUTED,
                                on_click=lambda _: self.on_open_repo(),
                                tooltip="Open repository",
                                icon_size=20,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.REFRESH_ROUNDED,
                                icon_color=theme.MUTED,
                                on_click=lambda _: self.on_refresh(),
                                tooltip="Refresh scan",
                                icon_size=20,
                            ),
                            self.pin_button,
                            ft.IconButton(
                                icon=ft.Icons.SETTINGS_ROUNDED,
                                icon_color=theme.MUTED,
                                on_click=lambda _: self.on_settings(),
                                tooltip="Settings",
                                icon_size=20,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.MINIMIZE_ROUNDED,
                                icon_color=theme.MUTED,
                                on_click=lambda _: self.on_minimize(),
                                tooltip="Minimize",
                                icon_size=20,
                            ),
                        ],
                        spacing=2,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def _handle_tab_click(self, index: int) -> None:
        self.set_active_tab(index)
        if self.on_tab_change:
            self.on_tab_change(index)

    def set_active_tab(self, index: int) -> None:
        self._active_tab = index
        for i, (tab, txt) in enumerate(zip(self._tab_controls, self._tab_texts)):
            active = i == index
            txt.color = theme.TEAL if active else theme.MUTED
            tab.border = ft.border.only(bottom=ft.BorderSide(2, theme.TEAL)) if active else None

    def update(self, repo_path: str | None, scan_state: ScanState, always_on_top: bool, has_result: bool) -> None:
        self.scan_chip.content.value = scan_state.value
        self.scan_chip.bgcolor = theme.scan_state_color(scan_state)
        self.pin_button.icon = ft.Icons.PUSH_PIN_ROUNDED if always_on_top else ft.Icons.PUSH_PIN_OUTLINED
        self.pin_button.icon_color = theme.TEAL if always_on_top else theme.MUTED
