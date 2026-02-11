"""Rules 管理页面"""

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

    @ui.page("/rules")
    @dec
    async def rules_page(request: Request):
        config = ConfigManager.load_json(ConfigPaths.get_opencode_config()) or {}
        instructions = config.get("instructions", [])
        if not isinstance(instructions, list):
            instructions = []

        def content():
            rows = [{"idx": i, "path": p} for i, p in enumerate(instructions)]
            cols = [
                {"name": "idx", "label": "#", "field": "idx"},
                {"name": "path", "label": "路径", "field": "path"},
            ]
            ui.table(columns=cols, rows=rows, row_key="idx").classes("w-full")
            with ui.dialog() as dlg, ui.card().classes("w-[450px]"):
                ui.label(tr("common.add") + " Instruction").classes("text-lg font-bold")
                d_path = ui.input(
                    label="文件路径 / URL / Glob", placeholder="./AGENTS.md"
                ).classes("w-full")
                with ui.row().classes("w-full justify-end gap-2 mt-2"):
                    ui.button(tr("common.cancel"), on_click=dlg.close).props("flat")

                    def do_add():
                        v = (d_path.value or "").strip()
                        if not v:
                            ui.notify("请输入路径", type="warning")
                            return
                        if "instructions" not in config:
                            config["instructions"] = []
                        config["instructions"].append(v)
                        ConfigManager.save_json(
                            ConfigPaths.get_opencode_config(), config, BackupManager()
                        )
                        ui.notify(tr("common.success"), type="positive")
                        dlg.close()
                        ui.navigate.to("/rules")

                    ui.button(tr("common.save"), on_click=do_add)
            ui.button(tr("common.add"), icon="add", on_click=dlg.open).classes("mt-2")

        render_layout(
            request=request,
            page_key="menu.rules",
            content_builder=content,
            auth_enabled=auth_enabled,
        )
