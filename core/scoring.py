from __future__ import annotations

from core.enums import Severity
from core.models import FileMetrics, Finding


class ScoringService:
    def file_risk_score(self, metrics: FileMetrics, findings: list[Finding]) -> int:
        score = 0
        score += min(metrics.line_count / 8, 15)
        score += min(metrics.size_bytes / 32_000, 10)
        score += min(metrics.estimated_complexity * 1.8, 18)
        score += min(metrics.max_nesting * 4, 16)
        score += min(metrics.git_churn * 2.5, 15)
        score += min(metrics.lines_deleted / 12, 12)
        score += min(metrics.duplicate_hits * 4, 10)
        score += sum(finding.score_impact for finding in findings)
        return max(0, min(int(score), 100))

    def repo_health_score(self, file_scores: list[int], findings: list[Finding], hotspots_count: int) -> int:
        if not file_scores:
            base = 90
        else:
            average_risk = sum(file_scores) / len(file_scores)
            base = 100 - int(average_risk * 0.75)
        penalties = hotspots_count * 2 + sum(self._severity_penalty(item.severity) for item in findings)
        return max(0, min(100, base - penalties))

    def severity_for_score(self, score: int) -> Severity:
        if score >= 75:
            return Severity.HIGH
        if score >= 50:
            return Severity.IMPORTANT
        if score >= 25:
            return Severity.WATCH
        return Severity.INFO

    def _severity_penalty(self, severity: Severity) -> int:
        if severity == Severity.HIGH:
            return 3
        if severity == Severity.IMPORTANT:
            return 2
        if severity == Severity.WATCH:
            return 1
        return 0
