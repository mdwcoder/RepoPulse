from __future__ import annotations

from collections.abc import Callable

import flet as ft

from app.ui import theme
from core.git_service import relative_time
from core.models import FileAnalysis
from core.utils.path_utils import format_bytes


class FileDetailPanel:
    def __init__(
        self,
        on_open_file: Callable[[str], None] | None = None,
    ) -> None:
        self.on_open_file = on_open_file

    def build_panel(self, analysis: FileAnalysis | None, on_open_file: Callable[[str], None] | None = None) -> ft.Control:
        open_file_cb = on_open_file or self.on_open_file

        if analysis is None:
            return theme.surface_card(
                ft.Column(
                    [
                        ft.Text("Selected Hotspot", size=11, color=theme.TEAL, weight=ft.FontWeight.W_600),
                        ft.Text("Select a file to inspect its metrics and preview.", size=13, color=theme.MUTED),
                    ],
                    spacing=10,
                ),
                expand=True,
            )

        metrics = analysis.metrics
        info_tiles = ft.ResponsiveRow(
            [
                ft.Container(col={"xs": 6, "md": 6}, content=theme.metric_tile("Size", format_bytes(metrics.size_bytes), theme.TEAL)),
                ft.Container(col={"xs": 6, "md": 6}, content=theme.metric_tile("LOC", str(metrics.line_count), theme.AMBER)),
                ft.Container(col={"xs": 6, "md": 6}, content=theme.metric_tile("Complexity", str(metrics.estimated_complexity), theme.ORANGE)),
                ft.Container(col={"xs": 6, "md": 6}, content=theme.metric_tile("Churn", str(metrics.git_churn), theme.BLUE)),
            ],
            spacing=10,
            run_spacing=10,
        )
        badges = ft.Row(
            [theme.badge(badge, color=theme.severity_color(analysis.severity)) for badge in analysis.badges[:5]],
            spacing=6,
            wrap=True,
            run_spacing=6,
        )
        why_lines = ft.Column(
            [ft.Text(reason, size=12, color=theme.TEXT) for reason in analysis.why_flagged]
            or [ft.Text("No strong flags were raised for this file.", size=12, color=theme.MUTED)],
            spacing=8,
        )
        preview = ft.Container(
            bgcolor="#040B16",
            border_radius=14,
            border=ft.border.all(1, "#17304F"),
            padding=12,
            content=ft.Text(
                metrics.preview,
                size=11,
                color="#9EEFD8",
                font_family="monospace",
                selectable=True,
            ),
        )

        controls: list[ft.Control] = [
            ft.Text("Selected Analysis", size=11, color=theme.TEAL, weight=ft.FontWeight.W_600),
            ft.Text(metrics.filename, size=20, weight=ft.FontWeight.W_700, color=theme.TEXT),
            ft.Text(metrics.path, size=11, color=theme.MUTED),
            ft.Row(
                [
                    ft.Text(str(analysis.risk_score), size=34, weight=ft.FontWeight.W_700, color=theme.severity_color(analysis.severity)),
                    ft.Column(
                        [
                            ft.Text("Risk score", size=10, color=theme.MUTED),
                            ft.Text(analysis.severity.value.upper(), size=11, color=theme.severity_color(analysis.severity)),
                        ],
                        spacing=2,
                    ),
                ],
                spacing=10,
            ),
            theme.progress_bar(analysis.risk_score / 100, theme.severity_color(analysis.severity)),
            badges,
            ft.Divider(color=theme.STROKE, height=18),
            ft.Text("Static Analysis", size=11, color=theme.MUTED, weight=ft.FontWeight.W_600),
            info_tiles,
            ft.Text("Why flagged", size=11, color=theme.MUTED, weight=ft.FontWeight.W_600),
            why_lines,
            ft.Text("Preview", size=11, color=theme.MUTED, weight=ft.FontWeight.W_600),
            preview,
        ]

        if open_file_cb is not None:
            controls.append(
                ft.FilledButton(
                    "Open in Editor",
                    on_click=lambda _, path=metrics.path: open_file_cb(path),
                    style=ft.ButtonStyle(
                        bgcolor=theme.TEAL,
                        color=theme.BG,
                        shape=ft.RoundedRectangleBorder(radius=12),
                    ),
                    expand=True,
                )
            )

        return theme.surface_card(
            ft.Column(
                controls,
                spacing=12,
                scroll=ft.ScrollMode.AUTO,
            ),
            expand=True,
        )

    def build_dialog(self, analysis: FileAnalysis) -> ft.AlertDialog:
        return ft.AlertDialog(
            modal=True,
            bgcolor=theme.SURFACE,
            title=ft.Text(analysis.metrics.filename, color=theme.TEXT),
            content=ft.Container(width=620, height=680, content=self.build_panel(analysis, on_open_file=self.on_open_file)),
        )
