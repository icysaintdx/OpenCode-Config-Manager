"""Rules 管理页面"""

from __future__ import annotations

from fastapi import Request
from nicegui import ui

from ..auth import AuthManager as WebAuth, require_auth
from ..i18n_web import tr
from ..layout import render_layout
from occm_core import BackupManager, ConfigManager, ConfigPaths


def register_page(auth: WebAuth | None):
    auth_enabled = auth is not None
    dec = require_auth(auth) if auth else lambda f: f

    @ui.page("/rules")
    @dec
    async def rules_page(request: Request):
        # 读取 OpenCode 配置并兜底
        config = ConfigManager.load_json(ConfigPaths.get_opencode_config()) or {}
        instructions = config.get("instructions", [])
        if not isinstance(instructions, list):
            instructions = []

        def content():
            # 表格行：通过索引定位到源列表
            rows = [{"idx": i, "path": str(p)} for i, p in enumerate(instructions)]
            cols = [
                {"name": "idx", "label": "#", "field": "idx"},
                {"name": "path", "label": tr("rules.path_label"), "field": "path"},
            ]

            # 当前选中行缓存（单选）
            selected_idx: dict[str, int | None] = {"value": None}

            table = ui.table(
                columns=cols,
                rows=rows,
                row_key="idx",
                selection="single",
            ).classes("w-full")

            def on_select(_: object) -> None:
                selected = table.selected or []
                selected_idx["value"] = int(selected[0]["idx"]) if selected else None

            table.on("selection", on_select)

            def get_selected_idx(require: bool = True) -> int | None:
                # 统一获取选中索引
                idx = selected_idx.get("value")
                if idx is not None:
                    return idx
                selected = table.selected or []
                if selected:
                    idx = int(selected[0]["idx"])
                    selected_idx["value"] = idx
                    return idx
                if require:
                    ui.notify(tr("common.select_item_first"), type="warning")
                return None

            # ---- 新增对话框 ----
            with ui.dialog() as add_dlg, ui.card().classes("w-[460px]"):
                ui.label(tr("common.add") + " Instruction").classes("text-lg font-bold")
                d_path = ui.input(
                    label=tr("rules.file_path_placeholder"), placeholder="./AGENTS.md"
                ).classes("w-full")
                with ui.row().classes("w-full justify-end gap-2 mt-2"):
                    ui.button(tr("common.cancel"), on_click=add_dlg.close).props("flat")

                    def do_add():
                        # 新增 instruction 项
                        v = (d_path.value or "").strip()
                        if not v:
                            ui.notify(tr("web.please_enter_path"), type="warning")
                            return
                        if "instructions" not in config or not isinstance(
                            config.get("instructions"), list
                        ):
                            config["instructions"] = []
                        config["instructions"].append(v)
                        ConfigManager.save_json(
                            ConfigPaths.get_opencode_config(), config, BackupManager()
                        )
                        ui.notify(tr("common.success"), type="positive")
                        add_dlg.close()
                        ui.navigate.to("/rules")

                    ui.button(tr("common.save"), on_click=do_add)

            # ---- 编辑对话框 ----
            with ui.dialog() as edit_dlg, ui.card().classes("w-[460px]"):
                ui.label(tr("common.edit") + " Instruction").classes(
                    "text-lg font-bold"
                )
                e_idx = ui.input(label="#").classes("w-full").props("readonly")
                e_path = ui.input(label=tr("rules.path_label")).classes("w-full")
                with ui.row().classes("w-full justify-end gap-2 mt-2"):
                    ui.button(tr("common.cancel"), on_click=edit_dlg.close).props(
                        "flat"
                    )

                    def do_edit():
                        # 编辑 instruction：按索引覆盖原值
                        raw_idx = (e_idx.value or "").strip()
                        new_path = (e_path.value or "").strip()
                        if not raw_idx:
                            ui.notify(tr("web.edit_target_not_found"), type="warning")
                            return
                        if not new_path:
                            ui.notify(tr("web.path_cannot_be_empty"), type="warning")
                            return
                        try:
                            idx = int(raw_idx)
                        except ValueError:
                            ui.notify(tr("web.invalid_index"), type="warning")
                            return

                        if "instructions" not in config or not isinstance(
                            config.get("instructions"), list
                        ):
                            config["instructions"] = []
                        if idx < 0 or idx >= len(config["instructions"]):
                            ui.notify(tr("web.record_not_exist"), type="warning")
                            return

                        config["instructions"][idx] = new_path
                        ConfigManager.save_json(
                            ConfigPaths.get_opencode_config(), config, BackupManager()
                        )
                        ui.notify(tr("common.success"), type="positive")
                        edit_dlg.close()
                        ui.navigate.to("/rules")

                    ui.button(tr("common.save"), on_click=do_edit)

            def open_edit_dialog() -> None:
                idx = get_selected_idx()
                if idx is None:
                    return
                if idx < 0 or idx >= len(instructions):
                    ui.notify(tr("web.record_not_exist"), type="warning")
                    return
                # 编辑弹窗预填当前值
                e_idx.value = str(idx)
                e_path.value = str(instructions[idx])
                edit_dlg.open()

            # ---- 删除确认对话框 ----
            with ui.dialog() as del_dlg, ui.card().classes("w-[420px]"):
                ui.label(tr("common.confirm_delete_title")).classes("text-lg font-bold")
                del_idx = ui.input(label="#").classes("w-full").props("readonly")
                del_path = (
                    ui.input(label=tr("rules.path_label"))
                    .classes("w-full")
                    .props("readonly")
                )
                ui.label(tr("web.delete_irreversible"))
                with ui.row().classes("w-full justify-end gap-2 mt-2"):
                    ui.button(tr("common.cancel"), on_click=del_dlg.close).props("flat")

                    def do_delete():
                        # 删除 instruction：从列表中移除对应索引
                        raw_idx = (del_idx.value or "").strip()
                        if not raw_idx:
                            ui.notify(tr("web.delete_target_not_found"), type="warning")
                            return
                        try:
                            idx = int(raw_idx)
                        except ValueError:
                            ui.notify(tr("web.invalid_index"), type="warning")
                            return

                        if "instructions" not in config or not isinstance(
                            config.get("instructions"), list
                        ):
                            config["instructions"] = []
                        if idx < 0 or idx >= len(config["instructions"]):
                            ui.notify(tr("web.record_not_exist"), type="warning")
                            return

                        config["instructions"].pop(idx)
                        ConfigManager.save_json(
                            ConfigPaths.get_opencode_config(), config, BackupManager()
                        )
                        ui.notify(tr("common.success"), type="positive")
                        del_dlg.close()
                        ui.navigate.to("/rules")

                    ui.button(tr("common.delete"), on_click=do_delete).props(
                        "color=negative"
                    )

            def open_delete_dialog() -> None:
                idx = get_selected_idx()
                if idx is None:
                    return
                if idx < 0 or idx >= len(instructions):
                    ui.notify(tr("web.record_not_exist"), type="warning")
                    return
                del_idx.value = str(idx)
                del_path.value = str(instructions[idx])
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
            page_key="menu.rules",
            content_builder=content,
            auth_enabled=auth_enabled,
        )
