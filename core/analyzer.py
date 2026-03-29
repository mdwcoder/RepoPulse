from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path

from core.enums import FindingCategory, GitStatusKind, ScanState, Severity
from core.models import (
    FileAnalysis,
    FileMetrics,
    Finding,
    FolderMetrics,
    GitSnapshot,
    RepoScanResult,
    ScanDataset,
)
from core.scoring import ScoringService
from core.utils.text_utils import count_imports, estimate_complexity, estimate_largest_block, max_nesting_depth


class RepositoryAnalyzer:
    def __init__(self, scoring: ScoringService) -> None:
        self.scoring = scoring

    def analyze(
        self,
        dataset: ScanDataset,
        git_snapshot: GitSnapshot,
        ignore_suggestions_count: int,
        duplication_hits: dict[str, tuple[int, int]],
        settings,
    ) -> RepoScanResult:
        file_analyses: list[FileAnalysis] = []
        findings: list[Finding] = []
        folder_map: dict[str, FolderMetrics] = defaultdict(FolderMetrics)

        git_status_map = {item.path: GitStatusKind.MODIFIED for item in git_snapshot.modified}
        git_status_map.update({item.path: GitStatusKind.DELETED for item in git_snapshot.deleted})
        git_status_map.update({item.path: GitStatusKind.UNTRACKED for item in git_snapshot.untracked})

        for scanned_file in dataset.scanned_files:
            metrics = self._build_metrics(
                dataset.repo_path,
                scanned_file,
                git_status_map,
                git_snapshot,
                duplication_hits,
            )
            analysis = self._analyze_file(metrics, settings.thresholds)
            file_analyses.append(analysis)
            findings.extend(analysis.findings)
            self._accumulate_folder(folder_map, analysis)

        repo_findings = self._repo_findings(git_snapshot, settings.thresholds, ignore_suggestions_count)
        findings.extend(repo_findings)

        file_scores = [analysis.risk_score for analysis in file_analyses]
        hotspots = sorted(
            [analysis for analysis in file_analyses if analysis.risk_score >= 30],
            key=lambda item: item.risk_score,
            reverse=True,
        )

        for folder_metrics in folder_map.values():
            if folder_metrics.files_count:
                folder_metrics.hotspot_density /= folder_metrics.files_count

        health_score = self.scoring.repo_health_score(file_scores, findings, len(hotspots))
        warnings = [item for item in findings if item.severity in {Severity.WATCH, Severity.IMPORTANT, Severity.HIGH}]
        warnings.sort(key=lambda item: item.score_impact, reverse=True)

        return RepoScanResult(
            repo_path=dataset.repo_path,
            repo_name=dataset.repo_path.name,
            scan_state=ScanState.SCANNED,
            scanned_at=datetime.now(),
            health_score=health_score,
            file_analyses=sorted(file_analyses, key=lambda item: item.risk_score, reverse=True),
            findings=findings,
            warnings=warnings[:8],
            hotspots=hotspots[:20],
            git_snapshot=git_snapshot,
            ignore_suggestions=[],
            folder_metrics=sorted(folder_map.values(), key=lambda item: item.total_lines, reverse=True),
            total_files_scanned=len(dataset.scanned_files),
            errors=dataset.errors + git_snapshot.errors,
        )

    def _build_metrics(
        self,
        repo_path: Path,
        scanned_file,
        git_status_map: dict[str, GitStatusKind],
        git_snapshot: GitSnapshot,
        duplication_hits: dict[str, tuple[int, int]],
    ) -> FileMetrics:
        text = scanned_file.text or ""
        lines = text.splitlines()
        duplicate_hits, duplicate_peers = duplication_hits.get(scanned_file.relative_path, (0, 0))
        diff_stats = git_snapshot.diff_by_path.get(scanned_file.relative_path)
        git_status = git_status_map.get(scanned_file.relative_path, GitStatusKind.CLEAN)

        return FileMetrics(
            path=scanned_file.relative_path,
            filename=Path(scanned_file.relative_path).name,
            extension=scanned_file.extension,
            size_bytes=scanned_file.size_bytes,
            line_count=scanned_file.line_count,
            estimated_complexity=estimate_complexity(text),
            max_nesting=max_nesting_depth(lines),
            control_flow_count=estimate_complexity(text),
            imports_count=count_imports(lines),
            largest_block_lines=estimate_largest_block(lines),
            is_binary=scanned_file.is_binary,
            git_status=git_status,
            git_churn=git_snapshot.churn_by_path.get(scanned_file.relative_path, 0),
            lines_added=diff_stats.lines_added if diff_stats else 0,
            lines_deleted=diff_stats.lines_deleted if diff_stats else 0,
            preview=scanned_file.preview,
            duplicate_hits=duplicate_hits,
            duplicate_peer_count=duplicate_peers,
        )

    def _analyze_file(self, metrics: FileMetrics, thresholds) -> FileAnalysis:
        findings: list[Finding] = []
        badges: list[str] = []
        reasons: list[str] = []

        def add_finding(
            identifier: str,
            severity: Severity,
            category: FindingCategory,
            title: str,
            explanation: str,
            score_impact: int,
            badge: str,
        ) -> None:
            findings.append(
                Finding(
                    id=identifier,
                    severity=severity,
                    category=category,
                    title=title,
                    short_explanation=explanation,
                    score_impact=score_impact,
                    file_path=metrics.path,
                )
            )
            badges.append(badge)
            reasons.append(explanation)

        if metrics.line_count >= thresholds.large_file_lines:
            add_finding(
                "large_file",
                Severity.IMPORTANT,
                FindingCategory.STRUCTURAL,
                "Large file",
                "This file is much larger than usual and may be harder to maintain.",
                8,
                "large",
            )
        if metrics.largest_block_lines >= thresholds.huge_function_lines:
            add_finding(
                "huge_function_estimate",
                Severity.WATCH,
                FindingCategory.STRUCTURAL,
                "Huge function estimate",
                "One function-like block looks unusually long and may hide too much logic.",
                6,
                "huge-fn",
            )
        if metrics.max_nesting >= thresholds.max_nesting:
            add_finding(
                "deep_nesting",
                Severity.IMPORTANT,
                FindingCategory.STRUCTURAL,
                "Deep nesting",
                "Nested branches are deeper than expected and may be harder to reason about.",
                8,
                "deep",
            )
        if metrics.control_flow_count >= thresholds.too_many_conditionals:
            add_finding(
                "too_many_conditionals",
                Severity.WATCH,
                FindingCategory.STRUCTURAL,
                "Too many conditionals",
                "This file contains a high number of control-flow branches.",
                5,
                "logic",
            )
        if metrics.imports_count >= thresholds.too_many_imports:
            add_finding(
                "too_many_imports",
                Severity.WATCH,
                FindingCategory.STRUCTURAL,
                "Too many imports",
                "A high import count can indicate wide coupling or too many responsibilities.",
                5,
                "imports",
            )
        if metrics.git_churn >= thresholds.high_churn:
            add_finding(
                "high_churn",
                Severity.IMPORTANT,
                FindingCategory.GIT,
                "High churn hotspot",
                "This file changes often and may contain unstable logic.",
                9,
                "churn",
            )
        if metrics.git_status in {GitStatusKind.MODIFIED, GitStatusKind.DELETED} and (
            metrics.lines_added + metrics.lines_deleted >= 80
        ):
            add_finding(
                "many_uncommitted_changes",
                Severity.WATCH,
                FindingCategory.GIT,
                "Many uncommitted changes",
                "A large amount of local change is concentrated in this file.",
                6,
                "dirty",
            )
        if metrics.lines_deleted >= thresholds.heavy_deletion_lines:
            add_finding(
                "heavy_deletion",
                Severity.HIGH,
                FindingCategory.GIT,
                "Heavy deletion",
                "A large amount of content has been deleted since the last commit.",
                10,
                "deleted",
            )
        if metrics.duplicate_hits >= 2:
            add_finding(
                "duplication_risk",
                Severity.WATCH,
                FindingCategory.DUPLICATION,
                "Possible duplication block",
                "This file shares repeated blocks with other files and may contain duplicated logic.",
                7,
                "duplicate",
            )
        if metrics.git_status == GitStatusKind.UNTRACKED and metrics.size_bytes >= 120_000:
            add_finding(
                "untracked_risk",
                Severity.WATCH,
                FindingCategory.GIT,
                "Untracked risk",
                "This untracked file is large enough to deserve review before it spreads in the repo.",
                6,
                "untracked-risk",
            )

        risk_score = self.scoring.file_risk_score(metrics, findings)
        severity = self.scoring.severity_for_score(risk_score)

        return FileAnalysis(
            metrics=metrics,
            findings=findings,
            risk_score=risk_score,
            severity=severity,
            badges=list(dict.fromkeys(badges)),
            why_flagged=reasons,
        )

    def _repo_findings(self, git_snapshot: GitSnapshot, thresholds, ignore_suggestions_count: int) -> list[Finding]:
        findings: list[Finding] = []

        if git_snapshot.heavy_deletion.detected:
            findings.append(
                Finding(
                    id="repo_heavy_deletion",
                    severity=Severity.HIGH,
                    category=FindingCategory.GIT,
                    title="Heavy deletion detected",
                    short_explanation="Recent local changes remove an unusually high amount of code.",
                    score_impact=10,
                    related_paths=[item.path for item in git_snapshot.heavy_deletion.worst_files],
                )
            )
        if len(git_snapshot.untracked) >= thresholds.many_untracked_files:
            findings.append(
                Finding(
                    id="many_untracked_files",
                    severity=Severity.WATCH,
                    category=FindingCategory.GIT,
                    title="Many untracked files",
                    short_explanation="A large group of untracked files may indicate local clutter or missing ignore rules.",
                    score_impact=6,
                )
            )
        if ignore_suggestions_count:
            findings.append(
                Finding(
                    id="ignore_suggestions",
                    severity=Severity.WATCH,
                    category=FindingCategory.HYGIENE,
                    title="Suggested ignore entries",
                    short_explanation="Generated or temporary files may be missing from .gitignore.",
                    score_impact=min(ignore_suggestions_count, 6),
                )
            )
        return findings

    def _accumulate_folder(self, folder_map: dict[str, FolderMetrics], analysis: FileAnalysis) -> None:
        path = Path(analysis.metrics.path).parent.as_posix()
        key = path if path != "." else "/"
        if key not in folder_map:
            folder_map[key] = FolderMetrics(path=key)
        folder = folder_map[key]
        folder.files_count += 1
        folder.total_lines += analysis.metrics.line_count
        folder.hotspot_density += analysis.risk_score / 100
        folder.churn_accumulation += analysis.metrics.git_churn
