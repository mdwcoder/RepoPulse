from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import subprocess

from core.enums import GitStatusKind
from core.models import (
    GitDiffStats,
    GitFileChange,
    GitSnapshot,
    HeavyDeletionSummary,
    RecentCommit,
)
from core.utils.logger import get_logger
from core.utils.thresholds import DEFAULT_CHURN_LOG_LIMIT, DEFAULT_RECENT_COMMITS


class GitService:
    def __init__(self) -> None:
        self.logger = get_logger()

    def inspect(self, repo_path: Path, heavy_deletion_line_threshold: int, heavy_deletion_percent: float) -> GitSnapshot:
        if not (repo_path / ".git").exists():
            return GitSnapshot(is_repo=False)

        snapshot = GitSnapshot(is_repo=True)
        snapshot.branch = self._branch(repo_path)
        snapshot.modified, snapshot.deleted, snapshot.untracked = self._status(repo_path)
        snapshot.recent_commits = self._recent_commits(repo_path)
        snapshot.churn_by_path = self._churn(repo_path)
        snapshot.diff_by_path = self._diff_stats(repo_path)
        snapshot.tracked_files = self._tracked_files(repo_path)
        snapshot.heavy_deletion = self._heavy_deletion(
            snapshot,
            heavy_deletion_line_threshold,
            heavy_deletion_percent,
        )
        return snapshot

    def _run(self, repo_path: Path, *args: str) -> subprocess.CompletedProcess[str] | None:
        command = ["git", *args]
        self.logger.info("git %s", " ".join(args))
        try:
            return subprocess.run(
                command,
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as exc:
            self.logger.error("Git execution failed: %s", exc)
            return None

    def _branch(self, repo_path: Path) -> str:
        result = self._run(repo_path, "rev-parse", "--abbrev-ref", "HEAD")
        if not result or result.returncode != 0:
            return "Unknown"
        return result.stdout.strip() or "Detached HEAD"

    def _status(self, repo_path: Path) -> tuple[list[GitFileChange], list[GitFileChange], list[GitFileChange]]:
        result = self._run(repo_path, "status", "--porcelain=v1", "--untracked-files=all")
        modified: list[GitFileChange] = []
        deleted: list[GitFileChange] = []
        untracked: list[GitFileChange] = []
        if not result or result.returncode != 0:
            return modified, deleted, untracked

        for raw_line in result.stdout.splitlines():
            if len(raw_line) < 4:
                continue
            status = raw_line[:2]
            path = raw_line[3:].strip()
            if status == "??":
                untracked.append(GitFileChange(path=path, status=GitStatusKind.UNTRACKED))
                continue
            if "D" in status:
                deleted.append(GitFileChange(path=path, status=GitStatusKind.DELETED))
            else:
                modified.append(GitFileChange(path=path, status=GitStatusKind.MODIFIED))
        return modified, deleted, untracked

    def _recent_commits(self, repo_path: Path) -> list[RecentCommit]:
        if not self._has_head(repo_path):
            return []
        result = self._run(
            repo_path,
            "log",
            f"-n{DEFAULT_RECENT_COMMITS}",
            "--date=iso-strict",
            "--pretty=format:%h%x1f%s%x1f%cI",
        )
        commits: list[RecentCommit] = []
        if not result or result.returncode != 0:
            return commits

        for line in result.stdout.splitlines():
            parts = line.split("\x1f")
            if len(parts) != 3:
                continue
            committed_at = datetime.fromisoformat(parts[2].strip())
            commits.append(
                RecentCommit(
                    short_hash=parts[0].strip(),
                    message=parts[1].strip(),
                    committed_at=committed_at,
                )
            )
        return commits

    def _churn(self, repo_path: Path) -> dict[str, int]:
        if not self._has_head(repo_path):
            return {}
        result = self._run(
            repo_path,
            "log",
            f"-n{DEFAULT_CHURN_LOG_LIMIT}",
            "--pretty=format:",
            "--name-only",
            "--no-merges",
        )
        if not result or result.returncode != 0:
            return {}
        counts = Counter(path.strip() for path in result.stdout.splitlines() if path.strip())
        return dict(counts)

    def _diff_stats(self, repo_path: Path) -> dict[str, GitDiffStats]:
        if not self._has_head(repo_path):
            return {}
        result = self._run(repo_path, "diff", "--numstat", "HEAD")
        stats: dict[str, GitDiffStats] = {}
        if not result or result.returncode != 0:
            return stats
        for line in result.stdout.splitlines():
            parts = line.split("\t")
            if len(parts) != 3:
                continue
            added_raw, deleted_raw, path = parts
            try:
                added = 0 if added_raw == "-" else int(added_raw)
                deleted = 0 if deleted_raw == "-" else int(deleted_raw)
            except ValueError:
                continue
            stats[path] = GitDiffStats(path=path, lines_added=added, lines_deleted=deleted)
        return stats

    def _tracked_files(self, repo_path: Path) -> set[str]:
        result = self._run(repo_path, "ls-files")
        if not result or result.returncode != 0:
            return set()
        return {line.strip() for line in result.stdout.splitlines() if line.strip()}

    def _heavy_deletion(
        self,
        snapshot: GitSnapshot,
        threshold: int,
        deletion_percent_threshold: float,
    ) -> HeavyDeletionSummary:
        total_deleted = sum(item.lines_deleted for item in snapshot.diff_by_path.values())
        deleted_files_count = len(snapshot.deleted)
        worst_files = sorted(
            snapshot.diff_by_path.values(),
            key=lambda item: item.lines_deleted,
            reverse=True,
        )[:5]

        detected = total_deleted >= threshold or deleted_files_count >= 2
        if not detected:
            for item in worst_files:
                baseline = item.lines_added + item.lines_deleted
                if baseline and (item.lines_deleted / baseline) >= deletion_percent_threshold:
                    detected = True
                    break

        return HeavyDeletionSummary(
            detected=detected,
            total_lines_deleted=total_deleted,
            deleted_files_count=deleted_files_count,
            worst_files=worst_files,
        )

    def _has_head(self, repo_path: Path) -> bool:
        result = self._run(repo_path, "rev-parse", "--verify", "HEAD")
        return bool(result and result.returncode == 0)


def relative_time(value: datetime) -> str:
    now = datetime.now(timezone.utc)
    other = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    delta = now - other.astimezone(timezone.utc)
    minutes = int(delta.total_seconds() // 60)
    if minutes < 1:
        return "just now"
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    return f"{days}d ago"
