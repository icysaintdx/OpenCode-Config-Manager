"""实时监控页面"""

from __future__ import annotations
from fastapi import Request
from nicegui import ui
from ..auth import AuthManager as WebAuth, require_auth
from ..i18n_web import tr
from ..layout import render_layout
from occm_core import ConfigPaths, ConfigManager


def register_page(auth: WebAuth | None):
    auth_enabled = auth is not None
    dec = require_auth(auth) if auth else lambda f: f

    @ui.page("/monitor")
    @dec
    async def monitor_page(request: Request):
        config = ConfigManager.load_json(ConfigPaths.get_opencode_config()) or {}
        providers = config.get("provider", {})
        polling = {"active": False}
        results: list[dict] = []

        def content():
            status_label = ui.label("监控未启动").classes("text-gray-500")
            result_col = ui.column().classes("w-full gap-2")

            def do_poll():
                if not polling["active"]:
                    return
                results.clear()
                for pkey, pval in providers.items():
                    if not isinstance(pval, dict):
                        continue
                    base = (pval.get("baseURL") or "").strip()
                    results.append(
                        {
                            "provider": pkey,
                            "baseURL": base or "(默认)",
                            "status": "✓ 在线" if base else "⚠ 未配置URL",
                        }
                    )
                result_col.clear()
                with result_col:
                    for r in results:
                        with ui.row().classes(
                            "w-full items-center gap-4 p-2 border rounded"
                        ):
                            ui.label(r["provider"]).classes("font-medium w-32")
                            ui.label(r["baseURL"]).classes("text-gray-600 flex-1")
                            ui.label(r["status"])

            timer = ui.timer(5.0, do_poll, active=False)

            def toggle():
                polling["active"] = not polling["active"]
                timer.active = polling["active"]
                status_label.set_text(
                    "监控运行中..." if polling["active"] else "监控已停止"
                )
                if polling["active"]:
                    do_poll()

            ui.button("开始/停止监控", icon="play_arrow", on_click=toggle).classes(
                "mt-2"
            )

        render_layout(
            request=request,
            page_key="menu.monitor",
            content_builder=content,
            auth_enabled=auth_enabled,
        )
