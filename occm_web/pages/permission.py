"""权限管理页面 - 内联编辑"""

from __future__ import annotations

from fastapi import Request
from nicegui import ui

from ..auth import AuthManager as WebAuth, require_auth
from ..i18n_web import tr
from ..layout import render_layout
from occm_core import BackupManager, ConfigManager, ConfigPaths

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
            config["permission"] = perms

        def _save():
            ConfigManager.save_json(
                ConfigPaths.get_opencode_config(), config, BackupManager()
            )

        def content():
            container = ui.column().classes("w-full gap-1")

            def rebuild():
                container.clear()
                with container:
                    for tool, val in list(perms.items()):
                        if isinstance(val, dict):
                            level = str(val.get("level", "ask"))
                            pattern = str(val.get("pattern", ""))
                        elif isinstance(val, str):
                            level, pattern = val, ""
                        else:
                            level, pattern = "ask", ""

                        with ui.row().classes(
                            "w-full items-center gap-2 occm-inline-row"
                        ):
                            ui.label(tool).classes("w-28 font-medium")

                            sel = ui.select(
                                options=["allow", "ask", "deny"],
                                value=level,
                            ).classes("w-32")

                            pat = ui.input(
                                label=tr("web.command_pattern_optional"),
                                value=pattern,
                            ).classes("flex-grow")

                            def _on_change(_, t=tool, s=sel, p=pat):
                                lv = str(s.value or "ask")
                                pt = (p.value or "").strip()
                                perms[t] = {"level": lv, "pattern": pt} if pt else lv
                                _save()

                            sel.on("update:model-value", _on_change)
                            pat.on("blur", _on_change)

                            def _on_del(_, t=tool):
                                perms.pop(t, None)
                                _save()
                                ui.notify(tr("common.success"), type="positive")
                                rebuild()

                            ui.button(icon="delete", on_click=_on_del).props(
                                "flat round color=negative size=sm"
                            )

                    if not perms:
                        ui.label(tr("common.no_data")).classes(
                            "text-gray-400 text-center w-full py-4"
                        )

            rebuild()

            ui.separator().classes("my-2")
            with ui.row().classes("w-full items-center gap-2"):
                new_tool = ui.select(
                    label=tr("permission.tool_name"),
                    options=BUILTIN_TOOLS,
                    value="Bash",
                    with_input=True,
                ).classes("w-40")
                new_level = ui.select(
                    options=["allow", "ask", "deny"], value="ask"
                ).classes("w-32")
                new_pattern = ui.input(
                    label=tr("web.command_pattern_optional"),
                ).classes("flex-grow")

                def do_add(_):
                    t = (new_tool.value or "").strip()
                    if not t:
                        ui.notify(tr("web.enter_valid_tool"), type="warning")
                        return
                    lv = str(new_level.value or "ask")
                    pt = (new_pattern.value or "").strip()
                    perms[t] = {"level": lv, "pattern": pt} if pt else lv
                    _save()
                    new_tool.value = "Bash"
                    new_level.value = "ask"
                    new_pattern.value = ""
                    ui.notify(tr("common.success"), type="positive")
                    rebuild()

                ui.button(tr("common.add"), icon="add", on_click=do_add).props(
                    "unelevated"
                )

        render_layout(
            request=request,
            page_key="menu.permission",
            content_builder=content,
            auth_enabled=auth_enabled,
        )
