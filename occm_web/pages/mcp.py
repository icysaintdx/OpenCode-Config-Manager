"""MCP 服务器管理页面"""

from __future__ import annotations
from fastapi import Request
from nicegui import ui
from ..auth import AuthManager as WebAuth, require_auth
from ..i18n_web import tr
from ..layout import render_layout
from occm_core import ConfigPaths, ConfigManager, BackupManager


def _load_config() -> dict[str, object]:
    return ConfigManager.load_json(ConfigPaths.get_opencode_config()) or {}


def _load_omo() -> dict[str, object]:
    return ConfigManager.load_json(ConfigPaths.get_ohmyopencode_config()) or {}


def _save_config(config: dict[str, object]) -> None:
    ConfigManager.save_json(ConfigPaths.get_opencode_config(), config, BackupManager())


def _save_omo(config: dict[str, object]) -> None:
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
                tab_mcp = ui.tab(tr("mcp.title"))
                tab_omo = ui.tab(tr("mcp.oh_my_mcp"))

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


def _render_mcp_table(config: dict[str, object], mcp_cfg: dict[str, object]):
    import json as _json

    def _as_int(value: object, default: int = 5000) -> int:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            try:
                return int(value)
            except Exception:
                return default
        return default

    def _ensure_mcp_map() -> dict[str, object]:
        current = config.get("mcp")
        if isinstance(current, dict):
            normalized = {str(k): v for k, v in current.items()}
        else:
            normalized = {}
        config["mcp"] = normalized
        return normalized

    # 记录当前选中行，供编辑/删除复用
    selected_name: dict[str, str | None] = {"value": None}

    rows: list[dict[str, object]] = []
    for name, val in mcp_cfg.items():
        if not isinstance(val, dict):
            continue
        mtype = "remote" if val.get("url") else "local"
        cmd_value = val.get("command", [])
        if isinstance(cmd_value, list):
            cmd_display = " ".join(str(item) for item in cmd_value)
        else:
            cmd_display = ""
        rows.append(
            {
                "name": name,
                "type": mtype,
                "enabled": "✓" if val.get("enabled", True) else "✗",
                "command": cmd_display,
                "url": str(val.get("url", "")),
                "timeout": _as_int(val.get("timeout", 5000), 5000),
            }
        )

    columns = [
        {"name": "name", "label": tr("common.name"), "field": "name", "sortable": True},
        {"name": "type", "label": tr("common.type"), "field": "type"},
        {"name": "enabled", "label": tr("common.status"), "field": "enabled"},
        {"name": "command", "label": "Command", "field": "command"},
        {"name": "url", "label": "URL", "field": "url"},
        {"name": "timeout", "label": "Timeout(ms)", "field": "timeout"},
    ]

    table = ui.table(
        columns=columns,
        rows=rows,
        row_key="name",
        selection="single",
        pagination=10,
    ).classes("w-full")

    def _get_selected_name(require: bool = True) -> str | None:
        if selected_name["value"]:
            return selected_name["value"]
        selected = table.selected or []
        if selected:
            selected_name["value"] = selected[0].get("name")
            return selected_name["value"]
        if require:
            ui.notify(tr("common.select_item_first"), type="warning")
        return None

    def _on_select(_: object) -> None:
        selected = table.selected or []
        selected_name["value"] = selected[0].get("name") if selected else None

    table.on("selection", _on_select)

    def _open_upsert_dialog(mode: str, edit_key: str | None = None) -> None:
        is_edit = mode == "edit"
        default_type = "local" if mode == "add_local" else "remote"

        origin_data: dict[str, object] = {}
        if is_edit:
            current = mcp_cfg.get(edit_key or "", {})
            if isinstance(current, dict):
                origin_data = current
            default_type = "remote" if origin_data.get("url") else "local"

        initial_command = (
            origin_data.get("command", []) if isinstance(origin_data, dict) else []
        )
        if not isinstance(initial_command, list):
            initial_command = []
        initial_env = (
            origin_data.get("environment", {}) if isinstance(origin_data, dict) else {}
        )
        if not isinstance(initial_env, dict):
            initial_env = {}

        with ui.dialog() as dlg, ui.card().classes("w-[680px] max-w-full"):
            ui.label(
                tr("mcp.dialog.edit_title")
                if is_edit
                else tr("mcp.dialog.add_local_title")
            ).classes("text-lg font-bold")

            name_input = ui.input(
                label=tr("common.name"),
                value=str(edit_key or ""),
                placeholder="context7",
            ).classes("w-full")

            type_select = ui.select(
                label=tr("common.type"),
                options=["local", "remote"],
                value=default_type,
            ).classes("w-full")

            cmd_input = ui.input(
                label="Command (JSON数组)",
                value=_json.dumps(initial_command, ensure_ascii=False),
                placeholder='["npx", "-y", "@upstash/context7-mcp"]',
            ).classes("w-full")

            url_input = ui.input(
                label="URL",
                value=str(origin_data.get("url", "")),
                placeholder="https://...",
            ).classes("w-full")

            env_input = ui.input(
                label=tr("mcp.env") + " (JSON)",
                value=_json.dumps(initial_env, ensure_ascii=False),
                placeholder='{"API_KEY": "xxx"}',
            ).classes("w-full")

            timeout_input = ui.number(
                label="Timeout(ms)",
                value=_as_int(origin_data.get("timeout", 5000), 5000),
            ).classes("w-full")

            enabled_switch = ui.switch(
                tr("common.enable"),
                value=bool(origin_data.get("enabled", True)) if is_edit else True,
            )

            # 根据类型切换可见字段
            def _apply_type_visibility() -> None:
                if type_select.value == "local":
                    cmd_input.visible = True
                    url_input.visible = False
                else:
                    cmd_input.visible = False
                    url_input.visible = True

            type_select.on_value_change(lambda _: _apply_type_visibility())
            _apply_type_visibility()

            with ui.row().classes("w-full justify-end gap-2 mt-2"):
                ui.button(tr("common.cancel"), on_click=dlg.close).props("flat")

                def _do_save() -> None:
                    name = (name_input.value or "").strip()
                    if not name:
                        ui.notify(tr("mcp.dialog.name_required"), type="warning")
                        return

                    mcp_map = _ensure_mcp_map()

                    entry: dict[str, object] = {"enabled": bool(enabled_switch.value)}

                    if type_select.value == "local":
                        raw_cmd = (cmd_input.value or "").strip()
                        if not raw_cmd:
                            ui.notify(tr("mcp.dialog.command_required"), type="warning")
                            return
                        try:
                            parsed_cmd = _json.loads(raw_cmd)
                        except Exception:
                            ui.notify(
                                tr("mcp.dialog.command_invalid", error="JSON"),
                                type="warning",
                            )
                            return
                        if not isinstance(parsed_cmd, list):
                            ui.notify(
                                tr("mcp.dialog.command_invalid", error="array"),
                                type="warning",
                            )
                            return
                        entry["command"] = parsed_cmd
                    else:
                        url = (url_input.value or "").strip()
                        if not url:
                            ui.notify(tr("mcp.dialog.url_required"), type="warning")
                            return
                        entry["url"] = url

                    raw_env = (env_input.value or "").strip()
                    if raw_env:
                        try:
                            parsed_env = _json.loads(raw_env)
                        except Exception:
                            ui.notify(
                                tr("mcp.dialog.env_invalid", error="JSON"),
                                type="warning",
                            )
                            return
                        if not isinstance(parsed_env, dict):
                            ui.notify(
                                tr("mcp.dialog.env_invalid", error="object"),
                                type="warning",
                            )
                            return
                        entry["environment"] = parsed_env

                    timeout_val = _as_int(timeout_input.value, 5000)
                    if timeout_val != 5000:
                        entry["timeout"] = timeout_val

                    old_name = edit_key if is_edit else None
                    if old_name and old_name != name and name in mcp_map:
                        ui.notify(tr("mcp.dialog.name_exists"), type="warning")
                        return

                    if old_name and old_name != name:
                        mcp_map.pop(old_name, None)
                    mcp_map[name] = entry

                    _save_config(config)
                    dlg.close()
                    ui.notify(tr("common.success"), type="positive")
                    ui.navigate.to("/mcp")

                ui.button(tr("common.save"), on_click=_do_save)

        dlg.open()

    with ui.row().classes("w-full gap-2 mt-2"):
        ui.button(
            tr("mcp.add_local"),
            icon="add",
            on_click=lambda: _open_upsert_dialog("add_local"),
        )
        ui.button(
            tr("mcp.add_remote"),
            icon="add",
            on_click=lambda: _open_upsert_dialog("add_remote"),
        )

        def _on_edit() -> None:
            key = _get_selected_name(require=True)
            if not key:
                return
            _open_upsert_dialog("edit", key)

        ui.button(tr("common.edit"), icon="edit", on_click=_on_edit)

        with ui.dialog() as delete_dlg, ui.card().classes("w-[420px]"):
            ui.label(tr("common.confirm_delete_title")).classes(
                "text-base font-semibold"
            )
            delete_msg = ui.label("")

            with ui.row().classes("w-full justify-end gap-2 mt-2"):
                ui.button(tr("common.cancel"), on_click=delete_dlg.close).props("flat")

                def _confirm_delete() -> None:
                    key = _get_selected_name(require=False)
                    if not key:
                        delete_dlg.close()
                        ui.notify(tr("common.select_item_first"), type="warning")
                        return
                    mcp_map = _ensure_mcp_map()
                    mcp_map.pop(key, None)
                    _save_config(config)
                    delete_dlg.close()
                    ui.notify(tr("common.success"), type="positive")
                    ui.navigate.to("/mcp")

                ui.button(
                    tr("common.delete"), color="negative", on_click=_confirm_delete
                )

        def _on_delete() -> None:
            key = _get_selected_name(require=True)
            if not key:
                return
            delete_msg.text = tr("mcp.delete_confirm", name=key)
            delete_dlg.open()

        ui.button(
            tr("common.delete"), icon="delete", color="negative", on_click=_on_delete
        )


def _render_omo_mcp(omo: dict[str, object]):
    def _ensure_omo_mcp_map() -> dict[str, object]:
        current = omo.get("mcp")
        if isinstance(current, dict):
            normalized = {str(k): v for k, v in current.items()}
        else:
            normalized = {}
        omo["mcp"] = normalized
        return normalized

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

            # 保留原有 Oh My MCP 开关逻辑
            def toggle(n=name, s=sw):
                omo_mcp_map = _ensure_omo_mcp_map()
                target = omo_mcp_map.get(n)
                if not isinstance(target, dict):
                    target = {}
                    omo_mcp_map[n] = target
                target["enabled"] = s.value
                _save_omo(omo)
                ui.notify(tr("common.success"), type="positive")

            sw.on("change", toggle)
