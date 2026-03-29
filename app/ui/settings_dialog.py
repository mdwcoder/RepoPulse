from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy

import flet as ft

from app.ui import theme
from core.models import AppSettings


class SettingsDialog:
    def __init__(
        self,
        page: ft.Page,
        on_save: Callable[[AppSettings], None],
        on_reset_geometry: Callable[[], None],
    ) -> None:
        self.page = page
        self.on_save = on_save
        self.on_reset_geometry = on_reset_geometry
        self.dialog = ft.AlertDialog(modal=True, bgcolor=theme.SURFACE)

    def open(self, settings: AppSettings) -> None:
        working = deepcopy(settings)

        remember_geometry = ft.Switch(label="Remember window geometry", value=working.remember_window_geometry, active_color=theme.TEAL)
        restore_last_repo = ft.Switch(label="Restore last repo", value=working.restore_last_repo, active_color=theme.TEAL)
        always_on_top_default = ft.Switch(label="Always on top by default", value=working.always_on_top_default, active_color=theme.TEAL)
        ignore_hidden = ft.Switch(label="Ignore hidden files", value=working.ignore_hidden_files, active_color=theme.TEAL)
        ignore_binary = ft.Switch(label="Ignore binary files", value=working.ignore_binary_files, active_color=theme.TEAL)
        scan_ignored = ft.Switch(label="Scan ignored directories", value=working.scan_ignored_directories, active_color=theme.TEAL)
        window_on_top = ft.Switch(label="Always on top", value=working.window.always_on_top, active_color=theme.TEAL)

        max_preview_lines = self._number_field(str(working.max_preview_lines))
        preview_cap = self._number_field(str(working.file_size_cap_preview_kb))
        large_file_threshold = self._number_field(str(working.thresholds.large_file_lines))
        heavy_deletion_threshold = self._number_field(str(working.thresholds.heavy_deletion_lines))
        max_nesting_threshold = self._number_field(str(working.thresholds.max_nesting))
        high_churn_threshold = self._number_field(str(working.thresholds.high_churn))

        def save(_):
            try:
                working.remember_window_geometry = remember_geometry.value
                working.restore_last_repo = restore_last_repo.value
                working.always_on_top_default = always_on_top_default.value
                working.ignore_hidden_files = ignore_hidden.value
                working.ignore_binary_files = ignore_binary.value
                working.scan_ignored_directories = scan_ignored.value
                working.window.always_on_top = window_on_top.value
                working.max_preview_lines = int(max_preview_lines.value)
                working.file_size_cap_preview_kb = int(preview_cap.value)
                working.thresholds.large_file_lines = int(large_file_threshold.value)
                working.thresholds.heavy_deletion_lines = int(heavy_deletion_threshold.value)
                working.thresholds.max_nesting = int(max_nesting_threshold.value)
                working.thresholds.high_churn = int(high_churn_threshold.value)
            except (TypeError, ValueError):
                self.page.snack_bar = ft.SnackBar(ft.Text("Settings require valid numeric values."))
                self.page.snack_bar.open = True
                self.page.update()
                return

            self.dialog.open = False
            self.page.update()
            self.on_save(working)

        self.dialog.title = ft.Text("Settings", color=theme.TEXT)
        self.dialog.content = ft.Container(
            width=650,
            content=ft.Column(
                [
                    self._section("General", [remember_geometry, restore_last_repo, always_on_top_default]),
                    self._section(
                        "Scan",
                        [
                            self._labeled_field("Max preview lines", max_preview_lines),
                            ignore_hidden,
                            ignore_binary,
                            self._labeled_field("Preview size cap (KB)", preview_cap),
                            scan_ignored,
                        ],
                    ),
                    self._section(
                        "Thresholds",
                        [
                            self._labeled_field("Large file line threshold", large_file_threshold),
                            self._labeled_field("Heavy deletion line threshold", heavy_deletion_threshold),
                            self._labeled_field("Max nesting threshold", max_nesting_threshold),
                            self._labeled_field("High churn threshold", high_churn_threshold),
                        ],
                    ),
                    self._section(
                        "Window",
                        [
                            window_on_top,
                            ft.TextButton("Reset geometry", on_click=lambda _: self.on_reset_geometry()),
                        ],
                    ),
                ],
                spacing=16,
                scroll=ft.ScrollMode.AUTO,
                height=540,
            ),
        )
        self.dialog.actions = [
            ft.TextButton("Cancel", on_click=lambda _: self._close()),
            ft.FilledButton("Save", on_click=save, style=ft.ButtonStyle(bgcolor=theme.TEAL, color=theme.BG)),
        ]
        self.page.dialog = self.dialog
        self.dialog.open = True
        self.page.update()

    def _close(self) -> None:
        self.dialog.open = False
        self.page.update()

    def _section(self, title: str, controls: list[ft.Control]) -> ft.Control:
        return theme.surface_card(
            ft.Column(
                [ft.Text(title, size=16, weight=ft.FontWeight.W_700, color=theme.TEXT), *controls],
                spacing=12,
            )
        )

    def _number_field(self, value: str) -> ft.TextField:
        return ft.TextField(
            value=value,
            width=160,
            dense=True,
            border_color=theme.STROKE,
            bgcolor=theme.SURFACE_3,
            color=theme.TEXT,
        )

    def _labeled_field(self, label: str, field: ft.TextField) -> ft.Control:
        return ft.Row(
            [
                ft.Text(label, size=13, color=theme.TEXT, expand=True),
                field,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
