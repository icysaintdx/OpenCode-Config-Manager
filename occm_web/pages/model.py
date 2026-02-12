"""Model 管理页面"""

from __future__ import annotations

# pyright: reportMissingImports=false

import json

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

        def content():
            # 中文：当前选中的行（单选）
            selected_row: dict[str, str | None] = {"value": None}

            def _providers_map() -> dict:
                providers = config.get("provider", {})
                return providers if isinstance(providers, dict) else {}

            def _provider_options() -> list[str]:
                return list(_providers_map().keys())

            def _build_rows() -> list[dict]:
                rows: list[dict] = []
                for pkey, pval in _providers_map().items():
                    if not isinstance(pval, dict):
                        continue
                    models = pval.get("models", {})
                    if not isinstance(models, dict):
                        continue
                    for mkey, mval in models.items():
                        if not isinstance(mval, dict):
                            mval = {}
                        limit = mval.get("limit", {})
                        if not isinstance(limit, dict):
                            limit = {}
                        rows.append(
                            {
                                "id": f"{pkey}::{mkey}",
                                "provider": pkey,
                                "model": mkey,
                                "context": limit.get("context", ""),
                                "output": limit.get("output", ""),
                                "has_options": "✓" if mval.get("options") else "",
                                "has_variants": "✓" if mval.get("variants") else "",
                            }
                        )
                rows.sort(
                    key=lambda x: (
                        str(x.get("provider") or ""),
                        str(x.get("model") or ""),
                    )
                )
                return rows

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

            # 中文：表格开启单选能力，点击行后可用于编辑/删除
            table = ui.table(
                columns=columns,
                rows=_build_rows(),
                row_key="id",
                selection="single",
                pagination=10,
            ).classes("w-full")

            with ui.row().classes("w-full gap-2"):
                ui.button(tr("common.add"), on_click=lambda: open_add_dialog()).props(
                    "unelevated icon=add"
                )
                ui.button(tr("common.edit"), on_click=lambda: edit_selected()).props(
                    "outline icon=edit"
                )
                ui.button(
                    tr("common.delete"), on_click=lambda: delete_selected()
                ).props("outline color=negative icon=delete")
                ui.button(
                    tr("common.refresh"), on_click=lambda: ui.navigate.to("/model")
                ).props("outline icon=refresh")

            def _get_selected(require: bool = True) -> dict | None:
                selected = table.selected or []
                if selected:
                    selected_row["value"] = str(selected[0].get("id") or "")
                    return selected[0]
                selected_id = (selected_row.get("value") or "").strip()
                if selected_id:
                    for row in table.rows:
                        if str(row.get("id") or "") == selected_id:
                            return row
                if require:
                    ui.notify("请先选择一行模型", type="warning")
                return None

            def _build_model_payload(
                context_value: float | int | None,
                output_value: float | int | None,
                thinking_type_value: str,
                thinking_budget_value: float | int | None,
                options_json_text: str | None = None,
                variants_json_text: str | None = None,
            ) -> tuple[dict | None, str | None]:
                # 中文：构建写入配置的模型对象，同时校验 JSON 字段
                model_cfg: dict = {}

                context_num = int(context_value or 0)
                output_num = int(output_value or 0)
                if context_num or output_num:
                    model_cfg["limit"] = {}
                    if context_num:
                        model_cfg["limit"]["context"] = context_num
                    if output_num:
                        model_cfg["limit"]["output"] = output_num

                if thinking_type_value:
                    model_cfg.setdefault("options", {})
                    model_cfg["options"]["thinking"] = {
                        "type": thinking_type_value,
                        "budgetTokens": int(thinking_budget_value or 16000),
                    }

                if options_json_text is not None and options_json_text.strip():
                    try:
                        parsed_options = json.loads(options_json_text)
                    except Exception:
                        return None, "options 必须是合法 JSON"
                    if not isinstance(parsed_options, dict):
                        return None, "options 必须是 JSON 对象"
                    model_cfg["options"] = parsed_options

                if variants_json_text is not None and variants_json_text.strip():
                    try:
                        parsed_variants = json.loads(variants_json_text)
                    except Exception:
                        return None, "variants 必须是合法 JSON"
                    if not isinstance(parsed_variants, dict):
                        return None, "variants 必须是 JSON 对象"
                    model_cfg["variants"] = parsed_variants

                return model_cfg, None

            def _save_and_reload() -> None:
                _save_config(config)
                ui.notify(tr("common.success"), type="positive")
                ui.navigate.to("/model")

            def open_add_dialog() -> None:
                provider_options = _provider_options()
                with ui.dialog() as add_dlg, ui.card().classes("w-[560px] max-w-full"):
                    ui.label(tr("common.add") + " Model").classes("text-lg font-bold")
                    d_provider = ui.select(
                        label="Provider",
                        options=provider_options,
                        value=provider_options[0] if provider_options else "",
                    ).classes("w-full")
                    d_model_id = ui.input(
                        label="Model ID", placeholder="claude-sonnet-4-5-20250929"
                    ).classes("w-full")
                    d_context = ui.number(label="Context Window", value=0).classes(
                        "w-full"
                    )
                    d_output = ui.number(label="Max Output", value=0).classes("w-full")

                    ui.label("Thinking 配置 (可选)").classes(
                        "text-sm text-gray-500 mt-2"
                    )
                    d_thinking_type = ui.select(
                        label="Thinking Type",
                        options=["", "enabled", "disabled"],
                        value="",
                    ).classes("w-full")
                    d_thinking_budget = ui.number(
                        label="Budget Tokens", value=16000
                    ).classes("w-full")

                    def do_add() -> None:
                        pkey = str(d_provider.value or "").strip()
                        mid = str(d_model_id.value or "").strip()
                        if not pkey:
                            ui.notify("请先选择 Provider", type="warning")
                            return
                        if not mid:
                            ui.notify("请输入 Model ID", type="warning")
                            return

                        providers = _providers_map()
                        if pkey not in providers:
                            ui.notify("Provider 不存在", type="warning")
                            return
                        provider_cfg = providers.get(pkey)
                        if not isinstance(provider_cfg, dict):
                            ui.notify("Provider 配置异常", type="warning")
                            return

                        models = provider_cfg.get("models")
                        if not isinstance(models, dict):
                            models = {}
                        if mid in models:
                            ui.notify("该 Model 已存在", type="warning")
                            return

                        model_cfg, error = _build_model_payload(
                            context_value=d_context.value,
                            output_value=d_output.value,
                            thinking_type_value=str(
                                d_thinking_type.value or ""
                            ).strip(),
                            thinking_budget_value=d_thinking_budget.value,
                        )
                        if error:
                            ui.notify(error, type="warning")
                            return

                        models[mid] = model_cfg or {}
                        provider_cfg["models"] = models
                        providers[pkey] = provider_cfg
                        config["provider"] = providers
                        add_dlg.close()
                        _save_and_reload()

                    with ui.row().classes("w-full justify-end gap-2 mt-2"):
                        ui.button(tr("common.cancel"), on_click=add_dlg.close).props(
                            "flat"
                        )
                        ui.button(tr("common.save"), on_click=do_add).props(
                            "unelevated"
                        )

                add_dlg.open()

            def open_edit_dialog(selected: dict) -> None:
                old_provider = str(selected.get("provider") or "").strip()
                old_model = str(selected.get("model") or "").strip()

                providers = _providers_map()
                current_provider = providers.get(old_provider)
                if not isinstance(current_provider, dict):
                    ui.notify("选中模型所在 Provider 不存在", type="warning")
                    return
                models = current_provider.get("models", {})
                if not isinstance(models, dict):
                    ui.notify("Provider models 配置异常", type="warning")
                    return
                model_data = models.get(old_model, {})
                if not isinstance(model_data, dict):
                    model_data = {}

                limit = model_data.get("limit", {})
                if not isinstance(limit, dict):
                    limit = {}
                options = model_data.get("options", {})
                if not isinstance(options, dict):
                    options = {}
                variants = model_data.get("variants", {})
                if not isinstance(variants, dict):
                    variants = {}
                thinking = options.get("thinking", {})
                if not isinstance(thinking, dict):
                    thinking = {}

                with ui.dialog() as edit_dlg, ui.card().classes("w-[680px] max-w-full"):
                    ui.label(tr("common.edit") + " Model").classes("text-lg font-bold")

                    e_provider = ui.select(
                        label="Provider",
                        options=_provider_options(),
                        value=old_provider,
                    ).classes("w-full")
                    e_model_id = ui.input(label="Model ID", value=old_model).classes(
                        "w-full"
                    )
                    e_context = ui.number(
                        label="Context Window", value=int(limit.get("context") or 0)
                    ).classes("w-full")
                    e_output = ui.number(
                        label="Max Output", value=int(limit.get("output") or 0)
                    ).classes("w-full")

                    ui.label("Thinking 配置 (可选)").classes(
                        "text-sm text-gray-500 mt-2"
                    )
                    e_thinking_type = ui.select(
                        label="Thinking Type",
                        options=["", "enabled", "disabled"],
                        value=str(thinking.get("type") or ""),
                    ).classes("w-full")
                    e_thinking_budget = ui.number(
                        label="Budget Tokens",
                        value=int(thinking.get("budgetTokens") or 16000),
                    ).classes("w-full")

                    # 中文：编辑对话框增加 options / variants JSON 编辑能力
                    e_options_json = (
                        ui.textarea(
                            label="options (JSON)",
                            value=json.dumps(options, ensure_ascii=False, indent=2)
                            if options
                            else "",
                        )
                        .props("autogrow")
                        .classes("w-full")
                    )
                    e_variants_json = (
                        ui.textarea(
                            label="variants (JSON)",
                            value=json.dumps(variants, ensure_ascii=False, indent=2)
                            if variants
                            else "",
                        )
                        .props("autogrow")
                        .classes("w-full")
                    )

                    def do_edit_save() -> None:
                        new_provider = str(e_provider.value or "").strip()
                        new_model = str(e_model_id.value or "").strip()
                        if not new_provider:
                            ui.notify("请先选择 Provider", type="warning")
                            return
                        if not new_model:
                            ui.notify("请输入 Model ID", type="warning")
                            return

                        providers_map = _providers_map()
                        target_provider_cfg = providers_map.get(new_provider)
                        if not isinstance(target_provider_cfg, dict):
                            ui.notify("目标 Provider 不存在", type="warning")
                            return
                        target_models = target_provider_cfg.get("models")
                        if not isinstance(target_models, dict):
                            target_models = {}

                        if (
                            new_provider != old_provider or new_model != old_model
                        ) and new_model in target_models:
                            ui.notify(
                                "目标 Provider 下已存在同名 Model", type="warning"
                            )
                            return

                        model_cfg, error = _build_model_payload(
                            context_value=e_context.value,
                            output_value=e_output.value,
                            thinking_type_value=str(
                                e_thinking_type.value or ""
                            ).strip(),
                            thinking_budget_value=e_thinking_budget.value,
                            options_json_text=str(e_options_json.value or ""),
                            variants_json_text=str(e_variants_json.value or ""),
                        )
                        if error:
                            ui.notify(error, type="warning")
                            return

                        # 中文：先删旧键，再写入新键，支持 Provider/Model ID 改名
                        old_provider_cfg = providers_map.get(old_provider)
                        if isinstance(old_provider_cfg, dict):
                            old_models = old_provider_cfg.get("models")
                            if isinstance(old_models, dict):
                                old_models.pop(old_model, None)
                                old_provider_cfg["models"] = old_models
                                providers_map[old_provider] = old_provider_cfg

                        target_provider_cfg = providers_map.get(new_provider)
                        if not isinstance(target_provider_cfg, dict):
                            ui.notify("目标 Provider 配置异常", type="warning")
                            return
                        target_models = target_provider_cfg.get("models")
                        if not isinstance(target_models, dict):
                            target_models = {}
                        target_models[new_model] = model_cfg or {}
                        target_provider_cfg["models"] = target_models
                        providers_map[new_provider] = target_provider_cfg
                        config["provider"] = providers_map

                        edit_dlg.close()
                        _save_and_reload()

                    with ui.row().classes("w-full justify-end gap-2 mt-2"):
                        ui.button(tr("common.cancel"), on_click=edit_dlg.close).props(
                            "flat"
                        )
                        ui.button(tr("common.save"), on_click=do_edit_save).props(
                            "unelevated"
                        )

                edit_dlg.open()

            def edit_selected() -> None:
                selected = _get_selected(require=True)
                if selected:
                    open_edit_dialog(selected)

            def delete_selected() -> None:
                selected = _get_selected(require=True)
                if not selected:
                    return

                provider = str(selected.get("provider") or "").strip()
                model = str(selected.get("model") or "").strip()

                with ui.dialog() as del_dlg, ui.card().classes("w-[420px] max-w-full"):
                    ui.label(tr("common.confirm_delete_title")).classes(
                        "text-lg font-bold"
                    )
                    ui.label(
                        f"确认删除模型？\nProvider: {provider}\nModel ID: {model}"
                    ).classes("whitespace-pre-line")

                    def do_delete() -> None:
                        providers = _providers_map()
                        provider_cfg = providers.get(provider)
                        if not isinstance(provider_cfg, dict):
                            ui.notify("Provider 不存在", type="warning")
                            return
                        models = provider_cfg.get("models")
                        if not isinstance(models, dict) or model not in models:
                            ui.notify("未找到该模型", type="warning")
                            return

                        del models[model]
                        provider_cfg["models"] = models
                        providers[provider] = provider_cfg
                        config["provider"] = providers
                        del_dlg.close()
                        _save_and_reload()

                    with ui.row().classes("w-full justify-end gap-2 mt-2"):
                        ui.button(tr("common.cancel"), on_click=del_dlg.close).props(
                            "flat"
                        )
                        ui.button(tr("common.delete"), on_click=do_delete).props(
                            "unelevated color=negative"
                        )

                del_dlg.open()

            def on_select(_: dict) -> None:
                selected = table.selected or []
                selected_row["value"] = (
                    str(selected[0].get("id") or "") if selected else None
                )

            table.on("selection", on_select)

        render_layout(
            request=request,
            page_key="menu.model",
            content_builder=content,
            auth_enabled=auth_enabled,
        )
