"""插件管理页面"""

from __future__ import annotations
from fastapi import Request
from nicegui import ui
from ..auth import AuthManager as WebAuth, require_auth
from ..i18n_web import tr
from ..layout import render_layout


def register_page(auth: WebAuth | None):
    auth_enabled = auth is not None
    dec = require_auth(auth) if auth else lambda f: f

    @ui.page("/plugin")
    @dec
    async def plugin_page(request: Request):
        def content():
            ui.label("已安装插件").classes("text-base font-medium")
            ui.label("暂无已安装插件").classes("text-gray-500")
            ui.separator()
            with ui.row().classes("gap-2 mt-2"):
                gh_input = ui.input(
                    label="GitHub URL", placeholder="https://github.com/user/repo"
                ).classes("w-96")

                def do_install():
                    val = (gh_input.value or "").strip()
                    if not val:
                        ui.notify("请输入 GitHub URL", type="warning")
                        return
                    ui.notify(f"安装插件 {val} ...", type="info")

                ui.button(tr("common.install"), on_click=do_install)

        render_layout(
            request=request,
            page_key="menu.plugin",
            content_builder=content,
            auth_enabled=auth_enabled,
        )
