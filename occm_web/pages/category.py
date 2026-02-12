"""Category 管理页面"""

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

    @ui.page("/category")
    @dec
    async def category_page(request: Request):
        # 读取 OMO 配置并兜底，避免异常结构导致页面报错
        omo = ConfigManager.load_json(ConfigPaths.get_ohmyopencode_config()) or {}
        cats = omo.get("categories", {})
        if not isinstance(cats, dict):
            cats = {}

        def content():
            # 表格数据
            rows = [
                {
                    "name": k,
                    "model": (v.get("model", "") if isinstance(v, dict) else ""),
                    "temperature": (
                        v.get("temperature", 0.5) if isinstance(v, dict) else 0.5
                    ),
                }
                for k, v in cats.items()
            ]
            cols = [
                {
                    "name": "name",
                    "label": tr("common.name"),
                    "field": "name",
                    "sortable": True,
                },
                {"name": "model", "label": "Model", "field": "model"},
                {"name": "temperature", "label": "Temperature", "field": "temperature"},
            ]

            # 当前选中行缓存（单选）
            selected_name: dict[str, str | None] = {"value": None}

            table = ui.table(
                columns=cols,
                rows=rows,
                row_key="name",
                selection="single",
            ).classes("w-full")

            def on_select(_: object) -> None:
                selected = table.selected or []
                selected_name["value"] = selected[0]["name"] if selected else None

            table.on("selection", on_select)

            def get_selected_name(require: bool = True) -> str | None:
                # 统一获取选中项，兼容未触发事件但已有 selected 的情况
                name = selected_name.get("value")
                if name:
                    return name
                selected = table.selected or []
                if selected:
                    name = selected[0]["name"]
                    selected_name["value"] = name
                    return name
                if require:
                    ui.notify("请先选择一条记录", type="warning")
                return None

            # ---- 新增对话框 ----
            with ui.dialog() as add_dlg, ui.card().classes("w-[480px]"):
                ui.label(tr("common.add") + " Category").classes("text-lg font-bold")
                d_name = ui.input(
                    label=tr("common.name"), placeholder="visual-engineering"
                ).classes("w-full")
                d_model = ui.input(
                    label="Model", placeholder="provider/model-id"
                ).classes("w-full")
                d_temp = ui.slider(min=0, max=2, step=0.1, value=0.5).classes("w-full")
                ui.label("").bind_text_from(
                    d_temp, "value", backward=lambda v: f"Temperature: {v}"
                )
                with ui.row().classes("w-full justify-end gap-2 mt-2"):
                    ui.button(tr("common.cancel"), on_click=add_dlg.close).props("flat")

                    def do_add():
                        # 新增分类：name 作为 key，model/temperature 为配置值
                        n = (d_name.value or "").strip()
                        if not n:
                            ui.notify("请输入名称", type="warning")
                            return
                        if (
                            isinstance(omo.get("categories"), dict)
                            and n in omo["categories"]
                        ):
                            ui.notify("该分类已存在", type="warning")
                            return
                        if "categories" not in omo or not isinstance(
                            omo.get("categories"), dict
                        ):
                            omo["categories"] = {}
                        omo["categories"][n] = {
                            "model": d_model.value or "",
                            "temperature": float(d_temp.value or 0.5),
                        }
                        ConfigManager.save_json(
                            ConfigPaths.get_ohmyopencode_config(), omo, BackupManager()
                        )
                        ui.notify(tr("common.success"), type="positive")
                        add_dlg.close()
                        ui.navigate.to("/category")

                    ui.button(tr("common.save"), on_click=do_add)

            # ---- 编辑对话框 ----
            with ui.dialog() as edit_dlg, ui.card().classes("w-[480px]"):
                ui.label(tr("common.edit") + " Category").classes("text-lg font-bold")
                e_name = (
                    ui.input(label=tr("common.name"))
                    .classes("w-full")
                    .props("readonly")
                )
                e_model = ui.input(label="Model").classes("w-full")
                e_temp = ui.slider(min=0, max=2, step=0.1, value=0.5).classes("w-full")
                ui.label("").bind_text_from(
                    e_temp, "value", backward=lambda v: f"Temperature: {v}"
                )
                with ui.row().classes("w-full justify-end gap-2 mt-2"):
                    ui.button(tr("common.cancel"), on_click=edit_dlg.close).props(
                        "flat"
                    )

                    def do_edit():
                        # 编辑分类：name 只读，不允许改 key
                        key = (e_name.value or "").strip()
                        if not key:
                            ui.notify("未找到要编辑的分类", type="warning")
                            return
                        if "categories" not in omo or not isinstance(
                            omo.get("categories"), dict
                        ):
                            omo["categories"] = {}
                        if key not in omo["categories"]:
                            ui.notify("分类不存在，可能已被删除", type="warning")
                            return
                        omo["categories"][key] = {
                            "model": e_model.value or "",
                            "temperature": float(e_temp.value or 0.5),
                        }
                        ConfigManager.save_json(
                            ConfigPaths.get_ohmyopencode_config(), omo, BackupManager()
                        )
                        ui.notify(tr("common.success"), type="positive")
                        edit_dlg.close()
                        ui.navigate.to("/category")

                    ui.button(tr("common.save"), on_click=do_edit)

            def open_edit_dialog() -> None:
                key = get_selected_name()
                if not key:
                    return
                current = cats.get(key, {})
                current = current if isinstance(current, dict) else {}
                # 编辑弹窗预填当前值
                e_name.value = key
                e_model.value = str(current.get("model") or "")
                temp_value = current.get("temperature", 0.5)
                try:
                    e_temp.value = float(temp_value)
                except (TypeError, ValueError):
                    e_temp.value = 0.5
                edit_dlg.open()

            # ---- 删除确认对话框 ----
            with ui.dialog() as del_dlg, ui.card().classes("w-[420px]"):
                ui.label(tr("common.confirm_delete_title")).classes("text-lg font-bold")
                del_name = (
                    ui.input(label=tr("common.name"))
                    .classes("w-full")
                    .props("readonly")
                )
                ui.label("删除后不可恢复，请确认操作。")
                with ui.row().classes("w-full justify-end gap-2 mt-2"):
                    ui.button(tr("common.cancel"), on_click=del_dlg.close).props("flat")

                    def do_delete():
                        # 删除选中分类
                        key = (del_name.value or "").strip()
                        if not key:
                            ui.notify("未找到要删除的分类", type="warning")
                            return
                        if (
                            isinstance(omo.get("categories"), dict)
                            and key in omo["categories"]
                        ):
                            del omo["categories"][key]
                            ConfigManager.save_json(
                                ConfigPaths.get_ohmyopencode_config(),
                                omo,
                                BackupManager(),
                            )
                            ui.notify(tr("common.success"), type="positive")
                            del_dlg.close()
                            ui.navigate.to("/category")
                        else:
                            ui.notify("分类不存在，可能已被删除", type="warning")

                    ui.button(tr("common.delete"), on_click=do_delete).props(
                        "color=negative"
                    )

            def open_delete_dialog() -> None:
                key = get_selected_name()
                if not key:
                    return
                del_name.value = key
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
            page_key="menu.category",
            content_builder=content,
            auth_enabled=auth_enabled,
        )
