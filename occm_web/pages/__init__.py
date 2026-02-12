"""页面注册入口 - 统一注册所有业务页面"""

from __future__ import annotations

from ..auth import AuthManager as WebAuth

from . import (
    agent,
    backup,
    category,
    cli_export,
    compaction,
    help_page,
    home,
    import_page,
    mcp,
    model,
    monitor,
    native_provider,
    permission,
    plugin,
    provider,
    remote,
    rules,
    skill,
)

# 所有页面模块（每个模块必须暴露 register_page(auth) 函数）
_PAGE_MODULES = [
    home,
    provider,
    native_provider,
    model,
    mcp,
    agent,
    category,
    permission,
    skill,
    plugin,
    rules,
    compaction,
    import_page,
    cli_export,
    monitor,
    backup,
    remote,
    help_page,
]


def register_all_pages(auth: WebAuth | None) -> None:
    """注册所有业务页面路由"""
    for mod in _PAGE_MODULES:
        mod.register_page(auth)
