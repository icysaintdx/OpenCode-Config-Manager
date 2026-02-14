from __future__ import annotations

# pyright: reportMissingImports=false

import argparse
import secrets

from nicegui import ui

from .app import configure_app


def main() -> None:
    parser = argparse.ArgumentParser(description="OCCM Web")
    parser.add_argument("--port", type=int, default=8080, help="服务端口，默认 8080")
    parser.add_argument(
        "--host", type=str, default="127.0.0.1", help="监听地址，默认 127.0.0.1"
    )
    parser.add_argument("--no-auth", action="store_true", help="禁用认证")
    parser.add_argument("--debug", action="store_true", help="调试模式")
    args = parser.parse_args()

    auth_manager = configure_app(no_auth=args.no_auth, debug=args.debug)

    if auth_manager is not None:
        generated_password = auth_manager.ensure_admin_password()
        if generated_password:
            print("\n[OCCM Web] 首次启动已生成管理密码，请立即保存：")
            print(f"[OCCM Web] 管理员密码: {generated_password}\n")

    storage_secret = (
        auth_manager.jwt_secret if auth_manager else secrets.token_urlsafe(48)
    )

    ui.run(
        host=args.host,
        port=args.port,
        reload=args.debug,
        show=False,
        storage_secret=storage_secret,
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
