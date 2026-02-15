"""外部导入页面（真实业务逻辑）"""

from __future__ import annotations

# pyright: reportMissingImports=false

import json
from typing import Any

from fastapi import Request
from nicegui import ui

from occm_core import BackupManager, ConfigManager, ConfigPaths, ImportService

from ..auth import AuthManager as WebAuth, require_auth
from ..i18n_web import tr
from ..layout import render_layout


SUPPORTED_TYPES = {"claude": "Claude Code", "codex": "Codex", "gemini": "Gemini"}


def register_page(auth: WebAuth | None):
    auth_enabled = auth is not None
    dec = require_auth(auth) if auth else lambda f: f

    @ui.page("/external-import")
    @dec
    async def import_page(request: Request):
        service = ImportService()
        config_path = ConfigPaths.get_opencode_config()

        def load_config() -> dict[str, Any]:
            cfg = ConfigManager.load_json(config_path) or {}
            return cfg if isinstance(cfg, dict) else {}

        config = load_config()

        def save_config() -> bool:
            ok, _ = ConfigManager.save_json(config_path, config, BackupManager())
            if ok:
                ui.notify(tr("import.import_success"), type="positive")
                return True
            ui.notify(tr("import.import_failed"), type="negative")
            return False

        def content():
            selected = {"type": None}
            converted_cache: dict[str, dict[str, Any]] = {}

            with ui.row().classes("occm-toolbar"):
                ui.button(
                    tr("web.scan_detect"),
                    icon="search",
                    on_click=lambda: scan_sources(),
                ).props("unelevated")
                ui.button(
                    tr("import.preview_convert"),
                    icon="preview",
                    on_click=lambda: preview_selected(),
                ).props("outline")
                ui.button(
                    tr("import.import_selected"),
                    icon="download",
                    on_click=lambda: import_selected(),
                ).props("outline")

            source_table = ui.table(
                columns=[
                    {
                        "name": "source",
                        "label": tr("import.source"),
                        "field": "source",
                        "sortable": True,
                    },
                    {
                        "name": "type",
                        "label": tr("common.type"),
                        "field": "type",
                        "sortable": True,
                    },
                    {"name": "exists", "label": tr("import.status"), "field": "exists"},
                    {
                        "name": "path",
                        "label": tr("import.config_path"),
                        "field": "path",
                    },
                ],
                rows=[],
                row_key="type",
                selection="single",
                pagination=10,
            ).classes("w-full occm-table")

            def on_select(_: Any) -> None:
                rows = source_table.selected or []
                selected["type"] = rows[0]["type"] if rows else None

            source_table.on("selection", on_select)

            preview_label = ui.label(tr("web.preview_hint")).classes("text-gray-600")
            preview_code = ui.code("{}", language="json").classes("w-full")

            def scan_sources() -> None:
                results = service.scan_external_configs()
                rows: list[dict[str, Any]] = []
                for name, info in results.items():
                    source_type = str(info.get("type") or "")
                    if source_type not in SUPPORTED_TYPES:
                        continue
                    exists = bool(info.get("exists"))
                    rows.append(
                        {
                            "source": SUPPORTED_TYPES[source_type],
                            "type": source_type,
                            "exists": "✅ " + tr("import.detected")
                            if exists
                            else "❌ " + tr("import.not_detected"),
                            "path": str(info.get("path") or ""),
                        }
                    )
                rows.sort(key=lambda r: r["source"])
                source_table.rows = rows
                source_table.update()
                converted_cache.clear()
                preview_label.set_text(tr("web.scan_done_select"))
                preview_code.set_content("{}")

            def preview_selected() -> None:
                source_type = selected.get("type")
                if not source_type:
                    ui.notify(tr("common.select_item_first"), type="warning")
                    return
                results = service.scan_external_configs()
                matched = None
                for info in results.values():
                    if info.get("type") == source_type:
                        matched = info
                        break
                if not matched or not matched.get("exists"):
                    ui.notify(tr("web.source_not_detected"), type="warning")
                    return
                converted = service.convert_to_opencode(
                    source_type, matched.get("data") or {}
                )
                if not converted:
                    ui.notify(tr("web.convert_failed"), type="negative")
                    return
                converted_cache[source_type] = converted
                preview_label.set_text(
                    f"{SUPPORTED_TYPES[source_type]} {tr('web.convert_preview')}"
                )
                preview_code.set_content(
                    json.dumps(converted, ensure_ascii=False, indent=2)
                )

            def import_selected() -> None:
                source_type = selected.get("type")
                if not source_type:
                    ui.notify(tr("common.select_item_first"), type="warning")
                    return
                converted = converted_cache.get(source_type)
                if not converted:
                    ui.notify(tr("web.please_preview_first"), type="warning")
                    return

                # 合并 provider/permission 到现有 OpenCode 配置
                providers = converted.get("provider", {})
                permissions = converted.get("permission", {})

                if "provider" not in config or not isinstance(
                    config.get("provider"), dict
                ):
                    config["provider"] = {}
                if "permission" not in config or not isinstance(
                    config.get("permission"), dict
                ):
                    config["permission"] = {}

                config["provider"].update(
                    providers if isinstance(providers, dict) else {}
                )
                config["permission"].update(
                    permissions if isinstance(permissions, dict) else {}
                )
                save_config()

            scan_sources()

        render_layout(
            request=request,
            page_key="menu.import",
            content_builder=content,
            auth_enabled=auth_enabled,
        )
