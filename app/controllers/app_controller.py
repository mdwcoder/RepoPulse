from __future__ import annotations

from pathlib import Path
import threading
from typing import TYPE_CHECKING

import flet as ft

from app.controllers.scan_controller import ScanController
from app.controllers.settings_controller import SettingsController
from core.enums import ScanState, ViewName
from core.models import AppSettings, RepoScanResult
from core.repository_validator import RepositoryValidator
from core.window_service import WindowService

if TYPE_CHECKING:
    from app.ui.main_window import MainWindow


class AppController:
    def __init__(
        self,
        page: ft.Page,
        settings_controller: SettingsController,
        scan_controller: ScanController,
        validator: RepositoryValidator,
        window_service: WindowService,
    ) -> None:
        self.page = page
        self.settings_controller = settings_controller
        self.scan_controller = scan_controller
        self.validator = validator
        self.window_service = window_service
        self.main_window: MainWindow | None = None
        self.current_repo: Path | None = None
        self.last_result: RepoScanResult | None = None
        self.scan_state = ScanState.IDLE
        self._scan_lock = threading.Lock()

    @property
    def settings(self) -> AppSettings:
        return self.settings_controller.settings

    def attach_window(self, main_window: "MainWindow") -> None:
        self.main_window = main_window

    def bootstrap(self) -> None:
        self.window_service.apply_base_window(self.page, self.settings)
        if self.settings.restore_last_repo and self.settings.last_repo_path:
            repo_path = Path(self.settings.last_repo_path)
            if repo_path.exists():
                self.current_repo = repo_path
                self.start_scan(repo_path)
        self._refresh_header()

    def open_repository_picker(self) -> None:
        if self.main_window:
            self.main_window.open_directory_picker()

    def handle_directory_selected(self, directory_path: str | None) -> None:
        if not directory_path:
            return
        target = Path(directory_path).expanduser()
        validation = self.validator.validate(target)
        if not validation.exists:
            self._show_error(validation.message or "This folder could not be opened.")
            return
        if validation.looks_like_git_repo:
            self.start_scan(target)
            return
        if self.main_window:
            self.main_window.show_non_git_dialog(target, validation.message or "This folder does not look like a Git repository.")

    def scan_non_git_folder(self, path: Path) -> None:
        self.start_scan(path)

    def refresh_scan(self) -> None:
        if self.current_repo:
            self.start_scan(self.current_repo)

    def start_scan(self, repo_path: Path) -> None:
        if not self._scan_lock.acquire(blocking=False):
            return
        self.current_repo = repo_path
        self.scan_state = ScanState.SCANNING
        if self.settings.restore_last_repo:
            self.settings.last_repo_path = repo_path.as_posix()
            self.settings_controller.save()
        self._refresh_header()
        if self.main_window:
            self.main_window.set_scanning(True)
        worker = threading.Thread(target=self._run_scan_worker, args=(repo_path,), daemon=True)
        worker.start()

    def _run_scan_worker(self, repo_path: Path) -> None:
        try:
            result = self.scan_controller.run_scan(repo_path, self.settings)
            self.last_result = result
            self.scan_state = ScanState.SCANNED
            if self.main_window:
                self.main_window.apply_scan_result(result)
        except Exception as exc:
            self.scan_state = ScanState.ERROR
            self._show_error(str(exc))
        finally:
            if self.main_window:
                self.main_window.set_scanning(False)
            self._refresh_header()
            self._scan_lock.release()

    def open_settings(self) -> None:
        if self.main_window:
            self.main_window.open_settings_dialog(self.settings)

    def save_settings(self, updated_settings: AppSettings) -> None:
        self.settings_controller.update(updated_settings)
        self.page.window.always_on_top = updated_settings.window.always_on_top
        self._refresh_header()
        if self.main_window:
            self.main_window.on_settings_updated(updated_settings)

    def reset_geometry(self) -> None:
        settings = self.window_service.reset_geometry(self.page, self.settings)
        self.settings_controller.update(settings)
        self.page.update()

    def toggle_pin(self) -> None:
        self.page.window.always_on_top = not bool(self.page.window.always_on_top)
        self.settings.window.always_on_top = bool(self.page.window.always_on_top)
        self.settings_controller.save()
        self._refresh_header()

    def minimize_window(self) -> None:
        self.page.window.minimized = True

    def open_detail(self, path: str, source_view: ViewName | None = None) -> None:
        if self.main_window:
            self.main_window.select_file(path, source_view)

    def switch_view(self, view_name: ViewName) -> None:
        if self.main_window:
            self.main_window.switch_view(view_name)

    def handle_window_change(self, *_args) -> None:
        if self.settings.remember_window_geometry:
            self.window_service.capture_geometry(self.page, self.settings)
            self.settings_controller.save()
        if self.main_window:
            self.main_window.handle_resize()

    def _refresh_header(self) -> None:
        if self.main_window:
            self.main_window.update_header_state(
                repo_path=self.current_repo.as_posix() if self.current_repo else None,
                scan_state=self.scan_state,
                always_on_top=bool(self.page.window.always_on_top),
                has_result=self.last_result is not None,
            )

    def _show_error(self, message: str) -> None:
        if self.main_window:
            self.main_window.show_error(message)
