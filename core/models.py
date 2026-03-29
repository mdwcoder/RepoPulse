from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from core.enums import FindingCategory, GitStatusKind, IgnoreType, ScanState, Severity


@dataclass(slots=True)
class ThresholdConfig:
    large_file_lines: int = 450
    huge_function_lines: int = 90
    max_nesting: int = 5
    high_churn: int = 7
    heavy_deletion_lines: int = 250
    heavy_deletion_percent: float = 0.35
    too_many_conditionals: int = 18
    too_many_imports: int = 20
    oversized_folder_lines: int = 5000
    many_untracked_files: int = 12


@dataclass(slots=True)
class WindowGeometry:
    width: int = 520
    height: int = 880
    left: int | None = None
    top: int | None = None
    always_on_top: bool = False


@dataclass(slots=True)
class AppSettings:
    remember_window_geometry: bool = True
    restore_last_repo: bool = True
    always_on_top_default: bool = False
    last_repo_path: str | None = None
    max_preview_lines: int = 80
    ignore_hidden_files: bool = True
    ignore_binary_files: bool = True
    file_size_cap_preview_kb: int = 200
    scan_ignored_directories: bool = False
    thresholds: ThresholdConfig = field(default_factory=ThresholdConfig)
    window: WindowGeometry = field(default_factory=WindowGeometry)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppSettings":
        thresholds = ThresholdConfig(**data.get("thresholds", {}))
        window = WindowGeometry(**data.get("window", {}))
        base = {k: v for k, v in data.items() if k not in {"thresholds", "window"}}
        return cls(**base, thresholds=thresholds, window=window)


@dataclass(slots=True)
class GitFileChange:
    path: str
    status: GitStatusKind
    lines_added: int = 0
    lines_deleted: int = 0


@dataclass(slots=True)
class RecentCommit:
    short_hash: str
    message: str
    committed_at: datetime


@dataclass(slots=True)
class GitDiffStats:
    path: str
    lines_added: int
    lines_deleted: int


@dataclass(slots=True)
class HeavyDeletionSummary:
    detected: bool = False
    total_lines_deleted: int = 0
    deleted_files_count: int = 0
    worst_files: list[GitDiffStats] = field(default_factory=list)


@dataclass(slots=True)
class GitSnapshot:
    is_repo: bool = False
    branch: str = "Not a Git repo"
    modified: list[GitFileChange] = field(default_factory=list)
    deleted: list[GitFileChange] = field(default_factory=list)
    untracked: list[GitFileChange] = field(default_factory=list)
    recent_commits: list[RecentCommit] = field(default_factory=list)
    churn_by_path: dict[str, int] = field(default_factory=dict)
    diff_by_path: dict[str, GitDiffStats] = field(default_factory=dict)
    tracked_files: set[str] = field(default_factory=set)
    heavy_deletion: HeavyDeletionSummary = field(default_factory=HeavyDeletionSummary)
    errors: list[str] = field(default_factory=list)

    @property
    def total_changes(self) -> int:
        return len(self.modified) + len(self.deleted) + len(self.untracked)


@dataclass(slots=True)
class ScannedFile:
    path: Path
    relative_path: str
    extension: str
    size_bytes: int
    line_count: int
    is_binary: bool
    text: str | None
    preview: str


@dataclass(slots=True)
class FileMetrics:
    path: str
    filename: str
    extension: str
    size_bytes: int
    line_count: int
    estimated_complexity: int
    max_nesting: int
    control_flow_count: int
    imports_count: int
    largest_block_lines: int
    is_binary: bool
    git_status: GitStatusKind
    git_churn: int
    lines_added: int
    lines_deleted: int
    preview: str
    duplicate_hits: int = 0
    duplicate_peer_count: int = 0


@dataclass(slots=True)
class FolderMetrics:
    path: str
    files_count: int = 0
    total_lines: int = 0
    hotspot_density: float = 0.0
    churn_accumulation: int = 0


@dataclass(slots=True)
class Finding:
    id: str
    severity: Severity
    category: FindingCategory
    title: str
    short_explanation: str
    score_impact: int
    file_path: str | None = None
    related_paths: list[str] = field(default_factory=list)


@dataclass(slots=True)
class IgnoreSuggestion:
    path: str
    ignore_type: IgnoreType
    explanation: str
    suggested_pattern: str
    tracked: bool = False
    untracked: bool = False


@dataclass(slots=True)
class FileAnalysis:
    metrics: FileMetrics
    findings: list[Finding] = field(default_factory=list)
    risk_score: int = 0
    severity: Severity = Severity.INFO
    badges: list[str] = field(default_factory=list)
    why_flagged: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ScanDataset:
    repo_path: Path
    scanned_files: list[ScannedFile]
    folder_metrics: dict[str, FolderMetrics]
    errors: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RepoScanResult:
    repo_path: Path
    repo_name: str
    scan_state: ScanState
    scanned_at: datetime
    health_score: int
    file_analyses: list[FileAnalysis]
    findings: list[Finding]
    warnings: list[Finding]
    hotspots: list[FileAnalysis]
    git_snapshot: GitSnapshot
    ignore_suggestions: list[IgnoreSuggestion]
    folder_metrics: list[FolderMetrics]
    total_files_scanned: int
    errors: list[str] = field(default_factory=list)
