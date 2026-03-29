from __future__ import annotations

from collections.abc import Callable

import flet as ft

from app.ui import theme
from core.enums import FindingCategory, Severity, ViewName
from core.models import FileAnalysis, RepoScanResult
from core.utils.path_utils import shorten_path


class OverviewView:
    def __init__(
        self,
        on_open_detail: Callable[[str, ViewName | None], None],
        on_jump_warning,
        on_view_log: Callable[[], None] | None = None,
    ) -> None:
        self.on_open_detail = on_open_detail
        self.on_jump_warning = on_jump_warning
        self.on_view_log = on_view_log
        self.root = ft.Container(expand=True, padding=18)
        self.result: RepoScanResult | None = None
        self.wide_mode = False
        self.selected_hotspot: FileAnalysis | None = None
        self._set_empty()

    def update(self, result: RepoScanResult | None, wide_mode: bool = False) -> None:
        self.result = result
        self.wide_mode = wide_mode
        if result is None:
            self._set_empty()
            return

        # Auto-select first hotspot if none selected
        if self.selected_hotspot is None and result.hotspots:
            self.selected_hotspot = result.hotspots[0]

        self._rebuild()

    def _rebuild(self) -> None:
        result = self.result
        if result is None:
            self._set_empty()
            return

        health = theme.surface_card(
            ft.Column(
                [
                    ft.Stack(
                        [
                            ft.Container(
                                width=170,
                                height=170,
                                alignment=ft.alignment.Alignment(0, 0),
                                content=ft.ProgressRing(
                                    value=result.health_score / 100,
                                    color=self._health_color(result.health_score),
                                    stroke_width=10,
                                    width=150,
                                    height=150,
                                    bgcolor="#08121F",
                                ),
                            ),
                            ft.Container(
                                width=170,
                                height=170,
                                alignment=ft.alignment.Alignment(0, 0),
                                content=ft.Column(
                                    [
                                        ft.Text(f"{result.health_score}%", size=34, weight=ft.FontWeight.W_700, color=theme.TEXT, text_align=ft.TextAlign.CENTER),
                                        ft.Text("HEALTHY" if result.health_score >= 70 else "WATCH", size=11, color=self._health_color(result.health_score), text_align=ft.TextAlign.CENTER),
                                    ],
                                    spacing=2,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    alignment=ft.MainAxisAlignment.CENTER,
                                ),
                            ),
                        ],
                        width=170,
                        height=170,
                    ),
                    ft.Text("Repo Health Score", size=18, weight=ft.FontWeight.W_700, color=theme.TEXT),
                    ft.Text("Fast signal for where you should inspect the repository first.", size=12, color=theme.MUTED),
                ],
                spacing=14,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            expand=True,
        )

        blocking_count = sum(1 for f in result.findings if f.severity.value == "high")

        cards = ft.ResponsiveRow(
            [
                ft.Container(col={"xs": 6, "md": 6}, content=theme.metric_tile("FILES ANALYZED", str(result.total_files_scanned), theme.TEAL)),
                ft.Container(col={"xs": 6, "md": 6}, content=theme.metric_tile("COMPLEX HOTSPOTS", str(len(result.hotspots)), theme.ORANGE)),
                ft.Container(col={"xs": 6, "md": 6}, content=theme.metric_tile("GIT CHANGES (24H)", str(result.git_snapshot.total_changes), theme.AMBER)),
                ft.Container(col={"xs": 6, "md": 6}, content=theme.metric_tile("BLOCKING ISSUES", str(blocking_count), theme.RED)),
            ],
            spacing=12,
            run_spacing=12,
        )

        hotspot_items = [
            self._hotspot_item(item)
            for item in result.hotspots[:5]
        ] or [ft.Text("No critical hotspots detected.", size=12, color=theme.MUTED)]

        warning_items = [
            self._warning_item(item)
            for item in result.warnings[:5]
        ] or [ft.Text("No recent warnings.", size=12, color=theme.MUTED)]

        view_log_btn = ft.TextButton(
            "VIEW LOG",
            on_click=lambda _: self.on_view_log() if self.on_view_log else None,
            style=ft.ButtonStyle(color=theme.TEAL),
        )

        pulse_section = theme.surface_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text("Recent Pulse", size=17, weight=ft.FontWeight.W_700, color=theme.TEXT),
                            view_log_btn,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    *warning_items,
                ],
                spacing=12,
            )
        )

        hotspots_section = theme.surface_card(
            ft.Column(
                [theme.title("Critical Hotspots"), *hotspot_items],
                spacing=12,
            )
        )

        if self.wide_mode:
            center_content = ft.Column(
                [cards, hotspots_section, pulse_section],
                spacing=14,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            )

            detail_panel = self._build_detail_panel(self.selected_hotspot)

            self.root.content = ft.Column(
                [
                    ft.ResponsiveRow(
                        [
                            ft.Container(col={"xs": 12, "md": 3}, content=health),
                            ft.Container(col={"xs": 12, "md": 5}, content=center_content),
                            ft.Container(col={"xs": 12, "md": 4}, content=detail_panel),
                        ],
                        spacing=14,
                        run_spacing=14,
                        expand=True,
                    ),
                ],
                spacing=14,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            )
        else:
            self.root.content = ft.Column(
                [
                    ft.ResponsiveRow(
                        [
                            ft.Container(col={"xs": 12, "md": 4}, content=health),
                            ft.Container(
                                col={"xs": 12, "md": 8},
                                content=ft.Column([cards], spacing=0),
                            ),
                        ],
                        spacing=14,
                        run_spacing=14,
                    ),
                    ft.ResponsiveRow(
                        [
                            ft.Container(
                                col={"xs": 12, "md": 6},
                                content=hotspots_section,
                            ),
                            ft.Container(
                                col={"xs": 12, "md": 6},
                                content=pulse_section,
                            ),
                        ],
                        spacing=14,
                        run_spacing=14,
                    ),
                ],
                spacing=14,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            )

    def _build_detail_panel(self, analysis: FileAnalysis | None) -> ft.Control:
        if analysis is None:
            return theme.surface_card(
                ft.Column(
                    [
                        ft.Text("SELECTED HOTSPOT", size=11, color=theme.TEAL, weight=ft.FontWeight.W_600),
                        ft.Text("Select a hotspot to inspect its details.", size=13, color=theme.MUTED),
                    ],
                    spacing=10,
                ),
                expand=True,
            )

        metrics = analysis.metrics
        color = theme.severity_color(analysis.severity)

        severity_label_map = {
            Severity.HIGH: "CRITICAL",
            Severity.IMPORTANT: "IMPORTANT",
            Severity.WATCH: "WATCH",
            Severity.INFO: "INFO",
        }
        severity_label = severity_label_map.get(analysis.severity, analysis.severity.value.upper())

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

        badges_row = ft.Row(
            [theme.badge(item, color=color) for item in analysis.badges[:5]],
            spacing=6,
            wrap=True,
            run_spacing=6,
        )

        optimize_btn = ft.FilledButton(
            "OPTIMIZE FILE",
            on_click=lambda _: self.on_open_detail(metrics.path, ViewName.HOTSPOTS),
            style=ft.ButtonStyle(
                bgcolor=theme.TEAL,
                color=theme.BG,
                shape=ft.RoundedRectangleBorder(radius=12),
            ),
            expand=True,
        )

        return theme.surface_card(
            ft.Column(
                [
                    ft.Text("SELECTED HOTSPOT", size=11, color=theme.TEAL, weight=ft.FontWeight.W_600),
                    ft.Text(metrics.filename, size=18, weight=ft.FontWeight.W_700, color=theme.TEXT),
                    ft.Text(shorten_path(metrics.path, 48), size=11, color=theme.MUTED),
                    ft.Row(
                        [
                            ft.Text("COMPLEXITY SCORE", size=11, color=theme.MUTED, weight=ft.FontWeight.W_600),
                            theme.badge(severity_label, color=color),
                        ],
                        spacing=10,
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    theme.progress_bar(analysis.risk_score / 100, color),
                    badges_row,
                    ft.Text("Preview", size=11, color=theme.MUTED, weight=ft.FontWeight.W_600),
                    preview,
                    ft.Container(
                        content=optimize_btn,
                        margin=ft.margin.only(top=6),
                    ),
                ],
                spacing=12,
                scroll=ft.ScrollMode.AUTO,
            ),
            expand=True,
        )

    def _set_empty(self) -> None:
        self.root.content = theme.surface_card(
            ft.Column(
                [
                    ft.Text("Overview", size=22, weight=ft.FontWeight.W_700, color=theme.TEXT),
                    ft.Text("Open a repository to scan its health, hotspots and Git hygiene.", size=13, color=theme.MUTED),
                ],
                spacing=12,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            expand=True,
        )

    def _hotspot_item(self, analysis: FileAnalysis) -> ft.Control:
        color = theme.severity_color(analysis.severity)
        is_selected = self.selected_hotspot and self.selected_hotspot.metrics.path == analysis.metrics.path

        def _on_click(_, a=analysis):
            self.selected_hotspot = a
            self._rebuild()

        return ft.Container(
            bgcolor=theme.SURFACE_3,
            border_radius=14,
            border=ft.border.all(1, color if is_selected else theme.STROKE),
            padding=12,
            on_click=_on_click,
            ink=True,
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text(analysis.metrics.filename, size=15, weight=ft.FontWeight.W_700, color=theme.TEXT),
                                    ft.Text(shorten_path(analysis.metrics.path, 42), size=11, color=theme.MUTED),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.Text(str(analysis.risk_score), size=18, weight=ft.FontWeight.W_700, color=color),
                        ],
                    ),
                    theme.progress_bar(analysis.risk_score / 100, color),
                    ft.Row(
                        [theme.badge(item, color=color) for item in analysis.badges[:5]],
                        spacing=6,
                        wrap=True,
                        run_spacing=6,
                    ),
                ],
                spacing=10,
            ),
        )

    def _warning_item(self, finding) -> ft.Control:
        color = theme.severity_color(finding.severity)
        return ft.Container(
            bgcolor=theme.SURFACE_3,
            border_radius=14,
            border=ft.border.all(1, theme.STROKE),
            padding=12,
            ink=True,
            on_click=lambda _, item=finding: self.on_jump_warning(item),
            content=ft.Row(
                [
                    ft.Container(width=10, height=10, border_radius=999, bgcolor=color),
                    ft.Column(
                        [
                            ft.Text(finding.title, size=14, weight=ft.FontWeight.W_700, color=theme.TEXT),
                            ft.Text(finding.short_explanation, size=12, color=theme.MUTED),
                        ],
                        spacing=4,
                        expand=True,
                    ),
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
        )

    def _health_color(self, score: int) -> str:
        if score >= 75:
            return theme.TEAL
        if score >= 50:
            return theme.AMBER
        return theme.RED
