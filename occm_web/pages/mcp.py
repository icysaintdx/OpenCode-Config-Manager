"""MCP 服务器管理页面"""

from __future__ import annotations
from fastapi import Request
from nicegui import ui
from ..auth import AuthManager as WebAuth, require_auth
from ..i18n_web import tr
from ..layout import render_layout
from occm_core import ConfigPaths, ConfigManager, BackupManager


def _load_config() -> dict:
    return ConfigManager.load_json(ConfigPaths.get_opencode_config()) or {}


def _load_omo() -> dict:
    return ConfigManager.load_json(ConfigPaths.get_ohmyopencode_config()) or {}


def _save_config(config: dict) -> None:
    ConfigManager.save_json(ConfigPaths.get_opencode_config(), config, BackupManager())


def _save_omo(config: dict) -> None:
    ConfigManager.save_json(
        ConfigPaths.get_ohmyopencode_config(), config, BackupManager()
    )


def register_page(auth: WebAuth | None):
    auth_enabled = auth is not None
    dec = require_auth(auth) if auth else lambda f: f

    @ui.page("/mcp")
    @dec
    async def mcp_page(request: Request):
        config = _load_config()
        omo = _load_omo()
        mcp_cfg = config.get("mcp", {})
        if not isinstance(mcp_cfg, dict):
            mcp_cfg = {}

        def content():
            with ui.tabs().classes("w-full") as tabs:
                tab_mcp = ui.tab("MCP 服务器")
                tab_omo = ui.tab("Oh My MCP")

            with ui.tab_panels(tabs, value=tab_mcp).classes("w-full"):
                with ui.tab_panel(tab_mcp):
                    _render_mcp_table(config, mcp_cfg)
                with ui.tab_panel(tab_omo):
                    _render_omo_mcp(omo)

        render_layout(
            request=request,
            page_key="menu.mcp",
            content_builder=content,
            auth_enabled=auth_enabled,
        )


def _render_mcp_table(config: dict, mcp_cfg: dict):
    rows = []
    for key, val in mcp_cfg.items():
        if not isinstance(val, dict):
            continue
        mtype = "remote" if val.get("url") else "local"
        rows.append(
            {
                "name": key,
                "type": mtype,
                "enabled": "✓" if val.get("enabled", True) else "✗",
                "command": " ".join(val.get("command", []))
                if isinstance(val.get("command"), list)
                else str(val.get("url", "")),
            }
        )

    columns = [
        {"name": "name", "label": tr("common.name"), "field": "name", "sortable": True},
        {"name": "type", "label": tr("common.type"), "field": "type"},
        {"name": "enabled", "label": tr("common.status"), "field": "enabled"},
        {"name": "command", "label": "Command / URL", "field": "command"},
    ]
    table = ui.table(columns=columns, rows=rows, row_key="name").classes("w-full")

    with ui.dialog() as dlg, ui.card().classes("w-[520px]"):
        ui.label(tr("common.add") + " MCP").classes("text-lg font-bold")
        d_name = ui.input(label=tr("common.name"), placeholder="context7").classes(
            "w-full"
        )
        d_type = ui.select(
            label=tr("common.type"), options=["local", "remote"], value="local"
        ).classes("w-full")
        d_cmd = ui.input(
            label="Command (JSON数组)",
            placeholder='["npx", "-y", "@upstash/context7-mcp"]',
        ).classes("w-full")
        d_url = ui.input(label="URL", placeholder="https://...").classes("w-full")
        d_env = ui.input(
            label="环境变量 (JSON)", placeholder='{"API_KEY": "xxx"}'
        ).classes("w-full")
        d_timeout = ui.number(label="Timeout (ms)", value=5000).classes("w-full")
        d_enabled = ui.switch("启用", value=True)

        with ui.row().classes("w-full justify-end gap-2 mt-2"):
            ui.button(tr("common.cancel"), on_click=dlg.close).props("flat")

            def do_add():
                import json as _json

                name = (d_name.value or "").strip()
                if not name:
                    ui.notify("请输入名称", type="warning")
                    return
                entry: dict = {"enabled": d_enabled.value}
                if d_type.value == "local":
                    try:
                        entry["command"] = _json.loads(d_cmd.value or "[]")
                    except Exception:
                        entry["command"] = [d_cmd.value or ""]
                else:
                    entry["url"] = (d_url.value or "").strip()
                if d_env.value:
                    try:
                        entry["environment"] = _json.loads(d_env.value)
                    except Exception:
                        pass
                t = int(d_timeout.value or 5000)
                if t != 5000:
                    entry["timeout"] = t
                if "mcp" not in config:
                    config["mcp"] = {}
                config["mcp"][name] = entry
                _save_config(config)
                ui.notify(tr("common.success"), type="positive")
                dlg.close()
                ui.navigate.to("/mcp")

            ui.button(tr("common.save"), on_click=do_add)

    ui.button(tr("common.add"), icon="add", on_click=dlg.open).classes("mt-2")


def _render_omo_mcp(omo: dict):
    omo_mcp = omo.get("mcp", {})
    if not isinstance(omo_mcp, dict):
        omo_mcp = {}
    builtin = ["websearch", "context7", "grep_app"]
    for name in builtin:
        val = omo_mcp.get(name, {})
        enabled = val.get("enabled", False) if isinstance(val, dict) else False
        with ui.row().classes("w-full items-center gap-4 p-2 border-b"):
            ui.label(name).classes("text-base font-medium w-40")
            sw = ui.switch("", value=enabled)

            def toggle(n=name, s=sw):
                if "mcp" not in omo:
                    omo["mcp"] = {}
                if n not in omo["mcp"]:
                    omo["mcp"][n] = {}
                omo["mcp"][n]["enabled"] = s.value
                _save_omo(omo)
                ui.notify(tr("common.success"), type="positive")

            sw.on("change", toggle)
