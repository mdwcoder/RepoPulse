from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import flet as ft

from app.controllers.app_controller import AppController
from app.controllers.scan_controller import ScanController
from app.controllers.settings_controller import SettingsController
from app.ui import theme
from app.ui.file_detail_panel import FileDetailPanel
from app.ui.files_view import FilesView
from app.ui.git_view import GitView
from app.ui.header import HeaderBar
from app.ui.hotspots_view import HotspotsView
from app.ui.ignore_view import IgnoreView
from app.ui.overview_view import OverviewView
from app.ui.settings_dialog import SettingsDialog
from core.enums import FindingCategory, ScanState, ViewName
from core.models import AppSettings, FileAnalysis, RepoScanResult
from core.repository_validator import RepositoryValidator
from core.window_service import WindowService


class MainWindow:
    def __init__(self, page: ft.Page, controller: AppController) -> None:
        self.page = page
        self.controller = controller
        self.result: RepoScanResult | None = None
        self.wide_mode = False
        self._active_view_index = 0

        self.file_detail_panel = FileDetailPanel(on_open_file=self._open_file_in_editor)

        self.header = HeaderBar(
            on_open_repo=self.controller.open_repository_picker,
            on_refresh=self.controller.refresh_scan,
            on_toggle_pin=self.controller.toggle_pin,
            on_settings=self.controller.open_settings,
            on_minimize=self.controller.minimize_window,
            on_tab_change=self._on_tab_change,
        )
        self.overview_view = OverviewView(
            on_open_detail=self.controller.open_detail,
            on_jump_warning=self._handle_warning_click,
            on_view_log=lambda: self.switch_view(ViewName.GIT),
        )
        self.hotspots_view = HotspotsView(
            self.show_file_dialog,
            on_open_file=self._open_file_in_editor,
        )
        self.git_view = GitView(on_action_result=self._on_git_result)
        self.ignore_view = IgnoreView(on_add_pattern=self._add_ignore_pattern)
        self.files_view = FilesView(
            self.show_file_dialog,
            on_open_file=self._open_file_in_editor,
        )
        self.settings_dialog = SettingsDialog(
            page=self.page,
            on_save=self.controller.save_settings,
            on_reset_geometry=self.controller.reset_geometry,
        )

        self.progress = ft.ProgressBar(visible=False, color=theme.TEAL, bgcolor=theme.SURFACE_3)
        self.footer_last_scan = ft.Text("No scan yet", size=11, color=theme.MUTED)
        self.footer_files = ft.Text("0 files scanned", size=11, color=theme.MUTED)
        self.footer_repo_name = ft.Text("No repository selected", size=11, color=theme.MUTED)
        self.footer_state = ft.Text("idle", size=11, color=theme.MUTED)
        self.footer_version = ft.Text("V1.0.4", size=11, color=theme.MUTED)

        self.file_picker = ft.FilePicker()
        self.page.services.append(self.file_picker)

        self._views = [
            self.overview_view.root,
            self.hotspots_view.root,
            self.git_view.root,
            self.ignore_view.root,
            self.files_view.root,
        ]

        self.content_area = ft.Column(
            controls=[self.overview_view.root],
            expand=True,
            spacing=0,
        )

        self.root = ft.Container(
            expand=True,
            bgcolor=theme.BG,
            content=ft.Column(
                [
                    self.header.root,
                    self.progress,
                    self.content_area,
                    self._footer(),
                ],
                spacing=0,
                expand=True,
            ),
        )

    def build(self) -> None:
        theme.configure_page_theme(self.page)
        self.page.add(self.root)
        self.handle_resize()
        self.page.update()

    def open_directory_picker(self) -> None:
        self.page.run_task(self._pick_directory)

    async def _pick_directory(self) -> None:
        path = await self.file_picker.get_directory_path(dialog_title="Open Repository")
        self.controller.handle_directory_selected(path)

    def show_non_git_dialog(self, path: Path, message: str) -> None:
        dialog = ft.AlertDialog(
            modal=True,
            bgcolor=theme.SURFACE,
            title=ft.Text("Folder Warning", color=theme.TEXT),
            content=ft.Text(message, color=theme.MUTED),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self._close_dialog(dialog)),
                ft.FilledButton(
                    "Scan folder anyway",
                    on_click=lambda _: self._confirm_non_git(dialog, path),
                    style=ft.ButtonStyle(bgcolor=theme.TEAL, color=theme.BG),
                ),
            ],
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def set_scanning(self, scanning: bool) -> None:
        self.progress.visible = scanning
        self.progress.value = None if scanning else 0
        self.footer_state.value = "scanning..." if scanning else self.footer_state.value
        self.page.update()

    def apply_scan_result(self, result: RepoScanResult) -> None:
        self.result = result
        self.overview_view.update(result, self.wide_mode)
        self.hotspots_view.update(result, self.wide_mode)
        self.git_view.update(result)
        self.git_view.set_repo_path(result.repo_path)
        self.ignore_view.update(result)
        self.files_view.update(result, self.wide_mode)
        self.footer_last_scan.value = f"Last scan: {result.scanned_at.strftime('%H:%M:%S')}"
        self.footer_files.value = f"{result.total_files_scanned} files scanned"
        self.footer_repo_name.value = result.repo_path.name
        self.footer_state.value = result.scan_state.value
        self.page.update()

    def update_header_state(self, repo_path: str | None, scan_state: ScanState, always_on_top: bool, has_result: bool) -> None:
        self.header.update(repo_path, scan_state, always_on_top, has_result)
        self.footer_state.value = scan_state.value
        self.page.update()

    def open_settings_dialog(self, settings: AppSettings) -> None:
        self.settings_dialog.open(settings)

    def on_settings_updated(self, _settings: AppSettings) -> None:
        self.page.update()

    def show_error(self, message: str) -> None:
        self.page.snack_bar = ft.SnackBar(
            ft.Text(message, color=theme.TEXT),
            bgcolor=theme.RED,
        )
        self.page.snack_bar.open = True
        self.page.update()

    def switch_view(self, view_name: ViewName) -> None:
        view_to_index = {
            ViewName.OVERVIEW: 0,
            ViewName.HOTSPOTS: 1,
            ViewName.GIT: 2,
            ViewName.IGNORE: 3,
            ViewName.FILES: 4,
        }
        index = view_to_index[view_name]
        self._active_view_index = index
        self.header.set_active_tab(index)
        self.content_area.controls = [self._views[index]]
        self.page.update()

    def _on_tab_change(self, index: int) -> None:
        self._active_view_index = index
        self.content_area.controls = [self._views[index]]
        self.page.update()

    def select_file(self, path: str, source_view: ViewName | None = None) -> None:
        if source_view == ViewName.FILES:
            self.switch_view(ViewName.FILES)
            self.files_view.select_path(path, self.wide_mode)
        else:
            self.switch_view(ViewName.HOTSPOTS)
            self.hotspots_view.select_path(path, self.wide_mode)
            self.files_view.select_path(path, self.wide_mode)
        self.page.update()

    def handle_resize(self) -> None:
        width = self.page.window.width or self.page.width or 0
        self.wide_mode = bool(width and width >= 1180)
        self.overview_view.update(self.result, self.wide_mode)
        self.hotspots_view.update(self.result, self.wide_mode)
        self.files_view.update(self.result, self.wide_mode)
        self.page.update()

    def show_file_dialog(self, analysis: FileAnalysis) -> None:
        dialog = self.file_detail_panel.build_dialog(analysis)
        dialog.actions = [ft.TextButton("Close", on_click=lambda _: self._close_dialog(dialog))]
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def _on_git_result(self, success: bool, message: str) -> None:
        self.page.snack_bar = ft.SnackBar(
            ft.Text(message, color=theme.TEXT),
            bgcolor=theme.TEAL if success else theme.RED,
        )
        self.page.snack_bar.open = True
        self.page.update()

    def _add_ignore_pattern(self, pattern: str) -> None:
        if not self.result:
            return
        gitignore_path = self.result.repo_path / ".gitignore"
        try:
            existing = gitignore_path.read_text(encoding="utf-8") if gitignore_path.exists() else ""
            if pattern not in existing:
                with open(gitignore_path, "a") as f:
                    f.write(f"\n{pattern}\n")
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Added {pattern} to .gitignore"), bgcolor=theme.TEAL)
            self.page.snack_bar.open = True
            self.page.update()
        except OSError as e:
            self.show_error(str(e))

    def _open_file_in_editor(self, path: str) -> None:
        full_path = self.result.repo_path / path if self.result else Path(path)
        try:
            if sys.platform == "linux":
                subprocess.Popen(["xdg-open", str(full_path)])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(full_path)])
            else:
                import os
                os.startfile(str(full_path))
        except Exception as e:
            self.show_error(str(e))

    def _footer(self) -> ft.Control:
        return ft.Container(
            padding=ft.padding.symmetric(horizontal=18, vertical=12),
            bgcolor="#081426",
            border=ft.border.only(top=ft.BorderSide(1, theme.STROKE)),
            content=ft.Row(
                [
                    ft.Row(
                        [
                            self.footer_repo_name,
                            self.footer_last_scan,
                            self.footer_files,
                            self.footer_state,
                        ],
                        spacing=18,
                        wrap=True,
                        run_spacing=6,
                        expand=True,
                    ),
                    self.footer_version,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
        )

    def _handle_warning_click(self, finding) -> None:
        if finding.file_path:
            self.controller.open_detail(finding.file_path, ViewName.HOTSPOTS)
            return
        if finding.category == FindingCategory.GIT:
            self.switch_view(ViewName.GIT)
            return
        if finding.category == FindingCategory.HYGIENE:
            self.switch_view(ViewName.IGNORE)
            return
        self.switch_view(ViewName.HOTSPOTS)

    def _confirm_non_git(self, dialog: ft.AlertDialog, path: Path) -> None:
        self._close_dialog(dialog)
        self.controller.scan_non_git_folder(path)

    def _close_dialog(self, dialog: ft.AlertDialog) -> None:
        dialog.open = False
        self.page.update()


async def start(page: ft.Page) -> None:
    settings_controller = SettingsController()
    scan_controller = ScanController()
    controller = AppController(
        page=page,
        settings_controller=settings_controller,
        scan_controller=scan_controller,
        validator=RepositoryValidator(),
        window_service=WindowService(),
    )
    main_window = MainWindow(page, controller)
    controller.attach_window(main_window)

    page.on_resize = controller.handle_window_change
    page.window.on_event = controller.handle_window_change

    main_window.build()
    controller.bootstrap()
    page.window.visible = True
    page.update()


def run() -> None:
    ft.app(target=start, view=ft.AppView.FLET_APP_HIDDEN, assets_dir="assets")
