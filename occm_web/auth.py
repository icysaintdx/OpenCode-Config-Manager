from __future__ import annotations

# pyright: reportMissingImports=false

import inspect
import json
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any

import bcrypt
import jwt
from fastapi import Request
from nicegui import app, ui
from starlette.responses import JSONResponse, RedirectResponse

from .i18n_web import tr


AUTH_CONFIG_PATH = Path.home() / ".config" / "opencode" / "occm-web.json"
COOKIE_NAME = "occm_web_token"


@dataclass
class LockState:
    attempts: int = 0
    lock_until: datetime | None = None


class AuthManager:
    def __init__(self, token_exp_hours: int = 24) -> None:
        self.token_exp_hours = token_exp_hours
        self._lock_map: dict[str, LockState] = {}
        self._config = self._load_config()
        if "jwt_secret" not in self._config:
            self._config["jwt_secret"] = secrets.token_urlsafe(48)
            self._save_config(self._config)

    @property
    def jwt_secret(self) -> str:
        return str(self._config["jwt_secret"])

    def _load_config(self) -> dict[str, Any]:
        if not AUTH_CONFIG_PATH.exists():
            return {}
        try:
            return json.loads(AUTH_CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_config(self, config: dict[str, Any]) -> None:
        AUTH_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        AUTH_CONFIG_PATH.write_text(
            json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    @staticmethod
    def _hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def _verify_password(password: str, hashed: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
        except Exception:
            return False

    def ensure_admin_password(self) -> str | None:
        if self._config.get("password_hash"):
            return None
        generated = secrets.token_urlsafe(12)
        self._config["password_hash"] = self._hash_password(generated)
        self._save_config(self._config)
        return generated

    def _get_lock_state(self, client_key: str) -> LockState:
        state = self._lock_map.get(client_key)
        if state is None:
            state = LockState()
            self._lock_map[client_key] = state
        return state

    def verify_login(self, password: str, client_key: str) -> tuple[bool, str]:
        state = self._get_lock_state(client_key)
        now = datetime.now(UTC)

        if state.lock_until and now < state.lock_until:
            remain = int((state.lock_until - now).total_seconds() // 60) + 1
            return False, f"登录失败过多，请 {remain} 分钟后再试"

        stored_hash = self._config.get("password_hash", "")
        if not stored_hash or not self._verify_password(password, stored_hash):
            state.attempts += 1
            if state.attempts >= 5:
                state.lock_until = now + timedelta(minutes=15)
                state.attempts = 0
                return False, "登录失败 5 次，已锁定 15 分钟"
            return False, f"密码错误，还可尝试 {5 - state.attempts} 次"

        state.attempts = 0
        state.lock_until = None
        return True, "登录成功"

    def create_token(self, subject: str = "admin") -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": subject,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=self.token_exp_hours)).timestamp()),
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")

    def decode_token(self, token: str) -> dict[str, Any] | None:
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            return dict(payload)
        except Exception:
            return None

    def set_auth_cookie(self, response: JSONResponse, token: str) -> None:
        response.set_cookie(
            key=COOKIE_NAME,
            value=token,
            httponly=True,
            max_age=self.token_exp_hours * 3600,
            samesite="lax",
            secure=False,
            path="/",
        )

    def clear_auth_cookie(self, response: JSONResponse) -> None:
        response.delete_cookie(key=COOKIE_NAME, path="/")

    def change_password(self, old_password: str, new_password: str) -> tuple[bool, str]:
        if len(new_password) < 8:
            return False, "新密码至少 8 位"
        old_hash = self._config.get("password_hash", "")
        if not self._verify_password(old_password, old_hash):
            return False, "原密码错误"
        self._config["password_hash"] = self._hash_password(new_password)
        self._save_config(self._config)
        return True, "密码修改成功"


def _extract_request(args: tuple[Any, ...], kwargs: dict[str, Any]) -> Request | None:
    if isinstance(kwargs.get("request"), Request):
        return kwargs["request"]
    for item in args:
        if isinstance(item, Request):
            return item
    return None


def require_auth(auth: AuthManager) -> Callable[..., Any]:
    def _decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        is_async = inspect.iscoroutinefunction(func)

        @wraps(func)
        async def _async_wrapper(*args: Any, **kwargs: Any) -> Any:
            request = _extract_request(args, kwargs)
            if not request:
                return RedirectResponse(url="/login", status_code=303)
            token = request.cookies.get(COOKIE_NAME, "")
            payload = auth.decode_token(token) if token else None
            if not payload:
                return RedirectResponse(url="/login", status_code=303)
            request.state.user = payload
            return await func(*args, **kwargs)

        @wraps(func)
        def _sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            request = _extract_request(args, kwargs)
            if not request:
                return RedirectResponse(url="/login", status_code=303)
            token = request.cookies.get(COOKIE_NAME, "")
            payload = auth.decode_token(token) if token else None
            if not payload:
                return RedirectResponse(url="/login", status_code=303)
            request.state.user = payload
            return func(*args, **kwargs)

        return _async_wrapper if is_async else _sync_wrapper

    return _decorator


def register_auth_api(auth: AuthManager) -> None:
    @app.post("/api/auth/login")
    async def auth_login(request: Request) -> JSONResponse:
        payload = await request.json()
        password = str(payload.get("password", ""))
        client_key = request.client.host if request.client else "unknown"
        ok, message = auth.verify_login(password, client_key)
        if not ok:
            return JSONResponse({"ok": False, "message": message}, status_code=401)
        token = auth.create_token(subject="admin")
        response = JSONResponse({"ok": True, "message": message})
        auth.set_auth_cookie(response, token)
        return response

    @app.post("/api/auth/logout")
    async def auth_logout() -> JSONResponse:
        response = JSONResponse({"ok": True, "message": "已退出登录"})
        auth.clear_auth_cookie(response)
        return response

    @app.post("/api/auth/change-password")
    async def auth_change_password(request: Request) -> JSONResponse:
        token = request.cookies.get(COOKIE_NAME, "")
        if not token or not auth.decode_token(token):
            return JSONResponse({"ok": False, "message": "未登录"}, status_code=401)

        payload = await request.json()
        old_password = str(payload.get("old_password", ""))
        new_password = str(payload.get("new_password", ""))
        ok, message = auth.change_password(old_password, new_password)
        status = 200 if ok else 400
        return JSONResponse({"ok": ok, "message": message}, status_code=status)


def register_login_pages(auth: AuthManager) -> None:
    @ui.page("/login")
    async def login_page(request: Request) -> None:
        token = request.cookies.get(COOKIE_NAME, "")
        if token and auth.decode_token(token):
            ui.navigate.to("/")
            return

        with ui.column().classes(
            "w-full h-screen items-center justify-center bg-slate-100 dark:bg-slate-900"
        ):
            with ui.card().classes("w-[360px] p-6 gap-4"):
                title = ui.label(tr("app.title")).classes("text-xl font-bold")
                subtitle = ui.label("OCCM Web 登录").classes("text-sm text-gray-500")
                password = ui.input(
                    "管理密码", password=True, password_toggle_button=True
                ).classes("w-full")

                async def do_login() -> None:
                    script = f"""
                    const resp = await fetch('/api/auth/login', {{
                      method: 'POST',
                      headers: {{'Content-Type': 'application/json'}},
                      credentials: 'same-origin',
                      body: JSON.stringify({{password: {json.dumps(password.value or "")}}}),
                    }});
                    const data = await resp.json();
                    return {{ok: resp.ok, message: data.message || ''}};
                    """
                    result = await ui.run_javascript(script)
                    if result and result.get("ok"):
                        ui.navigate.to("/")
                    else:
                        ui.notify(
                            (result or {}).get("message", "登录失败"), type="negative"
                        )

                ui.button("登录", on_click=do_login).classes("w-full")
                title.update()
                subtitle.update()

    @ui.page("/change-password")
    @require_auth(auth)
    async def change_password_page(request: Request) -> None:
        with ui.column().classes(
            "w-full h-screen items-center justify-center bg-slate-100 dark:bg-slate-900"
        ):
            with ui.card().classes("w-[420px] p-6 gap-4"):
                ui.label(tr("common.update")).classes("text-lg font-bold")
                old_password = ui.input(
                    "原密码", password=True, password_toggle_button=True
                ).classes("w-full")
                new_password = ui.input(
                    "新密码", password=True, password_toggle_button=True
                ).classes("w-full")

                async def do_change() -> None:
                    payload = {
                        "old_password": old_password.value or "",
                        "new_password": new_password.value or "",
                    }
                    script = f"""
                    const resp = await fetch('/api/auth/change-password', {{
                      method: 'POST',
                      headers: {{'Content-Type': 'application/json'}},
                      credentials: 'same-origin',
                      body: JSON.stringify({json.dumps(payload)}),
                    }});
                    const data = await resp.json();
                    return {{ok: resp.ok, message: data.message || ''}};
                    """
                    result = await ui.run_javascript(script)
                    if result and result.get("ok"):
                        ui.notify(
                            (result or {}).get("message", "密码已更新"), type="positive"
                        )
                        ui.navigate.to("/")
                    else:
                        ui.notify(
                            (result or {}).get("message", "修改失败"), type="negative"
                        )

                ui.button("提交", on_click=do_change).classes("w-full")
