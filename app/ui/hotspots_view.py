from __future__ import annotations

from collections.abc import Callable

import flet as ft

from app.ui import theme
from app.ui.file_detail_panel import FileDetailPanel
from core.models import FileAnalysis, RepoScanResult
from core.utils.path_utils import shorten_path


class HotspotsView:
    def __init__(
        self,
        on_open_modal: Callable[[FileAnalysis], None],
        on_open_file: Callable[[str], None] | None = None,
    ) -> None:
        self.on_open_modal = on_open_modal
        self.on_open_file = on_open_file
        self.detail_panel = FileDetailPanel(on_open_file=on_open_file)
        self.root = ft.Container(expand=True, padding=18)
        self.result: RepoScanResult | None = None
        self.selected_path: str | None = None
        self.wide_mode = False
        self._set_empty()

    def update(self, result: RepoScanResult | None, wide_mode: bool) -> None:
        self.result = result
        self.wide_mode = wide_mode
        if result and not self.selected_path and result.hotspots:
            self.selected_path = result.hotspots[0].metrics.path
        self._rebuild()

    def select_path(self, path: str, wide_mode: bool) -> None:
        self.selected_path = path
        self.wide_mode = wide_mode
        if not self.result:
            return
        if wide_mode:
            self._rebuild()
        else:
            analysis = self._selected_analysis()
            if analysis:
                self.on_open_modal(analysis)

    def _rebuild(self) -> None:
        if self.result is None:
            self._set_empty()
            return
        items = [self._item(analysis) for analysis in self.result.hotspots] or [
            ft.Text("No hotspots detected.", size=12, color=theme.MUTED)
        ]

        list_card = theme.surface_card(
            ft.Column(
                [
                    theme.title("Architectural Hotspots", "Files that deserve a first look."),
                    *items,
                ],
                spacing=12,
                scroll=ft.ScrollMode.AUTO,
            ),
            expand=True,
        )

        if self.wide_mode:
            self.root.content = ft.Row(
                [
                    ft.Container(expand=5, content=list_card),
                    ft.Container(expand=3, content=self.detail_panel.build_panel(self._selected_analysis())),
                ],
                spacing=14,
                expand=True,
            )
        else:
            self.root.content = list_card

    def _set_empty(self) -> None:
        self.root.content = theme.surface_card(
            ft.Text("Run a scan to populate hotspots.", size=13, color=theme.MUTED),
            expand=True,
        )

    def _item(self, analysis: FileAnalysis) -> ft.Control:
        color = theme.severity_color(analysis.severity)
        return ft.Container(
            bgcolor=theme.SURFACE_3,
            border_radius=16,
            border=ft.border.all(1, color if self.selected_path == analysis.metrics.path else theme.STROKE),
            padding=14,
            ink=True,
            on_click=lambda _, path=analysis.metrics.path: self.select_path(path, self.wide_mode),
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text(analysis.metrics.filename, size=16, weight=ft.FontWeight.W_700, color=theme.TEXT),
                                    ft.Text(shorten_path(analysis.metrics.path, 56), size=11, color=theme.MUTED),
                                ],
                                spacing=4,
                                expand=True,
                            ),
                            ft.Text(str(analysis.risk_score), size=28, weight=ft.FontWeight.W_700, color=color),
                        ],
                    ),
                    theme.progress_bar(analysis.risk_score / 100, color),
                    ft.Row(
                        [
                            theme.badge(analysis.severity.value, color=color),
                            *[theme.badge(item, muted=True) for item in analysis.badges[:5]],
                        ],
                        spacing=6,
                        wrap=True,
                        run_spacing=6,
                    ),
                ],
                spacing=10,
            ),
        )

    def _selected_analysis(self) -> FileAnalysis | None:
        if not self.result or not self.selected_path:
            return None
        return next((item for item in self.result.file_analyses if item.metrics.path == self.selected_path), None)
