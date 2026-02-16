from __future__ import annotations

# pyright: reportMissingImports=false

import argparse
import os
import secrets
import webbrowser
from pathlib import Path

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
    _parser.add_argument(
        "--config-dir",
        type=str,
        default="",
        help="自定义配置目录路径 (默认 ~/.config/opencode/)",
    )
    _parser.add_argument(
        "--no-browser",
        action="store_true",
        help="启动时不自动打开浏览器",
    )
    _args = _parser.parse_args()
    os.environ["_OCCM_MP_CHILD"] = "1"
    os.environ["_OCCM_HOST"] = _args.host
    os.environ["_OCCM_PORT"] = str(_args.port)
    os.environ["_OCCM_NO_AUTH"] = "1" if _args.no_auth else ""
    os.environ["_OCCM_DEBUG"] = "1" if _args.debug else ""
    os.environ["_OCCM_NO_BROWSER"] = "1" if _args.no_browser else ""
    # --config-dir > 环境变量 OPENCODE_CONFIG_DIR > 默认
    _cfg_dir = _args.config_dir or os.environ.get("OPENCODE_CONFIG_DIR", "")
    os.environ["_OCCM_CONFIG_DIR"] = _cfg_dir

# 读取环境变量
_host = os.environ.get("_OCCM_HOST", "127.0.0.1")
_port = int(os.environ.get("_OCCM_PORT", "8080"))
_no_auth = bool(os.environ.get("_OCCM_NO_AUTH"))
_debug = bool(os.environ.get("_OCCM_DEBUG"))
_no_browser = bool(os.environ.get("_OCCM_NO_BROWSER"))
_cfg_dir = os.environ.get("_OCCM_CONFIG_DIR", "")

# 应用自定义配置路径
if _cfg_dir:
    from occm_core import ConfigPaths  # type: ignore

    p = Path(_cfg_dir).expanduser().resolve()
    p.mkdir(parents=True, exist_ok=True)
    ConfigPaths.set_opencode_config(p / "opencode.json")
    ConfigPaths.set_ohmyopencode_config(p / "oh-my-opencode.json")
    ConfigPaths.set_backup_dir(p / "backups")

auth_manager = configure_app(no_auth=_no_auth, debug=_debug)

if not _is_mp_child and auth_manager is not None:
    generated_password = auth_manager.ensure_admin_password()
    if generated_password:
        print("\n[OCCM Web] 首次启动已生成管理密码，请立即保存：")
        print(f"[OCCM Web] 管理员密码: {generated_password}\n")

if not _is_mp_child:
    from occm_core import ConfigPaths as _CP  # type: ignore

    print(f"[OCCM Web] 配置目录: {_CP.get_config_base_dir()}")
    print(f"[OCCM Web] 访问地址: http://{_host}:{_port}")

# 自动打开浏览器
if not _is_mp_child and not _no_browser:
    import threading

    def _open_browser() -> None:
        import time

        time.sleep(1.5)
        webbrowser.open(f"http://{_host}:{_port}")

    threading.Thread(target=_open_browser, daemon=True).start()

_storage_secret = auth_manager.jwt_secret if auth_manager else secrets.token_urlsafe(48)

ui.run(
    host=_host,
    port=_port,
    reload=_debug,
    show=False,
    storage_secret=_storage_secret,
)
