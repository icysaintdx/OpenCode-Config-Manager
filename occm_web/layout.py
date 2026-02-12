from __future__ import annotations

# pyright: reportMissingImports=false

from collections.abc import Callable
from typing import Any

from fastapi import Request
from nicegui import ui

from .i18n_web import get_i18n, tr
from .theme import get_theme_manager


NAV_ITEMS: list[dict[str, str]] = [
    {"route": "/", "key": "menu.home", "fallback": "首页"},
    {"route": "/provider", "key": "menu.provider", "fallback": "Provider管理"},
    {
        "route": "/native-provider",
        "key": "menu.native_provider",
        "fallback": "原生Provider",
    },
    {"route": "/model", "key": "menu.model", "fallback": "Model管理"},
    {"route": "/mcp", "key": "menu.mcp", "fallback": "MCP服务器"},
    {
        "route": "/agent-opencode",
        "key": "menu.agent",
        "fallback": "Agent配置(OpenCode)",
    },
    {"route": "/agent-omo", "key": "menu.ohmyagent", "fallback": "Agent配置(OMO)"},
    {"route": "/category", "key": "menu.category", "fallback": "Category管理"},
    {"route": "/permission", "key": "menu.permission", "fallback": "权限管理"},
    {"route": "/skill", "key": "menu.skill", "fallback": "Skill管理"},
    {"route": "/plugin", "key": "menu.plugin", "fallback": "插件管理"},
    {"route": "/rules", "key": "menu.rules", "fallback": "Rules管理"},
    {"route": "/compaction", "key": "menu.compaction", "fallback": "上下文压缩"},
    {"route": "/external-import", "key": "menu.import", "fallback": "外部导入"},
    {"route": "/cli-export", "key": "menu.export", "fallback": "CLI导出"},
    {"route": "/monitor", "key": "menu.monitor", "fallback": "监控"},
    {"route": "/backup", "key": "menu.backup", "fallback": "备份管理"},
    {"route": "/remote", "key": "menu.remote", "fallback": "远程管理"},
    {"route": "/help", "key": "menu.help", "fallback": "帮助"},
]


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

                ui.button("退出登录", on_click=_logout).props("outline")

    with ui.left_drawer(top_corner=True, bottom_corner=True).classes("w-64") as drawer:
        with ui.column().classes("w-full gap-1 p-2"):
            for item in NAV_ITEMS:
                text = tr(item["key"])
                if text == item["key"]:
                    text = item["fallback"]
                color = "primary" if item["route"] == current_path else "grey-8"
                btn = ui.button(
                    text, on_click=lambda r=item["route"]: ui.navigate.to(r)
                ).props("align=left unelevated")
                btn.classes("w-full justify-start")
                btn.style(
                    f"background: {'rgba(25,118,210,0.15)' if color == 'primary' else 'transparent'}"
                )
                if text != item["fallback"]:
                    i18n.bind_text(btn, item["key"])

    with ui.column().classes("w-full p-4 md:p-6"):
        page_title = ui.label(tr(page_key)).classes("text-xl font-bold mb-4")
        i18n.bind_text(page_title, page_key)
        content_builder()
