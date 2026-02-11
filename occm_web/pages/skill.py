"""Skill 管理页面"""

from __future__ import annotations
from fastapi import Request
from nicegui import ui
from ..auth import AuthManager as WebAuth, require_auth
from ..i18n_web import tr
from ..layout import render_layout
from occm_core import ConfigPaths, ConfigManager, BackupManager


def register_page(auth: WebAuth | None):
    auth_enabled = auth is not None
    dec = require_auth(auth) if auth else lambda f: f

    @ui.page("/skill")
    @dec
    async def skill_page(request: Request):
        config = ConfigManager.load_json(ConfigPaths.get_opencode_config()) or {}
        skills = config.get("skill", {})
        if not isinstance(skills, dict):
            skills = {}

        def content():
            with ui.tabs().classes("w-full") as tabs:
                t1 = ui.tab("已安装 Skills")
                t2 = ui.tab("Skill 市场")
            with ui.tab_panels(tabs, value=t1).classes("w-full"):
                with ui.tab_panel(t1):
                    rows = [
                        {
                            "name": k,
                            "permission": (
                                v.get("permission", "")
                                if isinstance(v, dict)
                                else str(v)
                            ),
                        }
                        for k, v in skills.items()
                    ]
                    cols = [
                        {
                            "name": "name",
                            "label": tr("common.name"),
                            "field": "name",
                            "sortable": True,
                        },
                        {
                            "name": "permission",
                            "label": "Permission",
                            "field": "permission",
                        },
                    ]
                    ui.table(columns=cols, rows=rows, row_key="name").classes("w-full")
                    with ui.row().classes("gap-2 mt-2"):
                        gh_input = ui.input(
                            label="GitHub (user/repo)",
                            placeholder="vercel-labs/git-release",
                        ).classes("w-80")

                        def do_install():
                            val = (gh_input.value or "").strip()
                            if not val:
                                ui.notify("请输入 GitHub 地址", type="warning")
                                return
                            ui.notify(f"安装 {val} ...", type="info")

                        ui.button(tr("common.install"), on_click=do_install)
                with ui.tab_panel(t2):
                    ui.label("Skill 市场功能开发中...").classes("text-gray-500")

        render_layout(
            request=request,
            page_key="menu.skill",
            content_builder=content,
            auth_enabled=auth_enabled,
        )
