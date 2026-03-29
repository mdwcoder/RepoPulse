from __future__ import annotations

import subprocess
from collections.abc import Callable
from pathlib import Path

import flet as ft

from app.ui import theme
from core.git_service import relative_time
from core.models import RepoScanResult


class GitView:
    def __init__(
        self,
        on_action_result: Callable[[bool, str], None] | None = None,
    ) -> None:
        self.on_action_result = on_action_result
        self.result: RepoScanResult | None = None
        self.repo_path: Path | None = None
        self.root = ft.Container(expand=True, padding=18)
        self._set_empty()

    def set_repo_path(self, path: Path) -> None:
        self.repo_path = path

    def update(self, result: RepoScanResult | None) -> None:
        self.result = result
        if result is None:
            self._set_empty()
            return

        snapshot = result.git_snapshot

        summary = ft.ResponsiveRow(
            [
                ft.Container(col={"xs": 6, "md": 3}, content=theme.metric_tile("Modified", str(len(snapshot.modified)), theme.TEAL)),
                ft.Container(col={"xs": 6, "md": 3}, content=theme.metric_tile("Deleted", str(len(snapshot.deleted)), theme.RED)),
                ft.Container(col={"xs": 6, "md": 3}, content=theme.metric_tile("Untracked", str(len(snapshot.untracked)), theme.AMBER)),
                ft.Container(col={"xs": 6, "md": 3}, content=theme.metric_tile("Recent commits", str(len(snapshot.recent_commits)), theme.BLUE)),
            ],
            spacing=12,
            run_spacing=12,
        )

        heavy = theme.surface_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text("Heavy deletion detected" if snapshot.heavy_deletion.detected else "Deletion profile", size=16, weight=ft.FontWeight.W_700, color=theme.TEXT),
                            theme.badge(
                                "high risk" if snapshot.heavy_deletion.detected else "stable",
                                color=theme.RED if snapshot.heavy_deletion.detected else theme.TEAL,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Text(
                        f"Lines deleted: {snapshot.heavy_deletion.total_lines_deleted}  |  Files deleted: {snapshot.heavy_deletion.deleted_files_count}",
                        size=12,
                        color=theme.MUTED,
                    ),
                    ft.Column(
                        [ft.Text(item.path, size=12, color=theme.TEXT) for item in snapshot.heavy_deletion.worst_files[:5]]
                        or [ft.Text("No significant deletions detected.", size=12, color=theme.MUTED)],
                        spacing=6,
                    ),
                ],
                spacing=10,
            )
        )

        commits = [
            ft.Container(
                bgcolor=theme.SURFACE_3,
                border_radius=14,
                padding=12,
                content=ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text(commit.message, size=14, weight=ft.FontWeight.W_600, color=theme.TEXT),
                                ft.Row(
                                    [
                                        theme.badge(commit.short_hash, muted=True),
                                        ft.Text(relative_time(commit.committed_at), size=11, color=theme.MUTED),
                                    ],
                                    spacing=8,
                                ),
                            ],
                            spacing=6,
                            expand=True,
                        ),
                    ]
                ),
            )
            for commit in snapshot.recent_commits
        ] or [ft.Text("No recent commits available.", size=12, color=theme.MUTED)]

        left_content = ft.Column(
            [
                theme.surface_card(
                    ft.Column(
                        [
                            ft.Text("Git Status", size=26, weight=ft.FontWeight.W_700, color=theme.TEXT),
                            ft.Text(f"Branch: {snapshot.branch}", size=12, color=theme.MUTED),
                            summary,
                        ],
                        spacing=14,
                    )
                ),
                ft.ResponsiveRow(
                    [
                        ft.Container(col={"xs": 12, "md": 8}, content=self._changes_card(snapshot)),
                        ft.Container(col={"xs": 12, "md": 4}, content=heavy),
                    ],
                    spacing=14,
                    run_spacing=14,
                ),
                theme.surface_card(ft.Column([theme.title("Recent Commits"), *commits], spacing=10)),
            ],
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        right_panel = self._build_stage_panel(snapshot)

        self.root.content = ft.Row(
            [
                ft.Container(expand=2, content=left_content),
                ft.Container(expand=1, content=right_panel),
            ],
            spacing=14,
            expand=True,
        )

    def _build_stage_panel(self, snapshot) -> ft.Control:
        total_files = len(snapshot.modified) + len(snapshot.deleted)

        commit_msg_field = ft.TextField(
            hint_text="Commit message (Required)",
            multiline=False,
            border_color=theme.STROKE,
            bgcolor=theme.SURFACE_3,
            color=theme.TEXT,
            cursor_color=theme.TEAL,
        )

        stage_all = ft.Checkbox(
            label=f"Stage all {total_files} files",
            value=True,
            active_color=theme.TEAL,
        )

        def _do_commit(_):
            msg = (commit_msg_field.value or "").strip()
            if not msg:
                if self.on_action_result:
                    self.on_action_result(False, "Commit message is required.")
                return
            if not self.repo_path:
                if self.on_action_result:
                    self.on_action_result(False, "No repository path set.")
                return
            try:
                proc = subprocess.run(
                    ["git", "commit", "-am", msg],
                    cwd=str(self.repo_path),
                    capture_output=True,
                    text=True,
                )
                success = proc.returncode == 0
                out_msg = proc.stdout.strip() or proc.stderr.strip() or ("Committed successfully." if success else "Commit failed.")
                if self.on_action_result:
                    self.on_action_result(success, out_msg)
            except Exception as e:
                if self.on_action_result:
                    self.on_action_result(False, str(e))

        commit_btn = ft.FilledButton(
            "Commit to Main",
            on_click=_do_commit,
            style=ft.ButtonStyle(
                bgcolor=theme.TEAL,
                color=theme.BG,
                shape=ft.RoundedRectangleBorder(radius=12),
            ),
            expand=True,
        )

        alerts: list[ft.Control] = []
        if snapshot.heavy_deletion.detected:
            alerts.append(
                ft.Container(
                    bgcolor=theme.SURFACE_3,
                    border_radius=10,
                    border=ft.border.only(left=ft.BorderSide(4, theme.RED)),
                    padding=ft.padding.symmetric(horizontal=12, vertical=10),
                    content=ft.Text("Heavy deletion detected", size=12, color=theme.RED, weight=ft.FontWeight.W_600),
                )
            )
        if len(snapshot.untracked) > 5:
            alerts.append(
                ft.Container(
                    bgcolor=theme.SURFACE_3,
                    border_radius=10,
                    border=ft.border.only(left=ft.BorderSide(4, theme.AMBER)),
                    padding=ft.padding.symmetric(horizontal=12, vertical=10),
                    content=ft.Text("Log pollution potential", size=12, color=theme.AMBER, weight=ft.FontWeight.W_600),
                )
            )
        alerts.append(
            ft.Container(
                bgcolor=theme.SURFACE_3,
                border_radius=10,
                border=ft.border.only(left=ft.BorderSide(4, theme.BLUE)),
                padding=ft.padding.symmetric(horizontal=12, vertical=10),
                content=ft.Text("Remote status unknown", size=12, color=theme.BLUE, weight=ft.FontWeight.W_600),
            )
        )

        return theme.surface_card(
            ft.Column(
                [
                    ft.Text("Stage Changes", size=17, weight=ft.FontWeight.W_700, color=theme.TEXT),
                    stage_all,
                    commit_msg_field,
                    ft.Container(content=commit_btn),
                    ft.Text("Press Ctrl + Enter to commit fast", size=10, color=theme.MUTED),
                    ft.Divider(color=theme.STROKE),
                    ft.Text("ALERTS & INSIGHTS", size=11, color=theme.MUTED, weight=ft.FontWeight.W_600),
                    *alerts,
                ],
                spacing=12,
                scroll=ft.ScrollMode.AUTO,
            ),
            expand=True,
        )

    def _changes_card(self, snapshot) -> ft.Control:
        def section(title: str, items, color: str) -> ft.Control:
            rows = [
                ft.Text(change.path, size=12, color=theme.TEXT)
                for change in items[:10]
            ] or [ft.Text("None", size=12, color=theme.MUTED)]
            return theme.subtle_card(
                ft.Column(
                    [
                        ft.Row([ft.Text(title, size=15, weight=ft.FontWeight.W_700, color=color), theme.badge(str(len(items)), color=color)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        *rows,
                    ],
                    spacing=8,
                ),
                expand=True,
            )

        return theme.surface_card(
            ft.Column(
                [
                    theme.title("Current Changes"),
                    ft.ResponsiveRow(
                        [
                            ft.Container(col={"xs": 12, "md": 4}, content=section("Modified", snapshot.modified, theme.TEAL)),
                            ft.Container(col={"xs": 12, "md": 4}, content=section("Deleted", snapshot.deleted, theme.RED)),
                            ft.Container(col={"xs": 12, "md": 4}, content=section("Untracked", snapshot.untracked, theme.AMBER)),
                        ],
                        spacing=12,
                        run_spacing=12,
                    ),
                ],
                spacing=12,
            )
        )

    def _set_empty(self) -> None:
        self.root.content = theme.surface_card(ft.Text("Git data will appear after scanning a repository.", size=13, color=theme.MUTED), expand=True)
