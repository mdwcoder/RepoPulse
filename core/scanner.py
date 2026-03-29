from __future__ import annotations

from pathlib import Path

from core.models import FolderMetrics, ScanDataset, ScannedFile
from core.preview import PreviewService
from core.utils.file_utils import is_binary_file, should_skip_large_file
from core.utils.logger import get_logger
from core.utils.path_utils import relative_to_root


IGNORED_DIRS = {
    ".git",
    "node_modules",
    ".next",
    "dist",
    "build",
    "__pycache__",
    ".venv",
    "venv",
    ".dart_tool",
    ".idea",
}


class RepositoryScanner:
    def __init__(self, preview_service: PreviewService) -> None:
        self.preview_service = preview_service
        self.logger = get_logger()

    def scan(self, repo_path: Path, settings) -> ScanDataset:
        scanned_files: list[ScannedFile] = []
        folder_metrics: dict[str, FolderMetrics] = {}
        errors: list[str] = []

        for path in repo_path.rglob("*"):
            if path.is_dir():
                continue
            if not settings.scan_ignored_directories and any(part in IGNORED_DIRS for part in path.parts):
                continue
            if settings.ignore_hidden_files and self._is_hidden(path, repo_path):
                continue
            try:
                relative_path = relative_to_root(path, repo_path)
                size_bytes = path.stat().st_size
                binary = is_binary_file(path)
                if settings.ignore_binary_files and binary:
                    continue
                if should_skip_large_file(path):
                    preview = "Preview omitted because this file exceeds the scan cap."
                    line_count = self._count_lines(path) if not binary else 0
                    scanned_files.append(
                        ScannedFile(
                            path=path,
                            relative_path=relative_path,
                            extension=path.suffix.lower(),
                            size_bytes=size_bytes,
                            line_count=line_count,
                            is_binary=binary,
                            text=None,
                            preview=preview,
                        )
                    )
                    continue

                text = None if binary else path.read_text(encoding="utf-8", errors="replace")
                preview = self.preview_service.build_preview(
                    path,
                    max_lines=settings.max_preview_lines,
                    size_cap_kb=settings.file_size_cap_preview_kb,
                )
                line_count = text.count("\n") + 1 if text else 0
                scanned_files.append(
                    ScannedFile(
                        path=path,
                        relative_path=relative_path,
                        extension=path.suffix.lower(),
                        size_bytes=size_bytes,
                        line_count=line_count,
                        is_binary=binary,
                        text=text,
                        preview=preview,
                    )
                )
            except OSError as exc:
                self.logger.error("Failed to scan %s: %s", path, exc)
                errors.append(f"Could not read {path.name}.")

        return ScanDataset(
            repo_path=repo_path,
            scanned_files=scanned_files,
            folder_metrics=folder_metrics,
            errors=errors,
        )

    def _is_hidden(self, path: Path, repo_path: Path) -> bool:
        parts = path.relative_to(repo_path).parts
        return any(part.startswith(".") and part != ".gitignore" for part in parts)

    def _count_lines(self, path: Path) -> int:
        try:
            with path.open("r", encoding="utf-8", errors="replace") as handle:
                return sum(1 for _ in handle)
        except OSError:
            return 0
