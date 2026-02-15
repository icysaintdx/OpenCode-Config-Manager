from __future__ import annotations

# pyright: reportMissingImports=false

from collections.abc import Callable
from pathlib import Path
from typing import Any

from fastapi import Request
from nicegui import app, ui

from .i18n_web import get_i18n, tr
from .theme import get_theme_manager

STATIC_DIR = Path(__file__).parent / "static"

NAV_GROUPS: list[dict[str, object]] = [
    {
        "label_key": "web.nav_group.core",
        "fallback": "Core",
        "icon": "settings",
        "items": [
            {"route": "/", "key": "menu.home", "fallback": "Home", "icon": "home"},
            {
                "route": "/provider",
                "key": "menu.provider",
                "fallback": "Provider & Model",
                "icon": "dns",
            },
            {
                "route": "/native-provider",
                "key": "menu.native_provider",
                "fallback": "Native Provider",
                "icon": "cloud",
            },
            {
                "route": "/mcp",
                "key": "menu.mcp",
                "fallback": "MCP Server",
                "icon": "hub",
            },
        ],
    },
    {
        "label_key": "web.nav_group.agent",
        "fallback": "Agent & Rules",
        "icon": "smart_toy",
        "items": [
            {
                "route": "/agent-opencode",
                "key": "menu.agent",
                "fallback": "Agent (OC)",
                "icon": "smart_toy",
            },
            {
                "route": "/agent-omo",
                "key": "menu.ohmyagent",
                "fallback": "Agent (OMO)",
                "icon": "group",
            },
            {
                "route": "/category",
                "key": "menu.category",
                "fallback": "Category",
                "icon": "category",
            },
            {
                "route": "/permission",
                "key": "menu.permission",
                "fallback": "Permission",
                "icon": "security",
            },
            {
                "route": "/rules",
                "key": "menu.rules",
                "fallback": "Rules",
                "icon": "rule",
            },
            {
                "route": "/compaction",
                "key": "menu.compaction",
                "fallback": "Compaction",
                "icon": "compress",
            },
        ],
    },
    {
        "label_key": "web.nav_group.extend",
        "fallback": "Extensions",
        "icon": "extension",
        "items": [
            {
                "route": "/skill",
                "key": "menu.skill",
                "fallback": "Skill",
                "icon": "auto_awesome",
            },
            {
                "route": "/plugin",
                "key": "menu.plugin",
                "fallback": "Plugin",
                "icon": "extension",
            },
        ],
    },
    {
        "label_key": "web.nav_group.tools",
        "fallback": "Tools",
        "icon": "build",
        "items": [
            {
                "route": "/external-import",
                "key": "menu.import",
                "fallback": "Import",
                "icon": "upload",
            },
            {
                "route": "/cli-export",
                "key": "menu.export",
                "fallback": "CLI Export",
                "icon": "download",
            },
            {
                "route": "/monitor",
                "key": "menu.monitor",
                "fallback": "Monitor",
                "icon": "monitor_heart",
            },
            {
                "route": "/backup",
                "key": "menu.backup",
                "fallback": "Backup",
                "icon": "backup",
            },
            {
                "route": "/remote",
                "key": "menu.remote",
                "fallback": "Remote",
                "icon": "cloud_sync",
            },
            {
                "route": "/help",
                "key": "menu.help",
                "fallback": "Help",
                "icon": "help_outline",
            },
        ],
    },
]

# Flat list for backward compat
NAV_ITEMS: list[dict[str, str]] = []
for _g in NAV_GROUPS:
    for _item in _g["items"]:  # type: ignore[union-attr]
        NAV_ITEMS.append(_item)  # type: ignore[arg-type]

# 注册静态文件目录（仅一次）
_static_registered = False


def _ensure_static() -> None:
    global _static_registered
    if not _static_registered and STATIC_DIR.exists():
        app.add_static_files("/static", str(STATIC_DIR))
        _static_registered = True


def render_layout(
    request: Request,
    page_key: str,
    content_builder: Callable[[], Any],
    auth_enabled: bool,
) -> None:
    _ensure_static()
    i18n = get_i18n()
    theme = get_theme_manager()
    theme.apply()

    # 注入全局样式
    ui.add_head_html('<link rel="stylesheet" href="/static/style.css">')

    current_path = request.url.path

    # --- Header ---
    with ui.header(elevated=False).classes("items-center justify-between px-4 py-2"):
        with ui.row().classes("items-center gap-3"):
            ui.button(icon="menu", on_click=lambda: drawer.toggle()).props(
                "flat round size=sm"
            )
            ui.icon("settings_suggest", size="sm").classes("text-indigo-400")
            title_label = ui.label(tr("app.title")).classes(
                "text-sm md:text-base font-semibold tracking-tight"
            )
            i18n.bind_text(title_label, "app.title")

        with ui.row().classes("items-center gap-1"):

            def _switch_theme() -> None:
                theme.cycle_mode()
                theme.apply()

            theme_btn = ui.button(icon="contrast", on_click=_switch_theme).props(
                "flat round size=sm"
            )
            theme_btn.tooltip("Toggle theme")

            lang_button = ui.button("", on_click=lambda: _switch_language()).props(
                "flat dense size=sm"
            )

            def _switch_language() -> None:
                i18n.toggle_language()
                lang_button.set_text("中文" if i18n.get_language() == "zh_CN" else "EN")
                ui.navigate.to(request.url.path)

            lang_button.set_text("中文" if i18n.get_language() == "zh_CN" else "EN")

            if auth_enabled:

                async def _logout() -> None:
                    await ui.run_javascript(
                        """
                        await fetch('/api/auth/logout', {
                          method: 'POST',
                          credentials: 'same-origin',
                        });
                        """
                    )
                    ui.navigate.to("/login")

                ui.button(tr("web.logout"), on_click=_logout).props(
                    "flat dense size=sm"
                )

    # --- Sidebar ---
    with ui.left_drawer(top_corner=True, bottom_corner=True).classes(
        "w-60 p-0"
    ) as drawer:
        with ui.column().classes("w-full gap-0 py-2"):
            for group in NAV_GROUPS:
                group_label = tr(group["label_key"])  # type: ignore[arg-type]
                if group_label == group["label_key"]:
                    group_label = group["fallback"]  # type: ignore[assignment]
                ui.label(str(group_label)).classes("occm-nav-group-label")

                for item in group["items"]:  # type: ignore[union-attr]
                    text = tr(item["key"])
                    if text == item["key"]:
                        text = item["fallback"]
                    is_active = item["route"] == current_path
                    btn = ui.button(
                        text,
                        icon=item.get("icon", ""),
                        on_click=lambda r=item["route"]: ui.navigate.to(r),
                    ).props("align=left unelevated no-caps flat")
                    btn.classes(
                        "w-full justify-start occm-nav-btn"
                        + (" occm-nav-active" if is_active else "")
                    )
                    if text != item["fallback"]:
                        i18n.bind_text(btn, item["key"])

    # --- Main Content ---
    with ui.column().classes("w-full p-4 md:p-8 max-w-7xl mx-auto"):
        page_title = ui.label(tr(page_key)).classes("occm-page-title")
        i18n.bind_text(page_title, page_key)
        content_builder()
