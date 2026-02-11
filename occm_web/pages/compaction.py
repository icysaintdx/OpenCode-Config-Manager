"""上下文压缩配置页面"""

from __future__ import annotations
from fastapi import Request
from nicegui import ui
from ..auth import AuthManager as WebAuth, require_auth
from ..i18n_web import tr
from ..layout import render_layout
from occm_core import ConfigPaths, ConfigManager, BackupManager


def register_page(auth: WebAuth | None):
    auth_enabled = auth is not None
    dec = require_auth(auth) if auth else lambda f: f

    @ui.page("/compaction")
    @dec
    async def compaction_page(request: Request):
        config = ConfigManager.load_json(ConfigPaths.get_opencode_config()) or {}
        comp = config.get("compaction", {})
        if not isinstance(comp, dict):
            comp = {}

        def content():
            auto_val = comp.get("auto", True)
            prune_val = comp.get("prune", True)
            sw_auto = ui.switch("自动压缩 (auto)", value=auto_val)
            sw_prune = ui.switch("修剪旧输出 (prune)", value=prune_val)

            def do_save():
                if "compaction" not in config:
                    config["compaction"] = {}
                config["compaction"]["auto"] = sw_auto.value
                config["compaction"]["prune"] = sw_prune.value
                ConfigManager.save_json(
                    ConfigPaths.get_opencode_config(), config, BackupManager()
                )
                ui.notify(tr("common.success"), type="positive")

            ui.button(tr("common.save"), icon="save", on_click=do_save).classes("mt-4")

        render_layout(
            request=request,
            page_key="menu.compaction",
            content_builder=content,
            auth_enabled=auth_enabled,
        )
