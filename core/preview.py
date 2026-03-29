from __future__ import annotations

from pathlib import Path


class PreviewService:
    def build_preview(self, path: Path, max_lines: int, size_cap_kb: int) -> str:
        try:
            if path.stat().st_size > size_cap_kb * 1024:
                return "Preview omitted because this file is larger than the preview cap."
        except OSError:
            return "Preview unavailable."

        try:
            with path.open("r", encoding="utf-8", errors="replace") as handle:
                lines: list[str] = []
                for index, line in enumerate(handle):
                    if index >= max_lines:
                        lines.append("…")
                        break
                    lines.append(line.rstrip("\n"))
                return "\n".join(lines) if lines else "File is empty."
        except OSError:
            return "Preview unavailable."
