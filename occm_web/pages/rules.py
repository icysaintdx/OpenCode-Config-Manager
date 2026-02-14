"""Rules 管理页面 - 内联编辑"""

from __future__ import annotations

from fastapi import Request
from nicegui import ui

from ..auth import AuthManager as WebAuth, require_auth
from ..i18n_web import tr
from ..layout import render_layout
from occm_core import BackupManager, ConfigManager, ConfigPaths


def register_page(auth: WebAuth | None):
    auth_enabled = auth is not None
    dec = require_auth(auth) if auth else lambda f: f

    @ui.page("/rules")
    @dec
    async def rules_page(request: Request):
        config = ConfigManager.load_json(ConfigPaths.get_opencode_config()) or {}
        instructions = config.get("instructions", [])
        if not isinstance(instructions, list):
            instructions = []
            config["instructions"] = instructions

        def _save():
            ConfigManager.save_json(
                ConfigPaths.get_opencode_config(), config, BackupManager()
            )

        def content():
            container = ui.column().classes("w-full gap-1")

            def rebuild():
                container.clear()
                with container:
                    for i, path in enumerate(instructions):
                        with ui.row().classes(
                            "w-full items-center gap-2 p-2 rounded hover:bg-gray-50"
                        ):
                            ui.label(f"#{i}").classes("text-gray-400 w-8 text-right")
                            inp = ui.input(value=str(path)).classes("flex-grow")

                            def _on_blur(_, idx=i, field=inp):
                                instructions[idx] = field.value or ""
                                _save()

                            inp.on("blur", _on_blur)

                            def _on_del(_, idx=i):
                                instructions.pop(idx)
                                _save()
                                ui.notify(tr("common.success"), type="positive")
                                rebuild()

                            ui.button(icon="delete", on_click=_on_del).props(
                                "flat round color=negative size=sm"
                            )

                    if not instructions:
                        ui.label(tr("common.no_data")).classes(
                            "text-gray-400 text-center w-full py-4"
                        )

            rebuild()

            ui.separator().classes("my-2")
            with ui.row().classes("w-full items-center gap-2"):
                new_input = ui.input(
                    label=tr("rules.file_path_placeholder"),
                    placeholder="./AGENTS.md",
                ).classes("flex-grow")

                def do_add(_):
                    v = (new_input.value or "").strip()
                    if not v:
                        ui.notify(tr("web.please_enter_path"), type="warning")
                        return
                    instructions.append(v)
                    _save()
                    new_input.value = ""
                    ui.notify(tr("common.success"), type="positive")
                    rebuild()

                ui.button(tr("common.add"), icon="add", on_click=do_add).props(
                    "unelevated"
                )

        render_layout(
            request=request,
            page_key="menu.rules",
            content_builder=content,
            auth_enabled=auth_enabled,
        )
