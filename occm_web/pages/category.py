"""Category 管理页面 - 内联编辑"""

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

    @ui.page("/category")
    @dec
    async def category_page(request: Request):
        omo = ConfigManager.load_json(ConfigPaths.get_ohmyopencode_config()) or {}
        cats = omo.get("categories", {})
        if not isinstance(cats, dict):
            cats = {}
            omo["categories"] = cats

        def _save():
            ConfigManager.save_json(
                ConfigPaths.get_ohmyopencode_config(), omo, BackupManager()
            )

        def content():
            container = ui.column().classes("w-full gap-1")

            def rebuild():
                container.clear()
                with container:
                    for name, val in list(cats.items()):
                        val = val if isinstance(val, dict) else {}
                        with ui.row().classes(
                            "w-full items-center gap-2 occm-inline-row"
                        ):
                            ui.label(name).classes("w-40 font-medium truncate")
                            m_inp = ui.input(
                                label="Model",
                                value=str(val.get("model", "")),
                            ).classes("flex-grow")
                            t_num = ui.number(
                                label="Temp",
                                value=float(val.get("temperature", 0.5)),
                                min=0,
                                max=2,
                                step=0.1,
                            ).classes("w-24")

                            def _on_change(_, n=name, m=m_inp, t=t_num):
                                cats[n] = {
                                    "model": m.value or "",
                                    "temperature": float(t.value or 0.5),
                                }
                                _save()

                            m_inp.on("blur", _on_change)
                            t_num.on("blur", _on_change)

                            def _on_del(_, n=name):
                                cats.pop(n, None)
                                _save()
                                ui.notify(tr("common.success"), type="positive")
                                rebuild()

                            ui.button(icon="delete", on_click=_on_del).props(
                                "flat round color=negative size=sm"
                            )

                    if not cats:
                        ui.label(tr("common.no_data")).classes(
                            "text-gray-400 text-center w-full py-4"
                        )

            rebuild()

            ui.separator().classes("my-2")
            with ui.row().classes("w-full items-center gap-2"):
                new_name = ui.input(
                    label=tr("common.name"), placeholder="visual-engineering"
                ).classes("w-40")
                new_model = ui.input(
                    label="Model", placeholder="provider/model-id"
                ).classes("flex-grow")
                new_temp = ui.number(
                    label="Temp", value=0.5, min=0, max=2, step=0.1
                ).classes("w-24")

                def do_add(_):
                    n = (new_name.value or "").strip()
                    if not n:
                        ui.notify(tr("web.please_enter_name"), type="warning")
                        return
                    if n in cats:
                        ui.notify(tr("web.category_exists"), type="warning")
                        return
                    cats[n] = {
                        "model": new_model.value or "",
                        "temperature": float(new_temp.value or 0.5),
                    }
                    _save()
                    new_name.value = ""
                    new_model.value = ""
                    new_temp.value = 0.5
                    ui.notify(tr("common.success"), type="positive")
                    rebuild()

                ui.button(tr("common.add"), icon="add", on_click=do_add).props(
                    "unelevated"
                )

        render_layout(
            request=request,
            page_key="menu.category",
            content_builder=content,
            auth_enabled=auth_enabled,
        )
