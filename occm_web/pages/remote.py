"""远程服务器配置管理页面"""

from __future__ import annotations

# pyright: reportMissingImports=false

import json as _json
from typing import Any

from fastapi import Request
from nicegui import ui

from ..auth import AuthManager as WebAuth, require_auth
from ..i18n_web import tr
from ..layout import render_layout

# 远程管理模块（paramiko 可选依赖）
try:
    from occm_core.remote_manager import RemoteManager, RemoteServer, RemoteServerStore

    _HAS_REMOTE = True
except Exception:
    _HAS_REMOTE = False


def register_page(auth: WebAuth | None) -> None:
    auth_enabled = auth is not None
    dec = require_auth(auth) if auth else lambda f: f

    @ui.page("/remote")
    @dec
    async def remote_page(request: Request) -> None:
        def content() -> None:
            if not _HAS_REMOTE:
                ui.label(
                    "⚠️ 远程管理功能需要安装 paramiko：pip install paramiko"
                ).classes("text-red-500 text-lg")
                return

            store = RemoteServerStore()
            manager = RemoteManager()
            servers = store.list_servers()
            selected: dict[str, str | None] = {"value": None}

            # --- 服务器列表 ---
            def build_rows() -> list[dict[str, Any]]:
                rows = []
                for s in store.list_servers():
                    rows.append(
                        {
                            "nickname": s.nickname or s.host,
                            "host": s.host,
                            "port": s.port,
                            "username": s.username,
                            "auth_type": s.auth_type,
                        }
                    )
                return rows

            cols = [
                {
                    "name": "nickname",
                    "label": "名称",
                    "field": "nickname",
                    "sortable": True,
                },
                {"name": "host", "label": "主机", "field": "host", "sortable": True},
                {"name": "port", "label": "端口", "field": "port"},
                {"name": "username", "label": "用户名", "field": "username"},
                {"name": "auth_type", "label": "认证方式", "field": "auth_type"},
            ]
            table = ui.table(
                columns=cols, rows=build_rows(), row_key="host", selection="single"
            ).classes("w-full")

            def on_select(e: Any) -> None:
                sel = e.selection
                selected["value"] = sel[0]["host"] if sel else None

            table.on("selection", on_select)

            # --- 工具栏 ---
            with ui.row().classes("gap-2 mt-2"):
                # 添加服务器对话框
                with ui.dialog() as add_dlg, ui.card().classes("w-[520px]"):
                    ui.label("添加远程服务器").classes("text-lg font-bold")
                    d_nick = ui.input(
                        label="名称(可选)", placeholder="我的服务器"
                    ).classes("w-full")
                    d_host = ui.input(
                        label="主机地址", placeholder="192.168.1.100"
                    ).classes("w-full")
                    d_port = ui.number(
                        label="SSH端口", value=22, min=1, max=65535
                    ).classes("w-full")
                    d_user = ui.input(label="用户名", placeholder="root").classes(
                        "w-full"
                    )
                    d_auth = ui.select(
                        label="认证方式", options=["password", "key"], value="password"
                    ).classes("w-full")
                    d_pass = ui.input(
                        label="密码", password=True, password_toggle_button=True
                    ).classes("w-full")
                    d_key = ui.input(
                        label="密钥路径", placeholder="~/.ssh/id_rsa"
                    ).classes("w-full")
                    d_path = ui.input(
                        label="远程配置路径(可选)", placeholder="~/.config/opencode"
                    ).classes("w-full")

                    with ui.row().classes("w-full justify-end gap-2 mt-2"):
                        ui.button(tr("common.cancel"), on_click=add_dlg.close).props(
                            "flat"
                        )

                        def do_add() -> None:
                            host = (d_host.value or "").strip()
                            if not host:
                                ui.notify("请输入主机地址", type="warning")
                                return
                            server = RemoteServer(
                                host=host,
                                port=int(d_port.value or 22),
                                username=(d_user.value or "root").strip(),
                                auth_type=d_auth.value or "password",
                                password=(d_pass.value or "").strip() or None,
                                key_path=(d_key.value or "").strip() or None,
                                nickname=(d_nick.value or "").strip() or None,
                                custom_config_path=(d_path.value or "").strip() or None,
                            )
                            store.add_server(server)
                            ui.notify(
                                f"已添加 {server.nickname or server.host}",
                                type="positive",
                            )
                            add_dlg.close()
                            ui.navigate.to("/remote")

                        ui.button(tr("common.save"), on_click=do_add)

                ui.button("添加服务器", icon="add", on_click=add_dlg.open)

                # 测试连接
                def do_test() -> None:
                    if not selected["value"]:
                        ui.notify("请先选择服务器", type="warning")
                        return
                    srv = _find_server(store, selected["value"])
                    if not srv:
                        return
                    ok, msg = manager.test_connection(srv)
                    if ok:
                        ui.notify(f"✅ 连接成功: {msg}", type="positive")
                    else:
                        ui.notify(f"❌ 连接失败: {msg}", type="negative")

                ui.button("测试连接", icon="wifi", on_click=do_test).props("outline")

                # 删除服务器
                with ui.dialog() as del_dlg, ui.card().classes("w-[400px]"):
                    ui.label("确认删除").classes("text-lg font-bold")
                    ui.label("确定要删除选中的服务器吗？")
                    with ui.row().classes("w-full justify-end gap-2 mt-2"):
                        ui.button(tr("common.cancel"), on_click=del_dlg.close).props(
                            "flat"
                        )

                        def do_delete() -> None:
                            if selected["value"]:
                                store.remove_server(selected["value"])
                                ui.notify("已删除", type="info")
                                del_dlg.close()
                                ui.navigate.to("/remote")

                        ui.button(tr("common.delete"), on_click=do_delete).props(
                            "color=negative"
                        )

                def open_del() -> None:
                    if not selected["value"]:
                        ui.notify("请先选择服务器", type="warning")
                        return
                    del_dlg.open()

                ui.button(tr("common.delete"), icon="delete", on_click=open_del).props(
                    "outline color=red"
                )

            # --- 远程操作区域 ---
            ui.separator().classes("my-4")
            ui.label("远程配置操作").classes("text-lg font-bold")

            with ui.row().classes("gap-2"):

                def do_read_config(config_type: str = "opencode") -> None:
                    if not selected["value"]:
                        ui.notify("请先选择服务器", type="warning")
                        return
                    srv = _find_server(store, selected["value"])
                    if not srv:
                        return
                    try:
                        data = manager.read_remote_config(srv, config_type)
                        config_display.set_content(
                            f"```json\n{_json.dumps(data, indent=2, ensure_ascii=False)}\n```"
                        )
                        ui.notify(f"已读取 {config_type} 配置", type="positive")
                    except Exception as e:
                        ui.notify(f"读取失败: {e}", type="negative")

                ui.button(
                    "读取 opencode.json",
                    icon="download",
                    on_click=lambda: do_read_config("opencode"),
                )
                ui.button(
                    "读取 oh-my-opencode.json",
                    icon="download",
                    on_click=lambda: do_read_config("oh-my-opencode"),
                )
                ui.button(
                    "读取 auth.json",
                    icon="download",
                    on_click=lambda: do_read_config("auth"),
                )

            with ui.row().classes("gap-2 mt-2"):

                def do_status() -> None:
                    if not selected["value"]:
                        ui.notify("请先选择服务器", type="warning")
                        return
                    srv = _find_server(store, selected["value"])
                    if not srv:
                        return
                    try:
                        status = manager.get_remote_opencode_status(srv)
                        config_display.set_content(
                            f"```json\n{_json.dumps(status, indent=2, ensure_ascii=False)}\n```"
                        )
                        ui.notify("已获取状态", type="positive")
                    except Exception as e:
                        ui.notify(f"获取状态失败: {e}", type="negative")

                def do_remote_backup() -> None:
                    if not selected["value"]:
                        ui.notify("请先选择服务器", type="warning")
                        return
                    srv = _find_server(store, selected["value"])
                    if not srv:
                        return
                    try:
                        path = manager.create_remote_backup(srv)
                        ui.notify(f"远程备份已创建: {path}", type="positive")
                    except Exception as e:
                        ui.notify(f"备份失败: {e}", type="negative")

                ui.button("查看远程状态", icon="info", on_click=do_status).props(
                    "outline"
                )
                ui.button(
                    "创建远程备份", icon="backup", on_click=do_remote_backup
                ).props("outline")

            # 配置显示区域
            config_display = ui.markdown("*选择服务器后点击读取按钮查看配置*").classes(
                "w-full mt-4"
            )

        render_layout(
            request=request,
            page_key="menu.remote",
            content_builder=content,
            auth_enabled=auth_enabled,
        )


def _find_server(store: Any, host: str) -> Any:
    """根据host查找服务器"""
    for s in store.list_servers():
        if s.host == host:
            return s
    ui.notify("未找到服务器", type="warning")
    return None
