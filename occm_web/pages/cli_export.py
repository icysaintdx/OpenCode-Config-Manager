"""CLI 工具导出页面"""

from __future__ import annotations
from fastapi import Request
from nicegui import ui
from ..auth import AuthManager as WebAuth, require_auth
from ..i18n_web import tr
from ..layout import render_layout
from occm_core import ConfigPaths, ConfigManager


def register_page(auth: WebAuth | None):
    auth_enabled = auth is not None
    dec = require_auth(auth) if auth else lambda f: f

    @ui.page("/cli-export")
    @dec
    async def cli_export_page(request: Request):
        config = ConfigManager.load_json(ConfigPaths.get_opencode_config()) or {}
        providers = config.get("provider", {})

        def content():
            with ui.tabs().classes("w-full") as tabs:
                t1 = ui.tab("Claude Code")
                t2 = ui.tab("Codex")
                t3 = ui.tab("Gemini")
            with ui.tab_panels(tabs, value=t1).classes("w-full"):
                for panel, name in [(t1, "Claude Code"), (t2, "Codex"), (t3, "Gemini")]:
                    with ui.tab_panel(panel):
                        prov_opts = (
                            list(providers.keys()) if providers else ["(无Provider)"]
                        )
                        ui.select(
                            label="选择 Provider",
                            options=prov_opts,
                            value=prov_opts[0] if prov_opts else "",
                        ).classes("w-full")
                        ui.code("// 配置预览将在选择后生成", language="json").classes(
                            "w-full mt-2"
                        )
                        ui.button(
                            f"导出到 {name}",
                            icon="download",
                            on_click=lambda n=name: ui.notify(
                                f"导出 {n} 配置...", type="info"
                            ),
                        ).classes("mt-2")

        render_layout(
            request=request,
            page_key="menu.export",
            content_builder=content,
            auth_enabled=auth_enabled,
        )
