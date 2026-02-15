from __future__ import annotations

# pyright: reportMissingImports=false

import json
from pathlib import Path
from typing import Any

from fastapi import Request
from nicegui import ui

from occm_core import AuthManager as CoreAuthManager
from occm_core import BackupManager, ConfigManager, ConfigPaths

from ..auth import AuthManager as WebAuth
from ..auth import require_auth
from ..i18n_web import tr
from ..layout import render_layout


def _file_meta(path: Path) -> dict[str, Any]:
    info = ConfigPaths.get_config_file_info(path)
    exists = bool(info.get("exists"))
    return {
        "exists": exists,
        "size": info.get("size_str", "-"),
        "mtime": info.get("mtime_str", "-"),
        "path": str(path),
    }


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def register_page(auth: WebAuth | None) -> None:
    auth_enabled = auth is not None
    dec = require_auth(auth) if auth else lambda f: f

    @ui.page("/")
    @dec
    async def home_page(request: Request) -> None:
        def content() -> None:
            opencode_path = ConfigPaths.get_opencode_config()
            ohmy_path = ConfigPaths.get_ohmyopencode_config()
            auth_path = CoreAuthManager().auth_path

            with ui.row().classes("w-full gap-4 items-stretch flex-wrap"):
                opencode_card = ui.card().classes(
                    "flex-1 min-w-[280px] occm-status-card"
                )
                ohmy_card = ui.card().classes("flex-1 min-w-[280px] occm-status-card")
                auth_card = ui.card().classes("flex-1 min-w-[280px] occm-status-card")

            with ui.row().classes("w-full gap-4 items-stretch flex-wrap mt-4"):
                providers_count = ui.element("div").classes("flex-1 min-w-[160px]")
                models_count = ui.element("div").classes("flex-1 min-w-[160px]")
                mcp_count = ui.element("div").classes("flex-1 min-w-[160px]")
                mcp_enabled_count = ui.element("div").classes("flex-1 min-w-[160px]")

            with ui.card().classes("w-full mt-4 occm-card"):
                with ui.row().classes("w-full items-center gap-2"):
                    ui.label(tr("home.validation_details")).classes(
                        "text-base font-semibold"
                    )
                    file_selector = ui.select(
                        {
                            str(
                                opencode_path
                            ): f"{tr('home.opencode_config')} ({opencode_path.name})",
                            str(
                                ohmy_path
                            ): f"{tr('home.ohmyopencode_config')} ({ohmy_path.name})",
                            str(auth_path): f"auth.json ({auth_path.name})",
                        },
                        value=str(opencode_path),
                        label=tr("home.select_config"),
                    ).classes("min-w-[320px]")
                    refresh_btn = ui.button(tr("common.refresh"))

                json_view = (
                    ui.textarea(
                        label=tr("model.full_json_preview"),
                        value="",
                    )
                    .props("readonly autogrow outlined")
                    .classes("w-full font-mono text-xs")
                )

            def render_status_card(
                target: ui.card, title: str, meta: dict[str, Any]
            ) -> None:
                target.clear()
                with target:
                    with ui.row().classes("items-center gap-2 mb-2"):
                        ui.icon(
                            "check_circle" if meta["exists"] else "cancel",
                            size="xs",
                        ).classes(
                            "text-green-400" if meta["exists"] else "text-red-400"
                        )
                        ui.label(title).classes("text-sm font-semibold")
                    ui.label(meta["path"]).classes("text-xs break-all opacity-50 mb-2")
                    with ui.row().classes("gap-4 text-xs opacity-70"):
                        ui.label(f"{meta['size']}")
                        ui.label(f"{meta['mtime']}")

            _gradients = [
                "background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)",
                "background: linear-gradient(135deg, #06b6d4 0%, #22d3ee 100%)",
                "background: linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%)",
                "background: linear-gradient(135deg, #10b981 0%, #34d399 100%)",
            ]
            _grad_idx = {"v": 0}

            def render_count_card(target: Any, title: str, value: int) -> None:  # noqa: ANN401
                target.clear()
                with target:
                    with (
                        ui.element("div")
                        .classes("occm-stat-card")
                        .style(_gradients[_grad_idx["v"] % 4])
                    ):
                        ui.label(str(value)).classes("stat-value")
                        ui.label(title).classes("stat-label")
                _grad_idx["v"] += 1

            def refresh_all() -> None:
                try:
                    opencode_cfg = _safe_dict(ConfigManager.load_json(opencode_path))
                    provider_map = _safe_dict(opencode_cfg.get("provider"))
                    mcp_map = _safe_dict(opencode_cfg.get("mcp"))

                    model_total = 0
                    for pdata in provider_map.values():
                        if isinstance(pdata, dict):
                            models = pdata.get("models", {})
                            if isinstance(models, dict):
                                model_total += len(models)

                    mcp_enabled_total = 0
                    for item in mcp_map.values():
                        if not isinstance(item, dict):
                            continue
                        if item.get("enabled", True):
                            mcp_enabled_total += 1

                    render_status_card(
                        opencode_card,
                        tr("home.opencode_config"),
                        _file_meta(opencode_path),
                    )
                    render_status_card(
                        ohmy_card,
                        tr("home.ohmyopencode_config"),
                        _file_meta(ohmy_path),
                    )
                    render_status_card(auth_card, "auth.json", _file_meta(auth_path))

                    render_count_card(
                        providers_count, tr("menu.provider"), len(provider_map)
                    )
                    render_count_card(models_count, tr("menu.model"), model_total)
                    render_count_card(mcp_count, tr("menu.mcp"), len(mcp_map))
                    render_count_card(
                        mcp_enabled_count,
                        tr("common.enabled"),
                        mcp_enabled_total,
                    )

                    selected = Path(str(file_selector.value or opencode_path))
                    loaded = ConfigManager.load_json(selected)
                    if loaded is None:
                        json_view.value = tr("home.invalid_config")
                    else:
                        json_view.value = json.dumps(
                            loaded, ensure_ascii=False, indent=2
                        )
                except Exception as exc:
                    ui.notify(f"{tr('common.error')}: {exc}", type="negative")

            def on_select_change() -> None:
                refresh_all()

            file_selector.on_value_change(lambda _: on_select_change())
            refresh_btn.on_click(refresh_all)
            refresh_all()

        render_layout(
            request=request,
            page_key="menu.home",
            content_builder=content,
            auth_enabled=auth_enabled,
        )
