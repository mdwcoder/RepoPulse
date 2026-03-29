from __future__ import annotations

import flet as ft

from core.enums import ScanState, Severity


BG = "#06111F"
SURFACE = "#0B1730"
SURFACE_2 = "#0F2040"
SURFACE_3 = "#0B1426"
STROKE = "#143059"
TEXT = "#EEF4FF"
MUTED = "#7E93BC"
TEAL = "#14D6A6"
AMBER = "#F6B94C"
ORANGE = "#FF9D48"
RED = "#FF6B7D"
BLUE = "#7E8EFF"


def configure_page_theme(page: ft.Page) -> None:
    page.bgcolor = BG
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=TEAL,
            secondary=AMBER,
            surface=SURFACE,
            error=RED,
            on_primary=BG,
            on_secondary=BG,
            on_surface=TEXT,
            on_error=TEXT,
            outline=STROKE,
            surface_container=SURFACE_2,
            surface_container_low=SURFACE_3,
        ),
        font_family="Sans",
        scaffold_bgcolor=BG,
        card_bgcolor=SURFACE,
    )


def severity_color(severity: Severity) -> str:
    if severity == Severity.HIGH:
        return RED
    if severity == Severity.IMPORTANT:
        return ORANGE
    if severity == Severity.WATCH:
        return AMBER
    return TEAL


def scan_state_color(state: ScanState) -> str:
    if state == ScanState.SCANNING:
        return BLUE
    if state == ScanState.SCANNED:
        return TEAL
    if state == ScanState.ERROR:
        return RED
    if state == ScanState.STALE:
        return AMBER
    return MUTED


def badge(label: str, color: str | None = None, muted: bool = False) -> ft.Control:
    background = color if color else (SURFACE_2 if not muted else SURFACE_3)
    return ft.Container(
        padding=ft.padding.symmetric(horizontal=8, vertical=4),
        bgcolor=background,
        border_radius=8,
        content=ft.Text(
            label.upper(),
            size=10,
            weight=ft.FontWeight.W_600,
            color=TEXT if color else (MUTED if muted else TEXT),
        ),
    )


def surface_card(content: ft.Control, padding: int = 16, expand: bool | int = False) -> ft.Container:
    return ft.Container(
        expand=expand,
        bgcolor=SURFACE,
        border=ft.border.all(1, STROKE),
        border_radius=18,
        padding=padding,
        content=content,
    )


def subtle_card(content: ft.Control, padding: int = 14, expand: bool | int = False) -> ft.Container:
    return ft.Container(
        expand=expand,
        bgcolor=SURFACE_3,
        border=ft.border.all(1, "#0D2344"),
        border_radius=16,
        padding=padding,
        content=content,
    )


def title(text: str, subtitle: str | None = None) -> ft.Control:
    controls: list[ft.Control] = [
        ft.Text(text, size=17, weight=ft.FontWeight.W_700, color=TEXT),
    ]
    if subtitle:
        controls.append(ft.Text(subtitle, size=11, color=MUTED))
    return ft.Column(controls, spacing=4)


def progress_bar(value: float, color: str) -> ft.Control:
    return ft.ProgressBar(
        value=max(0.0, min(1.0, value)),
        color=color,
        bgcolor="#07101F",
        bar_height=8,
    )


def metric_tile(label: str, value: str, accent: str = TEAL, subtitle: str | None = None) -> ft.Control:
    items: list[ft.Control] = [
        ft.Text(label.upper(), size=10, color=MUTED, weight=ft.FontWeight.W_600),
        ft.Text(value, size=24, color=TEXT, weight=ft.FontWeight.W_700),
    ]
    if subtitle:
        items.append(ft.Text(subtitle, size=11, color=MUTED))
    return ft.Container(
        bgcolor=SURFACE_2,
        border_radius=16,
        border=ft.border.all(1, STROKE),
        padding=16,
        content=ft.Column(items, spacing=6),
        gradient=ft.LinearGradient(
            begin=ft.alignment.Alignment(-1, -1),
            end=ft.alignment.Alignment(1, 1),
            colors=[SURFACE_2, SURFACE],
        ),
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=18,
            color=f"{accent}22",
            offset=ft.Offset(0, 4),
        ),
    )
