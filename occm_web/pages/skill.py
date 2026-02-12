"""Skill 管理页面（真实业务逻辑）"""

from __future__ import annotations

# pyright: reportMissingImports=false

import shutil
from pathlib import Path
from typing import Any

from fastapi import Request
from nicegui import ui

from occm_core import (
    BackupManager,
    ConfigManager,
    ConfigPaths,
    DiscoveredSkill,
    SkillDiscovery,
    SkillInstaller,
    SkillMarket,
    SkillUpdater,
)  # type: ignore

from ..auth import AuthManager as WebAuth, require_auth
from ..i18n_web import tr
from ..layout import render_layout


def register_page(auth: WebAuth | None):
    auth_enabled = auth is not None
    dec = require_auth(auth) if auth else lambda f: f

    @ui.page("/skill")
    @dec
    async def skill_page(request: Request):
        config_path = ConfigPaths.get_opencode_config()

        def load_config() -> dict[str, Any]:
            cfg = ConfigManager.load_json(config_path) or {}
            if not isinstance(cfg, dict):
                cfg = {}
            skill_cfg = cfg.get("skill", {})
            if not isinstance(skill_cfg, dict):
                skill_cfg = {}
            cfg["skill"] = skill_cfg
            return cfg

        config = load_config()

        def save_config() -> bool:
            ok, _ = ConfigManager.save_json(config_path, config, BackupManager())
            if ok:
                ui.notify(tr("common.success"), type="positive")
                return True
            ui.notify(tr("common.error"), type="negative")
            return False

        def get_target_dir() -> Path:
            # 统一安装到 OpenCode 全局 skills 目录
            return Path.home() / ".config" / "opencode" / "skills"

        def ensure_skill_entry(skill_name: str) -> None:
            skill_cfg = config.get("skill", {})
            if not isinstance(skill_cfg, dict):
                skill_cfg = {}
                config["skill"] = skill_cfg
            if skill_name not in skill_cfg or not isinstance(
                skill_cfg.get(skill_name), dict
            ):
                skill_cfg[skill_name] = {"permission": "ask"}
            elif "permission" not in skill_cfg[skill_name]:
                skill_cfg[skill_name]["permission"] = "ask"

        def content():
            selected: dict[str, str | None] = {"name": None}

            with ui.tabs().classes("w-full") as tabs:
                t_installed = ui.tab("已安装 Skills")
                t_market = ui.tab("Skill 市场")

            with ui.tab_panels(tabs, value=t_installed).classes("w-full"):
                with ui.tab_panel(t_installed):
                    with ui.row().classes("w-full gap-2"):
                        ui.button(
                            "刷新", icon="refresh", on_click=lambda: refresh_installed()
                        ).props("outline")
                        ui.button(
                            "编辑权限", icon="edit", on_click=lambda: open_edit_dialog()
                        ).props("outline")
                        ui.button(
                            "删除 Skill",
                            icon="delete",
                            on_click=lambda: delete_selected(),
                        ).props("outline color=negative")
                        ui.button(
                            "检查更新",
                            icon="update",
                            on_click=lambda: refresh_installed(check_update=True),
                        ).props("outline")

                    installed_table = ui.table(
                        columns=[
                            {
                                "name": "name",
                                "label": tr("common.name"),
                                "field": "name",
                                "sortable": True,
                            },
                            {
                                "name": "source",
                                "label": "来源",
                                "field": "source",
                                "sortable": True,
                            },
                            {
                                "name": "permission",
                                "label": "权限",
                                "field": "permission",
                            },
                            {"name": "path", "label": "路径", "field": "path"},
                            {"name": "update", "label": "更新状态", "field": "update"},
                        ],
                        rows=[],
                        row_key="name",
                        selection="single",
                        pagination=12,
                    ).classes("w-full")

                    def on_select(_: Any) -> None:
                        rows = installed_table.selected or []
                        selected["name"] = rows[0]["name"] if rows else None

                    installed_table.on("selection", on_select)

                    with ui.row().classes("w-full gap-2 mt-2"):
                        gh_input = ui.input(
                            label="GitHub (user/repo 或 URL)",
                            placeholder="vercel-labs/git-release",
                        ).classes("w-96")

                        def install_from_github() -> None:
                            source = (gh_input.value or "").strip()
                            if not source:
                                ui.notify("请输入 GitHub 地址", type="warning")
                                return
                            try:
                                source_type, details = SkillInstaller.parse_source(
                                    source
                                )
                            except Exception as exc:
                                ui.notify(f"来源解析失败: {exc}", type="negative")
                                return
                            if source_type != "github":
                                ui.notify("仅支持 GitHub 地址", type="warning")
                                return

                            owner = details["owner"]
                            repo = details["repo"]
                            branch = SkillInstaller.detect_default_branch(owner, repo)
                            target_dir = get_target_dir()
                            target_dir.mkdir(parents=True, exist_ok=True)

                            success, message = SkillInstaller.install_from_github(
                                owner,
                                repo,
                                branch,
                                target_dir,
                            )
                            if not success:
                                ui.notify(message, type="negative")
                                return

                            # 安装后刷新发现列表，并补齐配置源
                            for found in SkillDiscovery.discover_all():
                                ensure_skill_entry(found.name)
                            save_config()
                            refresh_installed(check_update=False)
                            ui.notify(message, type="positive")

                        ui.button(
                            tr("common.install"),
                            icon="download",
                            on_click=install_from_github,
                        )

                    with ui.dialog() as edit_dlg, ui.card().classes("w-[420px]"):
                        ui.label("编辑 Skill 权限").classes("text-lg font-bold")
                        perm_select = ui.select(
                            label="permission",
                            options=["allow", "ask", "deny"],
                            value="ask",
                        ).classes("w-full")
                        with ui.row().classes("w-full justify-end gap-2"):
                            ui.button(
                                tr("common.cancel"), on_click=edit_dlg.close
                            ).props("flat")

                            def save_permission() -> None:
                                name = selected.get("name")
                                if not name:
                                    ui.notify("请先选择一行 Skill", type="warning")
                                    return
                                ensure_skill_entry(name)
                                config["skill"][name] = {
                                    "permission": perm_select.value or "ask"
                                }
                                if save_config():
                                    refresh_installed(check_update=False)
                                    edit_dlg.close()

                            ui.button(tr("common.save"), on_click=save_permission)

                    def open_edit_dialog() -> None:
                        name = selected.get("name")
                        if not name:
                            ui.notify("请先选择一行 Skill", type="warning")
                            return
                        ensure_skill_entry(name)
                        perm_select.value = config["skill"][name].get(
                            "permission", "ask"
                        )
                        edit_dlg.open()

                    def delete_selected() -> None:
                        name = selected.get("name")
                        if not name:
                            ui.notify("请先选择一行 Skill", type="warning")
                            return
                        target = SkillDiscovery.get_skill_by_name(name)
                        if not target:
                            ui.notify("未找到 Skill 文件目录", type="negative")
                            return
                        try:
                            shutil.rmtree(target.path.parent)
                        except Exception as exc:
                            ui.notify(f"删除失败: {exc}", type="negative")
                            return
                        if isinstance(config.get("skill"), dict):
                            config["skill"].pop(name, None)
                            save_config()
                        selected["name"] = None
                        refresh_installed(check_update=False)

                    def refresh_installed(check_update: bool = False) -> None:
                        discovered = SkillDiscovery.discover_all()
                        update_map: dict[str, str] = {}
                        if check_update and discovered:
                            for item in SkillUpdater.check_updates(discovered):
                                skill = item.get("skill")
                                if isinstance(skill, DiscoveredSkill):
                                    update_map[skill.name] = str(
                                        item.get("status") or "未知"
                                    )

                        rows: list[dict[str, Any]] = []
                        for item in discovered:
                            ensure_skill_entry(item.name)
                            rows.append(
                                {
                                    "name": item.name,
                                    "source": item.source,
                                    "permission": config["skill"]
                                    .get(item.name, {})
                                    .get("permission", "ask"),
                                    "path": str(item.path.parent),
                                    "update": update_map.get(item.name, "未检查"),
                                }
                            )
                        rows.sort(key=lambda r: r["name"])
                        installed_table.rows = rows
                        installed_table.update()

                    refresh_installed(check_update=False)

                with ui.tab_panel(t_market):
                    market_table = ui.table(
                        columns=[
                            {
                                "name": "name",
                                "label": tr("common.name"),
                                "field": "name",
                                "sortable": True,
                            },
                            {"name": "repo", "label": "仓库", "field": "repo"},
                            {
                                "name": "category",
                                "label": "分类",
                                "field": "category",
                                "sortable": True,
                            },
                            {
                                "name": "description",
                                "label": "描述",
                                "field": "description",
                            },
                        ],
                        rows=SkillMarket.get_all_skills(),
                        row_key="name",
                        selection="single",
                        pagination=10,
                    ).classes("w-full")

                    def install_from_market() -> None:
                        picked = market_table.selected or []
                        if not picked:
                            ui.notify("请先选择市场 Skill", type="warning")
                            return
                        row = picked[0]
                        repo = str(row.get("repo") or "")
                        if "/" not in repo:
                            ui.notify("市场仓库格式无效", type="negative")
                            return
                        owner, repo_name = repo.split("/", 1)
                        branch = SkillInstaller.detect_default_branch(owner, repo_name)
                        target_dir = get_target_dir()
                        target_dir.mkdir(parents=True, exist_ok=True)
                        success, message = SkillInstaller.install_from_github(
                            owner,
                            repo_name,
                            branch,
                            target_dir,
                            subdir=row.get("subdir") or None,
                        )
                        if not success:
                            ui.notify(message, type="negative")
                            return
                        for found in SkillDiscovery.discover_all():
                            ensure_skill_entry(found.name)
                        save_config()
                        ui.notify(message, type="positive")

                    with ui.row().classes("mt-2"):
                        ui.button(
                            "安装选中市场 Skill",
                            icon="download",
                            on_click=install_from_market,
                        )

        render_layout(
            request=request,
            page_key="menu.skill",
            content_builder=content,
            auth_enabled=auth_enabled,
        )
