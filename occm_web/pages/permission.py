"""权限管理页面"""

from __future__ import annotations

from fastapi import Request
from nicegui import ui

from ..auth import AuthManager as WebAuth, require_auth
from ..i18n_web import tr
from ..layout import render_layout
from occm_core import BackupManager, ConfigManager, ConfigPaths

BUILTIN_TOOLS = [
    "Bash",
    "Read",
    "Write",
    "Edit",
    "Glob",
    "Grep",
    "WebFetch",
    "WebSearch",
    "Task",
]


def register_page(auth: WebAuth | None):
    auth_enabled = auth is not None
    dec = require_auth(auth) if auth else lambda f: f

    @ui.page("/permission")
    @dec
    async def permission_page(request: Request):
        # 读取 OpenCode 配置并兜底
        config = ConfigManager.load_json(ConfigPaths.get_opencode_config()) or {}
        perms = config.get("permission", {})
        if not isinstance(perms, dict):
            perms = {}

        def content():
            # 将 dict/字符串 两种配置形式统一转成表格行
            rows: list[dict[str, str]] = []
            for tool, val in perms.items():
                if isinstance(val, dict):
                    rows.append(
                        {
                            "tool": str(tool),
                            "level": str(val.get("level", "ask") or "ask"),
                            "pattern": str(val.get("pattern", "") or ""),
                        }
                    )
                elif isinstance(val, str):
                    rows.append({"tool": str(tool), "level": val, "pattern": ""})
                else:
                    rows.append({"tool": str(tool), "level": "ask", "pattern": ""})

            cols = [
                {"name": "tool", "label": "工具", "field": "tool", "sortable": True},
                {"name": "level", "label": "权限", "field": "level"},
                {"name": "pattern", "label": "模式", "field": "pattern"},
            ]

            # 当前选中行缓存（单选）
            selected_tool: dict[str, str | None] = {"value": None}

            table = ui.table(
                columns=cols,
                rows=rows,
                row_key="tool",
                selection="single",
            ).classes("w-full")

            def on_select(_: object) -> None:
                selected = table.selected or []
                selected_tool["value"] = selected[0]["tool"] if selected else None

            table.on("selection", on_select)

            def get_selected_tool(require: bool = True) -> str | None:
                # 统一获取选中工具
                tool = selected_tool.get("value")
                if tool:
                    return tool
                selected = table.selected or []
                if selected:
                    tool = selected[0]["tool"]
                    selected_tool["value"] = tool
                    return tool
                if require:
                    ui.notify("请先选择一条记录", type="warning")
                return None

            # ---- 新增对话框 ----
            with ui.dialog() as add_dlg, ui.card().classes("w-[460px]"):
                ui.label(tr("common.add") + " 权限规则").classes("text-lg font-bold")
                d_tool = ui.select(
                    label="工具",
                    options=BUILTIN_TOOLS + ["(自定义)"],
                    value="Bash",
                    with_input=True,
                ).classes("w-full")
                d_level = ui.select(
                    label="权限级别", options=["allow", "ask", "deny"], value="ask"
                ).classes("w-full")
                d_pattern = ui.input(
                    label="命令模式（可选）", placeholder="git *"
                ).classes("w-full")
                with ui.row().classes("w-full justify-end gap-2 mt-2"):
                    ui.button(tr("common.cancel"), on_click=add_dlg.close).props("flat")

                    def do_add():
                        # 新增规则：pattern 为空时写字符串，否则写对象
                        tool = (d_tool.value or "").strip()
                        if not tool or tool == "(自定义)":
                            ui.notify("请输入有效工具名", type="warning")
                            return
                        if "permission" not in config or not isinstance(
                            config.get("permission"), dict
                        ):
                            config["permission"] = {}

                        level = str(d_level.value or "ask")
                        pattern = (d_pattern.value or "").strip()
                        entry: dict[str, str] | str = level
                        if pattern:
                            entry = {"level": level, "pattern": pattern}
                        config["permission"][tool] = entry

                        ConfigManager.save_json(
                            ConfigPaths.get_opencode_config(), config, BackupManager()
                        )
                        ui.notify(tr("common.success"), type="positive")
                        add_dlg.close()
                        ui.navigate.to("/permission")

                    ui.button(tr("common.save"), on_click=do_add)

            # ---- 编辑对话框 ----
            with ui.dialog() as edit_dlg, ui.card().classes("w-[460px]"):
                ui.label(tr("common.edit") + " 权限规则").classes("text-lg font-bold")
                e_tool = ui.input(label="工具").classes("w-full").props("readonly")
                e_level = ui.select(
                    label="权限级别", options=["allow", "ask", "deny"], value="ask"
                ).classes("w-full")
                e_pattern = ui.input(
                    label="命令模式（可选）", placeholder="git *"
                ).classes("w-full")
                with ui.row().classes("w-full justify-end gap-2 mt-2"):
                    ui.button(tr("common.cancel"), on_click=edit_dlg.close).props(
                        "flat"
                    )

                    def do_edit():
                        # 编辑规则：tool 只读，按原 key 覆盖
                        tool = (e_tool.value or "").strip()
                        if not tool:
                            ui.notify("未找到要编辑的工具", type="warning")
                            return
                        if "permission" not in config or not isinstance(
                            config.get("permission"), dict
                        ):
                            config["permission"] = {}
                        if tool not in config["permission"]:
                            ui.notify("规则不存在，可能已被删除", type="warning")
                            return

                        level = str(e_level.value or "ask")
                        pattern = (e_pattern.value or "").strip()
                        entry: dict[str, str] | str = level
                        if pattern:
                            entry = {"level": level, "pattern": pattern}
                        config["permission"][tool] = entry

                        ConfigManager.save_json(
                            ConfigPaths.get_opencode_config(), config, BackupManager()
                        )
                        ui.notify(tr("common.success"), type="positive")
                        edit_dlg.close()
                        ui.navigate.to("/permission")

                    ui.button(tr("common.save"), on_click=do_edit)

            def open_edit_dialog() -> None:
                tool = get_selected_tool()
                if not tool:
                    return
                current = perms.get(tool)
                # 编辑弹窗预填当前值
                e_tool.value = tool
                if isinstance(current, dict):
                    e_level.value = str(current.get("level", "ask") or "ask")
                    e_pattern.value = str(current.get("pattern", "") or "")
                elif isinstance(current, str):
                    e_level.value = current
                    e_pattern.value = ""
                else:
                    e_level.value = "ask"
                    e_pattern.value = ""
                edit_dlg.open()

            # ---- 删除确认对话框 ----
            with ui.dialog() as del_dlg, ui.card().classes("w-[420px]"):
                ui.label(tr("common.confirm_delete_title")).classes("text-lg font-bold")
                del_tool = ui.input(label="工具").classes("w-full").props("readonly")
                ui.label("删除后不可恢复，请确认操作。")
                with ui.row().classes("w-full justify-end gap-2 mt-2"):
                    ui.button(tr("common.cancel"), on_click=del_dlg.close).props("flat")

                    def do_delete():
                        # 删除选中权限规则
                        tool = (del_tool.value or "").strip()
                        if not tool:
                            ui.notify("未找到要删除的工具", type="warning")
                            return
                        if (
                            isinstance(config.get("permission"), dict)
                            and tool in config["permission"]
                        ):
                            del config["permission"][tool]
                            ConfigManager.save_json(
                                ConfigPaths.get_opencode_config(),
                                config,
                                BackupManager(),
                            )
                            ui.notify(tr("common.success"), type="positive")
                            del_dlg.close()
                            ui.navigate.to("/permission")
                        else:
                            ui.notify("规则不存在，可能已被删除", type="warning")

                    ui.button(tr("common.delete"), on_click=do_delete).props(
                        "color=negative"
                    )

            def open_delete_dialog() -> None:
                tool = get_selected_tool()
                if not tool:
                    return
                del_tool.value = tool
                del_dlg.open()

            # ---- 工具栏 ----
            with ui.row().classes("w-full gap-2 mt-2"):
                ui.button(tr("common.add"), icon="add", on_click=lambda: add_dlg.open())
                ui.button(
                    tr("common.edit"),
                    icon="edit",
                    on_click=lambda: open_edit_dialog(),
                ).props("outline")
                ui.button(
                    tr("common.delete"),
                    icon="delete",
                    on_click=lambda: open_delete_dialog(),
                ).props("outline color=negative")

        render_layout(
            request=request,
            page_key="menu.permission",
            content_builder=content,
            auth_enabled=auth_enabled,
        )
