"""外部导入页面"""

from __future__ import annotations
from fastapi import Request
from nicegui import ui
from ..auth import AuthManager as WebAuth, require_auth
from ..i18n_web import tr
from ..layout import render_layout


def register_page(auth: WebAuth | None):
    auth_enabled = auth is not None
    dec = require_auth(auth) if auth else lambda f: f

    @ui.page("/external-import")
    @dec
    async def import_page(request: Request):
        def content():
            ui.label("支持导入源").classes("text-base font-medium")
            sources = ["Claude Code", "Codex", "Gemini", "cc-switch"]
            for s in sources:
                with ui.row().classes("items-center gap-4 p-2 border rounded"):
                    ui.label(s).classes("w-32 font-medium")
                    ui.button(
                        "扫描检测",
                        on_click=lambda src=s: ui.notify(
                            f"扫描 {src} 配置...", type="info"
                        ),
                    ).props("outline")

        render_layout(
            request=request,
            page_key="menu.import",
            content_builder=content,
            auth_enabled=auth_enabled,
        )
