from __future__ import annotations

from pathlib import Path

from core.utils.thresholds import MAX_FILE_SCAN_BYTES


TEXT_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".json",
    ".md",
    ".txt",
    ".yaml",
    ".yml",
    ".toml",
    ".sh",
    ".bash",
    ".zsh",
    ".dart",
    ".java",
    ".kt",
    ".go",
    ".rb",
    ".rs",
    ".c",
    ".cc",
    ".cpp",
    ".h",
    ".hpp",
    ".css",
    ".scss",
    ".html",
    ".xml",
    ".swift",
    ".php",
    ".sql",
}


def is_binary_file(path: Path) -> bool:
    if path.suffix.lower() in TEXT_EXTENSIONS:
        return False
    try:
        with path.open("rb") as handle:
            chunk = handle.read(1024)
    except OSError:
        return True
    if not chunk:
        return False
    return b"\x00" in chunk


def should_skip_large_file(path: Path) -> bool:
    try:
        return path.stat().st_size > MAX_FILE_SCAN_BYTES
    except OSError:
        return True
