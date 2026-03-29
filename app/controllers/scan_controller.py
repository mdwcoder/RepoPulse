from __future__ import annotations

from pathlib import Path

from core.analyzer import RepositoryAnalyzer
from core.duplication import DuplicationDetector
from core.git_service import GitService
from core.gitignore_checker import GitignoreChecker
from core.preview import PreviewService
from core.scanner import RepositoryScanner
from core.scoring import ScoringService


class ScanController:
    def __init__(self) -> None:
        self.scoring = ScoringService()
        self.preview = PreviewService()
        self.git_service = GitService()
        self.scanner = RepositoryScanner(self.preview)
        self.duplication = DuplicationDetector()
        self.gitignore_checker = GitignoreChecker()
        self.analyzer = RepositoryAnalyzer(self.scoring)

    def run_scan(self, repo_path: Path, settings):
        git_snapshot = self.git_service.inspect(
            repo_path,
            heavy_deletion_line_threshold=settings.thresholds.heavy_deletion_lines,
            heavy_deletion_percent=settings.thresholds.heavy_deletion_percent,
        )
        dataset = self.scanner.scan(repo_path, settings)
        duplication_hits = self.duplication.detect(dataset.scanned_files)
        ignore_suggestions = self.gitignore_checker.inspect(repo_path, git_snapshot)
        result = self.analyzer.analyze(
            dataset,
            git_snapshot,
            ignore_suggestions_count=len(ignore_suggestions),
            duplication_hits=duplication_hits,
            settings=settings,
        )
        result.ignore_suggestions = ignore_suggestions
        return result
