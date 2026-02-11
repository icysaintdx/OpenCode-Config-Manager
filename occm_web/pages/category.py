"""Category 管理页面"""

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

    @ui.page("/category")
    @dec
    async def category_page(request: Request):
        omo = ConfigManager.load_json(ConfigPaths.get_ohmyopencode_config()) or {}
        cats = omo.get("categories", {})
        if not isinstance(cats, dict):
            cats = {}

        def content():
            rows = [
                {
                    "name": k,
                    "model": (v.get("model", "") if isinstance(v, dict) else ""),
                    "temperature": (
                        v.get("temperature", "") if isinstance(v, dict) else ""
                    ),
                }
                for k, v in cats.items()
            ]
            cols = [
                {
                    "name": "name",
                    "label": tr("common.name"),
                    "field": "name",
                    "sortable": True,
                },
                {"name": "model", "label": "Model", "field": "model"},
                {"name": "temperature", "label": "Temperature", "field": "temperature"},
            ]
            ui.table(columns=cols, rows=rows, row_key="name").classes("w-full")
            with ui.dialog() as dlg, ui.card().classes("w-[480px]"):
                ui.label(tr("common.add") + " Category").classes("text-lg font-bold")
                d_name = ui.input(
                    label=tr("common.name"), placeholder="visual-engineering"
                ).classes("w-full")
                d_model = ui.input(
                    label="Model", placeholder="provider/model-id"
                ).classes("w-full")
                d_temp = ui.slider(min=0, max=2, step=0.1, value=0.5).classes("w-full")
                ui.label("").bind_text_from(
                    d_temp, "value", backward=lambda v: f"Temperature: {v}"
                )
                with ui.row().classes("w-full justify-end gap-2 mt-2"):
                    ui.button(tr("common.cancel"), on_click=dlg.close).props("flat")

                    def do_add():
                        n = (d_name.value or "").strip()
                        if not n:
                            ui.notify("请输入名称", type="warning")
                            return
                        if "categories" not in omo:
                            omo["categories"] = {}
                        omo["categories"][n] = {
                            "model": d_model.value or "",
                            "temperature": d_temp.value,
                        }
                        ConfigManager.save_json(
                            ConfigPaths.get_ohmyopencode_config(), omo, BackupManager()
                        )
                        ui.notify(tr("common.success"), type="positive")
                        dlg.close()
                        ui.navigate.to("/category")

                    ui.button(tr("common.save"), on_click=do_add)
            ui.button(tr("common.add"), icon="add", on_click=dlg.open).classes("mt-2")

        render_layout(
            request=request,
            page_key="menu.category",
            content_builder=content,
            auth_enabled=auth_enabled,
        )
