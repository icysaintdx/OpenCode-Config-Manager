"""Agent 配置页面 (OpenCode + Oh My OpenCode)"""

from __future__ import annotations
from fastapi import Request
from nicegui import ui
from ..auth import AuthManager as WebAuth, require_auth
from ..i18n_web import tr
from ..layout import render_layout
from occm_core import ConfigPaths, ConfigManager, BackupManager


def _load_oc() -> dict:
    return ConfigManager.load_json(ConfigPaths.get_opencode_config()) or {}


def _load_omo() -> dict:
    return ConfigManager.load_json(ConfigPaths.get_ohmyopencode_config()) or {}


def _save_oc(c: dict):
    ConfigManager.save_json(ConfigPaths.get_opencode_config(), c, BackupManager())


def _save_omo(c: dict):
    ConfigManager.save_json(ConfigPaths.get_ohmyopencode_config(), c, BackupManager())


def register_page(auth: WebAuth | None):
    auth_enabled = auth is not None
    dec = require_auth(auth) if auth else lambda f: f

    @ui.page("/agent-opencode")
    @dec
    async def agent_oc_page(request: Request):
        config = _load_oc()
        agents = config.get("agent", {})
        if not isinstance(agents, dict):
            agents = {}

        def content():
            rows = []
            for k, v in agents.items():
                if not isinstance(v, dict):
                    v = {}
                rows.append(
                    {
                        "name": k,
                        "mode": v.get("mode", ""),
                        "temperature": v.get("temperature", ""),
                        "disabled": "✗" if v.get("disable") else "✓",
                    }
                )
            cols = [
                {
                    "name": "name",
                    "label": tr("common.name"),
                    "field": "name",
                    "sortable": True,
                },
                {"name": "mode", "label": "Mode", "field": "mode"},
                {"name": "temperature", "label": "Temperature", "field": "temperature"},
                {"name": "disabled", "label": tr("common.status"), "field": "disabled"},
            ]
            ui.table(columns=cols, rows=rows, row_key="name").classes("w-full")
            with ui.dialog() as dlg, ui.card().classes("w-[500px]"):
                ui.label(tr("common.add") + " Agent").classes("text-lg font-bold")
                d_name = ui.input(label=tr("common.name"), placeholder="build").classes(
                    "w-full"
                )
                d_mode = ui.select(
                    label="Mode",
                    options=["primary", "subagent", "all"],
                    value="primary",
                ).classes("w-full")
                d_temp = ui.number(
                    label="Temperature", value=0.0, min=0.0, max=2.0, step=0.1
                ).classes("w-full")
                d_steps = ui.number(label="Max Steps", value=0).classes("w-full")
                d_prompt = ui.textarea(label="System Prompt").classes("w-full")
                with ui.row().classes("w-full justify-end gap-2 mt-2"):
                    ui.button(tr("common.cancel"), on_click=dlg.close).props("flat")

                    def do_add():
                        n = (d_name.value or "").strip()
                        if not n:
                            ui.notify("请输入名称", type="warning")
                            return
                        entry: dict = {}
                        if d_mode.value:
                            entry["mode"] = d_mode.value
                        t = float(d_temp.value or 0)
                        if t > 0:
                            entry["temperature"] = t
                        s = int(d_steps.value or 0)
                        if s > 0:
                            entry["maxSteps"] = s
                        if d_prompt.value:
                            entry["prompt"] = d_prompt.value
                        if "agent" not in config:
                            config["agent"] = {}
                        config["agent"][n] = entry
                        _save_oc(config)
                        ui.notify(tr("common.success"), type="positive")
                        dlg.close()
                        ui.navigate.to("/agent-opencode")

                    ui.button(tr("common.save"), on_click=do_add)
            ui.button(tr("common.add"), icon="add", on_click=dlg.open).classes("mt-2")

        render_layout(
            request=request,
            page_key="menu.agent",
            content_builder=content,
            auth_enabled=auth_enabled,
        )

    @ui.page("/agent-omo")
    @dec
    async def agent_omo_page(request: Request):
        omo = _load_omo()
        agents = omo.get("agents", {})
        if not isinstance(agents, dict):
            agents = {}

        def content():
            rows = [
                {
                    "name": k,
                    "provider": (v.get("provider", "") if isinstance(v, dict) else ""),
                    "model": (v.get("model", "") if isinstance(v, dict) else ""),
                }
                for k, v in agents.items()
            ]
            cols = [
                {
                    "name": "name",
                    "label": tr("common.name"),
                    "field": "name",
                    "sortable": True,
                },
                {"name": "provider", "label": "Provider", "field": "provider"},
                {"name": "model", "label": "Model", "field": "model"},
            ]
            ui.table(columns=cols, rows=rows, row_key="name").classes("w-full")
            with ui.dialog() as dlg, ui.card().classes("w-[500px]"):
                ui.label(tr("common.add") + " OMO Agent").classes("text-lg font-bold")
                d_name = ui.input(
                    label=tr("common.name"), placeholder="oracle"
                ).classes("w-full")
                d_prov = ui.input(label="Provider", placeholder="anthropic").classes(
                    "w-full"
                )
                d_model = ui.input(
                    label="Model", placeholder="claude-sonnet-4-5-20250929"
                ).classes("w-full")
                with ui.row().classes("w-full justify-end gap-2 mt-2"):
                    ui.button(tr("common.cancel"), on_click=dlg.close).props("flat")

                    def do_add():
                        n = (d_name.value or "").strip()
                        if not n:
                            ui.notify("请输入名称", type="warning")
                            return
                        if "agents" not in omo:
                            omo["agents"] = {}
                        omo["agents"][n] = {
                            "provider": d_prov.value or "",
                            "model": d_model.value or "",
                        }
                        _save_omo(omo)
                        ui.notify(tr("common.success"), type="positive")
                        dlg.close()
                        ui.navigate.to("/agent-omo")

                    ui.button(tr("common.save"), on_click=do_add)
            ui.button(tr("common.add"), icon="add", on_click=dlg.open).classes("mt-2")

        render_layout(
            request=request,
            page_key="menu.ohmyagent",
            content_builder=content,
            auth_enabled=auth_enabled,
        )
