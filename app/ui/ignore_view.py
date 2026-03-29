from __future__ import annotations

from collections.abc import Callable

import flet as ft

from app.ui import theme
from core.models import RepoScanResult


class IgnoreView:
    def __init__(
        self,
        on_add_pattern: Callable[[str], None] | None = None,
    ) -> None:
        self.on_add_pattern = on_add_pattern
        self.root = ft.Container(expand=True, padding=18)
        self._set_empty()

    def update(self, result: RepoScanResult | None) -> None:
        if result is None:
            self._set_empty()
            return

        suggestions = result.ignore_suggestions

        def _ignore_all(_):
            if self.on_add_pattern:
                for item in suggestions:
                    self.on_add_pattern(item.suggested_pattern)

        items = [
            theme.surface_card(
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Text(item.path, size=16, weight=ft.FontWeight.W_700, color=theme.TEXT),
                                        theme.badge(item.ignore_type.value, color=theme.TEAL if item.untracked else theme.AMBER),
                                    ],
                                    spacing=8,
                                    wrap=True,
                                    run_spacing=8,
                                ),
                                ft.Text(item.explanation, size=12, color=theme.MUTED),
                                ft.Row(
                                    [
                                        theme.badge(f"Suggested: {item.suggested_pattern}", muted=True),
                                        theme.badge("tracked" if item.tracked else "untracked", color=theme.RED if item.tracked else theme.TEAL),
                                    ],
                                    spacing=8,
                                    wrap=True,
                                    run_spacing=8,
                                ),
                            ],
                            spacing=8,
                            expand=True,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.ADD_CIRCLE_OUTLINE_ROUNDED,
                            icon_color=theme.TEAL,
                            tooltip=f"Add {item.suggested_pattern} to .gitignore",
                            on_click=lambda _, p=item.suggested_pattern: self.on_add_pattern(p) if self.on_add_pattern else None,
                        ),
                    ]
                )
            )
            for item in suggestions
        ] or [theme.surface_card(ft.Text("No obvious .gitignore gaps were detected.", size=13, color=theme.MUTED))]

        self.root.content = ft.Column(
            [
                ft.ResponsiveRow(
                    [
                        ft.Container(
                            col={"xs": 12, "md": 8},
                            content=ft.Column(
                                [
                                    ft.Row(
                                        [
                                            ft.Column(
                                                [
                                                    ft.Text("Ignore Suggestions", size=28, weight=ft.FontWeight.W_700, color=theme.TEXT),
                                                    ft.Text("Suggested ignore entries based on generated, local-only or temporary files found in this repository.", size=13, color=theme.MUTED),
                                                ],
                                                spacing=4,
                                                expand=True,
                                            ),
                                            ft.FilledButton(
                                                "Ignore All Detected",
                                                on_click=_ignore_all,
                                                style=ft.ButtonStyle(
                                                    bgcolor=theme.TEAL,
                                                    color=theme.BG,
                                                    shape=ft.RoundedRectangleBorder(radius=12),
                                                ),
                                            ),
                                        ],
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                        vertical_alignment=ft.CrossAxisAlignment.START,
                                    ),
                                    *items,
                                ],
                                spacing=14,
                            ),
                        ),
                        ft.Container(
                            col={"xs": 12, "md": 4},
                            content=theme.surface_card(
                                ft.Column(
                                    [
                                        ft.Text("Hygiene Snapshot", size=16, weight=ft.FontWeight.W_700, color=theme.TEXT),
                                        theme.metric_tile("Suggestions", str(len(suggestions)), theme.TEAL),
                                        theme.metric_tile("Tracked risk", str(sum(1 for item in suggestions if item.tracked)), theme.RED),
                                        theme.metric_tile("Untracked clutter", str(sum(1 for item in suggestions if item.untracked)), theme.AMBER),
                                    ],
                                    spacing=12,
                                ),
                                expand=True,
                            ),
                        ),
                    ],
                    spacing=14,
                    run_spacing=14,
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _set_empty(self) -> None:
        self.root.content = theme.surface_card(ft.Text("Ignore suggestions will appear after scanning.", size=13, color=theme.MUTED), expand=True)
