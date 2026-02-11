"""原生 Provider 管理页面"""

from __future__ import annotations

# pyright: reportMissingImports=false

from typing import Any

from fastapi import Request
from nicegui import ui

from occm_core import (
    AuthManager as CoreAuthManager,
    EnvVarDetector,
    NATIVE_PROVIDERS,
    NativeProviderConfig,
    get_native_provider,
)

from ..auth import AuthManager as WebAuth, require_auth
from ..i18n_web import tr
from ..layout import render_layout


def register_page(auth: WebAuth | None) -> None:
    auth_enabled = auth is not None
    dec = require_auth(auth) if auth else lambda f: f

    @ui.page("/native-provider")
    @dec
    async def native_provider_page(request: Request) -> None:
        core_auth = CoreAuthManager()
        detector = EnvVarDetector()

        def content() -> None:
            # --- 环境变量检测区域 ---
            with ui.card().classes("w-full mb-4"):
                ui.label("环境变量检测").classes("text-lg font-bold mb-2")
                detect_container = ui.column().classes("w-full")

                def do_detect() -> None:
                    detect_container.clear()
                    detected = detector.detect_all_env_vars()
                    with detect_container:
                        if not detected:
                            ui.label("未检测到已配置的环境变量").classes(
                                "text-gray-500"
                            )
                            return
                        rows = []
                        for pid, env_map in detected.items():
                            prov = get_native_provider(pid)
                            name = prov.name if prov else pid
                            for var, val in env_map.items():
                                masked = CoreAuthManager.mask_api_key(val)
                                rows.append(
                                    {"provider": name, "env_var": var, "value": masked}
                                )
                        cols = [
                            {
                                "name": "provider",
                                "label": "Provider",
                                "field": "provider",
                                "sortable": True,
                            },
                            {
                                "name": "env_var",
                                "label": "环境变量",
                                "field": "env_var",
                            },
                            {"name": "value", "label": "值(已遮蔽)", "field": "value"},
                        ]
                        ui.table(columns=cols, rows=rows, row_key="env_var").classes(
                            "w-full"
                        )

                ui.button("检测已配置", on_click=do_detect, icon="search").props(
                    "outline"
                )

            # --- Provider 列表 ---
            with ui.card().classes("w-full"):
                ui.label("原生 Provider 列表").classes("text-lg font-bold mb-2")

                selected: dict[str, str | None] = {"value": None}

                def build_rows() -> list[dict[str, Any]]:
                    rows = []
                    for p in NATIVE_PROVIDERS:
                        pa = core_auth.get_provider_auth(p.id)
                        status = "✅ 已配置" if pa and pa.get("apiKey") else "❌ 未配置"
                        rows.append(
                            {"id": p.id, "name": p.name, "sdk": p.sdk, "status": status}
                        )
                    return rows

                cols = [
                    {"name": "id", "label": "ID", "field": "id", "sortable": True},
                    {
                        "name": "name",
                        "label": tr("common.name"),
                        "field": "name",
                        "sortable": True,
                    },
                    {"name": "sdk", "label": "SDK", "field": "sdk"},
                    {"name": "status", "label": "状态", "field": "status"},
                ]
                table = ui.table(columns=cols, rows=build_rows(), row_key="id").classes(
                    "w-full"
                )
                table.on("rowClick", lambda e: _on_select(e.args[1]["id"]))

                detail_container = ui.column().classes("w-full mt-4")

                def _on_select(pid: str) -> None:
                    selected["value"] = pid
                    _render_detail(pid)

                def _render_detail(pid: str) -> None:
                    detail_container.clear()
                    prov = get_native_provider(pid)
                    if not prov:
                        return
                    existing = core_auth.get_provider_auth(pid) or {}
                    inputs: dict[str, ui.input] = {}

                    with detail_container:
                        ui.label(f"配置 {prov.name}").classes(
                            "text-base font-semibold mb-2"
                        )

                        # 认证字段
                        for af in prov.auth_fields:
                            val = existing.get(af.key, "")
                            inp = ui.input(
                                label=af.label,
                                value=val,
                                placeholder=af.placeholder,
                                password=af.field_type == "password",
                                password_toggle_button=af.field_type == "password",
                            ).classes("w-full max-w-md")
                            inputs[af.key] = inp

                        # 选项字段
                        for of in prov.option_fields:
                            val = existing.get(of.key, of.default)
                            if of.field_type == "select" and of.options:
                                sel = ui.select(
                                    options=of.options,
                                    value=val or of.options[0],
                                    label=of.label,
                                ).classes("w-full max-w-md")
                                inputs[of.key] = sel  # type: ignore[assignment]
                            else:
                                inp = ui.input(
                                    label=of.label, value=val, placeholder=of.default
                                ).classes("w-full max-w-md")
                                inputs[of.key] = inp

                        with ui.row().classes("gap-2 mt-3"):

                            def do_save(p=pid) -> None:
                                data = {k: (v.value or "") for k, v in inputs.items()}
                                core_auth.set_provider_auth(p, data)
                                ui.notify(f"{prov.name} 已保存", type="positive")
                                table.rows = build_rows()
                                table.update()

                            def do_delete(p=pid) -> None:
                                if core_auth.delete_provider_auth(p):
                                    ui.notify(f"{prov.name} 已删除", type="info")
                                else:
                                    ui.notify("未找到配置", type="warning")
                                table.rows = build_rows()
                                table.update()
                                detail_container.clear()

                            ui.button(tr("common.save"), on_click=do_save, icon="save")
                            ui.button(
                                tr("common.delete"), on_click=do_delete, icon="delete"
                            ).props("outline color=red")

        render_layout(
            request=request,
            page_key="menu.native_provider",
            content_builder=content,
            auth_enabled=auth_enabled,
        )
