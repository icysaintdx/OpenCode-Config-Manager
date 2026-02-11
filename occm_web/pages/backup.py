"""备份管理页面"""

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

    @ui.page("/backup")
    @dec
    async def backup_page(request: Request):
        bm = BackupManager()

        def content():
            backup_dir = ConfigPaths.get_backup_dir()
            files = (
                sorted(
                    backup_dir.glob("*.json"),
                    key=lambda p: p.stat().st_mtime,
                    reverse=True,
                )
                if backup_dir.exists()
                else []
            )
            rows = []
            for f in files:
                st = f.stat()
                from datetime import datetime

                rows.append(
                    {
                        "name": f.name,
                        "size": f"{st.st_size:,} B",
                        "time": datetime.fromtimestamp(st.st_mtime).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                    }
                )
            cols = [
                {
                    "name": "name",
                    "label": tr("common.name"),
                    "field": "name",
                    "sortable": True,
                },
                {"name": "size", "label": "大小", "field": "size"},
                {"name": "time", "label": "时间", "field": "time", "sortable": True},
            ]
            ui.table(columns=cols, rows=rows, row_key="name").classes("w-full")

            def do_backup():
                bm.backup(ConfigPaths.get_opencode_config(), tag="manual")
                ui.notify(tr("common.success"), type="positive")
                ui.navigate.to("/backup")

            ui.button("创建备份", icon="backup", on_click=do_backup).classes("mt-2")

        render_layout(
            request=request,
            page_key="menu.backup",
            content_builder=content,
            auth_enabled=auth_enabled,
        )
