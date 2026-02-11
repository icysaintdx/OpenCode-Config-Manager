"""Model 管理页面"""

from __future__ import annotations

# pyright: reportMissingImports=false

from fastapi import Request
from nicegui import ui

from ..auth import AuthManager as WebAuth, require_auth
from ..i18n_web import tr
from ..layout import render_layout

from occm_core import ConfigPaths, ConfigManager, BackupManager


def _load_config() -> dict:
    return ConfigManager.load_json(ConfigPaths.get_opencode_config()) or {}


def _save_config(config: dict) -> None:
    bm = BackupManager()
    ConfigManager.save_json(ConfigPaths.get_opencode_config(), config, bm)


def register_page(auth: WebAuth | None):
    auth_enabled = auth is not None
    dec = require_auth(auth) if auth else lambda f: f

    @ui.page("/model")
    @dec
    async def model_page(request: Request):
        config = _load_config()
        providers = config.get("provider", {})

        def content():
            # 收集所有模型
            rows: list[dict] = []
            for pkey, pval in providers.items():
                if not isinstance(pval, dict):
                    continue
                models = pval.get("models", {})
                if not isinstance(models, dict):
                    continue
                for mkey, mval in models.items():
                    if not isinstance(mval, dict):
                        mval = {}
                    limit = mval.get("limit", {})
                    rows.append(
                        {
                            "provider": pkey,
                            "model": mkey,
                            "context": limit.get("context", ""),
                            "output": limit.get("output", ""),
                            "has_options": "✓" if mval.get("options") else "",
                            "has_variants": "✓" if mval.get("variants") else "",
                        }
                    )

            columns = [
                {
                    "name": "provider",
                    "label": "Provider",
                    "field": "provider",
                    "sortable": True,
                },
                {
                    "name": "model",
                    "label": tr("common.name"),
                    "field": "model",
                    "sortable": True,
                },
                {"name": "context", "label": "Context", "field": "context"},
                {"name": "output", "label": "Output", "field": "output"},
                {"name": "has_options", "label": "Options", "field": "has_options"},
                {"name": "has_variants", "label": "Variants", "field": "has_variants"},
            ]

            table = ui.table(columns=columns, rows=rows, row_key="model").classes(
                "w-full"
            )
            table.add_slot(
                "top-left",
                r'''
                <q-btn flat icon="add" label="'''
                + tr("common.add")
                + r'''" @click="$parent.$emit('add')" />
                <q-btn flat icon="delete" label="'''
                + tr("common.delete")
                + r"""" @click="$parent.$emit('delete')" />
            """,
            )

            # ---- 添加模型对话框 ----
            with ui.dialog() as add_dlg, ui.card().classes("w-[500px]"):
                ui.label(tr("common.add") + " Model").classes("text-lg font-bold")
                provider_options = (
                    list(providers.keys()) if providers else ["anthropic"]
                )
                d_provider = ui.select(
                    label="Provider",
                    options=provider_options,
                    value=provider_options[0] if provider_options else "",
                ).classes("w-full")
                d_model_id = ui.input(
                    label="Model ID", placeholder="claude-sonnet-4-5-20250929"
                ).classes("w-full")
                d_context = ui.number(label="Context Window", value=0).classes("w-full")
                d_output = ui.number(label="Max Output", value=0).classes("w-full")

                ui.label("Thinking 配置 (可选)").classes("text-sm text-gray-500 mt-2")
                d_thinking_type = ui.select(
                    label="Thinking Type", options=["", "enabled", "disabled"], value=""
                ).classes("w-full")
                d_thinking_budget = ui.number(label="Budget Tokens", value=0).classes(
                    "w-full"
                )

                with ui.row().classes("w-full justify-end gap-2 mt-2"):
                    ui.button(tr("common.cancel"), on_click=add_dlg.close).props("flat")

                    def do_add():
                        pkey = d_provider.value
                        mid = (d_model_id.value or "").strip()
                        if not mid:
                            ui.notify("请输入 Model ID", type="warning")
                            return
                        if pkey not in config.get("provider", {}):
                            ui.notify("Provider 不存在", type="warning")
                            return
                        prov = config["provider"][pkey]
                        if "models" not in prov:
                            prov["models"] = {}
                        model_cfg: dict = {}
                        ctx = int(d_context.value or 0)
                        out = int(d_output.value or 0)
                        if ctx or out:
                            model_cfg["limit"] = {}
                            if ctx:
                                model_cfg["limit"]["context"] = ctx
                            if out:
                                model_cfg["limit"]["output"] = out
                        if d_thinking_type.value:
                            model_cfg["options"] = {
                                "thinking": {
                                    "type": d_thinking_type.value,
                                    "budgetTokens": int(
                                        d_thinking_budget.value or 16000
                                    ),
                                }
                            }
                        prov["models"][mid] = model_cfg
                        _save_config(config)
                        ui.notify(tr("common.success"), type="positive")
                        add_dlg.close()
                        ui.navigate.to("/model")

                    ui.button(tr("common.save"), on_click=do_add)

            # ---- 删除模型对话框 ----
            with ui.dialog() as del_dlg, ui.card().classes("w-[400px]"):
                ui.label(tr("common.confirm_delete_title")).classes("text-lg font-bold")
                del_provider = ui.input(label="Provider").classes("w-full")
                del_model = ui.input(label="Model ID").classes("w-full")
                with ui.row().classes("w-full justify-end gap-2 mt-2"):
                    ui.button(tr("common.cancel"), on_click=del_dlg.close).props("flat")

                    def do_delete():
                        pk = (del_provider.value or "").strip()
                        mk = (del_model.value or "").strip()
                        if pk in config.get("provider", {}) and mk in config[
                            "provider"
                        ][pk].get("models", {}):
                            del config["provider"][pk]["models"][mk]
                            _save_config(config)
                            ui.notify(tr("common.success"), type="positive")
                            del_dlg.close()
                            ui.navigate.to("/model")
                        else:
                            ui.notify("未找到该模型", type="warning")

                    ui.button(tr("common.delete"), on_click=do_delete).props(
                        "color=negative"
                    )

            table.on("add", lambda: add_dlg.open())
            table.on("delete", lambda: del_dlg.open())

        render_layout(
            request=request,
            page_key="menu.model",
            content_builder=content,
            auth_enabled=auth_enabled,
        )
