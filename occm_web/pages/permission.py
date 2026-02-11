"""权限管理页面"""

from __future__ import annotations
from fastapi import Request
from nicegui import ui
from ..auth import AuthManager as WebAuth, require_auth
from ..i18n_web import tr
from ..layout import render_layout
from occm_core import ConfigPaths, ConfigManager, BackupManager

BUILTIN_TOOLS = [
    "Bash",
    "Read",
    "Write",
    "Edit",
    "Glob",
    "Grep",
    "WebFetch",
    "WebSearch",
    "Task",
]


def register_page(auth: WebAuth | None):
    auth_enabled = auth is not None
    dec = require_auth(auth) if auth else lambda f: f

    @ui.page("/permission")
    @dec
    async def permission_page(request: Request):
        config = ConfigManager.load_json(ConfigPaths.get_opencode_config()) or {}
        perms = config.get("permission", {})
        if not isinstance(perms, dict):
            perms = {}

        def content():
            rows = []
            for tool, val in perms.items():
                if isinstance(val, dict):
                    rows.append(
                        {
                            "tool": tool,
                            "level": val.get("level", "ask"),
                            "pattern": val.get("pattern", ""),
                        }
                    )
                elif isinstance(val, str):
                    rows.append({"tool": tool, "level": val, "pattern": ""})
            cols = [
                {"name": "tool", "label": "工具", "field": "tool", "sortable": True},
                {"name": "level", "label": "权限", "field": "level"},
                {"name": "pattern", "label": "模式", "field": "pattern"},
            ]
            ui.table(columns=cols, rows=rows, row_key="tool").classes("w-full")
            with ui.dialog() as dlg, ui.card().classes("w-[450px]"):
                ui.label(tr("common.add") + " 权限规则").classes("text-lg font-bold")
                d_tool = ui.select(
                    label="工具",
                    options=BUILTIN_TOOLS + ["(自定义)"],
                    value="Bash",
                    with_input=True,
                ).classes("w-full")
                d_level = ui.select(
                    label="权限级别", options=["allow", "ask", "deny"], value="ask"
                ).classes("w-full")
                d_pattern = ui.input(
                    label="Bash 命令模式", placeholder="git *"
                ).classes("w-full")
                with ui.row().classes("w-full justify-end gap-2 mt-2"):
                    ui.button(tr("common.cancel"), on_click=dlg.close).props("flat")

                    def do_add():
                        tool = (d_tool.value or "").strip()
                        if not tool:
                            ui.notify("请选择工具", type="warning")
                            return
                        if "permission" not in config:
                            config["permission"] = {}
                        entry: dict | str = d_level.value or "ask"
                        if d_pattern.value:
                            entry = {"level": d_level.value, "pattern": d_pattern.value}
                        config["permission"][tool] = entry
                        ConfigManager.save_json(
                            ConfigPaths.get_opencode_config(), config, BackupManager()
                        )
                        ui.notify(tr("common.success"), type="positive")
                        dlg.close()
                        ui.navigate.to("/permission")

                    ui.button(tr("common.save"), on_click=do_add)
            ui.button(tr("common.add"), icon="add", on_click=dlg.open).classes("mt-2")

        render_layout(
            request=request,
            page_key="menu.permission",
            content_builder=content,
            auth_enabled=auth_enabled,
        )
