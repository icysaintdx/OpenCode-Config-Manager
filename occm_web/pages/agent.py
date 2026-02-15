"""Agent 配置页面 (OpenCode + Oh My OpenCode)"""
# pyright: reportMissingTypeArgument=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownParameterType=false, reportUnknownArgumentType=false, reportUnknownLambdaType=false, reportUntypedFunctionDecorator=false, reportUnusedFunction=false, reportUnusedCallResult=false, reportUnnecessaryIsInstance=false

from __future__ import annotations
import json
import importlib
from fastapi import Request
from nicegui import ui
from ..auth import AuthManager as WebAuth, require_auth
from ..i18n_web import tr
from ..layout import render_layout

# 中文注释：通过动态导入规避编辑器静态路径误报，同时保持运行时行为不变
_occm_core = importlib.import_module("occm_core")
ConfigPaths = _occm_core.ConfigPaths
ConfigManager = _occm_core.ConfigManager
BackupManager = _occm_core.BackupManager


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
            # 中文注释：构建表格行数据，统一处理异常结构
            rows = []
            for k, v in agents.items():
                if not isinstance(v, dict):
                    v = {}
                rows.append(
                    {
                        "name": k,
                        "mode": v.get("mode", ""),
                        "temperature": v.get("temperature", ""),
                        "maxSteps": v.get("maxSteps", ""),
                        "disabled": tr("common.yes")
                        if v.get("disable")
                        else tr("common.no"),
                        "hidden": tr("common.yes")
                        if v.get("hidden")
                        else tr("common.no"),
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
                {"name": "maxSteps", "label": "Max Steps", "field": "maxSteps"},
                {"name": "disabled", "label": tr("common.status"), "field": "disabled"},
                {"name": "hidden", "label": "Hidden", "field": "hidden"},
            ]

            # 中文注释：单选表格，后续编辑/删除基于当前选中行
            table = ui.table(
                columns=cols, rows=rows, row_key="name", selection="single"
            ).classes("w-full")

            def _get_selected_name() -> str:
                selected = table.selected or []
                if not selected:
                    return ""
                item = selected[0]
                if not isinstance(item, dict):
                    return ""
                return str(item.get("name") or "")

            # 中文注释：新增和编辑共用对话框，通过 edit_target 区分模式
            edit_target = {"original": ""}
            with ui.dialog() as dlg, ui.card().classes("w-[700px]"):
                title = ui.label(tr("common.add") + " Agent").classes(
                    "text-lg font-bold"
                )
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
                d_steps = ui.number(label="Max Steps", value=10, min=1, step=1).classes(
                    "w-full"
                )
                d_prompt = ui.textarea(label="System Prompt").classes("w-full")
                with ui.row().classes("w-full gap-6"):
                    d_disable = ui.switch("Disable", value=False)
                    d_hidden = ui.switch("Hidden", value=False)
                d_tools = (
                    ui.textarea(
                        label="Tools(JSON)",
                        placeholder='["Read", "Write"]',
                    )
                    .props("autogrow")
                    .classes("w-full")
                )

                def _open_add():
                    edit_target["original"] = ""
                    title.set_text(tr("common.add") + " Agent")
                    d_name.value = ""
                    d_mode.value = "primary"
                    d_temp.value = 0.5
                    d_steps.value = 10
                    d_prompt.value = ""
                    d_disable.value = False
                    d_hidden.value = False
                    d_tools.value = "[]"
                    dlg.open()

                def _open_edit():
                    selected_name = _get_selected_name()
                    if not selected_name:
                        ui.notify(tr("common.select_item_first"), type="warning")
                        return
                    current = agents.get(selected_name, {})
                    if not isinstance(current, dict):
                        current = {}
                    edit_target["original"] = selected_name
                    title.set_text(tr("common.edit") + " Agent")
                    d_name.value = selected_name
                    d_mode.value = current.get("mode", "primary")
                    d_temp.value = float(current.get("temperature", 0.5) or 0.5)
                    d_steps.value = int(current.get("maxSteps", 10) or 10)
                    d_prompt.value = current.get("prompt", "")
                    d_disable.value = bool(current.get("disable", False))
                    d_hidden.value = bool(current.get("hidden", False))
                    tools = current.get("tools", [])
                    d_tools.value = json.dumps(
                        tools if isinstance(tools, list) else [], ensure_ascii=False
                    )
                    dlg.open()

                with ui.row().classes("w-full justify-end gap-2 mt-2"):
                    ui.button(tr("common.cancel"), on_click=dlg.close).props("flat")

                    def do_save():
                        # 中文注释：保存前进行基础校验与JSON反序列化
                        n = (d_name.value or "").strip()
                        if not n:
                            ui.notify(tr("web.please_enter_name"), type="warning")
                            return

                        try:
                            parsed_tools = json.loads(
                                (d_tools.value or "[]").strip() or "[]"
                            )
                        except Exception:
                            ui.notify(tr("web.tools_must_be_json"), type="warning")
                            return
                        if not isinstance(parsed_tools, list):
                            ui.notify(tr("web.tools_must_be_array"), type="warning")
                            return

                        entry: dict = {
                            "mode": d_mode.value or "primary",
                            "temperature": float(d_temp.value or 0.5),
                            "maxSteps": int(d_steps.value or 10),
                            "prompt": d_prompt.value or "",
                            "disable": bool(d_disable.value),
                            "hidden": bool(d_hidden.value),
                            "tools": parsed_tools,
                        }

                        if "agent" not in config:
                            config["agent"] = {}

                        original = edit_target["original"]
                        if original and original != n and original in config["agent"]:
                            del config["agent"][original]
                        config["agent"][n] = entry

                        _save_oc(config)
                        ui.notify(tr("common.success"), type="positive")
                        dlg.close()
                        ui.navigate.to("/agent-opencode")

                    ui.button(tr("common.save"), on_click=do_save)

            # 中文注释：删除确认弹窗，避免误删
            with ui.dialog() as del_dlg, ui.card().classes("w-[420px]"):
                del_text = ui.label(tr("web.confirm_delete_agent"))
                with ui.row().classes("w-full justify-end gap-2 mt-2"):
                    ui.button(tr("common.cancel"), on_click=del_dlg.close).props("flat")

                    def _do_delete():
                        selected_name = _get_selected_name()
                        if not selected_name:
                            ui.notify(tr("common.select_item_first"), type="warning")
                            del_dlg.close()
                            return
                        if "agent" not in config or not isinstance(
                            config["agent"], dict
                        ):
                            config["agent"] = {}
                        if selected_name in config["agent"]:
                            del config["agent"][selected_name]
                            _save_oc(config)
                            ui.notify(tr("common.success"), type="positive")
                        del_dlg.close()
                        ui.navigate.to("/agent-opencode")

                    ui.button(
                        tr("common.delete"), color="negative", on_click=_do_delete
                    )

            with ui.row().classes("mt-2 gap-2"):
                ui.button(tr("common.add"), icon="add", on_click=_open_add)
                ui.button(tr("common.edit"), icon="edit", on_click=_open_edit)

                def _open_delete_confirm():
                    selected_name = _get_selected_name()
                    if not selected_name:
                        ui.notify(tr("common.select_item_first"), type="warning")
                        return
                    del_text.set_text(
                        f"{tr('common.confirm_delete_title')}: {selected_name}"
                    )
                    del_dlg.open()

                ui.button(
                    tr("common.delete"),
                    icon="delete",
                    color="negative",
                    on_click=_open_delete_confirm,
                )

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

        # 从 opencode.json 读取 provider 和 model 列表供下拉选择
        oc_cfg = _load_oc()
        _providers_map = oc_cfg.get("provider", {})
        if not isinstance(_providers_map, dict):
            _providers_map = {}

        def _provider_options() -> list[str]:
            return sorted(_providers_map.keys())

        def _model_options(provider_key: str) -> list[str]:
            pdata = _providers_map.get(provider_key, {})
            if not isinstance(pdata, dict):
                return []
            models = pdata.get("models", {})
            if not isinstance(models, dict):
                return []
            return sorted(models.keys())

        def _all_model_options() -> list[str]:
            result: list[str] = []
            for pkey, pdata in _providers_map.items():
                if not isinstance(pdata, dict):
                    continue
                models = pdata.get("models", {})
                if not isinstance(models, dict):
                    continue
                result.extend(sorted(models.keys()))
            return result

        def content():
            # 中文注释：构建 OMO Agent 列表
            rows = [
                {
                    "name": k,
                    "provider": (v.get("provider", "") if isinstance(v, dict) else ""),
                    "model": (v.get("model", "") if isinstance(v, dict) else ""),
                    "description": (
                        v.get("description", "") if isinstance(v, dict) else ""
                    ),
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
                {"name": "description", "label": "Description", "field": "description"},
            ]

            # 中文注释：单选模式，为编辑和删除提供当前行上下文
            table = ui.table(
                columns=cols, rows=rows, row_key="name", selection="single"
            ).classes("w-full")

            def _get_selected_name() -> str:
                selected = table.selected or []
                if not selected:
                    return ""
                item = selected[0]
                if not isinstance(item, dict):
                    return ""
                return str(item.get("name") or "")

            # 中文注释：新增与编辑复用同一个对话框
            edit_target = {"original": ""}
            with ui.dialog() as dlg, ui.card().classes("w-[600px]"):
                title = ui.label(tr("common.add") + " OMO Agent").classes(
                    "text-lg font-bold"
                )
                d_name = ui.input(
                    label=tr("common.name"), placeholder="oracle"
                ).classes("w-full")
                d_prov = ui.select(
                    label="Provider",
                    options=_provider_options(),
                    value="",
                    with_input=True,
                ).classes("w-full")
                d_model = ui.select(
                    label="Model",
                    options=_all_model_options(),
                    value="",
                    with_input=True,
                ).classes("w-full")

                def _on_provider_change(e):
                    pkey = str(e.value or "")
                    d_model.options = _model_options(pkey)
                    d_model.update()

                d_prov.on_value_change(_on_provider_change)
                d_desc = (
                    ui.textarea(label="Description").props("autogrow").classes("w-full")
                )

                def _open_add():
                    edit_target["original"] = ""
                    title.set_text(tr("common.add") + " OMO Agent")
                    d_name.value = ""
                    d_prov.value = ""
                    d_model.value = ""
                    d_desc.value = ""
                    dlg.open()

                def _open_edit():
                    selected_name = _get_selected_name()
                    if not selected_name:
                        ui.notify(tr("common.select_item_first"), type="warning")
                        return
                    current = agents.get(selected_name, {})
                    if not isinstance(current, dict):
                        current = {}
                    edit_target["original"] = selected_name
                    title.set_text(tr("common.edit") + " OMO Agent")
                    d_name.value = selected_name
                    d_prov.value = current.get("provider", "")
                    d_model.value = current.get("model", "")
                    d_desc.value = current.get("description", "")
                    dlg.open()

                with ui.row().classes("w-full justify-end gap-2 mt-2"):
                    ui.button(tr("common.cancel"), on_click=dlg.close).props("flat")

                    def do_save():
                        n = (d_name.value or "").strip()
                        if not n:
                            ui.notify(tr("web.please_enter_name"), type="warning")
                            return
                        if "agents" not in omo:
                            omo["agents"] = {}

                        entry = {
                            "provider": d_prov.value or "",
                            "model": d_model.value or "",
                            "description": d_desc.value or "",
                        }

                        original = edit_target["original"]
                        if original and original != n and original in omo["agents"]:
                            del omo["agents"][original]
                        omo["agents"][n] = entry

                        _save_omo(omo)
                        ui.notify(tr("common.success"), type="positive")
                        dlg.close()
                        ui.navigate.to("/agent-omo")

                    ui.button(tr("common.save"), on_click=do_save)

            # 中文注释：删除确认弹窗，删除前再次确认
            with ui.dialog() as del_dlg, ui.card().classes("w-[420px]"):
                del_text = ui.label(tr("web.confirm_delete_omo_agent"))
                with ui.row().classes("w-full justify-end gap-2 mt-2"):
                    ui.button(tr("common.cancel"), on_click=del_dlg.close).props("flat")

                    def _do_delete():
                        selected_name = _get_selected_name()
                        if not selected_name:
                            ui.notify(tr("common.select_item_first"), type="warning")
                            del_dlg.close()
                            return
                        if "agents" not in omo or not isinstance(omo["agents"], dict):
                            omo["agents"] = {}
                        if selected_name in omo["agents"]:
                            del omo["agents"][selected_name]
                            _save_omo(omo)
                            ui.notify(tr("common.success"), type="positive")
                        del_dlg.close()
                        ui.navigate.to("/agent-omo")

                    ui.button(
                        tr("common.delete"), color="negative", on_click=_do_delete
                    )

            with ui.row().classes("mt-2 gap-2"):
                ui.button(tr("common.add"), icon="add", on_click=_open_add)
                ui.button(tr("common.edit"), icon="edit", on_click=_open_edit)

                def _open_delete_confirm():
                    selected_name = _get_selected_name()
                    if not selected_name:
                        ui.notify(tr("common.select_item_first"), type="warning")
                        return
                    del_text.set_text(
                        f"{tr('common.confirm_delete_title')}: {selected_name}"
                    )
                    del_dlg.open()

                ui.button(
                    tr("common.delete"),
                    icon="delete",
                    color="negative",
                    on_click=_open_delete_confirm,
                )

        render_layout(
            request=request,
            page_key="menu.ohmyagent",
            content_builder=content,
            auth_enabled=auth_enabled,
        )
