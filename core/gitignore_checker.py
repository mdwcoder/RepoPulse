from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.enums import IgnoreType
from core.models import GitSnapshot, IgnoreSuggestion


@dataclass(slots=True)
class IgnorePatternSpec:
    pattern: str
    ignore_type: IgnoreType
    reason: str


KNOWN_PATTERNS = [
    IgnorePatternSpec("node_modules/", IgnoreType.BUILD, "Package manager dependencies are usually not committed."),
    IgnorePatternSpec("dist/", IgnoreType.BUILD, "Compiled build outputs are usually generated."),
    IgnorePatternSpec("build/", IgnoreType.BUILD, "Build directories are often generated artifacts."),
    IgnorePatternSpec(".next/", IgnoreType.BUILD, "Next.js build output is local or CI-generated."),
    IgnorePatternSpec("coverage/", IgnoreType.GENERATED, "Coverage reports are usually generated locally or in CI."),
    IgnorePatternSpec(".dart_tool/", IgnoreType.CACHE, "Dart tooling caches are usually local-only."),
    IgnorePatternSpec(".venv/", IgnoreType.CACHE, "Python virtual environments should stay local."),
    IgnorePatternSpec("venv/", IgnoreType.CACHE, "Python virtual environments should stay local."),
    IgnorePatternSpec("__pycache__/", IgnoreType.CACHE, "Python cache directories are usually not committed."),
    IgnorePatternSpec(".DS_Store", IgnoreType.LOCAL, "macOS metadata files provide no repository value."),
    IgnorePatternSpec("*.log", IgnoreType.LOGS, "Runtime logs are usually temporary and environment-specific."),
    IgnorePatternSpec(".idea/", IgnoreType.LOCAL, "IDE settings are often user-specific."),
    IgnorePatternSpec(".vscode/", IgnoreType.LOCAL, "Editor workspace settings can be local-only."),
]


class GitignoreChecker:
    def inspect(self, repo_path: Path, git_snapshot: GitSnapshot) -> list[IgnoreSuggestion]:
        gitignore_text = self._read_gitignore(repo_path)
        suggestions: list[IgnoreSuggestion] = []

        current_paths = {
            child.relative_to(repo_path).as_posix()
            for child in repo_path.rglob("*")
            if child != repo_path and ".git" not in child.parts
        }

        tracked = git_snapshot.tracked_files
        untracked = {item.path for item in git_snapshot.untracked}

        for spec in KNOWN_PATTERNS:
            if spec.pattern in gitignore_text:
                continue

            matches = self._matches_pattern(spec.pattern, current_paths)
            if not matches:
                continue

            tracked_match = any(match in tracked for match in matches)
            untracked_match = any(match in untracked for match in matches)

            suggestions.append(
                IgnoreSuggestion(
                    path=sorted(matches)[0],
                    ignore_type=spec.ignore_type,
                    explanation=spec.reason,
                    suggested_pattern=spec.pattern,
                    tracked=tracked_match,
                    untracked=untracked_match,
                )
            )

        suggestions.sort(key=lambda item: (not item.tracked, not item.untracked, item.path))
        return suggestions

    def _read_gitignore(self, repo_path: Path) -> str:
        gitignore_path = repo_path / ".gitignore"
        try:
            return gitignore_path.read_text(encoding="utf-8")
        except OSError:
            return ""

    def _matches_pattern(self, pattern: str, current_paths: set[str]) -> set[str]:
        matches: set[str] = set()
        if pattern.endswith("/"):
            prefix = pattern.rstrip("/")
            matches = {path for path in current_paths if path == prefix or path.startswith(f"{prefix}/")}
        elif pattern.startswith("*."):
            suffix = pattern[1:]
            matches = {path for path in current_paths if path.endswith(suffix)}
        else:
            matches = {path for path in current_paths if path == pattern or path.endswith(f"/{pattern}")}
        return matches
