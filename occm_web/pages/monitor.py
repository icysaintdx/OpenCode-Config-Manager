"""实时监控页面（真实业务逻辑）"""

from __future__ import annotations

# pyright: reportMissingImports=false

from typing import Any

from fastapi import Request
from nicegui import ui

from occm_core import (
    ConfigManager,
    ConfigPaths,
    MonitorResult,
    MonitorService,
    MonitorTarget,
)

from ..auth import AuthManager as WebAuth, require_auth
from ..i18n_web import tr
from ..layout import render_layout


def _status_text(status: str) -> str:
    mapping = {
        "operational": "✅ " + "OK",
        "degraded": "⚠️ " + "Degraded",
        "failed": "❌ " + "Failed",
        "error": "❌ " + "Error",
        "no_config": "ℹ️ " + "No Config",
    }
    return mapping.get(status, status)


def register_page(auth: WebAuth | None):
    auth_enabled = auth is not None
    dec = require_auth(auth) if auth else lambda f: f

    @ui.page("/monitor")
    @dec
    async def monitor_page(request: Request):
        config = ConfigManager.load_json(ConfigPaths.get_opencode_config()) or {}
        if not isinstance(config, dict):
            config = {}

        service = MonitorService(poll_interval_ms=10000)
        service.set_chat_test_enabled(True)

        def content():
            running = {"value": False}
            poll_done_flag = {"value": False}
            targets_cache: list = []

            status_label = ui.label(tr("web.monitor_not_started")).classes(
                "text-gray-500"
            )

            with ui.row().classes("w-full gap-2"):
                ui.button(
                    tr("web.refresh_targets"),
                    icon="refresh",
                    on_click=lambda: refresh_targets(),
                ).props("outline")
                ui.button(
                    tr("monitor.start_monitoring"),
                    icon="play_arrow",
                    on_click=lambda: start_monitor(),
                ).props("unelevated")
                ui.button(
                    tr("monitor.stop_monitoring"),
                    icon="stop",
                    on_click=lambda: stop_monitor(),
                ).props("outline")

            result_table = ui.table(
                columns=[
                    {
                        "name": "target_id",
                        "label": tr("web.target_id"),
                        "field": "target_id",
                        "sortable": True,
                    },
                    {"name": "provider", "label": "Provider", "field": "provider"},
                    {"name": "model", "label": "Model", "field": "model"},
                    {"name": "status", "label": tr("common.status"), "field": "status"},
                    {
                        "name": "latency_ms",
                        "label": tr("web.latency_ms"),
                        "field": "latency_ms",
                        "sortable": True,
                    },
                    {
                        "name": "ping_ms",
                        "label": "Ping(ms)",
                        "field": "ping_ms",
                        "sortable": True,
                    },
                    {
                        "name": "checked_at",
                        "label": tr("web.check_time"),
                        "field": "checked_at",
                        "sortable": True,
                    },
                    {
                        "name": "message",
                        "label": tr("web.description"),
                        "field": "message",
                    },
                ],
                rows=[],
                row_key="target_id",
                pagination=10,
            ).classes("w-full")

            def refresh_targets() -> None:
                targets_cache.clear()
                targets_cache.extend(service.load_targets_from_config(config))
                refresh_results()

            def refresh_results() -> None:
                rows: list[dict[str, Any]] = []
                for t in targets_cache:
                    history = list(service.get_history(t.target_id))
                    latest: MonitorResult | None = history[-1] if history else None
                    rows.append(
                        {
                            "target_id": t.target_id,
                            "provider": t.provider_name,
                            "model": t.model_name,
                            "status": _status_text(latest.status)
                            if latest
                            else tr("web.pending_check"),
                            "latency_ms": latest.latency_ms
                            if latest and latest.latency_ms is not None
                            else -1,
                            "ping_ms": latest.ping_ms
                            if latest and latest.ping_ms is not None
                            else -1,
                            "checked_at": latest.checked_at.strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )
                            if latest
                            else "-",
                            "message": latest.message
                            if latest
                            else tr("web.no_monitor_result"),
                        }
                    )
                rows.sort(key=lambda r: r["target_id"])
                result_table.rows = rows
                result_table.update()

            def start_monitor() -> None:
                if running["value"]:
                    return
                if not targets_cache:
                    refresh_targets()
                if not targets_cache:
                    ui.notify(tr("web.no_monitor_targets"), type="warning")
                    return
                service.start_polling()
                running["value"] = True
                status_label.set_text(tr("web.monitor_running"))
                status_label.classes(remove="text-gray-500")
                status_label.classes(add="text-positive")

            def stop_monitor() -> None:
                if not running["value"]:
                    return
                service.stop_polling()
                running["value"] = False
                status_label.set_text(tr("web.monitor_stopped"))
                status_label.classes(remove="text-positive")
                status_label.classes(add="text-gray-500")

            # 监听一次轮询结束事件，配合定时器刷新
            def on_poll_done() -> None:
                poll_done_flag["value"] = True

            service.add_poll_done_callback(on_poll_done)

            def tick() -> None:
                if poll_done_flag["value"] or running["value"]:
                    poll_done_flag["value"] = False
                    refresh_results()

            ui.timer(2.0, tick, active=True)

            refresh_targets()

        render_layout(
            request=request,
            page_key="menu.monitor",
            content_builder=content,
            auth_enabled=auth_enabled,
        )
