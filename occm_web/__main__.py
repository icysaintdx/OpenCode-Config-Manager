from __future__ import annotations

# pyright: reportMissingImports=false

import argparse
import os
import secrets

from nicegui import ui

from .app import configure_app

# NiceGUI reload=True 时用 multiprocessing 重新 import 本模块，
# 子进程无法再次 argparse，因此通过环境变量传递参数。
_is_mp_child = os.environ.get("_OCCM_MP_CHILD") == "1"

if not _is_mp_child:
    _parser = argparse.ArgumentParser(description="OCCM Web")
    _parser.add_argument("--port", type=int, default=8080)
    _parser.add_argument("--host", type=str, default="127.0.0.1")
    _parser.add_argument("--no-auth", action="store_true")
    _parser.add_argument("--debug", action="store_true")
    _args = _parser.parse_args()
    os.environ["_OCCM_MP_CHILD"] = "1"
    os.environ["_OCCM_HOST"] = _args.host
    os.environ["_OCCM_PORT"] = str(_args.port)
    os.environ["_OCCM_NO_AUTH"] = "1" if _args.no_auth else ""
    os.environ["_OCCM_DEBUG"] = "1" if _args.debug else ""

_host = os.environ.get("_OCCM_HOST", "127.0.0.1")
_port = int(os.environ.get("_OCCM_PORT", "8080"))
_no_auth = bool(os.environ.get("_OCCM_NO_AUTH"))
_debug = bool(os.environ.get("_OCCM_DEBUG"))

auth_manager = configure_app(no_auth=_no_auth, debug=_debug)

if not _is_mp_child and auth_manager is not None:
    generated_password = auth_manager.ensure_admin_password()
    if generated_password:
        print("\n[OCCM Web] 首次启动已生成管理密码，请立即保存：")
        print(f"[OCCM Web] 管理员密码: {generated_password}\n")

_storage_secret = auth_manager.jwt_secret if auth_manager else secrets.token_urlsafe(48)

ui.run(
    host=_host,
    port=_port,
    reload=_debug,
    show=False,
    storage_secret=_storage_secret,
)
