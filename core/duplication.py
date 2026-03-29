from __future__ import annotations

from collections import defaultdict

from core.models import ScannedFile
from core.utils.text_utils import normalize_line
from core.utils.thresholds import DUPLICATION_MAX_WINDOWS_PER_FILE, DUPLICATION_WINDOW_SIZE


class DuplicationDetector:
    def detect(self, files: list[ScannedFile]) -> dict[str, tuple[int, int]]:
        windows: dict[str, set[str]] = defaultdict(set)

        for scanned in files:
            if scanned.is_binary or not scanned.text:
                continue
            lines = [normalize_line(line) for line in scanned.text.splitlines()]
            lines = [line for line in lines if line]
            if len(lines) < DUPLICATION_WINDOW_SIZE:
                continue
            limit = min(len(lines) - DUPLICATION_WINDOW_SIZE + 1, DUPLICATION_MAX_WINDOWS_PER_FILE)
            for index in range(limit):
                window = lines[index : index + DUPLICATION_WINDOW_SIZE]
                block = "\n".join(window)
                if len(block) < 80:
                    continue
                windows[block].add(scanned.relative_path)

        hits: dict[str, tuple[int, int]] = defaultdict(lambda: (0, 0))
        for files_with_window in windows.values():
            if len(files_with_window) < 2:
                continue
            peer_count = len(files_with_window) - 1
            for path in files_with_window:
                current_hits, current_peers = hits[path]
                hits[path] = (current_hits + 1, max(current_peers, peer_count))
        return dict(hits)
