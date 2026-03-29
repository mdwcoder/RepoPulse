from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class RepositoryValidationResult:
    path: Path
    exists: bool
    looks_like_git_repo: bool
    message: str | None = None


class RepositoryValidator:
    def validate(self, path: Path) -> RepositoryValidationResult:
        if not path.exists() or not path.is_dir():
            return RepositoryValidationResult(
                path=path,
                exists=False,
                looks_like_git_repo=False,
                message="This folder could not be accessed.",
            )

        looks_like_git_repo = (path / ".git").exists()
        message = None
        if not looks_like_git_repo:
            message = "This folder does not look like a Git repository."

        return RepositoryValidationResult(
            path=path,
            exists=True,
            looks_like_git_repo=looks_like_git_repo,
            message=message,
        )
