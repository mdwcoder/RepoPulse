from __future__ import annotations

from pathlib import Path


def shorten_path(path: str, max_length: int = 58) -> str:
    if len(path) <= max_length:
        return path
    parts = Path(path).parts
    if len(parts) <= 3:
        return f"...{path[-max_length + 3:]}"
    return f"{parts[0]}/…/{'/'.join(parts[-2:])}"


def relative_to_root(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def format_bytes(size_bytes: int) -> str:
    value = float(size_bytes)
    units = ["B", "KB", "MB", "GB"]
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{size_bytes} B"


def split_path(path: str) -> tuple[str, str]:
    pure = Path(path)
    return pure.name, pure.parent.as_posix() if pure.parent.as_posix() != "." else "/"
