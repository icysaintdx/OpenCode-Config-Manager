"""Provider + Model 合并管理页面 - 折叠展开"""

from __future__ import annotations

# pyright: reportMissingImports=false

import json
from typing import Any

from fastapi import Request
from nicegui import ui

from occm_core import (
    AuthManager as CoreAuthManager,
    BackupManager,
    ConfigManager,
    ConfigPaths,
    EnvVarDetector,
    NATIVE_PROVIDERS,
)

from ..auth import AuthManager as WebAuth
from ..auth import require_auth
from ..i18n_web import tr
from ..layout import render_layout


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def register_page(auth: WebAuth | None) -> None:
    auth_enabled = auth is not None
    dec = require_auth(auth) if auth else lambda f: f

    @ui.page("/provider")
    @dec
    async def provider_page(request: Request) -> None:
        config_path = ConfigPaths.get_opencode_config()
        auth_manager = CoreAuthManager()
        env_detector = EnvVarDetector()
        native_ids = {item.id for item in NATIVE_PROVIDERS}

        def load_config() -> dict[str, Any]:
            cfg = ConfigManager.load_json(config_path) or {}
            if not isinstance(cfg, dict):
                cfg = {}
            cfg["provider"] = _safe_dict(cfg.get("provider"))
            return cfg

        config = load_config()

        def save_config() -> bool:
            ok, _ = ConfigManager.save_json(config_path, config, BackupManager())
            if ok:
                ui.notify(tr("common.success"), type="positive")
                return True
            ui.notify(tr("common.error"), type="negative")
            return False

        def content() -> None:
            main_container = ui.column().classes("w-full gap-3")

            def open_provider_dialog(edit_key: str | None = None) -> None:
                providers = _safe_dict(config.get("provider"))
                pdata = _safe_dict(providers.get(edit_key)) if edit_key else {}
                auth_info = _safe_dict(
                    auth_manager.get_provider_auth(edit_key or "") or {}
                )
                with ui.dialog() as dlg, ui.card().classes("w-[680px] max-w-full"):
                    ui.label(
                        tr("provider.edit_provider")
                        if edit_key
                        else tr("provider.add_provider")
                    ).classes("text-base font-semibold")
                    key_in = ui.input(
                        label=tr("provider.provider_key"), value=edit_key or ""
                    ).classes("w-full")
                    if edit_key:
                        key_in.disable()
                    name_in = ui.input(
                        label=tr("provider.provider_name"),
                        value=str(pdata.get("name") or edit_key or ""),
                    ).classes("w-full")
                    sdk_in = ui.input(
                        label=tr("provider.sdk_type"), value=str(pdata.get("sdk") or "")
                    ).classes("w-full")
                    url_in = ui.input(
                        label=tr("provider.base_url"),
                        value=str(
                            _safe_dict(pdata.get("options")).get("baseURL") or ""
                        ),
                    ).classes("w-full")
                    key_val = ui.input(
                        label=tr("provider.api_key"),
                        value=str(auth_info.get("apiKey") or ""),
                        password=True,
                        password_toggle_button=True,
                    ).classes("w-full")

                    def do_save() -> None:
                        try:
                            k = str(key_in.value or "").strip()
                            if not k:
                                ui.notify(tr("provider.enter_name"), type="warning")
                                return
                            pm = _safe_dict(config.get("provider"))
                            if not edit_key and k in pm:
                                ui.notify(
                                    tr("provider.provider_exists", name=k),
                                    type="warning",
                                )
                                return
                            cur = _safe_dict(pm.get(k))
                            models = _safe_dict(cur.get("models"))
                            opts = _safe_dict(cur.get("options"))
                            burl = str(url_in.value or "").strip()
                            if burl:
                                opts["baseURL"] = burl
                            else:
                                opts.pop("baseURL", None)
                            entry: dict[str, Any] = {
                                "name": str(name_in.value or "").strip() or k,
                                "sdk": str(sdk_in.value or "").strip(),
                            }
                            if models:
                                entry["models"] = models
                            if opts:
                                entry["options"] = opts
                            pm[k] = entry
                            config["provider"] = pm
                            ak = str(key_val.value or "").strip()
                            if ak:
                                auth_manager.set_provider_auth(k, {"apiKey": ak})
                            if not save_config():
                                return
                            dlg.close()
                            rebuild()
                        except Exception as exc:
                            ui.notify(f"{tr('common.error')}: {exc}", type="negative")

                    with ui.row().classes("justify-end gap-2 w-full"):
                        ui.button(tr("common.cancel"), on_click=dlg.close).props("flat")
                        ui.button(tr("common.save"), on_click=do_save).props(
                            "unelevated"
                        )
                dlg.open()

            def open_model_dialog(pkey: str, edit_model: str | None = None) -> None:
                providers = _safe_dict(config.get("provider"))
                pcfg = _safe_dict(providers.get(pkey))
                models = _safe_dict(pcfg.get("models"))
                mdata = _safe_dict(models.get(edit_model)) if edit_model else {}
                limit = _safe_dict(mdata.get("limit"))
                options = _safe_dict(mdata.get("options"))
                variants = _safe_dict(mdata.get("variants"))
                thinking = _safe_dict(options.get("thinking"))
                with ui.dialog() as dlg, ui.card().classes("w-[680px] max-w-full"):
                    ui.label(
                        (tr("common.edit") if edit_model else tr("common.add"))
                        + " Model"
                    ).classes("text-base font-semibold")
                    mid_in = ui.input(
                        label="Model ID",
                        value=edit_model or "",
                        placeholder="claude-sonnet-4-5-20250929",
                    ).classes("w-full")
                    if edit_model:
                        mid_in.disable()
                    ctx_in = ui.number(
                        label="Context Window", value=int(limit.get("context") or 0)
                    ).classes("w-full")
                    out_in = ui.number(
                        label="Max Output", value=int(limit.get("output") or 0)
                    ).classes("w-full")
                    ui.label(tr("web.thinking_config_optional")).classes(
                        "text-sm text-gray-500 mt-2"
                    )
                    tt_in = ui.select(
                        label="Thinking Type",
                        options=["", "enabled", "disabled"],
                        value=str(thinking.get("type") or ""),
                    ).classes("w-full")
                    tb_in = ui.number(
                        label="Budget Tokens",
                        value=int(thinking.get("budgetTokens") or 16000),
                    ).classes("w-full")
                    opts_in = (
                        ui.textarea(
                            label="options (JSON)",
                            value=json.dumps(options, ensure_ascii=False, indent=2)
                            if options
                            else "",
                        )
                        .props("autogrow")
                        .classes("w-full")
                    )
                    vars_in = (
                        ui.textarea(
                            label="variants (JSON)",
                            value=json.dumps(variants, ensure_ascii=False, indent=2)
                            if variants
                            else "",
                        )
                        .props("autogrow")
                        .classes("w-full")
                    )

                    def do_save() -> None:
                        mid = str(mid_in.value or "").strip()
                        if not mid:
                            ui.notify(tr("web.please_enter_model_id"), type="warning")
                            return
                        pm = _safe_dict(config.get("provider"))
                        pc = _safe_dict(pm.get(pkey))
                        ms = _safe_dict(pc.get("models"))
                        if not edit_model and mid in ms:
                            ui.notify(tr("web.model_exists"), type="warning")
                            return
                        mcfg: dict[str, Any] = {}
                        ctx = int(ctx_in.value or 0)
                        out = int(out_in.value or 0)
                        if ctx or out:
                            mcfg["limit"] = {}
                            if ctx:
                                mcfg["limit"]["context"] = ctx
                            if out:
                                mcfg["limit"]["output"] = out
                        tt = str(tt_in.value or "").strip()
                        if tt:
                            mcfg.setdefault("options", {})
                            mcfg["options"]["thinking"] = {
                                "type": tt,
                                "budgetTokens": int(tb_in.value or 16000),
                            }
                        otxt = str(opts_in.value or "").strip()
                        if otxt:
                            try:
                                po = json.loads(otxt)
                            except Exception:
                                ui.notify(
                                    tr("web.options_must_be_json"), type="warning"
                                )
                                return
                            if not isinstance(po, dict):
                                ui.notify(
                                    tr("web.options_must_be_object"), type="warning"
                                )
                                return
                            mcfg["options"] = po
                        vtxt = str(vars_in.value or "").strip()
                        if vtxt:
                            try:
                                pv = json.loads(vtxt)
                            except Exception:
                                ui.notify(
                                    tr("web.variants_must_be_json"), type="warning"
                                )
                                return
                            if not isinstance(pv, dict):
                                ui.notify(
                                    tr("web.variants_must_be_object"), type="warning"
                                )
                                return
                            mcfg["variants"] = pv
                        if edit_model and edit_model != mid:
                            ms.pop(edit_model, None)
                        ms[mid] = mcfg
                        pc["models"] = ms
                        pm[pkey] = pc
                        config["provider"] = pm
                        if not save_config():
                            return
                        dlg.close()
                        rebuild()

                    with ui.row().classes("justify-end gap-2 w-full"):
                        ui.button(tr("common.cancel"), on_click=dlg.close).props("flat")
                        ui.button(tr("common.save"), on_click=do_save).props(
                            "unelevated"
                        )
                dlg.open()

            def delete_provider(pkey: str) -> None:
                with ui.dialog() as dlg, ui.card().classes("w-[420px] max-w-full"):
                    ui.label(tr("provider.delete_confirm_title")).classes(
                        "text-base font-semibold"
                    )
                    ui.label(tr("provider.delete_confirm", name=pkey)).classes(
                        "whitespace-pre-line"
                    )

                    def do_del() -> None:
                        pm = _safe_dict(config.get("provider"))
                        pm.pop(pkey, None)
                        config["provider"] = pm
                        auth_manager.delete_provider_auth(pkey)
                        if not save_config():
                            return
                        dlg.close()
                        rebuild()

                    with ui.row().classes("justify-end gap-2 w-full"):
                        ui.button(tr("common.cancel"), on_click=dlg.close).props("flat")
                        ui.button(tr("common.delete"), on_click=do_del).props(
                            "unelevated color=negative"
                        )
                dlg.open()

            def delete_model(pkey: str, mid: str) -> None:
                with ui.dialog() as dlg, ui.card().classes("w-[420px] max-w-full"):
                    ui.label(tr("common.confirm_delete_title")).classes(
                        "text-base font-semibold"
                    )
                    ui.label(f"Provider: {pkey}\nModel: {mid}").classes(
                        "whitespace-pre-line"
                    )

                    def do_del() -> None:
                        pm = _safe_dict(config.get("provider"))
                        pc = _safe_dict(pm.get(pkey))
                        ms = _safe_dict(pc.get("models"))
                        ms.pop(mid, None)
                        pc["models"] = ms
                        pm[pkey] = pc
                        config["provider"] = pm
                        if not save_config():
                            return
                        dlg.close()
                        rebuild()

                    with ui.row().classes("justify-end gap-2 w-full"):
                        ui.button(tr("common.cancel"), on_click=dlg.close).props("flat")
                        ui.button(tr("common.delete"), on_click=do_del).props(
                            "unelevated color=negative"
                        )
                dlg.open()

            def _refresh_native_tags(container: Any) -> None:
                container.clear()
                providers = _safe_dict(config.get("provider"))
                for item in NATIVE_PROVIDERS:
                    cfg_exists = item.id in providers
                    auth_exists = bool(auth_manager.get_provider_auth(item.id))
                    env_exists = bool(env_detector.detect_env_vars(item.id))
                    label = item.name
                    if auth_exists:
                        label += f" | {tr('native_provider.configured')}"
                    elif env_exists:
                        label += f" | {tr('native_provider.detected_env_vars')}"
                    elif cfg_exists:
                        label += f" | {tr('common.enabled')}"
                    with container:
                        color = (
                            "positive"
                            if (auth_exists or env_exists or cfg_exists)
                            else "grey"
                        )
                        ui.chip(label, color=color).props("outline")

            def _refresh_env(tbl: Any) -> None:
                rows: list[dict[str, Any]] = []
                all_detected = env_detector.detect_all_env_vars()
                for item in NATIVE_PROVIDERS:
                    detected = all_detected.get(item.id, {})
                    env_vars = ", ".join(sorted(detected.keys())) if detected else "-"
                    rows.append(
                        {
                            "provider": item.name,
                            "sdk": item.sdk,
                            "env_vars": env_vars,
                            "status": tr("native_provider.configured")
                            if detected
                            else tr("native_provider.not_configured"),
                        }
                    )
                tbl.rows = rows
                tbl.update()

            def rebuild() -> None:
                main_container.clear()
                providers = _safe_dict(config.get("provider"))
                with main_container:
                    with ui.row().classes("w-full gap-2"):
                        ui.button(
                            tr("provider.add_provider"),
                            icon="add",
                            on_click=lambda: open_provider_dialog(),
                        ).props("unelevated")
                        ui.button(
                            tr("common.refresh"),
                            icon="refresh",
                            on_click=lambda: do_refresh(),
                        ).props("outline")
                    if not providers:
                        ui.label(tr("common.no_data")).classes(
                            "text-gray-400 text-center w-full py-8"
                        )
                    for pkey in sorted(providers.keys()):
                        pdata = _safe_dict(providers.get(pkey))
                        models = _safe_dict(pdata.get("models"))
                        options = _safe_dict(pdata.get("options"))
                        auth_info = _safe_dict(
                            auth_manager.get_provider_auth(pkey) or {}
                        )
                        api_key_raw = str(
                            auth_info.get("apiKey") or auth_info.get("key") or ""
                        )
                        is_native = pkey in native_ids
                        sdk_text = str(pdata.get("sdk") or "-")
                        model_count = len(models)
                        header = f"{pkey}  |  {sdk_text}  |  {model_count} models"
                        if is_native:
                            header += f"  |  {tr('provider.native_provider')}"
                        with (
                            ui.expansion(header, icon="dns")
                            .classes("w-full")
                            .props("dense header-class='text-weight-medium'")
                        ):
                            with ui.row().classes(
                                "w-full items-center gap-4 p-2 rounded bg-white/5"
                            ):
                                ui.label(
                                    f"{tr('provider.provider_name')}: {pdata.get('name') or pkey}"
                                ).classes("text-sm")
                                ui.label(f"SDK: {sdk_text}").classes("text-sm")
                                ui.label(
                                    f"{tr('provider.base_url')}: {options.get('baseURL') or '-'}"
                                ).classes("text-sm")
                                ui.label(
                                    f"API Key: {CoreAuthManager.mask_api_key(api_key_raw) if api_key_raw else '-'}"
                                ).classes("text-sm")
                            with ui.row().classes("gap-2 my-2"):
                                ui.button(
                                    tr("provider.edit_provider"),
                                    icon="edit",
                                    on_click=lambda pk=pkey: open_provider_dialog(pk),
                                ).props("outline dense size=sm")
                                ui.button(
                                    tr("provider.delete_provider"),
                                    icon="delete",
                                    on_click=lambda pk=pkey: delete_provider(pk),
                                ).props("outline dense size=sm color=negative")
                                ui.button(
                                    tr("common.add") + " Model",
                                    icon="add",
                                    on_click=lambda pk=pkey: open_model_dialog(pk),
                                ).props("outline dense size=sm")
                            if models:
                                m_rows = []
                                for mk, mv in sorted(models.items()):
                                    if not isinstance(mv, dict):
                                        mv = {}
                                    lim = _safe_dict(mv.get("limit"))
                                    m_rows.append(
                                        {
                                            "id": mk,
                                            "model": mk,
                                            "context": lim.get("context", ""),
                                            "output": lim.get("output", ""),
                                            "has_options": "Y"
                                            if mv.get("options")
                                            else "",
                                            "has_variants": "Y"
                                            if mv.get("variants")
                                            else "",
                                        }
                                    )
                                m_cols = [
                                    {
                                        "name": "model",
                                        "label": "Model",
                                        "field": "model",
                                        "sortable": True,
                                    },
                                    {
                                        "name": "context",
                                        "label": "Context",
                                        "field": "context",
                                    },
                                    {
                                        "name": "output",
                                        "label": "Output",
                                        "field": "output",
                                    },
                                    {
                                        "name": "has_options",
                                        "label": "Options",
                                        "field": "has_options",
                                    },
                                    {
                                        "name": "has_variants",
                                        "label": "Variants",
                                        "field": "has_variants",
                                    },
                                ]
                                mtable = ui.table(
                                    columns=m_cols,
                                    rows=m_rows,
                                    row_key="id",
                                    selection="single",
                                ).classes("w-full")
                                with ui.row().classes("gap-2 mt-1"):

                                    def _edit_model(
                                        pk: str = pkey, tbl: Any = mtable
                                    ) -> None:
                                        sel = tbl.selected or []
                                        if not sel:
                                            ui.notify(
                                                tr("common.select_item_first"),
                                                type="warning",
                                            )
                                            return
                                        open_model_dialog(pk, str(sel[0]["model"]))

                                    def _del_model(
                                        pk: str = pkey, tbl: Any = mtable
                                    ) -> None:
                                        sel = tbl.selected or []
                                        if not sel:
                                            ui.notify(
                                                tr("common.select_item_first"),
                                                type="warning",
                                            )
                                            return
                                        delete_model(pk, str(sel[0]["model"]))

                                    ui.button(
                                        tr("common.edit"),
                                        icon="edit",
                                        on_click=_edit_model,
                                    ).props("outline dense size=sm")
                                    ui.button(
                                        tr("common.delete"),
                                        icon="delete",
                                        on_click=_del_model,
                                    ).props("outline dense size=sm color=negative")
                            else:
                                ui.label(tr("common.no_data")).classes(
                                    "text-gray-400 py-2"
                                )
                    ui.separator().classes("my-3")
                    with ui.card().classes("w-full"):
                        ui.label(tr("provider.native_provider")).classes(
                            "text-base font-semibold"
                        )
                        native_row = ui.row().classes("w-full gap-2 flex-wrap")
                        _refresh_native_tags(native_row)
                    with ui.card().classes("w-full mt-3"):
                        with ui.row().classes("w-full items-center justify-between"):
                            ui.label(tr("native_provider.detected_env_vars")).classes(
                                "text-base font-semibold"
                            )
                            ui.button(
                                tr("native_provider.detect_configured"),
                                on_click=lambda: _refresh_env(env_tbl),
                            ).props("outline")
                        env_tbl = ui.table(
                            columns=[
                                {
                                    "name": "provider",
                                    "label": tr("native_provider.provider"),
                                    "field": "provider",
                                },
                                {
                                    "name": "sdk",
                                    "label": tr("native_provider.sdk"),
                                    "field": "sdk",
                                },
                                {
                                    "name": "env_vars",
                                    "label": tr("native_provider.env_vars"),
                                    "field": "env_vars",
                                },
                                {
                                    "name": "status",
                                    "label": tr("common.status"),
                                    "field": "status",
                                },
                            ],
                            rows=[],
                            row_key="provider",
                            pagination=8,
                        ).classes("w-full")
                        _refresh_env(env_tbl)

            def do_refresh() -> None:
                nonlocal config
                config = load_config()
                rebuild()

            rebuild()

        render_layout(
            request=request,
            page_key="menu.provider",
            content_builder=content,
            auth_enabled=auth_enabled,
        )
