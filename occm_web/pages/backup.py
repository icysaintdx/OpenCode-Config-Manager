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

            with ui.row().classes("w-full gap-2"):
                ui.button(
                    "创建备份", icon="backup", on_click=lambda: create_backup()
                ).props("unelevated")
                ui.button(
                    "恢复选中备份", icon="restore", on_click=lambda: restore_selected()
                ).props("outline")
                ui.button(
                    "删除选中备份", icon="delete", on_click=lambda: delete_selected()
                ).props("outline color=negative")
                ui.button(
                    "刷新", icon="refresh", on_click=lambda: refresh_table()
                ).props("outline")

            backup_table = ui.table(
                columns=[
                    {
                        "name": "file",
                        "label": "备份文件",
                        "field": "file",
                        "sortable": True,
                    },
                    {
                        "name": "time",
                        "label": "时间",
                        "field": "time",
                        "sortable": True,
                    },
                    {
                        "name": "size",
                        "label": "大小",
                        "field": "size",
                        "sortable": True,
                    },
                    {"name": "path", "label": "路径", "field": "path"},
                ],
                rows=[],
                row_key="path",
                selection="single",
                pagination=12,
            ).classes("w-full")

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
                    ui.notify("创建备份失败", type="negative")
                    return
                ui.notify(f"备份已创建: {path.name}", type="positive")
                refresh_table()

            def restore_selected() -> None:
                selected_path = selected.get("path")
                if not selected_path:
                    ui.notify("请先选择一行备份", type="warning")
                    return
                backup_path = Path(selected_path)
                ok = bm.restore(backup_path, ConfigPaths.get_opencode_config())
                if not ok:
                    ui.notify("恢复失败", type="negative")
                    return
                ui.notify("恢复成功", type="positive")

            def delete_selected() -> None:
                selected_path = selected.get("path")
                if not selected_path:
                    ui.notify("请先选择一行备份", type="warning")
                    return
                backup_path = Path(selected_path)
                ok = bm.delete_backup(backup_path)
                if not ok:
                    ui.notify("删除失败", type="negative")
                    return
                selected["path"] = None
                ui.notify("删除成功", type="positive")
                refresh_table()

            refresh_table()

        render_layout(
            request=request,
            page_key="menu.backup",
            content_builder=content,
            auth_enabled=auth_enabled,
        )
