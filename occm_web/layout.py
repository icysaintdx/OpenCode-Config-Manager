from __future__ import annotations

# pyright: reportMissingImports=false

from collections.abc import Callable
from typing import Any

from fastapi import Request
from nicegui import ui

from .i18n_web import get_i18n, tr
from .theme import get_theme_manager


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


def render_layout(
    request: Request,
    page_key: str,
    content_builder: Callable[[], Any],
    auth_enabled: bool,
) -> None:
    i18n = get_i18n()
    theme = get_theme_manager()
    theme.apply()

    current_path = request.url.path

    with ui.header(elevated=True).classes("items-center justify-between px-3"):
        with ui.row().classes("items-center gap-2"):
            ui.button(icon="menu", on_click=lambda: drawer.toggle()).props("flat")
            title_label = ui.label(tr("app.title")).classes(
                "text-base md:text-lg font-semibold"
            )
            i18n.bind_text(title_label, "app.title")

        with ui.row().classes("items-center gap-2"):
            theme_label = ui.label("")

            def _refresh_theme_label() -> None:
                mode = theme.get_mode()
                mapping = {"dark": "🌙 Dark", "light": "☀️ Light", "auto": "🖥 Auto"}
                theme_label.set_text(mapping.get(mode, "Auto"))

            def _switch_theme() -> None:
                theme.cycle_mode()
                _refresh_theme_label()
                theme.apply()

            _refresh_theme_label()
            ui.button(icon="contrast", on_click=_switch_theme).props("flat")

            lang_button = ui.button("", on_click=lambda: _switch_language()).props(
                "flat"
            )

            def _switch_language() -> None:
                i18n.toggle_language()
                lang_button.set_text(
                    "中文" if i18n.get_language() == "zh_CN" else "English"
                )
                ui.navigate.to(request.url.path)

            lang_button.set_text(
                "中文" if i18n.get_language() == "zh_CN" else "English"
            )

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

                ui.button(tr("web.logout"), on_click=_logout).props("outline")

    with ui.left_drawer(top_corner=True, bottom_corner=True).classes("w-64") as drawer:
        with ui.column().classes("w-full gap-0 p-2"):
            for group in NAV_GROUPS:
                group_label = tr(group["label_key"])  # type: ignore[arg-type]
                if group_label == group["label_key"]:
                    group_label = group["fallback"]  # type: ignore[assignment]
                ui.label(str(group_label)).classes(
                    "text-xs font-bold uppercase tracking-wide text-gray-400 mt-3 mb-1 px-2"
                )
                for item in group["items"]:  # type: ignore[union-attr]
                    text = tr(item["key"])
                    if text == item["key"]:
                        text = item["fallback"]
                    is_active = item["route"] == current_path
                    btn = ui.button(
                        text,
                        icon=item.get("icon", ""),
                        on_click=lambda r=item["route"]: ui.navigate.to(r),
                    ).props("align=left unelevated no-caps")
                    btn.classes("w-full justify-start text-sm")
                    btn.style(
                        f"background: {'rgba(25,118,210,0.15)' if is_active else 'transparent'};"
                        f"font-weight: {'600' if is_active else '400'}"
                    )
                    if text != item["fallback"]:
                        i18n.bind_text(btn, item["key"])

    with ui.column().classes("w-full p-4 md:p-6"):
        page_title = ui.label(tr(page_key)).classes("text-xl font-bold mb-4")
        i18n.bind_text(page_title, page_key)
        content_builder()
