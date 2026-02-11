from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional


class AuthManager:
    """认证凭证管理器 - 管理 auth.json 文件的读写操作

    auth.json 存储原生 Provider 的认证凭证，路径：
    - Windows: %LOCALAPPDATA%/opencode/auth.json 或 ~/.local/share/opencode/auth.json
    - macOS/Linux: ~/.local/share/opencode/auth.json
    """

    def __init__(self):
        self._auth_path: Optional[Path] = None

    @property
    def auth_path(self) -> Path:
        """获取 auth.json 路径（延迟初始化）"""
        if self._auth_path is None:
            self._auth_path = self._get_auth_path()
        return self._auth_path

    def _get_auth_path(self) -> Path:
        """获取 auth.json 路径（跨平台支持）

        Windows: 优先使用 %LOCALAPPDATA%/opencode，回退到 ~/.local/share/opencode
        Unix: 使用 ~/.local/share/opencode
        """
        if sys.platform == "win32":
            # Windows: 优先使用 LOCALAPPDATA
            local_app_data = os.environ.get("LOCALAPPDATA", "")
            if local_app_data:
                base = Path(local_app_data) / "opencode"
            else:
                # 回退到 Unix 风格路径
                base = Path.home() / ".local" / "share" / "opencode"
        else:
            # macOS / Linux
            base = Path.home() / ".local" / "share" / "opencode"

        return base / "auth.json"

    def _ensure_parent_dir(self) -> None:
        """确保 auth.json 的父目录存在"""
        parent = self.auth_path.parent
        if not parent.exists():
            parent.mkdir(parents=True, exist_ok=True)

    def read_auth(self) -> Dict[str, Any]:
        """读取 auth.json 文件

        Returns:
            认证配置字典，文件不存在时返回空字典

        Raises:
            json.JSONDecodeError: 当文件格式错误时（由调用方处理）
        """
        if not self.auth_path.exists():
            return {}

        try:
            with open(self.auth_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except json.JSONDecodeError:
            # 重新抛出，让调用方决定如何处理
            raise
        except Exception:
            # 其他读取错误，返回空字典
            return {}

    def write_auth(self, auth_data: Dict[str, Any]) -> None:
        """写入 auth.json 文件

        Args:
            auth_data: 要写入的认证配置字典
        """
        self._ensure_parent_dir()
        with open(self.auth_path, "w", encoding="utf-8") as f:
            json.dump(auth_data, f, indent=2, ensure_ascii=False)

    def get_provider_auth(self, provider_id: str) -> Optional[Dict[str, Any]]:
        """获取指定 Provider 的认证信息

        Args:
            provider_id: Provider 标识符（如 'anthropic', 'openai'）

        Returns:
            Provider 的认证配置字典，不存在时返回 None
            返回格式兼容旧格式：{'apiKey': 'xxx'} 用于UI显示
        """
        auth_data = self.read_auth()
        provider_auth = auth_data.get(provider_id)

        if not provider_auth:
            return None

        # 如果是新格式 {"type": "api", "key": "xxx"}，转换为UI兼容格式
        if "key" in provider_auth and "type" in provider_auth:
            return {"apiKey": provider_auth["key"], "type": provider_auth["type"]}

        # 保持原格式（用于特殊Provider或旧数据）
        return provider_auth

    def set_provider_auth(self, provider_id: str, auth_config: Dict[str, Any]) -> None:
        """设置指定 Provider 的认证信息

        Args:
            provider_id: Provider 标识符
            auth_config: 认证配置字典（如 {'apiKey': 'sk-xxx'}）
        """
        auth_data = self.read_auth()

        # 转换为OpenCode官方格式：{"type": "api", "key": "xxx"}
        # 支持输入格式：{'apiKey': 'xxx'} 或 {'key': 'xxx'}
        api_key = auth_config.get("apiKey") or auth_config.get("key")
        auth_type = auth_config.get("type", "api")  # 默认为api类型

        if api_key:
            auth_data[provider_id] = {"type": auth_type, "key": api_key}
        else:
            # 如果没有apiKey/key字段，保持原样（用于特殊Provider如AWS）
            auth_data[provider_id] = auth_config

        self.write_auth(auth_data)

    def delete_provider_auth(self, provider_id: str) -> bool:
        """删除指定 Provider 的认证信息

        Args:
            provider_id: Provider 标识符

        Returns:
            是否成功删除（Provider 不存在时返回 False）
        """
        auth_data = self.read_auth()
        if provider_id in auth_data:
            del auth_data[provider_id]
            self.write_auth(auth_data)
            return True
        return False

    @staticmethod
    def mask_api_key(api_key: str) -> str:
        """遮蔽 API Key，只显示首尾字符

        Args:
            api_key: 原始 API Key

        Returns:
            遮蔽后的字符串：
            - 长度 > 8: 显示首 4 字符 + ... + 尾 4 字符
            - 长度 <= 8: 显示 ****
        """
        if not api_key:
            return ""
        if len(api_key) <= 8:
            return "****"
        return f"{api_key[:4]}...{api_key[-4:]}"
