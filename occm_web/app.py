from __future__ import annotations

# pyright: reportMissingImports=false

import logging

from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from nicegui import app
from starlette.responses import JSONResponse

from .auth import AuthManager, register_auth_api, register_login_pages
from .pages import register_all_pages


logger = logging.getLogger("occm_web")


def _register_middlewares() -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def _register_exception_handler(debug: bool) -> None:
    @app.exception_handler(Exception)
    async def _global_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("未处理异常: %s", exc)
        if debug:
            return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
        return JSONResponse({"ok": False, "error": "服务器内部错误"}, status_code=500)


def configure_app(no_auth: bool = False, debug: bool = False) -> AuthManager | None:
    _register_middlewares()
    _register_exception_handler(debug=debug)

    auth_manager: AuthManager | None = None
    if not no_auth:
        auth_manager = AuthManager(token_exp_hours=24)
        register_auth_api(auth_manager)
        register_login_pages(auth_manager)

    # 注册所有业务页面（来自 pages/ 子包）
    register_all_pages(auth_manager)
    return auth_manager
