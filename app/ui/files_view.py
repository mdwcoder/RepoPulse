from __future__ import annotations

from collections.abc import Callable

import flet as ft

from app.ui import theme
from app.ui.file_detail_panel import FileDetailPanel
from core.enums import GitStatusKind
from core.models import FileAnalysis, RepoScanResult
from core.utils.path_utils import format_bytes, shorten_path


class FilesView:
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

        self.filter_field = ft.TextField(
            hint_text="Filter files...",
            dense=True,
            border_color=theme.STROKE,
            bgcolor=theme.SURFACE_3,
            color=theme.TEXT,
            cursor_color=theme.TEAL,
            on_change=lambda _: self._rebuild(),
        )
        self.sort_dropdown = ft.Dropdown(
            value="score",
            options=[
                ft.dropdown.Option("score", "Sort: Score"),
                ft.dropdown.Option("size", "Sort: Size"),
                ft.dropdown.Option("lines", "Sort: Line count"),
                ft.dropdown.Option("extension", "Sort: Extension"),
            ],
            dense=True,
            on_select=lambda _: self._rebuild(),
            border_color=theme.STROKE,
            bgcolor=theme.SURFACE_3,
            color=theme.TEXT,
        )
        self.status_dropdown = ft.Dropdown(
            value="all",
            options=[
                ft.dropdown.Option("all", "Git status: All"),
                ft.dropdown.Option("clean", "Clean"),
                ft.dropdown.Option("modified", "Modified"),
                ft.dropdown.Option("deleted", "Deleted"),
                ft.dropdown.Option("untracked", "Untracked"),
            ],
            dense=True,
            on_select=lambda _: self._rebuild(),
            border_color=theme.STROKE,
            bgcolor=theme.SURFACE_3,
            color=theme.TEXT,
        )
        self.extension_dropdown = ft.Dropdown(
            value="all",
            options=[ft.dropdown.Option("all", "Extension: All")],
            dense=True,
            on_select=lambda _: self._rebuild(),
            border_color=theme.STROKE,
            bgcolor=theme.SURFACE_3,
            color=theme.TEXT,
        )
        self.hotspot_only = ft.Switch(
            label="Hotspot only",
            value=False,
            active_color=theme.TEAL,
            on_change=lambda _: self._rebuild(),
        )
        self._set_empty()

    def update(self, result: RepoScanResult | None, wide_mode: bool) -> None:
        self.result = result
        self.wide_mode = wide_mode
        if result:
            self._sync_extensions(result)
            if not self.selected_path and result.file_analyses:
                self.selected_path = result.file_analyses[0].metrics.path
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

    def _sync_extensions(self, result: RepoScanResult) -> None:
        extensions = sorted({analysis.metrics.extension or "(no ext)" for analysis in result.file_analyses})
        current = self.extension_dropdown.value or "all"
        self.extension_dropdown.options = [ft.dropdown.Option("all", "Extension: All")]
        self.extension_dropdown.options.extend(
            ft.dropdown.Option(ext, ext) for ext in extensions
        )
        if current not in {option.key for option in self.extension_dropdown.options}:
            self.extension_dropdown.value = "all"

    def _rebuild(self) -> None:
        if self.result is None:
            self._set_empty()
            return
        visible = self._visible_files()
        items = [self._file_item(item) for item in visible] or [ft.Text("No files match the current filters.", size=12, color=theme.MUTED)]

        list_card = theme.surface_card(
            ft.Column(
                [
                    ft.Text("Files", size=28, weight=ft.FontWeight.W_700, color=theme.TEXT),
                    ft.Row(
                        [
                            ft.Container(width=220, content=self.filter_field),
                            ft.Container(width=170, content=self.sort_dropdown),
                            ft.Container(width=170, content=self.extension_dropdown),
                            ft.Container(width=170, content=self.status_dropdown),
                            self.hotspot_only,
                        ],
                        spacing=10,
                        wrap=True,
                        run_spacing=10,
                    ),
                    ft.Column(items, spacing=10, scroll=ft.ScrollMode.AUTO, expand=True),
                ],
                spacing=14,
                expand=True,
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

    def _visible_files(self) -> list[FileAnalysis]:
        if self.result is None:
            return []
        items = list(self.result.file_analyses)
        query = (self.filter_field.value or "").strip().lower()
        if query:
            items = [item for item in items if query in item.metrics.path.lower()]
        status = self.status_dropdown.value or "all"
        if status != "all":
            items = [item for item in items if item.metrics.git_status.value == status]
        extension = self.extension_dropdown.value or "all"
        if extension != "all":
            items = [item for item in items if (item.metrics.extension or "(no ext)") == extension]
        if self.hotspot_only.value:
            items = [item for item in items if item.risk_score >= 30]

        sort_key = self.sort_dropdown.value or "score"
        if sort_key == "size":
            items.sort(key=lambda item: item.metrics.size_bytes, reverse=True)
        elif sort_key == "lines":
            items.sort(key=lambda item: item.metrics.line_count, reverse=True)
        elif sort_key == "extension":
            items.sort(key=lambda item: (item.metrics.extension, -item.risk_score))
        else:
            items.sort(key=lambda item: item.risk_score, reverse=True)
        return items

    def _file_item(self, analysis: FileAnalysis) -> ft.Control:
        color = theme.severity_color(analysis.severity)
        return ft.Container(
            bgcolor=theme.SURFACE_3,
            border_radius=14,
            border=ft.border.all(1, color if self.selected_path == analysis.metrics.path else theme.STROKE),
            padding=12,
            ink=True,
            on_click=lambda _, path=analysis.metrics.path: self.select_path(path, self.wide_mode),
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text(analysis.metrics.filename, size=15, weight=ft.FontWeight.W_700, color=theme.TEXT),
                                    ft.Text(shorten_path(analysis.metrics.path, 58), size=11, color=theme.MUTED),
                                ],
                                spacing=4,
                                expand=True,
                            ),
                            theme.badge(str(analysis.risk_score), color=color),
                        ],
                    ),
                    ft.Row(
                        [
                            theme.badge(format_bytes(analysis.metrics.size_bytes), muted=True),
                            theme.badge(f"{analysis.metrics.line_count} loc", muted=True),
                            theme.badge(analysis.metrics.git_status.value, color=self._status_color(analysis.metrics.git_status)),
                            *[theme.badge(item, muted=True) for item in analysis.badges[:3]],
                        ],
                        spacing=6,
                        wrap=True,
                        run_spacing=6,
                    ),
                ],
                spacing=10,
            ),
        )

    def _status_color(self, status: GitStatusKind) -> str:
        if status == GitStatusKind.MODIFIED:
            return theme.TEAL
        if status == GitStatusKind.DELETED:
            return theme.RED
        if status == GitStatusKind.UNTRACKED:
            return theme.AMBER
        return theme.BLUE

    def _selected_analysis(self) -> FileAnalysis | None:
        if not self.result or not self.selected_path:
            return None
        return next((item for item in self.result.file_analyses if item.metrics.path == self.selected_path), None)

    def _set_empty(self) -> None:
        self.root.content = theme.surface_card(ft.Text("File inventory appears after scanning.", size=13, color=theme.MUTED), expand=True)
