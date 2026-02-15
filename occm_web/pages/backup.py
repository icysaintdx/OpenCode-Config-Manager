"""备份管理页面（真实业务逻辑）"""

from __future__ import annotations

# pyright: reportMissingImports=false

from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import Request
from nicegui import ui

from occm_core import BackupManager, ConfigPaths

from ..auth import AuthManager as WebAuth, require_auth
from ..i18n_web import tr
from ..layout import render_layout


def register_page(auth: WebAuth | None):
    auth_enabled = auth is not None
    dec = require_auth(auth) if auth else lambda f: f

    @ui.page("/backup")
    @dec
    async def backup_page(request: Request):
        bm = BackupManager()

        def content():
            selected: dict[str, str | None] = {"path": None}

            with ui.row().classes("occm-toolbar"):
                ui.button(
                    tr("backup.create_backup"),
                    icon="backup",
                    on_click=lambda: create_backup(),
                ).props("unelevated")
                ui.button(
                    tr("backup.restore_selected"),
                    icon="restore",
                    on_click=lambda: restore_selected(),
                ).props("outline")
                ui.button(
                    tr("common.delete"),
                    icon="delete",
                    on_click=lambda: delete_selected(),
                ).props("outline color=negative")
                ui.button(
                    tr("common.refresh"),
                    icon="refresh",
                    on_click=lambda: refresh_table(),
                ).props("outline")

            backup_table = ui.table(
                columns=[
                    {
                        "name": "file",
                        "label": tr("backup.config_file"),
                        "field": "file",
                        "sortable": True,
                    },
                    {
                        "name": "time",
                        "label": tr("backup.time"),
                        "field": "time",
                        "sortable": True,
                    },
                    {
                        "name": "size",
                        "label": tr("backup.backup_size"),
                        "field": "size",
                        "sortable": True,
                    },
                    {"name": "path", "label": tr("backup.path"), "field": "path"},
                ],
                rows=[],
                row_key="path",
                selection="single",
                pagination=12,
            ).classes("w-full occm-table")

            def on_select(_: Any) -> None:
                rows = backup_table.selected or []
                selected["path"] = rows[0]["path"] if rows else None

            backup_table.on("selection", on_select)

            def refresh_table() -> None:
                rows: list[dict[str, Any]] = []
                for item in bm.list_backups():
                    backup_path = item.get("path")
                    if not isinstance(backup_path, Path) or not backup_path.exists():
                        continue
                    stat = backup_path.stat()
                    rows.append(
                        {
                            "file": backup_path.name,
                            "time": datetime.fromtimestamp(stat.st_mtime).strftime(
                                "%Y-%m-%d %H:%M:%S"
                            ),
                            "size": stat.st_size,
                            "path": str(backup_path),
                        }
                    )
                rows.sort(key=lambda r: r["time"], reverse=True)
                backup_table.rows = rows
                backup_table.update()

            def create_backup() -> None:
                # 按任务要求调用 create_backup()
                path = bm.create_backup()
                if path is None:
                    ui.notify(tr("web.backup_create_failed"), type="negative")
                    return
                ui.notify(
                    f"{tr('backup.backup_success')}: {path.name}", type="positive"
                )
                refresh_table()

            def restore_selected() -> None:
                selected_path = selected.get("path")
                if not selected_path:
                    ui.notify(tr("common.select_item_first"), type="warning")
                    return
                backup_path = Path(selected_path)
                ok = bm.restore(backup_path, ConfigPaths.get_opencode_config())
                if not ok:
                    ui.notify(tr("web.restore_failed"), type="negative")
                    return
                ui.notify(tr("backup.restore_success"), type="positive")

            def delete_selected() -> None:
                selected_path = selected.get("path")
                if not selected_path:
                    ui.notify(tr("common.select_item_first"), type="warning")
                    return
                backup_path = Path(selected_path)
                ok = bm.delete_backup(backup_path)
                if not ok:
                    ui.notify(tr("web.delete_failed"), type="negative")
                    return
                selected["path"] = None
                ui.notify(tr("backup.delete_success"), type="positive")
                refresh_table()

            refresh_table()

        render_layout(
            request=request,
            page_key="menu.backup",
            content_builder=content,
            auth_enabled=auth_enabled,
        )
