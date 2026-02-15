"""上下文压缩配置页面（真实业务逻辑）"""

from __future__ import annotations

# pyright: reportMissingImports=false

from typing import Any

from fastapi import Request
from nicegui import ui

from occm_core import BackupManager, ConfigManager, ConfigPaths

from ..auth import AuthManager as WebAuth, require_auth
from ..i18n_web import tr
from ..layout import render_layout


def register_page(auth: WebAuth | None):
    auth_enabled = auth is not None
    dec = require_auth(auth) if auth else lambda f: f

    @ui.page("/compaction")
    @dec
    async def compaction_page(request: Request):
        config_path = ConfigPaths.get_opencode_config()
        config = ConfigManager.load_json(config_path) or {}
        if not isinstance(config, dict):
            config = {}

        def content():
            compaction = config.get("compaction", {})
            if not isinstance(compaction, dict):
                compaction = {}

            # 任务要求字段：enabled / strategy / maxTokens
            enabled_switch = ui.switch(
                tr("compaction.enable_compaction"),
                value=bool(compaction.get("enabled", True)),
            )
            strategy_select = ui.select(
                label=tr("web.compaction_strategy"),
                options=["balanced", "aggressive", "conservative"],
                value=str(compaction.get("strategy", "balanced")),
                with_input=True,
            ).classes("w-full")
            max_tokens_input = ui.number(
                label=tr("web.max_tokens"),
                value=int(compaction.get("maxTokens", 120000)),
                min=1024,
                max=1_000_000,
                step=1024,
            ).classes("w-full")

            preview = ui.code("{}", language="json").classes("w-full")

            def refresh_preview() -> None:
                data = {
                    "compaction": {
                        "enabled": bool(enabled_switch.value),
                        "strategy": str(strategy_select.value or "balanced"),
                        "maxTokens": int(max_tokens_input.value or 120000),
                    }
                }
                import json

                preview.set_content(json.dumps(data, ensure_ascii=False, indent=2))

            def do_save() -> None:
                config["compaction"] = {
                    "enabled": bool(enabled_switch.value),
                    "strategy": str(strategy_select.value or "balanced"),
                    "maxTokens": int(max_tokens_input.value or 120000),
                }
                ok, _ = ConfigManager.save_json(config_path, config, BackupManager())
                if ok:
                    ui.notify(tr("common.success"), type="positive")
                    refresh_preview()
                else:
                    ui.notify(tr("common.error"), type="negative")

            enabled_switch.on("change", lambda _: refresh_preview())
            strategy_select.on("update:model-value", lambda _: refresh_preview())
            max_tokens_input.on("update:model-value", lambda _: refresh_preview())

            with ui.row().classes("occm-toolbar mt-3"):
                ui.button(
                    tr("web.refresh_preview"), icon="refresh", on_click=refresh_preview
                ).props("outline")
                ui.button(tr("common.save"), icon="save", on_click=do_save).props(
                    "unelevated"
                )

            refresh_preview()

        render_layout(
            request=request,
            page_key="menu.compaction",
            content_builder=content,
            auth_enabled=auth_enabled,
        )
