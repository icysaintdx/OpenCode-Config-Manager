"""插件管理页面（真实业务逻辑）"""

from __future__ import annotations

# pyright: reportMissingImports=false

from typing import Any

from fastapi import Request
from nicegui import ui

from occm_core import (
    BackupManager,
    ConfigManager,
    ConfigPaths,
    PluginConfig,
    PluginManager,
)

from ..auth import AuthManager as WebAuth, require_auth
from ..i18n_web import tr
from ..layout import render_layout


def _parse_github_package(source: str) -> str:
    value = source.strip()
    if not value:
        return ""
    if value.startswith("https://github.com/"):
        repo_path = value.replace("https://github.com/", "", 1).strip("/")
        if repo_path:
            return f"github:{repo_path}"
    if "/" in value and not value.startswith("@"):
        return f"github:{value.strip('/')}"
    return value


def register_page(auth: WebAuth | None):
    auth_enabled = auth is not None
    dec = require_auth(auth) if auth else lambda f: f

    @ui.page("/plugin")
    @dec
    async def plugin_page(request: Request):
        config_path = ConfigPaths.get_opencode_config()

        def load_config() -> dict[str, Any]:
            cfg = ConfigManager.load_json(config_path) or {}
            if not isinstance(cfg, dict):
                cfg = {}
            plugins = cfg.get("plugins", [])
            if not isinstance(plugins, list):
                plugins = []
            cfg["plugins"] = plugins
            return cfg

        config = load_config()

        def save_config() -> bool:
            ok, _ = ConfigManager.save_json(config_path, config, BackupManager())
            if ok:
                ui.notify(tr("common.success"), type="positive")
                return True
            ui.notify(tr("common.error"), type="negative")
            return False

        def content():
            selected: dict[str, str | None] = {"name": None}

            with ui.row().classes("w-full gap-2"):
                ui.button(
                    tr("common.refresh"),
                    icon="refresh",
                    on_click=lambda: refresh_table(),
                ).props("outline")
                ui.button(
                    tr("web.uninstall_selected"),
                    icon="delete",
                    on_click=lambda: uninstall_selected(),
                ).props("outline color=negative")

            plugin_table = ui.table(
                columns=[
                    {
                        "name": "name",
                        "label": tr("common.name"),
                        "field": "name",
                        "sortable": True,
                    },
                    {"name": "version", "label": tr("web.version"), "field": "version"},
                    {"name": "source", "label": tr("web.source"), "field": "source"},
                    {"name": "type", "label": tr("common.type"), "field": "type"},
                ],
                rows=[],
                row_key="name",
                selection="single",
                pagination=10,
            ).classes("w-full")

            def on_select(_: Any) -> None:
                rows = plugin_table.selected or []
                selected["name"] = rows[0]["name"] if rows else None

            plugin_table.on("selection", on_select)

            with ui.row().classes("w-full gap-2 mt-2"):
                gh_input = ui.input(
                    label="GitHub URL / user/repo",
                    placeholder="https://github.com/user/repo",
                ).classes("w-96")

                def install_plugin() -> None:
                    source = (gh_input.value or "").strip()
                    if not source:
                        ui.notify(tr("web.please_enter_github_url"), type="warning")
                        return
                    package_name = _parse_github_package(source)
                    if not package_name:
                        ui.notify(tr("web.github_url_invalid"), type="negative")
                        return

                    manager_cfg = {"plugin": list(config.get("plugins", []))}
                    if not PluginManager.install_npm_plugin(
                        manager_cfg, package_name, ""
                    ):
                        ui.notify(tr("web.install_failed"), type="negative")
                        return
                    config["plugins"] = manager_cfg.get("plugin", [])
                    if save_config():
                        refresh_table()

                ui.button(
                    tr("common.install"), icon="download", on_click=install_plugin
                )

            def refresh_table() -> None:
                manager_cfg = {"plugin": list(config.get("plugins", []))}
                plugins = PluginManager.get_installed_plugins(manager_cfg)
                rows = [
                    {
                        "name": p.name,
                        "version": p.version,
                        "source": p.source,
                        "type": p.type,
                    }
                    for p in plugins
                ]
                rows.sort(key=lambda r: r["name"])
                plugin_table.rows = rows
                plugin_table.update()

            def uninstall_selected() -> None:
                name = selected.get("name")
                if not name:
                    ui.notify(tr("common.select_item_first"), type="warning")
                    return
                row = next(
                    (r for r in plugin_table.rows if r.get("name") == name), None
                )
                if not row:
                    ui.notify(tr("web.plugin_not_found"), type="negative")
                    return
                plugin = PluginConfig(
                    name=str(row.get("name") or ""),
                    version=str(row.get("version") or "latest"),
                    type=str(row.get("type") or "npm"),
                    source=str(row.get("source") or ""),
                    enabled=True,
                    description="",
                    homepage="",
                    installed_at="",
                )
                manager_cfg = {"plugin": list(config.get("plugins", []))}
                if not PluginManager.uninstall_plugin(manager_cfg, plugin):
                    ui.notify(tr("web.uninstall_failed"), type="negative")
                    return
                config["plugins"] = manager_cfg.get("plugin", [])
                selected["name"] = None
                if save_config():
                    refresh_table()

            refresh_table()

        render_layout(
            request=request,
            page_key="menu.plugin",
            content_builder=content,
            auth_enabled=auth_enabled,
        )
