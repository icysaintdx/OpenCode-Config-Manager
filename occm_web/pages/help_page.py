"""帮助说明页面"""

from __future__ import annotations
from fastapi import Request
from nicegui import ui
from ..auth import AuthManager as WebAuth, require_auth
from ..i18n_web import tr
from ..layout import render_layout
from occm_core import ConfigPaths


def register_page(auth: WebAuth | None):
    auth_enabled = auth is not None
    dec = require_auth(auth) if auth else lambda f: f

    @ui.page("/help")
    @dec
    async def help_page(request: Request):
        def content():
            ui.label("OCCM Web v1.8.0").classes("text-xl font-bold")
            ui.separator()
            with ui.card().classes("w-full"):
                ui.label("配置文件路径").classes("font-medium")
                ui.label(f"OpenCode: {ConfigPaths.get_opencode_config()}")
                ui.label(f"Oh My OpenCode: {ConfigPaths.get_ohmyopencode_config()}")
                ui.label(f"备份目录: {ConfigPaths.get_backup_dir()}")
            with ui.card().classes("w-full mt-4"):
                ui.label("相关链接").classes("font-medium")
                ui.link(
                    "GitHub - OpenCode Config Manager",
                    "https://github.com/icysaintdx/OpenCode-Config-Manager",
                    new_tab=True,
                )
                ui.link(
                    "OpenCode 官方文档",
                    "https://opencode.ai/docs/models/",
                    new_tab=True,
                )
                ui.link(
                    "Oh My OpenCode",
                    "https://github.com/code-yeongyu/oh-my-opencode",
                    new_tab=True,
                )

        render_layout(
            request=request,
            page_key="menu.help",
            content_builder=content,
            auth_enabled=auth_enabled,
        )
