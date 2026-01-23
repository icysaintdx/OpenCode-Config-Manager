#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenCode & Oh My OpenCode 配置管理器 v1.2.0 (QFluentWidgets 版本)
一个可视化的GUI工具，用于管理OpenCode和Oh My OpenCode的配置文件

基于 PyQt5 + QFluentWidgets 重写，提供现代化 Fluent Design 界面
"""

# 修复 PyInstaller 打包后中文用户名导致的 DLL 加载问题
# 必须在所有其他 import 之前执行
import os
import sys
import platform
import traceback
import time


# macOS 崩溃处理器 (必须在 PyQt5 导入之前设置)
def setup_macos_crash_handler():
    """设置 macOS 崩溃处理器"""
    if platform.system() != "Darwin":
        return

    def exception_handler(exc_type, exc_value, exc_traceback):
        """捕获未处理的异常"""
        from pathlib import Path

        # 写入崩溃日志
        crash_log_dir = Path.home() / "Library" / "Logs" / "OCCM"
        crash_log_dir.mkdir(parents=True, exist_ok=True)

        crash_log_file = crash_log_dir / f"crash_{int(time.time())}.log"

        with open(crash_log_file, "w", encoding="utf-8") as f:
            f.write(f"OCCM Crash Report\n")
            f.write(f"=" * 80 + "\n")
            f.write(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"System: {platform.platform()}\n")
            f.write(f"Python: {sys.version}\n")
            f.write(f"Architecture: {platform.machine()}\n")
            f.write(f"macOS Version: {platform.mac_ver()[0]}\n")
            f.write(f"\nException:\n")
            f.write("=" * 80 + "\n")
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)

        # 尝试显示错误对话框
        try:
            from PyQt5.QtWidgets import QMessageBox, QApplication

            app = QApplication.instance() or QApplication(sys.argv)
            QMessageBox.critical(
                None,
                "OCCM 崩溃",
                f"应用程序遇到错误并需要关闭。\n\n"
                f"错误日志已保存到:\n{crash_log_file}\n\n"
                f"请将此日志文件发送给开发者以帮助修复问题。\n\n"
                f"GitHub: https://github.com/icysaintdx/OpenCode-Config-Manager/issues",
            )
        except:
            # 如果 GUI 无法显示,至少打印到控制台
            print(f"\n{'=' * 80}")
            print(f"OCCM 崩溃 - 日志已保存到: {crash_log_file}")
            print(f"{'=' * 80}\n")

        # 调用默认处理器
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    sys.excepthook = exception_handler


# 立即设置崩溃处理器
setup_macos_crash_handler()

if sys.platform == "win32" and getattr(sys, "frozen", False):
    # 检查临时目录路径是否包含非 ASCII 字符
    temp_dir = os.environ.get("TEMP", "")
    try:
        temp_dir.encode("ascii")
    except UnicodeEncodeError:
        # 路径包含非 ASCII 字符，使用安全的临时目录
        safe_temp = "C:\\Temp"
        if not os.path.exists(safe_temp):
            try:
                os.makedirs(safe_temp)
            except OSError:
                pass
        if os.path.exists(safe_temp):
            os.environ["TEMP"] = safe_temp
            os.environ["TMP"] = safe_temp

import sys
import json
import re
import shutil
import webbrowser
import threading
import urllib.request
import urllib.error
import hashlib
import copy
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Deque
from functools import partial
from dataclasses import dataclass
from collections import deque
from concurrent.futures import ThreadPoolExecutor
import os
import time
import socket
from urllib.parse import urlparse


def _resolve_env_value(value: str) -> str:
    """解析 {env:VAR} 形式的环境变量引用"""
    if not value:
        return ""
    match = re.match(r"^\{env:([A-Z0-9_]+)\}$", value.strip())
    if not match:
        return value
    return os.environ.get(match.group(1), "")


def _safe_base_url(value: str) -> str:
    """规范化 baseURL 字符串"""
    return (value or "").strip().rstrip("/")


def _build_chat_url(base_url: str) -> str:
    """根据 baseURL 生成 chat/completions 地址"""
    value = (base_url or "").strip()
    if not value:
        return ""
    if value.endswith("/v1") or value.endswith("/v1/"):
        return value.rstrip("/") + "/chat/completions"
    if value.endswith("/"):
        return value + "v1/chat/completions"
    return value + "/v1/chat/completions"


def _extract_origin(base_url: str) -> str:
    """从 baseURL 提取可用于 Ping 的源站"""
    if not base_url:
        return ""
    parsed = urlparse(base_url)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}"
    return base_url


@dataclass
class MonitorTarget:
    provider_key: str
    provider_name: str
    base_url: str
    api_key: str
    model_id: str
    model_name: str

    @property
    def target_id(self) -> str:
        return f"{self.provider_key}/{self.model_id}"


@dataclass
class MonitorResult:
    target_id: str
    status: str
    latency_ms: Optional[int]
    ping_ms: Optional[int]
    checked_at: datetime
    message: str


# ==================== CLI 导出模块数据类 ====================
@dataclass
class CLIToolStatus:
    """CLI 工具安装状态"""

    cli_type: str  # "claude" | "codex" | "gemini"
    installed: bool  # 是否已安装（配置目录存在）
    config_dir: Optional[Path]  # 配置目录路径
    has_config: bool  # 是否已有配置文件
    version: Optional[str] = None  # CLI 版本（如果可检测）


@dataclass
class ValidationResult:
    """Provider 配置验证结果"""

    valid: bool
    errors: List[str]  # 错误信息列表
    warnings: List[str]  # 警告信息列表

    @staticmethod
    def success() -> "ValidationResult":
        """创建成功的验证结果"""
        return ValidationResult(valid=True, errors=[], warnings=[])

    @staticmethod
    def failure(
        errors: List[str], warnings: Optional[List[str]] = None
    ) -> "ValidationResult":
        """创建失败的验证结果"""
        return ValidationResult(valid=False, errors=errors, warnings=warnings or [])


@dataclass
class ExportResult:
    """单个 CLI 工具导出结果"""

    success: bool
    cli_type: str
    backup_path: Optional[Path]
    error_message: Optional[str]
    files_written: List[Path]

    @staticmethod
    def ok(
        cli_type: str, files_written: List[Path], backup_path: Optional[Path] = None
    ) -> "ExportResult":
        """创建成功的导出结果"""
        return ExportResult(
            success=True,
            cli_type=cli_type,
            backup_path=backup_path,
            error_message=None,
            files_written=files_written,
        )

    @staticmethod
    def fail(
        cli_type: str, error_message: str, backup_path: Optional[Path] = None
    ) -> "ExportResult":
        """创建失败的导出结果"""
        return ExportResult(
            success=False,
            cli_type=cli_type,
            backup_path=backup_path,
            error_message=error_message,
            files_written=[],
        )


@dataclass
class BatchExportResult:
    """批量导出结果"""

    total: int
    successful: int
    failed: int
    results: List[ExportResult]

    @property
    def all_success(self) -> bool:
        """是否全部成功"""
        return self.failed == 0

    @property
    def partial_success(self) -> bool:
        """是否部分成功"""
        return self.successful > 0 and self.failed > 0


@dataclass
class BackupInfo:
    """备份信息"""

    path: Path
    cli_type: str
    created_at: datetime
    files: List[str]


# ==================== CLI 导出模块异常类 ====================
class CLIExportError(Exception):
    """CLI 导出错误基类"""

    pass


class ProviderValidationError(CLIExportError):
    """Provider 配置验证错误"""

    def __init__(self, missing_fields: List[str]):
        self.missing_fields = missing_fields
        super().__init__(f"Provider 配置不完整: 缺少 {', '.join(missing_fields)}")


class ConfigWriteError(CLIExportError):
    """配置写入错误"""

    def __init__(self, path: Path, reason: str):
        self.path = path
        self.reason = reason
        super().__init__(f"写入配置失败 ({path}): {reason}")


class ConfigParseError(CLIExportError):
    """配置解析错误"""

    def __init__(self, path: Path, format_type: str, reason: str):
        self.path = path
        self.format_type = format_type
        self.reason = reason
        super().__init__(f"解析 {format_type} 配置失败 ({path}): {reason}")


class BackupError(CLIExportError):
    """备份操作错误"""

    def __init__(self, cli_type: str, reason: str):
        self.cli_type = cli_type
        self.reason = reason
        super().__init__(f"备份 {cli_type} 配置失败: {reason}")


class RestoreError(CLIExportError):
    """恢复操作错误"""

    def __init__(self, backup_path: Path, reason: str):
        self.backup_path = backup_path
        self.reason = reason
        super().__init__(f"恢复备份失败 ({backup_path}): {reason}")


# ==================== 原生 Provider 认证管理 ====================
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
        """
        auth_data = self.read_auth()
        return auth_data.get(provider_id)

    def set_provider_auth(self, provider_id: str, auth_config: Dict[str, Any]) -> None:
        """设置指定 Provider 的认证信息

        Args:
            provider_id: Provider 标识符
            auth_config: 认证配置字典（如 {'apiKey': 'sk-xxx'}）
        """
        auth_data = self.read_auth()
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


# ==================== 原生 Provider 配置数据类 ====================
@dataclass
class AuthField:
    """认证字段定义"""

    key: str  # 字段键名（如 'apiKey', 'accessKeyId'）
    label: str  # 显示标签（如 'API Key', 'Access Key ID'）
    field_type: str  # 字段类型: text, password, file
    required: bool  # 是否必填
    placeholder: str  # 占位符文本


@dataclass
class OptionField:
    """选项字段定义"""

    key: str  # 字段键名（如 'baseURL', 'region'）
    label: str  # 显示标签
    field_type: str  # 字段类型: text, select
    options: List[str]  # 可选值（select 类型时使用）
    default: str  # 默认值


@dataclass
class NativeProviderConfig:
    """原生 Provider 配置定义"""

    id: str  # Provider ID（如 'anthropic', 'openai'）
    name: str  # 显示名称（如 'Anthropic (Claude)'）
    sdk: str  # SDK 包名（如 '@ai-sdk/anthropic'）
    auth_fields: List[AuthField]  # 认证字段列表
    option_fields: List[OptionField]  # 选项字段列表
    env_vars: List[str]  # 相关环境变量
    test_endpoint: Optional[str]  # 测试端点（用于连接测试）


# 所有支持的原生 Provider 配置
NATIVE_PROVIDERS: List[NativeProviderConfig] = [
    NativeProviderConfig(
        id="anthropic",
        name="Anthropic (Claude)",
        sdk="@ai-sdk/anthropic",
        auth_fields=[
            AuthField("apiKey", "API Key", "password", True, "sk-ant-..."),
        ],
        option_fields=[
            OptionField("baseURL", "Base URL", "text", [], ""),
        ],
        env_vars=["ANTHROPIC_API_KEY"],
        test_endpoint="/v1/models",
    ),
    NativeProviderConfig(
        id="openai",
        name="OpenAI",
        sdk="@ai-sdk/openai",
        auth_fields=[
            AuthField("apiKey", "API Key", "password", True, "sk-..."),
        ],
        option_fields=[
            OptionField("baseURL", "Base URL", "text", [], ""),
        ],
        env_vars=["OPENAI_API_KEY"],
        test_endpoint="/v1/models",
    ),
    NativeProviderConfig(
        id="gemini",
        name="Google Gemini",
        sdk="@ai-sdk/google",
        auth_fields=[
            AuthField("apiKey", "API Key", "password", True, ""),
        ],
        option_fields=[
            OptionField("baseURL", "Base URL", "text", [], ""),
        ],
        env_vars=["GEMINI_API_KEY", "GOOGLE_API_KEY"],
        test_endpoint="/v1/models",
    ),
    NativeProviderConfig(
        id="amazon-bedrock",
        name="Amazon Bedrock",
        sdk="@ai-sdk/amazon-bedrock",
        auth_fields=[
            AuthField("accessKeyId", "Access Key ID", "password", False, "AKIA..."),
            AuthField("secretAccessKey", "Secret Access Key", "password", False, ""),
            AuthField("profile", "AWS Profile", "text", False, "default"),
        ],
        option_fields=[
            OptionField(
                "region",
                "Region",
                "select",
                ["us-east-1", "us-west-2", "eu-west-1", "ap-northeast-1"],
                "us-east-1",
            ),
            OptionField("endpoint", "VPC Endpoint", "text", [], ""),
        ],
        env_vars=[
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "AWS_PROFILE",
            "AWS_REGION",
        ],
        test_endpoint=None,
    ),
    NativeProviderConfig(
        id="azure",
        name="Azure OpenAI",
        sdk="@ai-sdk/azure",
        auth_fields=[
            AuthField("apiKey", "API Key", "password", True, ""),
            AuthField("resourceName", "Resource Name", "text", True, ""),
        ],
        option_fields=[
            OptionField("baseURL", "Base URL", "text", [], ""),
        ],
        env_vars=["AZURE_OPENAI_API_KEY", "AZURE_RESOURCE_NAME"],
        test_endpoint=None,
    ),
    NativeProviderConfig(
        id="copilot",
        name="GitHub Copilot",
        sdk="@ai-sdk/openai",
        auth_fields=[
            AuthField("token", "GitHub Token", "password", True, ""),
        ],
        option_fields=[],
        env_vars=[],
        test_endpoint=None,
    ),
    NativeProviderConfig(
        id="xai",
        name="xAI (Grok)",
        sdk="@ai-sdk/xai",
        auth_fields=[
            AuthField("apiKey", "API Key", "password", True, ""),
        ],
        option_fields=[
            OptionField("baseURL", "Base URL", "text", [], ""),
        ],
        env_vars=["XAI_API_KEY"],
        test_endpoint="/v1/models",
    ),
    NativeProviderConfig(
        id="groq",
        name="Groq",
        sdk="@ai-sdk/groq",
        auth_fields=[
            AuthField("apiKey", "API Key", "password", True, "gsk_..."),
        ],
        option_fields=[
            OptionField("baseURL", "Base URL", "text", [], ""),
        ],
        env_vars=["GROQ_API_KEY"],
        test_endpoint="/openai/v1/models",
    ),
    NativeProviderConfig(
        id="openrouter",
        name="OpenRouter",
        sdk="@ai-sdk/openai-compatible",
        auth_fields=[
            AuthField("apiKey", "API Key", "password", True, "sk-or-..."),
        ],
        option_fields=[
            OptionField(
                "baseURL", "Base URL", "text", [], "https://openrouter.ai/api/v1"
            ),
        ],
        env_vars=["OPENROUTER_API_KEY"],
        test_endpoint="/models",
    ),
    NativeProviderConfig(
        id="vertexai",
        name="Google Vertex AI",
        sdk="@ai-sdk/google-vertex",
        auth_fields=[
            AuthField("credentials", "Service Account JSON", "file", False, ""),
            AuthField("projectId", "Project ID", "text", True, ""),
        ],
        option_fields=[
            OptionField(
                "location",
                "Location",
                "select",
                ["global", "us-central1", "us-east1", "europe-west1", "asia-east1"],
                "global",
            ),
        ],
        env_vars=[
            "GOOGLE_APPLICATION_CREDENTIALS",
            "GOOGLE_CLOUD_PROJECT",
            "VERTEX_LOCATION",
        ],
        test_endpoint=None,
    ),
    NativeProviderConfig(
        id="deepseek",
        name="DeepSeek",
        sdk="@ai-sdk/openai-compatible",
        auth_fields=[
            AuthField("apiKey", "API Key", "password", True, "sk-..."),
        ],
        option_fields=[
            OptionField("baseURL", "Base URL", "text", [], "https://api.deepseek.com"),
        ],
        env_vars=["DEEPSEEK_API_KEY"],
        test_endpoint="/models",
    ),
    NativeProviderConfig(
        id="zhipu",
        name="智谱 GLM",
        sdk="@ai-sdk/openai-compatible",
        auth_fields=[
            AuthField("apiKey", "API Key", "password", True, ""),
        ],
        option_fields=[
            OptionField(
                "baseURL",
                "Base URL",
                "text",
                [],
                "https://open.bigmodel.cn/api/paas/v4/",
            ),
        ],
        env_vars=["ZHIPU_API_KEY"],
        test_endpoint="/models",
    ),
    NativeProviderConfig(
        id="qwen",
        name="千问 Qwen",
        sdk="@ai-sdk/openai-compatible",
        auth_fields=[
            AuthField("apiKey", "API Key", "password", True, "sk-..."),
        ],
        option_fields=[
            OptionField(
                "baseURL",
                "Base URL",
                "text",
                [],
                "https://dashscope.aliyuncs.com/compatible-mode/v1",
            ),
        ],
        env_vars=["DASHSCOPE_API_KEY", "QWEN_API_KEY"],
        test_endpoint="/models",
    ),
    NativeProviderConfig(
        id="kimi",
        name="Kimi (月之暗面)",
        sdk="@ai-sdk/openai-compatible",
        auth_fields=[
            AuthField("apiKey", "API Key", "password", True, ""),
        ],
        option_fields=[
            OptionField(
                "baseURL", "Base URL", "text", [], "https://api.moonshot.cn/v1"
            ),
        ],
        env_vars=["MOONSHOT_API_KEY", "KIMI_API_KEY"],
        test_endpoint="/models",
    ),
    NativeProviderConfig(
        id="yi",
        name="零一万物 Yi",
        sdk="@ai-sdk/openai-compatible",
        auth_fields=[
            AuthField("apiKey", "API Key", "password", True, ""),
        ],
        option_fields=[
            OptionField(
                "baseURL", "Base URL", "text", [], "https://api.lingyiwanwu.com/v1"
            ),
        ],
        env_vars=["YI_API_KEY"],
        test_endpoint="/models",
    ),
    NativeProviderConfig(
        id="minimax",
        name="MiniMax",
        sdk="@ai-sdk/openai-compatible",
        auth_fields=[
            AuthField("apiKey", "API Key", "password", True, ""),
        ],
        option_fields=[
            OptionField(
                "baseURL", "Base URL", "text", [], "https://api.minimax.chat/v1"
            ),
        ],
        env_vars=["MINIMAX_API_KEY"],
        test_endpoint="/models",
    ),
    NativeProviderConfig(
        id="opencode",
        name="OpenCode Zen",
        sdk="@ai-sdk/openai-compatible",
        auth_fields=[
            AuthField("apiKey", "API Key", "password", True, ""),
        ],
        option_fields=[
            OptionField(
                "baseURL", "Base URL", "text", [], "https://api.opencode.ai/v1"
            ),
        ],
        env_vars=[],
        test_endpoint="/models",
    ),
]


def get_native_provider(provider_id: str) -> Optional[NativeProviderConfig]:
    """根据 ID 获取原生 Provider 配置"""
    for provider in NATIVE_PROVIDERS:
        if provider.id == provider_id:
            return provider
    return None


# ==================== 环境变量检测器 ====================
class EnvVarDetector:
    """环境变量检测器 - 检测系统中已设置的 Provider 相关环境变量"""

    # Provider 与环境变量的映射
    PROVIDER_ENV_VARS: Dict[str, List[str]] = {
        "anthropic": ["ANTHROPIC_API_KEY"],
        "openai": ["OPENAI_API_KEY"],
        "gemini": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
        "amazon-bedrock": [
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "AWS_PROFILE",
            "AWS_REGION",
        ],
        "azure": ["AZURE_OPENAI_API_KEY", "AZURE_RESOURCE_NAME"],
        "xai": ["XAI_API_KEY"],
        "groq": ["GROQ_API_KEY"],
        "openrouter": ["OPENROUTER_API_KEY"],
        "vertexai": [
            "GOOGLE_APPLICATION_CREDENTIALS",
            "GOOGLE_CLOUD_PROJECT",
            "VERTEX_LOCATION",
        ],
        "deepseek": ["DEEPSEEK_API_KEY"],
        "zhipu": ["ZHIPU_API_KEY"],
        "qwen": ["DASHSCOPE_API_KEY", "QWEN_API_KEY"],
        "kimi": ["MOONSHOT_API_KEY", "KIMI_API_KEY"],
        "yi": ["YI_API_KEY"],
        "minimax": ["MINIMAX_API_KEY"],
    }

    # 环境变量到认证字段的映射
    ENV_TO_AUTH_FIELD: Dict[str, str] = {
        "ANTHROPIC_API_KEY": "apiKey",
        "OPENAI_API_KEY": "apiKey",
        "GEMINI_API_KEY": "apiKey",
        "GOOGLE_API_KEY": "apiKey",
        "AWS_ACCESS_KEY_ID": "accessKeyId",
        "AWS_SECRET_ACCESS_KEY": "secretAccessKey",
        "AWS_PROFILE": "profile",
        "AZURE_OPENAI_API_KEY": "apiKey",
        "AZURE_RESOURCE_NAME": "resourceName",
        "XAI_API_KEY": "apiKey",
        "GROQ_API_KEY": "apiKey",
        "OPENROUTER_API_KEY": "apiKey",
        "GOOGLE_APPLICATION_CREDENTIALS": "credentials",
        "GOOGLE_CLOUD_PROJECT": "projectId",
        "DEEPSEEK_API_KEY": "apiKey",
    }

    def detect_env_vars(self, provider_id: str) -> Dict[str, str]:
        """检测指定 Provider 的环境变量

        Args:
            provider_id: Provider 标识符

        Returns:
            已设置的环境变量字典 {变量名: 值}
        """
        env_vars = self.PROVIDER_ENV_VARS.get(provider_id, [])
        detected = {}
        for var in env_vars:
            value = os.environ.get(var)
            if value:
                detected[var] = value
        return detected

    def detect_all_env_vars(self) -> Dict[str, Dict[str, str]]:
        """检测所有 Provider 的环境变量

        Returns:
            {provider_id: {变量名: 值}}
        """
        result = {}
        for provider_id in self.PROVIDER_ENV_VARS:
            detected = self.detect_env_vars(provider_id)
            if detected:
                result[provider_id] = detected
        return result

    @staticmethod
    def format_env_reference(var_name: str) -> str:
        """格式化环境变量引用

        Args:
            var_name: 环境变量名

        Returns:
            格式化的引用字符串 {env:VARIABLE_NAME}
        """
        return f"{{env:{var_name}}}"

    def get_auth_field_for_env(self, env_var: str) -> Optional[str]:
        """获取环境变量对应的认证字段名

        Args:
            env_var: 环境变量名

        Returns:
            对应的认证字段名，未找到时返回 None
        """
        return self.ENV_TO_AUTH_FIELD.get(env_var)


STATUS_LABELS = {
    "operational": "monitor.status_operational",
    "degraded": "monitor.status_degraded",
    "failed": "monitor.status_failed",
    "error": "monitor.status_error",
    "no_config": "monitor.status_no_config",
}

# 状态颜色 - 与 UIConfig 配色方案一致
STATUS_COLORS = {
    "operational": "#4CAF50",  # UIConfig.COLOR_SUCCESS
    "degraded": "#FF9800",  # UIConfig.COLOR_WARNING
    "failed": "#F44336",  # UIConfig.COLOR_ERROR
    "error": "#F44336",  # UIConfig.COLOR_ERROR
    "no_config": "#9E9E9E",  # UIConfig.COLOR_TEXT_SECONDARY
}

STATUS_BG_COLORS = {
    "operational": "#1B3D1B",
    "degraded": "#3D3018",
    "failed": "#3D1B1B",
    "error": "#3D1B1B",
    "no_config": "#0d1117",
}


def _format_latency(value: Optional[int]) -> str:
    return f"{value} ms" if isinstance(value, int) else "—"


def _calc_availability(history: Deque[MonitorResult]) -> Optional[float]:
    if not history:
        return None
    total = len(history)
    ok = sum(1 for item in history if item.status in ("operational", "degraded"))
    if total == 0:
        return None
    return ok * 100.0 / total


def _measure_ping(origin: str, timeout_sec: float = 3.0) -> Optional[int]:
    if not origin:
        return None
    parsed = urlparse(origin)
    host = parsed.hostname
    if not host:
        return None
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    start = time.time()
    try:
        sock = socket.create_connection((host, port), timeout=timeout_sec)
        sock.close()
    except Exception:
        return None
    return int((time.time() - start) * 1000)


def _safe_json_load(data: bytes) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(data.decode("utf-8"))
    except Exception:
        return None


from PyQt5.QtCore import (
    Qt,
    QUrl,
    pyqtSignal,
    QTimer,
    QObject,
    QRegularExpression,
    Qt as QtCore,
    QMetaObject,
    Q_ARG,
    pyqtSlot,
    QSize,
)
from PyQt5.QtGui import (
    QIcon,
    QDesktopServices,
    QFont,
    QPixmap,
    QColor,
    QPainter,
    QPen,
    QTextCharFormat,
    QSyntaxHighlighter,
    QTextCursor,
    QFontMetrics,
)
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QStackedWidget,
    QSplitter,
    QScrollArea,
    QSizePolicy,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QMessageBox,
    QFileDialog,
    QDialog,
    QDialogButtonBox,
    QTextEdit,
    QListWidgetItem,
    QGroupBox,
    QComboBox as QNativeComboBox,
)

from qfluentwidgets import (
    FluentWindow,
    NavigationItemPosition,
    MessageBox as FluentMessageBox,
    MessageBoxBase,
    InfoBar,
    InfoBarPosition,
    InfoBarIcon,
    StateToolTip,
    PushButton,
    PrimaryPushButton,
    TransparentPushButton,
    TransparentToolButton,
    HyperlinkButton,
    HyperlinkLabel,
    ToolButton,
    LineEdit,
    TextEdit,
    PlainTextEdit,
    ComboBox,
    CheckBox,
    RadioButton,
    Slider,
    SpinBox,
    SubtitleLabel,
    BodyLabel,
    CaptionLabel,
    StrongBodyLabel,
    TitleLabel,
    SimpleCardWidget,
    ElevatedCardWidget,
    HeaderCardWidget,
    GroupHeaderCardWidget,
    CardWidget,
    TableWidget,
    TreeWidget,
    ListWidget,
    FlowLayout,
    ExpandLayout,
    Pivot,
    SegmentedWidget,
    FluentIcon as FIF,
    setTheme,
    Theme,
    isDarkTheme,
    qconfig,
    setThemeColor,
    setFont,
    SystemThemeListener,
)


# ==================== 语言管理器 ====================
class LanguageManager(QObject):
    """多语言管理器"""

    language_changed = pyqtSignal(str)  # 语言切换信号

    _instance = None
    _current_language = "zh_CN"
    _translations = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            QObject.__init__(cls._instance)
        return cls._instance

    def __init__(self):
        if not self._translations:
            self._load_translations()

    def _load_translations(self):
        """加载所有语言文件"""
        locales_dir = Path(__file__).parent / "locales"
        if not locales_dir.exists():
            return

        for lang_file in locales_dir.glob("*.json"):
            lang_code = lang_file.stem
            try:
                with open(lang_file, "r", encoding="utf-8") as f:
                    self._translations[lang_code] = json.load(f)
            except Exception as e:
                print(f"Failed to load language file {lang_file}: {e}")

    def set_language(self, lang_code: str):
        """设置当前语言"""
        if lang_code in self._translations:
            self._current_language = lang_code
            # 保存到配置文件
            self._save_language_preference(lang_code)
            # 发出语言切换信号
            self.language_changed.emit(lang_code)

    def get_current_language(self) -> str:
        """获取当前语言"""
        return self._current_language

    def get_available_languages(self) -> List[str]:
        """获取可用语言列表"""
        return list(self._translations.keys())

    def tr(self, key: str, **kwargs) -> str:
        """翻译文本

        Args:
            key: 翻译键，支持点号分隔的路径，如 "skill.title"
            **kwargs: 格式化参数

        Returns:
            翻译后的文本
        """
        keys = key.split(".")
        value = self._translations.get(self._current_language, {})

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return key

        if value is None:
            return key

        # 格式化参数
        if kwargs and isinstance(value, str):
            try:
                return value.format(**kwargs)
            except KeyError:
                return value

        return str(value)

    def _save_language_preference(self, lang_code: str):
        """保存语言偏好到配置文件"""
        config_file = Path.home() / ".config" / "opencode" / "ui_config.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)

        config = {}
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
            except Exception:
                pass

        config["language"] = lang_code

        try:
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save language preference: {e}")

    def _load_language_preference(self) -> str:
        """从配置文件加载语言偏好，如果没有则自动识别系统语言"""
        config_file = Path.home() / ".config" / "opencode" / "ui_config.json"
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    saved_lang = config.get("language")
                    if saved_lang:
                        return saved_lang
            except Exception:
                pass

        # 自动识别系统语言
        return self._detect_system_language()

    def _detect_system_language(self) -> str:
        """自动识别系统语言

        Returns:
            语言代码，zh_CN 或 en_US
        """
        try:
            # 方法1: 使用 PyQt5 的 QLocale
            from PyQt5.QtCore import QLocale

            system_locale = QLocale.system()
            locale_name = system_locale.name()  # 例如: "zh_CN", "en_US", "ja_JP"

            # 判断是否为中文
            if locale_name.startswith("zh"):
                return "zh_CN"
            else:
                return "en_US"
        except Exception:
            pass

        try:
            # 方法2: 使用 Python 的 locale 模块
            import locale

            system_locale = locale.getdefaultlocale()[0]  # 例如: "zh_CN", "en_US"
            if system_locale and system_locale.startswith("zh"):
                return "zh_CN"
            else:
                return "en_US"
        except Exception:
            pass

        # 默认返回中文
        return "zh_CN"


# 全局语言管理器实例
_lang_manager = LanguageManager()


def tr(key: str, **kwargs) -> str:
    """全局翻译函数"""
    return _lang_manager.tr(key, **kwargs)


# ==================== UI 样式配置 ====================
class UIConfig:
    """全局 UI 配置"""

    # 字体配置 - 参考 Any-code 项目，优先使用系统原生字体
    # Sans-serif 字体栈：优先系统字体，中文字体作为 fallback
    FONT_FAMILY_SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', 'Microsoft YaHei UI', '微软雅黑', 'PingFang SC', 'Hiragino Sans GB', 'SimSun', '宋体', 'Arial Unicode MS', sans-serif"

    # Monospace 字体栈：用于代码和等宽文本
    FONT_FAMILY_MONO = "'JetBrains Mono', 'Fira Code', 'SF Mono', 'Menlo', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', 'Microsoft YaHei Mono', '微软雅黑', monospace"

    # 字体大小配置
    FONT_SIZE_TITLE = 16
    FONT_SIZE_BODY = 14
    FONT_SIZE_SMALL = 12
    FONT_SIZE_NUMBER = 20

    # 状态颜色（不随主题变化）
    COLOR_PRIMARY = "#2196F3"  # 高亮/主色
    COLOR_SUCCESS = "#4CAF50"  # 成功
    COLOR_WARNING = "#FF9800"  # 警告
    COLOR_ERROR = "#F44336"  # 错误

    # 深色主题颜色 (GitHub Dark 风格 - 接近纯黑)
    DARK_BG = "#0d1117"  # 主背景
    DARK_CARD = "#161b22"  # 卡片背景
    DARK_BORDER = "#30363d"  # 边框

    # 布局
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 820

    @staticmethod
    def get_stylesheet() -> str:
        """获取全局 QSS 样式表 - 优化字体渲染，解决英文显示和遮挡问题"""
        # 字体栈定义
        font_sans = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', 'Microsoft YaHei UI', '微软雅黑', 'PingFang SC', 'Hiragino Sans GB', 'SimSun', '宋体', 'Arial Unicode MS', sans-serif"
        font_mono = "'JetBrains Mono', 'Fira Code', 'SF Mono', 'Menlo', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', 'Microsoft YaHei Mono', '微软雅黑', monospace"

        return f"""
            /* ==================== 全局字体 ==================== */
            * {{
                font-family: {font_sans};
            }}
            QWidget {{
                font-family: {font_sans};
                font-size: {UIConfig.FONT_SIZE_BODY}px;
            }}

            /* ==================== 字体大小层级 ==================== */
            TitleLabel {{
                font-size: 18px;
                font-weight: bold;
                font-family: {font_sans};
            }}
            SubtitleLabel {{
                font-size: {UIConfig.FONT_SIZE_TITLE}px;
                font-weight: bold;
                font-family: {font_sans};
            }}
            BodyLabel {{
                font-size: {UIConfig.FONT_SIZE_BODY}px;
                font-family: {font_sans};
            }}
            CaptionLabel {{
                font-size: {UIConfig.FONT_SIZE_SMALL}px;
                font-family: {font_sans};
            }}
            StrongBodyLabel {{
                font-size: {UIConfig.FONT_SIZE_BODY}px;
                font-weight: bold;
                font-family: {font_sans};
            }}

            /* ==================== 按钮字体 ==================== */
            QPushButton, PushButton, PrimaryPushButton, TransparentPushButton, ToolButton {{
                font-size: {UIConfig.FONT_SIZE_BODY}px;
                font-family: {font_sans};
                padding: 6px 16px;
                min-height: 32px;
            }}

            /* ==================== 输入框字体 ==================== */
            QLineEdit, LineEdit {{
                font-size: {UIConfig.FONT_SIZE_BODY}px;
                font-family: {font_sans};
                padding: 6px 12px;
                min-height: 32px;
            }}
            
            QTextEdit, TextEdit, QPlainTextEdit, PlainTextEdit {{
                font-size: {UIConfig.FONT_SIZE_BODY}px;
                font-family: {font_mono};
                line-height: 1.6;
            }}

            /* ==================== 下拉框字体 ==================== */
            QComboBox, ComboBox {{
                font-size: {UIConfig.FONT_SIZE_BODY}px;
                font-family: {font_sans};
                padding: 6px 12px;
                min-height: 32px;
            }}
            
            QComboBox::drop-down {{
                width: 30px;
            }}
            
            QComboBox QAbstractItemView {{
                font-size: {UIConfig.FONT_SIZE_BODY}px;
                font-family: {font_sans};
                padding: 4px;
            }}

            /* ==================== 表格字体 ==================== */
            QTableWidget, TableWidget {{
                font-size: {UIConfig.FONT_SIZE_BODY}px;
                font-family: {font_sans};
            }}
            QHeaderView::section {{
                font-weight: 600;
                font-size: 13px;
                font-family: {font_sans};
                padding: 8px 12px;
                min-height: 36px;
            }}
            
            /* ==================== 修复表格左上角单元格白色问题 ==================== */
            QTableWidget QTableCornerButton::section {{
                background-color: transparent;
                border: none;
            }}

            /* ==================== 列表字体 ==================== */
            QListWidget, ListWidget {{
                font-size: {UIConfig.FONT_SIZE_BODY}px;
                font-family: {font_sans};
            }}
            
            QListWidget::item {{
                padding: 8px 12px;
                min-height: 36px;
            }}

            /* ==================== 菜单字体 ==================== */
            QMenu {{
                font-size: {UIConfig.FONT_SIZE_BODY}px;
                font-family: {font_sans};
                padding: 4px;
            }}
            
            QMenu::item {{
                padding: 8px 24px 8px 12px;
                min-height: 32px;
            }}

            /* ==================== 滚动条样式 ==================== */
            QScrollBar:vertical {{
                width: 8px;
            }}
            QScrollBar:horizontal {{
                height: 8px;
            }}

            /* ==================== 工具提示字体 ==================== */
            QToolTip {{
                font-size: {UIConfig.FONT_SIZE_SMALL}px;
                font-family: {font_sans};
                padding: 6px 10px;
            }}
            
            /* ==================== 代码/等宽文本 ==================== */
            code, pre, .monospace {{
                font-family: {font_mono};
                font-size: {UIConfig.FONT_SIZE_SMALL}px;
            }}
        """


APP_VERSION = "1.5.0"
GITHUB_REPO = "icysaintdx/OpenCode-Config-Manager"
GITHUB_URL = f"https://github.com/{GITHUB_REPO}"
GITHUB_RELEASES_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
AUTHOR_NAME = "IcySaint"
AUTHOR_GITHUB = "https://github.com/icysaintdx"

# 监控页面配置
MONITOR_POLL_INTERVAL_MS = 60000
MONITOR_HISTORY_LIMIT = 60
DEGRADED_THRESHOLD_MS = 6000

# ==================== 版本检查配置 ====================
STARTUP_VERSION_CHECK_ENABLED = True  # 启动时是否检查版本
IMMEDIATE_VERSION_CHECK_MS = 5000  # 启动后首次检查延迟 (5秒)
UPDATE_INTERVAL_MS = 60 * 1000  # 定时检查间隔 (1分钟)


def get_resource_path(relative_path: str) -> Path:
    """获取资源文件路径 - 兼容 PyInstaller 打包后的环境"""
    base_path_value = getattr(sys, "_MEIPASS", None)
    base_path = Path(base_path_value) if base_path_value else Path(__file__).parent
    return base_path / relative_path


# ==================== 参数说明提示（用于Tooltip） ====================
# 根据 OpenCode 官方文档，所有提示都包含：关键字 + 白话解释 + 使用场景 + 示例
TOOLTIPS = {
    # ==================== Provider 相关 ====================
    "provider_name": """Provider 名称 (provider_name) ⓘ

【作用】Provider的唯一标识符，用于在配置中引用此Provider

【格式要求】
• 使用小写字母和连字符
• 不能有空格或特殊字符

【常见示例】
• anthropic - Anthropic官方
• openai - OpenAI官方
• my-proxy - 自定义中转站

【使用场景】
配置模型时需要指定 provider/model-id 格式""",
    "provider_display": """显示名称 (display name) ⓘ

【作用】在界面中显示的友好名称，方便识别

【格式要求】
• 可以使用中文、空格
• 建议简洁明了

【常见示例】
• Anthropic (Claude)
• OpenAI 官方
• 我的中转站""",
    "provider_sdk": """SDK 包名 (npm package) ⓘ

【作用】指定使用哪个AI SDK来调用API

【选择指南】
• Claude系列 → @ai-sdk/anthropic
• GPT/OpenAI系列 → @ai-sdk/openai
• Gemini系列 → @ai-sdk/google
• Azure OpenAI → @ai-sdk/azure
• 其他兼容OpenAI的API → @ai-sdk/openai-compatible

【重要提示】
SDK必须与模型厂商匹配，否则无法正常调用！""",
    "provider_url": """API 地址 (baseURL) ⓘ

【作用】API服务的访问地址

【使用场景】
• 使用官方API → 留空（自动使用默认地址）
• 使用中转站 → 填写中转站地址
• 使用私有部署 → 填写私有服务地址

【格式示例】
• https://api.openai.com/v1
• https://my-proxy.com/api
• 留空 = 使用SDK默认地址""",
    "provider_apikey": """API 密钥 (apiKey) ⓘ

【作用】用于身份验证的密钥

【获取方式】
• Anthropic: console.anthropic.com
• OpenAI: platform.openai.com
• Google: aistudio.google.com

【安全提示】
• 支持环境变量引用: {env:ANTHROPIC_API_KEY}
• 不要将密钥提交到代码仓库
• 定期轮换密钥""",
    "provider_model_list_url": """模型列表地址 (modelListUrl) ⓘ

【作用】用于拉取 Provider 支持的模型列表

【使用场景】
• API 地址不支持标准 /v1/models 时，填写自定义模型列表接口
• 私有部署或中转站需要自定义路径

【格式示例】
• https://api.example.com/v1/models
• /custom/models""",
    "provider_timeout": """请求超时 (timeout) ⓘ

【作用】API请求的最大等待时间

【单位】毫秒 (ms)

【推荐设置】
• 默认: 300000 (5分钟)
• 快速响应场景: 60000 (1分钟)
• 长文本生成: 600000 (10分钟)

【特殊值】
• false = 禁用超时（不推荐）""",
    # ==================== Model 相关 ====================
    "model_id": """模型 ID (model identifier) ⓘ

【作用】模型的唯一标识符，必须与API提供商的模型ID完全一致

【格式要求】
• 必须是API支持的有效模型名称
• 区分大小写

【常见示例】
• Claude: claude-sonnet-4-5-20250929
• GPT: gpt-5, gpt-4o
• Gemini: gemini-3-pro

【重要提示】
模型ID错误会导致API调用失败！""",
    "model_name": """显示名称 (display name) ⓘ

【作用】在界面中显示的友好名称

【建议】
• 使用易于识别的名称
• 可以包含版本信息

【示例】
• Claude Sonnet 4.5
• GPT-5 旗舰版
• Gemini 3 Pro""",
    "model_attachment": """支持附件 (attachment support) ⓘ

【作用】是否支持上传文件（图片、文档等）

【支持情况】
✓ 多模态模型通常支持（Claude、GPT-4o、Gemini）
✗ 纯文本模型不支持（o1系列）

【使用场景】
• 图片分析
• 文档解读
• 代码截图理解""",
    "model_context": """上下文窗口 (context window) ⓘ

【作用】模型能处理的最大输入长度（tokens）

【单位】tokens（约等于0.75个英文单词或0.5个中文字符）

【常见大小】
• 128K = 128,000 tokens ≈ 10万字
• 200K = 200,000 tokens ≈ 15万字
• 1M = 1,048,576 tokens ≈ 80万字
• 2M = 2,097,152 tokens ≈ 160万字

【影响】
上下文越大，能处理的对话历史和文件越多""",
    "model_output": """最大输出 (max output) ⓘ

【作用】模型单次回复的最大长度（tokens）

【常见大小】
• 8K = 8,192 tokens ≈ 6000字
• 16K = 16,384 tokens ≈ 12000字
• 32K = 32,768 tokens ≈ 24000字
• 64K = 65,536 tokens ≈ 48000字

【影响】
输出限制越大，单次回复可以越长""",
    "model_options": """模型默认配置 (Options) ⓘ

【作用】每次调用模型时自动使用的参数

【重要区别】
• Options = 默认配置，每次都用
• Variants = 可切换的预设，按需切换

【Claude thinking模式】
thinking.type = "enabled"
thinking.budgetTokens = 16000

【OpenAI推理模式】
reasoningEffort = "high"
textVerbosity = "low"

【Gemini thinking模式】
thinkingConfig.thinkingBudget = 8000

【提示】选择预设模型会自动填充推荐配置""",
    "model_variants": """模型变体 (Variants) ⓘ

【作用】可通过快捷键切换的预设配置组合

【使用场景】
• 同一模型的不同配置
• 快速切换推理强度
• 切换thinking开关

【切换方式】
使用 variant_cycle 快捷键循环切换

【配置示例】
high: {reasoningEffort: high}
low: {reasoningEffort: low}

【与Options的区别】
Options是默认值，Variants是可选预设""",
    "model_preset_category": """预设模型分类 ⓘ

【作用】快速选择常用模型系列

【可选分类】
• Claude 系列 - Anthropic的Claude模型
• OpenAI/Codex 系列 - GPT和推理模型
• Gemini 系列 - Google的Gemini模型
• 其他模型 - DeepSeek、Qwen等

【使用方法】
选择分类后，在右侧选择具体模型""",
    "model_preset_model": """预设模型选择 ⓘ

【作用】从预设列表中快速选择模型

【自动填充】
选择预设模型后会自动填充：
• 模型ID
• 显示名称
• 上下文/输出限制
• Options默认配置
• Variants变体配置

【提示】
选择后仍可手动修改任何参数""",
    # ==================== Options 快捷添加 ====================
    "option_reasoningEffort": """推理强度 (reasoningEffort) - OpenAI模型 ⓘ

【作用】控制模型的推理深度和思考时间

【可选值】
• xhigh - 超高强度，最深入的推理（GPT-5专属）
• high - 高强度，更准确但更慢
• medium - 中等强度，平衡速度和质量
• low - 低强度，更快但可能不够准确

【适用模型】
GPT-5、o1、o3系列

【使用建议】
• 复杂问题 → high/xhigh
• 简单问题 → low/medium""",
    "option_textVerbosity": """输出详细程度 (textVerbosity) - OpenAI模型 ⓘ

【作用】控制回复的详细程度

【可选值】
• low - 简洁输出，只给关键信息
• high - 详细输出，包含更多解释

【适用模型】
GPT-5系列

【使用建议】
• 代码生成 → low（减少废话）
• 学习解释 → high（详细说明）""",
    "option_reasoningSummary": """推理摘要 (reasoningSummary) - OpenAI模型 ⓘ

【作用】是否生成推理过程的摘要

【可选值】
• auto - 自动决定是否生成摘要
• none - 不生成摘要

【适用模型】
GPT-5、o1、o3系列

【使用场景】
• 需要了解推理过程 → auto
• 只要结果 → none""",
    "option_thinking_type": """Thinking模式类型 (thinking.type) - Claude模型 ⓘ

【作用】是否启用Claude的extended thinking功能

【可选值】
• enabled - 启用thinking模式
• disabled - 禁用thinking模式

【什么是Thinking模式？】
让Claude在回答前进行深度思考，
类似于人类的"让我想想..."

【适用模型】
Claude Opus 4.5、Claude Sonnet 4.5

【使用建议】
• 复杂推理/编程 → enabled
• 简单对话 → disabled""",
    "option_thinking_budget": """Thinking预算 (budgetTokens/thinkingBudget) ⓘ

【作用】控制模型思考的token数量

【单位】tokens

【推荐值】
• Claude: 8000-32000
• Gemini: 4000-16000

【影响】
• 预算越高 → 思考越深入 → 回答越准确
• 预算越高 → 消耗tokens越多 → 成本越高

【使用建议】
• 简单问题: 4000-8000
• 复杂问题: 16000-32000
• 极难问题: 32000-64000""",
    # ==================== OpenCode Agent 相关 ====================
    "agent_name": """Agent 名称 (agent name) ⓘ

【作用】Agent的唯一标识符

【格式要求】
• 小写字母、数字、连字符
• 不能有空格

【内置Agent】
• build - 默认主Agent
• plan - 规划分析Agent

【自定义示例】
• code-reviewer
• docs-writer
• security-auditor""",
    "agent_model": """绑定模型 (model) ⓘ

【作用】指定Agent使用的模型

【格式】
provider/model-id

【示例】
• anthropic/claude-sonnet-4-5-20250929
• openai/gpt-5
• google/gemini-3-pro

【留空】
使用系统默认模型""",
    "agent_description": """Agent 描述 (description) ⓘ

【作用】描述Agent的功能和用途

【要求】
• 必填项
• 简洁明了地说明Agent的专长

【示例】
• 代码审查专家，专注于代码质量和安全分析
• 技术文档写作专家，擅长README和API文档
• 快速代码库探索，用于搜索和模式发现""",
    "opencode_agent_mode": """Agent 模式 (mode) ⓘ

【作用】定义Agent的调用方式

【可选值】
• primary - 主Agent，可通过Tab键切换
• subagent - 子Agent，通过@提及调用
• all - 两种模式都支持

【使用场景】
• primary: 常用的主力Agent
• subagent: 专门任务的辅助Agent
• all: 灵活使用的通用Agent""",
    "opencode_agent_temperature": """生成温度 (temperature) ⓘ

【作用】控制回复的随机性和创造性

【取值范围】0.0 - 2.0

【推荐设置】
• 0.0-0.2: 确定性高，适合代码/分析
• 0.3-0.5: 平衡创造性和准确性
• 0.6-1.0: 创造性高，适合创意任务
• 1.0-2.0: 高度随机，可能不稳定

【使用建议】
• 代码生成 → 0.1-0.3
• 文档写作 → 0.3-0.5
• 创意写作 → 0.7-1.0""",
    "opencode_agent_maxSteps": """最大步数 (maxSteps) ⓘ

【作用】限制Agent执行的工具调用次数

【工作原理】
Agent每调用一次工具算一步，
达到限制后强制返回文本响应

【推荐设置】
• 留空 = 无限制
• 10-20: 简单任务
• 50-100: 复杂任务

【使用场景】
防止Agent陷入无限循环""",
    "opencode_agent_prompt": """系统提示词 (prompt) ⓘ

【作用】定义Agent的行为和专长

【支持格式】
• 直接写入提示词文本
• 文件引用: {file:./prompts/agent.txt}

【编写建议】
• 明确Agent的角色和专长
• 说明工作方式和限制
• 给出输出格式要求""",
    "opencode_agent_tools": """工具配置 (tools) ⓘ

【作用】配置Agent可用的工具

【格式】JSON对象

【配置方式】
• true - 启用工具
• false - 禁用工具

【支持通配符】
• mcp_* - 匹配所有MCP工具

【示例】
{"write": true, "edit": true, "bash": false}""",
    "opencode_agent_permission": """权限配置 (permission) ⓘ

【作用】配置Agent的操作权限

【格式】JSON对象

【权限级别】
• allow - 允许，无需确认
• ask - 每次询问用户
• deny - 禁止使用

【示例】
{"edit": "ask", "bash": "deny"}""",
    "opencode_agent_hidden": """隐藏 (hidden) ⓘ

【作用】是否在@自动完成中隐藏此Agent

【仅对subagent有效】

【使用场景】
• 内部使用的辅助Agent
• 不希望用户直接调用的Agent

【注意】
隐藏的Agent仍可被其他Agent调用""",
    "opencode_agent_disable": """禁用 (disable) ⓘ

【作用】完全禁用此Agent

【使用场景】
• 临时停用某个Agent
• 保留配置但不加载

【与hidden的区别】
• hidden: 隐藏但可调用
• disable: 完全不加载""",
    # ==================== Oh My OpenCode Agent 相关 ====================
    "ohmyopencode_agent_name": """Agent 名称 ⓘ

【作用】Oh My OpenCode中Agent的唯一标识符

【预设Agent】
• oracle - 架构设计、代码审查专家
• librarian - 文档查找、实现示例专家
• explore - 代码库探索专家
• frontend-ui-ux-engineer - UI/UX专家
• document-writer - 技术文档专家""",
    "ohmyopencode_agent_model": """绑定模型 ⓘ

【作用】指定Agent使用的模型

【格式】provider/model-id

【示例】
• anthropic/claude-sonnet-4-5-20250929
• openai/gpt-5

【注意】
必须是已配置的Provider下的模型""",
    "ohmyopencode_agent_description": """Agent 描述 ⓘ

【作用】描述Agent的功能和适用场景

【建议】
• 说明Agent的专长领域
• 描述适合处理的任务类型""",
    "ohmyopencode_preset_agent": """预设 Agent ⓘ

【作用】快速选择预配置的Agent模板

【可选预设】
• oracle - 复杂决策和深度分析
• librarian - 查找外部资源和文档
• explore - 代码搜索和模式发现
• code-reviewer - 代码审查任务
• debugger - 调试和问题排查""",
    # ==================== Category 相关 ====================
    "category_name": """Category 名称 ⓘ

【作用】任务分类的唯一标识符

【预设分类】
• visual - 前端、UI/UX相关
• business-logic - 后端逻辑、架构
• documentation - 文档编写
• code-analysis - 代码审查、重构""",
    "category_model": """绑定模型 ⓘ

【作用】该分类使用的默认模型

【格式】provider/model-id

【使用场景】
不同类型的任务使用不同的模型""",
    "category_temperature": """Temperature (温度) ⓘ

【作用】控制该分类任务的回复随机性

【推荐设置】
• visual (前端): 0.7 - 需要创造性
• business-logic (后端): 0.1 - 需要准确性
• documentation (文档): 0.3 - 平衡
• code-analysis (分析): 0.2 - 需要准确性""",
    "category_description": """分类描述 ⓘ

【作用】说明该分类的用途和适用场景

【示例】
• 前端、UI/UX、设计相关任务
• 后端逻辑、架构设计、战略推理
• 文档编写、技术写作任务""",
    # ==================== Permission 相关 ====================
    "permission_tool": """工具名称 (tool name) ⓘ

【作用】指定要配置权限的工具

【内置工具】
• Bash - 执行命令行命令
• Read - 读取文件
• Write - 写入文件
• Edit - 编辑文件
• Glob - 文件搜索
• Grep - 内容搜索
• WebFetch - 网页抓取
• WebSearch - 网页搜索
• Task - 任务管理

【MCP工具格式】
mcp_servername_toolname""",
    "permission_level": """权限级别 (permission level) ⓘ

【作用】控制工具的使用权限

【可选值】
• allow (允许) - 直接使用，无需确认
• ask (询问) - 每次使用前询问用户
• deny (拒绝) - 禁止使用

【安全建议】
• 危险操作 → ask 或 deny
• 只读操作 → allow
• 网络操作 → ask""",
    "permission_bash_pattern": """Bash 命令模式 ⓘ

【作用】精细控制Bash命令的权限

【支持通配符】
• * - 匹配所有命令
• git * - 匹配所有git命令
• git push - 匹配特定命令

【示例配置】
git *: allow
rm *: ask
sudo *: deny""",
    # ==================== MCP 相关 ====================
    "mcp_name": """MCP 名称 (server name) ⓘ

【作用】MCP服务器的唯一标识符

【命名建议】
• 简洁明了
• 反映服务功能

【常见示例】
• context7 - Context7文档服务
• sentry - Sentry错误追踪
• gh_grep - GitHub代码搜索
• filesystem - 文件系统操作""",
    "mcp_type": """MCP 类型 (type) ⓘ

【作用】指定MCP服务器的运行方式

【可选值】
• local - 本地进程
  通过命令启动，运行在本机
  
• remote - 远程服务
  通过URL连接，运行在远程服务器

【选择建议】
• 自己开发的MCP → local
• 第三方托管服务 → remote""",
    "mcp_enabled": """启用状态 (enabled) ⓘ

【作用】是否启用此MCP服务器

【使用场景】
• 勾选 = 启动时加载
• 不勾选 = 保留配置但不加载

【提示】
禁用后可随时重新启用""",
    "mcp_command": """启动命令 (command) - Local类型 ⓘ

【作用】本地MCP的启动命令

【格式】JSON数组

【常见格式】
• npx方式: ["npx", "-y", "@mcp/server"]
• bun方式: ["bun", "x", "my-mcp"]
• node方式: ["node", "./mcp-server.js"]
• python方式: ["python", "-m", "mcp_server"]""",
    "mcp_url": """服务器 URL (url) - Remote类型 ⓘ

【作用】远程MCP服务器的访问地址

【格式】完整的HTTP/HTTPS URL

【示例】
• https://mcp.context7.com/mcp
• https://api.example.com/mcp/v1

【注意】
确保URL可访问且支持MCP协议""",
    "mcp_headers": """请求头 (headers) - Remote类型 ⓘ

【作用】远程MCP请求时附带的HTTP头

【格式】JSON对象

【常见用途】
• 身份认证
• API密钥传递

【示例】
{"Authorization": "Bearer your-api-key"}""",
    "mcp_environment": """环境变量 (environment) - Local类型 ⓘ

【作用】本地MCP启动时的环境变量

【格式】JSON对象

【常见用途】
• 传递API密钥
• 配置运行参数

【示例】
{"API_KEY": "your-api-key", "DEBUG": "true"}""",
    "mcp_timeout": """超时时间 (timeout) ⓘ

【作用】MCP工具获取的超时时间

【单位】毫秒 (ms)

【默认值】5000 (5秒)

【调整建议】
• 网络慢 → 增加超时
• 本地MCP → 可以减少""",
    "mcp_oauth": """OAuth 配置 (oauth) ⓘ

【作用】OAuth认证配置

【可选值】
• 留空 - 自动检测
• false - 禁用OAuth
• JSON对象 - 预注册凭证""",
    # ==================== Skill 相关 ====================
    "skill_name": """Skill 名称 (skill name) ⓘ

【作用】Skill的唯一标识符

【格式要求】
• 1-64字符
• 小写字母、数字、连字符
• 不能以连字符开头或结尾
• 不能有连续的连字符

【示例】
• git-release
• pr-review
• code-format""",
    "skill_permission": """Skill 权限 (permission) ⓘ

【作用】控制Skill的加载权限

【可选值】
• allow - 立即加载，无需确认
• deny - 隐藏并拒绝访问
• ask - 加载前询问用户

【安全建议】
• 信任的Skill → allow
• 未知来源 → ask
• 不需要的 → deny""",
    "skill_pattern": """权限模式 (pattern) ⓘ

【作用】使用通配符批量配置Skill权限

【支持通配符】
• * - 匹配所有Skill
• internal-* - 匹配internal-开头的Skill
• *-review - 匹配以-review结尾的Skill""",
    # ==================== Instructions/Rules 相关 ====================
    "instructions_path": """指令文件路径 (instructions) ⓘ

【作用】指定额外的指令文件

【支持格式】
• 相对路径: CONTRIBUTING.md
• 绝对路径: /path/to/rules.md
• Glob模式: docs/*.md
• 远程URL: https://example.com/rules.md

【使用场景】
• 复用现有文档作为指令
• 团队共享规则
• 项目特定指南""",
    "rules_agents_md": """AGENTS.md 文件 ⓘ

【作用】项目级AI指令文件

【文件位置】
• 项目级: 项目根目录/AGENTS.md
• 全局级: ~/.config/opencode/AGENTS.md

【内容建议】
• 项目结构说明
• 代码规范要求
• 特殊约定说明

【创建方式】
运行 /init 命令自动生成""",
    # ==================== Compaction 相关 ====================
    "compaction_auto": """自动压缩 (auto) ⓘ

【作用】当上下文接近满时自动压缩会话

【工作原理】
OpenCode会自动检测上下文使用情况，
在接近限制时压缩历史消息

【建议】
• 长对话 → 启用
• 短对话 → 可以禁用

【默认值】true (启用)""",
    "compaction_prune": """修剪旧输出 (prune) ⓘ

【作用】删除旧的工具输出以节省tokens

【工作原理】
保留工具调用记录，但删除详细输出内容

【好处】
• 节省tokens
• 保持对话连续性
• 减少成本

【默认值】true (启用)""",
}


def get_tooltip(key: str) -> str:
    """获取tooltip文本，如果不存在返回空字符串"""
    return TOOLTIPS.get(key, "")


# ==================== 预设常用模型（含完整配置） ====================
# 根据 OpenCode 官方文档 (https://opencode.ai/docs/models/)
# - options: 模型的默认配置参数，每次调用都会使用
# - variants: 可切换的变体配置，用户可通过 variant_cycle 快捷键切换
PRESET_MODEL_CONFIGS = {
    "Claude 系列": {
        "sdk": "@ai-sdk/anthropic",
        "models": {
            "claude-opus-4-5-20251101": {
                "name": "Claude Opus 4.5",
                "attachment": True,
                "limit": {"context": 200000, "output": 32000},
                "modalities": {"input": ["text", "image"], "output": ["text"]},
                "options": {"thinking": {"type": "enabled", "budgetTokens": 16000}},
                "variants": {},
                "description": "最强大的Claude模型，支持extended thinking模式\noptions.thinking.budgetTokens 控制思考预算",
            },
            "claude-sonnet-4-5-20250929": {
                "name": "Claude Sonnet 4.5",
                "attachment": True,
                "limit": {"context": 200000, "output": 16000},
                "modalities": {"input": ["text", "image"], "output": ["text"]},
                "options": {"thinking": {"type": "enabled", "budgetTokens": 8000}},
                "variants": {},
                "description": "平衡性能与成本的Claude模型，支持thinking模式",
            },
            "claude-sonnet-4-20250514": {
                "name": "Claude Sonnet 4",
                "attachment": True,
                "limit": {"context": 200000, "output": 8192},
                "modalities": {"input": ["text", "image"], "output": ["text"]},
                "options": {},
                "variants": {},
                "description": "Claude Sonnet 4基础版，不支持thinking",
            },
            "claude-haiku-4-5-20250514": {
                "name": "Claude Haiku 4.5",
                "attachment": True,
                "limit": {"context": 200000, "output": 8192},
                "modalities": {"input": ["text", "image"], "output": ["text"]},
                "options": {},
                "variants": {},
                "description": "快速响应的轻量级Claude模型",
            },
        },
    },
    "OpenAI/Codex 系列": {
        "sdk": "@ai-sdk/openai",
        "models": {
            "gpt-5": {
                "name": "GPT-5",
                "attachment": True,
                "limit": {"context": 256000, "output": 32768},
                "modalities": {"input": ["text", "image"], "output": ["text"]},
                "options": {
                    "reasoningEffort": "high",
                    "textVerbosity": "low",
                    "reasoningSummary": "auto",
                },
                "variants": {
                    "high": {
                        "reasoningEffort": "high",
                        "textVerbosity": "low",
                        "reasoningSummary": "auto",
                    },
                    "medium": {
                        "reasoningEffort": "medium",
                        "textVerbosity": "low",
                        "reasoningSummary": "auto",
                    },
                    "low": {
                        "reasoningEffort": "low",
                        "textVerbosity": "low",
                        "reasoningSummary": "auto",
                    },
                    "xhigh": {
                        "reasoningEffort": "xhigh",
                        "textVerbosity": "low",
                        "reasoningSummary": "auto",
                    },
                },
                "description": "OpenAI最新旗舰模型\noptions.reasoningEffort: high/medium/low/xhigh",
            },
            "gpt-5.1-codex": {
                "name": "GPT-5.1 Codex",
                "attachment": True,
                "limit": {"context": 256000, "output": 65536},
                "modalities": {"input": ["text", "image"], "output": ["text"]},
                "options": {"reasoningEffort": "high", "textVerbosity": "low"},
                "variants": {
                    "high": {"reasoningEffort": "high"},
                    "medium": {"reasoningEffort": "medium"},
                    "low": {"reasoningEffort": "low"},
                },
                "description": "OpenAI代码专用模型，针对编程任务优化",
            },
            "gpt-4o": {
                "name": "GPT-4o",
                "attachment": True,
                "limit": {"context": 128000, "output": 16384},
                "modalities": {"input": ["text", "image"], "output": ["text"]},
                "options": {},
                "variants": {},
                "description": "OpenAI多模态模型",
            },
            "o1-preview": {
                "name": "o1 Preview",
                "attachment": False,
                "limit": {"context": 128000, "output": 32768},
                "modalities": {"input": ["text"], "output": ["text"]},
                "options": {"reasoningEffort": "high"},
                "variants": {
                    "high": {"reasoningEffort": "high"},
                    "medium": {"reasoningEffort": "medium"},
                    "low": {"reasoningEffort": "low"},
                },
                "description": "OpenAI推理模型，支持reasoningEffort参数",
            },
            "o3-mini": {
                "name": "o3 Mini",
                "attachment": False,
                "limit": {"context": 200000, "output": 100000},
                "modalities": {"input": ["text"], "output": ["text"]},
                "options": {"reasoningEffort": "high"},
                "variants": {
                    "high": {"reasoningEffort": "high"},
                    "medium": {"reasoningEffort": "medium"},
                    "low": {"reasoningEffort": "low"},
                },
                "description": "OpenAI最新推理模型",
            },
        },
    },
    "Gemini 系列": {
        "sdk": "@ai-sdk/google",
        "models": {
            "gemini-3-pro": {
                "name": "Gemini 3 Pro",
                "attachment": True,
                "limit": {"context": 2097152, "output": 65536},
                "modalities": {"input": ["text", "image"], "output": ["text"]},
                "options": {"thinkingConfig": {"thinkingBudget": 8000}},
                "variants": {
                    "low": {"thinkingConfig": {"thinkingBudget": 4000}},
                    "high": {"thinkingConfig": {"thinkingBudget": 16000}},
                    "max": {"thinkingConfig": {"thinkingBudget": 32000}},
                },
                "description": "Google最新Pro模型，支持thinking模式",
            },
            "gemini-2.0-flash": {
                "name": "Gemini 2.0 Flash",
                "attachment": True,
                "limit": {"context": 1048576, "output": 8192},
                "modalities": {"input": ["text", "image"], "output": ["text"]},
                "options": {"thinkingConfig": {"thinkingBudget": 4000}},
                "variants": {
                    "low": {"thinkingConfig": {"thinkingBudget": 2000}},
                    "high": {"thinkingConfig": {"thinkingBudget": 8000}},
                },
                "description": "Google Flash模型，支持thinking模式",
            },
            "gemini-2.0-flash-thinking-exp": {
                "name": "Gemini 2.0 Flash Thinking",
                "attachment": True,
                "limit": {"context": 1048576, "output": 65536},
                "modalities": {"input": ["text", "image"], "output": ["text"]},
                "options": {"thinkingConfig": {"thinkingBudget": 10000}},
                "variants": {},
                "description": "Gemini专用thinking实验模型",
            },
            "gemini-1.5-pro": {
                "name": "Gemini 1.5 Pro",
                "attachment": True,
                "limit": {"context": 2097152, "output": 8192},
                "modalities": {
                    "input": ["text", "image", "audio", "video"],
                    "output": ["text"],
                },
                "options": {},
                "variants": {},
                "description": "超长上下文的Gemini Pro模型",
            },
        },
    },
    "其他模型": {
        "sdk": "@ai-sdk/openai-compatible",
        "models": {
            "minimax-m2.1": {
                "name": "Minimax M2.1",
                "attachment": False,
                "limit": {"context": 128000, "output": 16384},
                "modalities": {"input": ["text"], "output": ["text"]},
                "options": {},
                "variants": {},
                "description": "Minimax M2.1模型",
            },
            "deepseek-chat": {
                "name": "DeepSeek Chat",
                "attachment": False,
                "limit": {"context": 64000, "output": 8192},
                "modalities": {"input": ["text"], "output": ["text"]},
                "options": {},
                "variants": {},
                "description": "DeepSeek对话模型",
            },
            "deepseek-reasoner": {
                "name": "DeepSeek Reasoner",
                "attachment": False,
                "limit": {"context": 64000, "output": 8192},
                "modalities": {"input": ["text"], "output": ["text"]},
                "options": {},
                "variants": {},
                "description": "DeepSeek推理模型",
            },
            "qwen-max": {
                "name": "Qwen Max",
                "attachment": False,
                "limit": {"context": 32000, "output": 8192},
                "modalities": {"input": ["text"], "output": ["text"]},
                "options": {},
                "variants": {},
                "description": "阿里通义千问Max模型",
            },
        },
    },
}

# 简化的模型列表（用于下拉选择）
PRESET_MODELS = {
    category: list(data["models"].keys())
    for category, data in PRESET_MODEL_CONFIGS.items()
}

PRESET_SDKS = [
    "@ai-sdk/anthropic",
    "@ai-sdk/openai",
    "@ai-sdk/google",
    "@ai-sdk/azure",
    "@ai-sdk/openai-compatible",
]

# 模型配置包预设（用于批量添加时的可选模板）
MODEL_PRESET_PACKS = {
    "Claude 系列": {
        "默认": {
            "attachment": False,
            "modalities": {"input": ["text"], "output": ["text"]},
            "limit": {"context": 200000, "output": 16000},
            "options": {"thinking": {"type": "enabled", "budgetTokens": 16000}},
            "variants": {},
        },
        "高思考": {
            "attachment": False,
            "modalities": {"input": ["text"], "output": ["text"]},
            "limit": {"context": 200000, "output": 16000},
            "options": {"thinking": {"type": "enabled", "budgetTokens": 32000}},
            "variants": {},
        },
        "最大思考": {
            "attachment": False,
            "modalities": {"input": ["text"], "output": ["text"]},
            "limit": {"context": 200000, "output": 16000},
            "options": {"thinking": {"type": "enabled", "budgetTokens": 64000}},
            "variants": {},
        },
        "轻量": {
            "attachment": False,
            "modalities": {"input": ["text"], "output": ["text"]},
            "limit": {"context": 200000, "output": 16000},
            "options": {"thinking": {"type": "disabled"}},
            "variants": {},
        },
    },
    "OpenAI/Codex 系列": {
        "基础": {
            "attachment": False,
            "modalities": {"input": ["text"], "output": ["text"]},
            "limit": {"context": 200000, "output": 16000},
            "options": {},
            "variants": {},
        },
        "fast": {
            "attachment": False,
            "modalities": {"input": ["text"], "output": ["text"]},
            "limit": {"context": 200000, "output": 16000},
            "options": {"reasoningEffort": "low"},
            "variants": {},
        },
        "high": {
            "attachment": False,
            "modalities": {"input": ["text"], "output": ["text"]},
            "limit": {"context": 200000, "output": 16000},
            "options": {"reasoningEffort": "high"},
            "variants": {},
        },
        "xhigh": {
            "attachment": False,
            "modalities": {"input": ["text"], "output": ["text"]},
            "limit": {"context": 200000, "output": 16000},
            "options": {"reasoningEffort": "xhigh"},
            "variants": {},
        },
    },
    "Gemini 系列": {
        "默认": {
            "attachment": True,
            "modalities": {"input": ["text", "image"], "output": ["text"]},
            "limit": {"context": 1048576, "output": 8192},
            "options": {"thinkingConfig": {"thinkingBudget": 8000}},
            "variants": {},
        },
        "16k": {
            "attachment": True,
            "modalities": {"input": ["text", "image"], "output": ["text"]},
            "limit": {"context": 1048576, "output": 8192},
            "options": {"thinkingConfig": {"thinkingBudget": 16000}},
            "variants": {},
        },
        "高": {
            "attachment": True,
            "modalities": {"input": ["text", "image"], "output": ["text"]},
            "limit": {"context": 1048576, "output": 8192},
            "options": {"thinkingConfig": {"thinkingBudget": 32000}},
            "variants": {},
        },
    },
    "其他模型": {
        "基础": {
            "attachment": False,
            "modalities": {"input": ["text"], "output": ["text"]},
            "limit": {"context": 64000, "output": 8192},
            "options": {},
            "variants": {},
        }
    },
}

MODEL_PRESET_DEFAULT = {
    "Claude 系列": "默认",
    "OpenAI/Codex 系列": "基础",
    "Gemini 系列": "默认",
    "其他模型": "基础",
}

MODEL_PRESET_CUSTOM = {
    "Claude 系列": {},
    "OpenAI/Codex 系列": {},
    "Gemini 系列": {},
    "其他模型": {},
}

# SDK与模型厂商的对应关系（用于提示）
SDK_MODEL_COMPATIBILITY = {
    "@ai-sdk/anthropic": ["Claude 系列"],
    "@ai-sdk/openai": ["OpenAI/Codex 系列", "其他模型"],
    "@ai-sdk/google": ["Gemini 系列"],
    "@ai-sdk/azure": ["OpenAI/Codex 系列"],
    "@ai-sdk/openai-compatible": ["其他模型"],
}

# Oh My OpenCode Agent 预设
PRESET_AGENTS = {
    "oracle": "架构设计、代码审查、策略规划专家 - 用于复杂决策和深度分析",
    "librarian": "多仓库分析、文档查找、实现示例专家 - 用于查找外部资源和文档",
    "explore": "快速代码库探索和模式匹配专家 - 用于代码搜索和模式发现",
    "frontend-ui-ux-engineer": "UI/UX 设计和前端开发专家 - 用于前端视觉相关任务",
    "document-writer": "技术文档写作专家 - 用于生成README、API文档等",
    "multimodal-looker": "视觉内容分析专家 - 用于分析图片、PDF等媒体文件",
    "code-reviewer": "代码质量审查、安全分析专家 - 用于代码审查任务",
    "debugger": "问题诊断、Bug 修复专家 - 用于调试和问题排查",
}

# OpenCode 原生 Agent 预设
PRESET_OPENCODE_AGENTS = {
    "build": {
        "mode": "primary",
        "description": "默认主Agent，拥有所有工具权限，用于开发工作",
        "tools": {"write": True, "edit": True, "bash": True},
    },
    "plan": {
        "mode": "primary",
        "description": "规划分析Agent，限制写入权限，用于代码分析和规划",
        "permission": {"edit": "ask", "bash": "ask"},
    },
    "general": {
        "mode": "subagent",
        "description": "通用子Agent，用于研究复杂问题和执行多步骤任务",
    },
    "explore": {
        "mode": "subagent",
        "description": "快速探索Agent，用于代码库搜索和模式发现",
    },
    "code-reviewer": {
        "mode": "subagent",
        "description": "代码审查Agent，只读权限，专注于代码质量分析",
        "tools": {"write": False, "edit": False},
    },
    "docs-writer": {
        "mode": "subagent",
        "description": "文档编写Agent，专注于技术文档创作",
        "tools": {"bash": False},
    },
    "security-auditor": {
        "mode": "subagent",
        "description": "安全审计Agent，只读权限，专注于安全漏洞分析",
        "tools": {"write": False, "edit": False},
    },
}

# Category 预设
PRESET_CATEGORIES = {
    "visual": {"temperature": 0.7, "description": "前端、UI/UX、设计相关任务"},
    "business-logic": {
        "temperature": 0.1,
        "description": "后端逻辑、架构设计、战略推理",
    },
    "documentation": {"temperature": 0.3, "description": "文档编写、技术写作任务"},
    "code-analysis": {"temperature": 0.2, "description": "代码审查、重构分析任务"},
}

# 参数说明提示（用于Tooltip）- 根据 OpenCode 官方文档
TOOLTIPS = {
    # Provider相关
    "provider_name": "Provider 名称 - Provider的唯一标识符，用于在配置中引用\n格式：小写字母和连字符，如 anthropic, openai, my-proxy",
    "provider_display": "显示名称 - 在界面中显示的友好名称\n示例：Anthropic (Claude)、OpenAI 官方",
    "provider_sdk": "SDK 包名 - 指定使用哪个AI SDK来调用API\n• Claude系列 → @ai-sdk/anthropic\n• GPT/OpenAI系列 → @ai-sdk/openai\n• Gemini系列 → @ai-sdk/google",
    "provider_url": "API 地址 (baseURL) - API服务的访问地址\n• 官方API → 留空（自动使用默认地址）\n• 中转站 → 填写中转站地址",
    "provider_apikey": "API 密钥 - 用于身份验证的密钥\n支持环境变量: {env:ANTHROPIC_API_KEY}",
    "provider_timeout": "请求超时 - 单位：毫秒 (ms)\n默认：300000 (5分钟)",
    # Model相关
    "model_id": "模型 ID - 模型的唯一标识符，必须与API提供商一致\n示例：claude-sonnet-4-5-20250929, gpt-5",
    "model_name": "显示名称 - 在界面中显示的友好名称",
    "model_attachment": "支持附件 - 是否支持上传文件（图片、文档等）",
    "model_context": "上下文窗口 - 模型能处理的最大输入长度（tokens）",
    "model_output": "最大输出 - 模型单次回复的最大长度（tokens）",
    "model_options": "模型默认配置 (Options) - 每次调用模型时自动使用的参数\n• Claude thinking: thinking.type, thinking.budgetTokens\n• OpenAI: reasoningEffort, textVerbosity\n• Gemini: thinkingConfig.thinkingBudget",
    "model_variants": "模型变体 (Variants) - 可通过快捷键切换的预设配置组合\n用于同一模型的不同配置，如不同的thinking预算",
    # Agent相关 (Oh My OpenCode)
    "agent_name": "Agent 名称 - Agent的唯一标识符\n预设Agent：oracle, librarian, explore, code-reviewer",
    "agent_model": "绑定模型 - 格式：provider/model-id\n示例：anthropic/claude-sonnet-4-5-20250929",
    "agent_description": "Agent 描述 - 描述Agent的功能和适用场景",
    # Agent相关 (OpenCode原生)
    "opencode_agent_mode": "Agent 模式\n• primary - 主Agent，可通过Tab键切换\n• subagent - 子Agent，通过@提及调用\n• all - 两种模式都支持",
    "opencode_agent_temperature": "生成温度 - 取值范围：0.0 - 2.0\n• 0.0-0.2: 适合代码/分析\n• 0.3-0.5: 平衡创造性和准确性",
    "opencode_agent_maxSteps": "最大步数 - 限制Agent执行的工具调用次数\n留空 = 无限制",
    "opencode_agent_prompt": "系统提示词 - 定义Agent的行为和专长\n支持文件引用: {file:./prompts/agent.txt}",
    "opencode_agent_tools": "工具配置 - JSON对象格式\n• true - 启用工具\n• false - 禁用工具",
    "opencode_agent_permission": "权限配置\n• allow - 允许，无需确认\n• ask - 每次询问用户\n• deny - 禁止使用",
    "opencode_agent_hidden": "隐藏 - 是否在@自动完成中隐藏此Agent\n仅对subagent有效",
    # Category相关
    "category_name": "Category 名称\n预设分类：visual, business-logic, documentation, code-analysis",
    "category_model": "绑定模型 - 格式：provider/model-id",
    "category_temperature": "Temperature - 推荐设置：\n• visual (前端): 0.7\n• business-logic (后端): 0.1\n• documentation (文档): 0.3",
    "category_description": "分类描述 - 说明该分类的用途和适用场景",
    # Permission相关
    "permission_tool": "工具名称\n内置工具：Bash, Read, Write, Edit, Glob, Grep, WebFetch, WebSearch, Task\nMCP工具格式：mcp_servername_toolname",
    "permission_level": "权限级别\n• allow - 直接使用，无需确认\n• ask - 每次使用前询问用户\n• deny - 禁止使用",
    "permission_bash_pattern": "Bash 命令模式 - 支持通配符\n• * - 匹配所有命令\n• git * - 匹配所有git命令",
    # MCP相关
    "mcp_name": "MCP 名称 - MCP服务器的唯一标识符\n示例：context7, sentry, gh_grep",
    "mcp_type": "MCP 类型\n• local - 本地进程，通过命令启动\n• remote - 远程服务，通过URL连接",
    "mcp_enabled": "启用状态 - 是否启用此MCP服务器\n禁用后保留配置但不加载",
    "mcp_command": '启动命令 (Local类型) - JSON数组格式\n示例：["npx", "-y", "@mcp/server"]',
    "mcp_url": "服务器 URL (Remote类型) - 完整的HTTP/HTTPS URL",
    "mcp_headers": '请求头 (Remote类型) - JSON对象格式\n示例：{"Authorization": "Bearer your-api-key"}',
    "mcp_environment": '环境变量 (Local类型) - JSON对象格式\n示例：{"API_KEY": "xxx"}',
    "mcp_timeout": "超时时间 - 单位：毫秒 (ms)\n默认值：5000 (5秒)",
    # Skill相关
    "skill_name": "Skill 名称 - 1-64字符，小写字母、数字、连字符\n示例：git-release, pr-review",
    "skill_permission": "Skill 权限\n• allow - 立即加载，无需确认\n• deny - 隐藏并拒绝访问\n• ask - 加载前询问用户",
    "skill_pattern": "权限模式 - 支持通配符\n• * - 匹配所有Skill\n• internal-* - 匹配internal-开头的Skill",
    "skill_description": "Skill 描述 - 描述Skill的功能，帮助Agent选择",
    # Instructions/Rules相关
    "instructions_path": "指令文件路径 - 支持相对路径、绝对路径、Glob模式、远程URL",
    "rules_agents_md": "AGENTS.md 文件 - 项目级或全局级的规则文件\n内容建议：项目结构说明、代码规范要求",
    # Compaction相关
    "compaction_auto": "自动压缩 - 当上下文接近满时自动压缩会话\n默认值：true (启用)",
    "compaction_prune": "修剪旧输出 - 删除旧的工具输出以节省tokens\n默认值：true (启用)",
}


# ==================== 核心服务类 ====================
class ConfigPaths:
    """
    配置文件路径管理 - 跨平台支持 (Windows/Linux/macOS)

    默认路径：
    - Windows: C:/Users/<user>/.config/opencode/
    - Linux: /home/<user>/.config/opencode/
    - macOS: /Users/<user>/.config/opencode/

    支持 .json 和 .jsonc 扩展名，支持自定义路径
    """

    # 自定义路径存储（None 表示使用默认路径）
    _custom_opencode_path: Optional[Path] = None
    _custom_ohmyopencode_path: Optional[Path] = None
    _custom_backup_path: Optional[Path] = None
    _custom_import_paths: Optional[Dict[str, Path]] = None

    @staticmethod
    def get_user_home() -> Path:
        """获取用户主目录（跨平台）"""
        return Path.home()

    @staticmethod
    def get_platform() -> str:
        """获取当前平台: windows, linux, macos"""
        import platform

        system = platform.system().lower()
        if system == "darwin":
            return "macos"
        return system

    @classmethod
    def get_config_base_dir(cls) -> Path:
        """
        获取配置文件基础目录（跨平台）

        所有平台统一使用 ~/.config/opencode/
        """
        return cls.get_user_home() / ".config" / "opencode"

    @classmethod
    def _get_config_path(cls, base_dir: Path, base_name: str) -> Path:
        """获取配置文件路径，优先检测 .jsonc，其次 .json"""
        jsonc_path = base_dir / f"{base_name}.jsonc"
        json_path = base_dir / f"{base_name}.json"

        # 优先返回存在的 .jsonc 文件
        if jsonc_path.exists():
            return jsonc_path
        # 其次返回存在的 .json 文件
        if json_path.exists():
            return json_path
        # 都不存在时，默认返回 .json 路径（用于创建新文件）
        return json_path

    @classmethod
    def check_config_conflict(cls, base_name: str) -> Optional[Tuple[Path, Path]]:
        """
        检查是否同时存在 .json 和 .jsonc 配置文件

        Args:
            base_name: 配置文件基础名称（如 "opencode" 或 "oh-my-opencode"）

        Returns:
            如果存在冲突，返回 (json_path, jsonc_path)；否则返回 None
        """
        base_dir = cls.get_config_base_dir()
        jsonc_path = base_dir / f"{base_name}.jsonc"
        json_path = base_dir / f"{base_name}.json"

        if jsonc_path.exists() and json_path.exists():
            return (json_path, jsonc_path)
        return None

    @classmethod
    def get_config_file_info(cls, path: Path) -> Dict:
        """获取配置文件信息（大小、修改时间）"""
        import os
        from datetime import datetime

        if not path.exists():
            return {"exists": False}

        stat = os.stat(path)
        return {
            "exists": True,
            "size": stat.st_size,
            "size_str": f"{stat.st_size:,} 字节",
            "mtime": datetime.fromtimestamp(stat.st_mtime),
            "mtime_str": datetime.fromtimestamp(stat.st_mtime).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        }

    @classmethod
    def get_opencode_config(cls) -> Path:
        """获取 OpenCode 配置路径（优先使用自定义路径）"""
        if cls._custom_opencode_path is not None:
            return cls._custom_opencode_path
        return cls._get_config_path(cls.get_config_base_dir(), "opencode")

    @classmethod
    def set_opencode_config(cls, path: Optional[Path]) -> None:
        """设置自定义 OpenCode 配置路径"""
        cls._custom_opencode_path = path

    @classmethod
    def get_ohmyopencode_config(cls) -> Path:
        """获取 Oh My OpenCode 配置路径（优先使用自定义路径）"""
        if cls._custom_ohmyopencode_path is not None:
            return cls._custom_ohmyopencode_path
        return cls._get_config_path(cls.get_config_base_dir(), "oh-my-opencode")

    @classmethod
    def set_ohmyopencode_config(cls, path: Optional[Path]) -> None:
        """设置自定义 Oh My OpenCode 配置路径"""
        cls._custom_ohmyopencode_path = path

    @classmethod
    def is_custom_path(cls, config_type: str) -> bool:
        """检查是否使用自定义路径"""
        if config_type == "opencode":
            return cls._custom_opencode_path is not None
        elif config_type == "ohmyopencode":
            return cls._custom_ohmyopencode_path is not None
        elif config_type == "backup":
            return cls._custom_backup_path is not None
        return False

    @classmethod
    def reset_to_default(cls, config_type: str) -> None:
        """重置为默认路径"""
        if config_type == "opencode":
            cls._custom_opencode_path = None
        elif config_type == "ohmyopencode":
            cls._custom_ohmyopencode_path = None
        elif config_type == "backup":
            cls._custom_backup_path = None

    @classmethod
    def get_claude_settings(cls) -> Path:
        """获取 Claude Code 设置路径"""
        base_dir = cls.get_user_home() / ".claude"
        return cls._get_config_path(base_dir, "settings")

    @classmethod
    def get_claude_providers(cls) -> Path:
        """获取 Claude Code providers 路径"""
        base_dir = cls.get_user_home() / ".claude"
        return cls._get_config_path(base_dir, "providers")

    @classmethod
    def get_backup_dir(cls) -> Path:
        """获取备份目录（优先使用自定义路径）"""
        if cls._custom_backup_path is not None:
            return cls._custom_backup_path
        return cls.get_config_base_dir() / "backups"

    @classmethod
    def set_backup_dir(cls, path: Optional[Path]) -> None:
        """设置自定义备份目录"""
        cls._custom_backup_path = path

    @classmethod
    def get_import_path(cls, source_type: str) -> Optional[Path]:
        """获取自定义导入路径"""
        if cls._custom_import_paths is None:
            return None
        return cls._custom_import_paths.get(source_type)

    @classmethod
    def set_import_path(cls, source_type: str, path: Optional[Path]) -> None:
        """设置自定义导入路径"""
        if cls._custom_import_paths is None:
            cls._custom_import_paths = {}
        if path is None:
            cls._custom_import_paths.pop(source_type, None)
            return
        cls._custom_import_paths[source_type] = path


class ConfigManager:
    """配置文件读写管理 - 支持 JSON 和 JSONC (带注释的JSON)"""

    @staticmethod
    def strip_jsonc_comments(content: str) -> str:
        """移除 JSONC 中的注释，支持 // 单行注释和 /* */ 多行注释"""
        result = []
        i = 0
        in_string = False
        escape_next = False

        while i < len(content):
            char = content[i]

            # 处理字符串内的转义
            if escape_next:
                result.append(char)
                escape_next = False
                i += 1
                continue

            # 检测转义字符
            if char == "\\" and in_string:
                result.append(char)
                escape_next = True
                i += 1
                continue

            # 检测字符串边界
            if char == '"' and not escape_next:
                in_string = not in_string
                result.append(char)
                i += 1
                continue

            # 不在字符串内时处理注释
            if not in_string:
                # 检测单行注释 //
                if char == "/" and i + 1 < len(content) and content[i + 1] == "/":
                    # 跳过到行尾
                    while i < len(content) and content[i] != "\n":
                        i += 1
                    continue

                # 检测多行注释 /* */
                if char == "/" and i + 1 < len(content) and content[i + 1] == "*":
                    i += 2  # 跳过 /*
                    # 查找 */
                    while i < len(content):
                        if (
                            content[i] == "*"
                            and i + 1 < len(content)
                            and content[i + 1] == "/"
                        ):
                            i += 2  # 跳过 */
                            break
                        i += 1
                    continue

            result.append(char)
            i += 1

        return "".join(result)

    @staticmethod
    def load_json(path: Path) -> Optional[Dict]:
        """加载 JSON/JSONC 文件"""
        try:
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()

                # 尝试直接解析 JSON
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    # 如果失败，尝试移除注释后再解析 (JSONC)
                    stripped_content = ConfigManager.strip_jsonc_comments(content)
                    return json.loads(stripped_content)
        except Exception as e:
            print(f"Load failed {path}: {e}")
        return None

    @staticmethod
    def is_jsonc_file(path: Path) -> bool:
        """检查文件是否为 JSONC 格式（包含注释）"""
        try:
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                # 尝试直接解析，如果失败说明可能有注释
                try:
                    json.loads(content)
                    return False  # 标准 JSON
                except json.JSONDecodeError:
                    return True  # 可能是 JSONC
        except Exception:
            pass
        return False

    @staticmethod
    def has_jsonc_comments(path: Path) -> bool:
        """检查文件是否包含 JSONC 注释（// 或 /* */）"""
        try:
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                # 检查是否包含注释标记（简单检测）
                # 需要排除字符串内的 // 和 /*
                in_string = False
                escape_next = False
                i = 0
                while i < len(content):
                    char = content[i]
                    if escape_next:
                        escape_next = False
                        i += 1
                        continue
                    if char == "\\" and in_string:
                        escape_next = True
                        i += 1
                        continue
                    if char == '"' and not escape_next:
                        in_string = not in_string
                        i += 1
                        continue
                    if not in_string:
                        # 检测 // 或 /*
                        if char == "/" and i + 1 < len(content):
                            next_char = content[i + 1]
                            if next_char == "/" or next_char == "*":
                                return True
                    i += 1
        except Exception:
            pass
        return False

    @staticmethod
    def save_json(path: Path, data: Dict, backup_manager=None) -> Tuple[bool, bool]:
        """
        保存为标准 JSON 格式

        注意：如果原文件是 JSONC 格式（带注释），保存后注释会丢失。
        会自动检测并备份 JSONC 文件。

        Args:
            path: 保存路径
            data: 要保存的数据
            backup_manager: 备份管理器实例（用于自动备份 JSONC 文件）

        Returns:
            Tuple[bool, bool]: (保存是否成功, 是否为 JSONC 文件且注释已丢失)
        """
        jsonc_warning = False
        try:
            # 保存前自动备份当前文件
            if backup_manager and path.exists():
                backup_manager.backup(path, tag="before-save")

            # 检测是否为 JSONC 文件（包含注释）
            if path.exists() and ConfigManager.has_jsonc_comments(path):
                jsonc_warning = True
                # 自动备份 JSONC 文件
                if backup_manager:
                    backup_manager.backup(path, tag="jsonc-auto")

            # 如果是 oh-my-opencode 配置文件，自动添加 $schema 字段
            if "oh-my-opencode" in str(path):
                # 创建新的数据副本，避免修改原始数据
                data_to_save = data.copy()
                # 添加 $schema 字段到最前面
                schema_url = "https://raw.githubusercontent.com/code-yeongyu/oh-my-opencode/master/assets/oh-my-opencode.schema.json"
                # 使用 OrderedDict 确保 $schema 在最前面
                from collections import OrderedDict

                ordered_data = OrderedDict()
                ordered_data["$schema"] = schema_url
                # 添加其他字段
                for key, value in data_to_save.items():
                    if key != "$schema":  # 避免重复
                        ordered_data[key] = value
                data_to_save = ordered_data
            else:
                data_to_save = data

            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, indent=2, ensure_ascii=False)
            return True, jsonc_warning
        except Exception as e:
            print(f"Save failed {path}: {e}")
            return False, jsonc_warning


class BackupManager:
    """备份管理器"""

    def __init__(self):
        self.backup_dir = ConfigPaths.get_backup_dir()
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def backup(self, config_path: Path, tag: str = "auto") -> Optional[Path]:
        """创建配置文件备份，支持自定义标签"""
        try:
            if not config_path.exists():
                return None
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{config_path.stem}.{timestamp}.{tag}.bak"
            backup_path = self.backup_dir / backup_name
            shutil.copy2(config_path, backup_path)
            return backup_path
        except Exception as e:
            print(f"Backup failed: {e}")
            return None

    def backup_data(
        self, config_path: Path, data: Dict, tag: str = "memory"
    ) -> Optional[Path]:
        """备份当前内存态配置（不依赖磁盘内容）"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{config_path.stem}.{timestamp}.{tag}.bak"
            backup_path = self.backup_dir / backup_name
            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return backup_path
        except Exception as e:
            print(f"Backup data failed: {e}")
            return None

    @staticmethod
    def file_hash(path: Path) -> Optional[str]:
        """计算文件哈希，用于检测外部修改"""
        try:
            if not path.exists():
                return None
            with open(path, "rb") as f:
                data = f.read()
            return hashlib.md5(data).hexdigest()
        except Exception as e:
            print(f"Hash failed: {e}")
            return None

    def list_backups(self, config_name: Optional[str] = None) -> List[Dict]:
        """列出所有备份文件，按时间倒序"""
        try:
            backups = []
            for f in self.backup_dir.glob("*.bak"):
                parts = f.stem.split(".")
                if len(parts) >= 3:
                    name = parts[0]
                    timestamp = parts[1]
                    tag = parts[2] if len(parts) > 2 else "auto"
                    if config_name is None or name == config_name:
                        backups.append(
                            {
                                "path": f,
                                "name": name,
                                "timestamp": timestamp,
                                "tag": tag,
                                "display": f"{name} - {timestamp} ({tag})",
                            }
                        )
            backups.sort(key=lambda x: x["timestamp"], reverse=True)
            return backups
        except Exception as e:
            print(f"List backups failed: {e}")
            return []

    def restore(self, backup_path: Path, target_path: Path) -> bool:
        """从备份恢复配置"""
        try:
            if not backup_path.exists():
                return False
            self.backup(target_path, tag="before_restore")
            shutil.copy2(backup_path, target_path)
            return True
        except Exception as e:
            print(f"Restore failed: {e}")
            return False

    def delete_backup(self, backup_path: Path) -> bool:
        """删除指定备份"""
        try:
            if backup_path.exists():
                backup_path.unlink()
                return True
            return False
        except Exception as e:
            print(f"Delete backup failed: {e}")
            return False


# ==================== CLI 导出模块 ====================
class CLIConfigWriter:
    """CLI 配置写入器 - 原子写入配置文件"""

    @staticmethod
    def get_claude_dir() -> Path:
        """获取 Claude 配置目录 (~/.claude/)"""
        return Path.home() / ".claude"

    @staticmethod
    def get_codex_dir() -> Path:
        """获取 Codex 配置目录 (~/.codex/)"""
        return Path.home() / ".codex"

    @staticmethod
    def get_gemini_dir() -> Path:
        """获取 Gemini 配置目录 (~/.gemini/)"""
        return Path.home() / ".gemini"

    @staticmethod
    def get_cli_dir(cli_type: str) -> Path:
        """根据 CLI 类型获取配置目录"""
        if cli_type == "claude":
            return CLIConfigWriter.get_claude_dir()
        elif cli_type == "codex":
            return CLIConfigWriter.get_codex_dir()
        elif cli_type == "gemini":
            return CLIConfigWriter.get_gemini_dir()
        else:
            raise ValueError(f"Unknown CLI type: {cli_type}")

    def atomic_write_json(self, path: Path, data: Dict) -> None:
        """原子写入 JSON 文件

        1. 写入临时文件 (path.tmp.timestamp)
        2. 验证 JSON 格式
        3. 重命名替换原文件

        Raises:
            ConfigWriteError: 写入失败时抛出
        """
        # 确保父目录存在
        path.parent.mkdir(parents=True, exist_ok=True)

        # 生成临时文件路径
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        temp_path = path.parent / f"{path.name}.tmp.{timestamp}"

        try:
            # 写入临时文件
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # 验证写入的 JSON 格式
            with open(temp_path, "r", encoding="utf-8") as f:
                json.load(f)

            # 原子替换（Windows 需要先删除目标文件）
            if sys.platform == "win32" and path.exists():
                path.unlink()
            temp_path.rename(path)

        except json.JSONDecodeError as e:
            if temp_path.exists():
                temp_path.unlink()
            raise ConfigWriteError(path, f"JSON 格式验证失败: {e}")
        except Exception as e:
            if temp_path.exists():
                temp_path.unlink()
            raise ConfigWriteError(path, str(e))

    def atomic_write_text(self, path: Path, content: str) -> None:
        """原子写入文本文件 (用于 TOML/.env)

        Raises:
            ConfigWriteError: 写入失败时抛出
        """
        # 确保父目录存在
        path.parent.mkdir(parents=True, exist_ok=True)

        # 生成临时文件路径
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        temp_path = path.parent / f"{path.name}.tmp.{timestamp}"

        try:
            # 写入临时文件
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(content)

            # 原子替换
            if sys.platform == "win32" and path.exists():
                path.unlink()
            temp_path.rename(path)

        except Exception as e:
            if temp_path.exists():
                temp_path.unlink()
            raise ConfigWriteError(path, str(e))

    def set_file_permissions(self, path: Path, mode: int = 0o600) -> None:
        """设置文件权限 (Unix only)

        Args:
            path: 文件路径
            mode: 权限模式，默认 600 (仅所有者可读写)
        """
        if sys.platform != "win32" and path.exists():
            try:
                path.chmod(mode)
            except Exception as e:
                print(f"设置文件权限失败 ({path}): {e}")

    def write_claude_settings(self, config: Dict, merge: bool = True) -> None:
        """写入 Claude settings.json

        Args:
            config: 要写入的配置（包含 env 字段）
            merge: 是否与现有配置合并 (保留非 env 字段)
        """
        settings_path = self.get_claude_dir() / "settings.json"

        if merge and settings_path.exists():
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                # 合并配置：保留现有字段，更新 env
                existing["env"] = config.get("env", {})
                config = existing
            except (json.JSONDecodeError, Exception):
                # 现有文件无效，直接覆盖
                pass

        self.atomic_write_json(settings_path, config)

    def write_codex_auth(self, auth: Dict) -> None:
        """写入 Codex auth.json"""
        auth_path = self.get_codex_dir() / "auth.json"
        self.atomic_write_json(auth_path, auth)

    def write_codex_config(self, config_toml: str, merge: bool = True) -> None:
        """写入 Codex config.toml

        Args:
            config_toml: TOML 格式配置字符串
            merge: 是否保留现有的 MCP 配置等
        """
        config_path = self.get_codex_dir() / "config.toml"

        if merge and config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    existing_content = f.read()
                # 简单合并：保留 [mcp] 段
                mcp_section = self._extract_toml_section(existing_content, "mcp")
                if mcp_section:
                    config_toml = config_toml.rstrip() + "\n\n" + mcp_section
            except Exception:
                pass

        self.atomic_write_text(config_path, config_toml)

    def _extract_toml_section(self, content: str, section_name: str) -> Optional[str]:
        """从 TOML 内容中提取指定段落"""
        lines = content.split("\n")
        result = []
        in_section = False

        for line in lines:
            stripped = line.strip()
            if stripped.startswith(f"[{section_name}"):
                in_section = True
                result.append(line)
            elif in_section:
                if stripped.startswith("[") and not stripped.startswith(
                    f"[{section_name}"
                ):
                    break
                result.append(line)

        return "\n".join(result) if result else None

    def write_gemini_env(self, env_map: Dict[str, str]) -> None:
        """写入 Gemini .env 文件

        格式: KEY=VALUE (每行一个)
        """
        env_path = self.get_gemini_dir() / ".env"

        # 生成 .env 内容
        lines = [f"{key}={value}" for key, value in env_map.items()]
        content = "\n".join(lines) + "\n"

        self.atomic_write_text(env_path, content)

        # 设置文件权限 (Unix: 600)
        self.set_file_permissions(env_path, 0o600)

    def write_gemini_settings(self, security_config: Dict, merge: bool = True) -> None:
        """写入 Gemini settings.json

        Args:
            security_config: security.auth.selectedType 配置
            merge: 是否保留现有的 mcpServers 等字段
        """
        settings_path = self.get_gemini_dir() / "settings.json"

        config = {"security": security_config.get("security", security_config)}

        if merge and settings_path.exists():
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                # 合并配置：保留 mcpServers 等字段
                for key, value in existing.items():
                    if key != "security":
                        config[key] = value
                # 深度合并 security 字段
                if "security" in existing:
                    existing_security = existing["security"]
                    new_security = config.get("security", {})
                    for key, value in existing_security.items():
                        if key not in new_security:
                            new_security[key] = value
                    config["security"] = new_security
            except (json.JSONDecodeError, Exception):
                pass

        self.atomic_write_json(settings_path, config)


class CLIBackupManager:
    """CLI 配置备份管理器"""

    BACKUP_DIR = Path.home() / ".opencode-backup"
    MAX_BACKUPS = 5

    def __init__(self):
        self.backup_dir = self.BACKUP_DIR
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, cli_type: str) -> Optional[Path]:
        """创建指定 CLI 工具的配置备份

        Args:
            cli_type: "claude" | "codex" | "gemini"

        Returns:
            备份目录路径，如 ~/.opencode-backup/claude_20250119_143052/

        Raises:
            BackupError: 备份失败时抛出
        """
        try:
            cli_dir = CLIConfigWriter.get_cli_dir(cli_type)
            if not cli_dir.exists():
                return None

            # 创建备份目录
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"{cli_type}_{timestamp}"
            backup_path.mkdir(parents=True, exist_ok=True)

            # 复制所有配置文件
            files_backed_up = []
            for item in cli_dir.iterdir():
                if item.is_file():
                    dest = backup_path / item.name
                    shutil.copy2(item, dest)
                    files_backed_up.append(item.name)

            if not files_backed_up:
                # 没有文件需要备份，删除空目录
                backup_path.rmdir()
                return None

            # 清理旧备份
            self.cleanup_old_backups(cli_type)

            return backup_path

        except Exception as e:
            raise BackupError(cli_type, str(e))

    def restore_backup(self, backup_path: Path, cli_type: str) -> bool:
        """从备份恢复配置

        Args:
            backup_path: 备份目录路径
            cli_type: CLI 类型

        Returns:
            是否恢复成功

        Raises:
            RestoreError: 恢复失败时抛出
        """
        try:
            if not backup_path.exists():
                raise RestoreError(backup_path, "备份目录不存在")

            cli_dir = CLIConfigWriter.get_cli_dir(cli_type)
            cli_dir.mkdir(parents=True, exist_ok=True)

            # 先备份当前配置
            self.create_backup(cli_type)

            # 恢复备份文件
            for item in backup_path.iterdir():
                if item.is_file():
                    dest = cli_dir / item.name
                    shutil.copy2(item, dest)

            return True

        except RestoreError:
            raise
        except Exception as e:
            raise RestoreError(backup_path, str(e))

    def list_backups(self, cli_type: str) -> List[BackupInfo]:
        """列出指定 CLI 工具的所有备份

        Args:
            cli_type: CLI 类型

        Returns:
            备份信息列表，按时间倒序
        """
        backups = []
        prefix = f"{cli_type}_"

        try:
            for item in self.backup_dir.iterdir():
                if item.is_dir() and item.name.startswith(prefix):
                    # 解析时间戳
                    timestamp_str = item.name[len(prefix) :]
                    try:
                        created_at = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    except ValueError:
                        continue

                    # 获取备份文件列表
                    files = [f.name for f in item.iterdir() if f.is_file()]

                    backups.append(
                        BackupInfo(
                            path=item,
                            cli_type=cli_type,
                            created_at=created_at,
                            files=files,
                        )
                    )

            # 按时间倒序排序
            backups.sort(key=lambda x: x.created_at, reverse=True)

        except Exception as e:
            print(f"列出备份失败: {e}")

        return backups

    def cleanup_old_backups(self, cli_type: str) -> None:
        """清理旧备份，保留最近 MAX_BACKUPS 个

        Args:
            cli_type: CLI 类型
        """
        backups = self.list_backups(cli_type)

        # 删除超出限制的旧备份
        for backup in backups[self.MAX_BACKUPS :]:
            try:
                shutil.rmtree(backup.path)
            except Exception as e:
                print(f"删除旧备份失败 ({backup.path}): {e}")


class CLIConfigGenerator:
    """CLI 配置生成器 - 将 OpenCode 配置转换为各 CLI 工具格式"""

    def generate_claude_config(self, provider: Dict, model: str = None) -> Dict:
        """生成 Claude Code settings.json 配置

        Args:
            provider: OpenCode Provider 配置，包含 baseURL 和 apiKey
            model: 默认模型 ID，如果为 None 或空字符串则不包含 ANTHROPIC_MODEL

        Returns:
            Claude settings.json 配置字典
        """
        base_url = provider.get("baseURL", "") or provider.get("options", {}).get(
            "baseURL", ""
        )
        api_key = provider.get("apiKey", "") or provider.get("options", {}).get(
            "apiKey", ""
        )

        env = {
            "ANTHROPIC_BASE_URL": base_url,
            "ANTHROPIC_AUTH_TOKEN": api_key,
        }

        # 仅当 model 有值时才添加
        if model:
            env["ANTHROPIC_MODEL"] = model

        # 添加模型映射（如果有）
        model_mappings = provider.get("modelMappings", {})
        if model_mappings.get("haiku"):
            env["ANTHROPIC_DEFAULT_HAIKU_MODEL"] = model_mappings["haiku"]
        if model_mappings.get("sonnet"):
            env["ANTHROPIC_DEFAULT_SONNET_MODEL"] = model_mappings["sonnet"]
        if model_mappings.get("opus"):
            env["ANTHROPIC_DEFAULT_OPUS_MODEL"] = model_mappings["opus"]

        return {"env": env}

    def generate_codex_auth(self, provider: Dict) -> Dict:
        """生成 Codex auth.json 配置

        Args:
            provider: OpenCode Provider 配置

        Returns:
            Codex auth.json 配置字典
        """
        api_key = provider.get("apiKey", "") or provider.get("options", {}).get(
            "apiKey", ""
        )
        return {"OPENAI_API_KEY": api_key}

    def generate_codex_config(self, provider: Dict, model: str) -> str:
        """生成 Codex config.toml 配置

        Args:
            provider: OpenCode Provider 配置
            model: 默认模型 ID

        Returns:
            TOML 格式配置字符串
        """
        base_url = provider.get("baseURL", "") or provider.get("options", {}).get(
            "baseURL", ""
        )

        # 确保 base_url 以 /v1 结尾
        if base_url and not base_url.rstrip("/").endswith("/v1"):
            base_url = base_url.rstrip("/") + "/v1"

        provider_name = provider.get("name", "newapi")

        lines = [
            f'model_provider = "{provider_name}"',
            f'model = "{model}"',
            'model_reasoning_effort = "high"',
            "disable_response_storage = true",
            "",
            f"[model_providers.{provider_name}]",
            f'name = "{provider_name}"',
            f'base_url = "{base_url}"',
            'wire_api = "responses"',
            "requires_openai_auth = true",
        ]

        return "\n".join(lines) + "\n"

    def generate_gemini_env(self, provider: Dict, model: str) -> Dict[str, str]:
        """生成 Gemini .env 配置

        Args:
            provider: OpenCode Provider 配置
            model: 默认模型 ID

        Returns:
            环境变量字典
        """
        base_url = provider.get("baseURL", "") or provider.get("options", {}).get(
            "baseURL", ""
        )
        api_key = provider.get("apiKey", "") or provider.get("options", {}).get(
            "apiKey", ""
        )

        return {
            "GOOGLE_GEMINI_BASE_URL": base_url,
            "GEMINI_API_KEY": api_key,
            "GEMINI_MODEL": model,
        }

    def generate_gemini_settings(self, auth_type: str = "gemini-api-key") -> Dict:
        """生成 Gemini settings.json 中的 security 配置

        Args:
            auth_type: 认证类型，默认 "gemini-api-key"

        Returns:
            security 配置字典
        """
        return {"security": {"auth": {"selectedType": auth_type}}}


class CLIExportManager:
    """CLI 工具导出管理器"""

    def __init__(self):
        self.config_generator = CLIConfigGenerator()
        self.config_writer = CLIConfigWriter()
        self.backup_manager = CLIBackupManager()

    def detect_cli_tools(self) -> Dict[str, CLIToolStatus]:
        """检测已安装的 CLI 工具

        Returns:
            {cli_type: CLIToolStatus} 字典
        """
        result = {}

        for cli_type in ["claude", "codex", "gemini"]:
            cli_dir = CLIConfigWriter.get_cli_dir(cli_type)
            installed = cli_dir.exists()

            # 检查是否有配置文件
            has_config = False
            if installed:
                if cli_type == "claude":
                    has_config = (cli_dir / "settings.json").exists()
                elif cli_type == "codex":
                    has_config = (cli_dir / "config.toml").exists() or (
                        cli_dir / "auth.json"
                    ).exists()
                elif cli_type == "gemini":
                    has_config = (cli_dir / "settings.json").exists() or (
                        cli_dir / ".env"
                    ).exists()

            result[cli_type] = CLIToolStatus(
                cli_type=cli_type,
                installed=installed,
                config_dir=cli_dir if installed else None,
                has_config=has_config,
                version=None,  # 版本检测暂不实现
            )

        return result

    def validate_provider(self, provider: Dict) -> ValidationResult:
        """验证 Provider 配置完整性

        Args:
            provider: OpenCode Provider 配置

        Returns:
            ValidationResult
        """
        errors = []
        warnings = []

        # 检查 baseURL
        base_url = provider.get("baseURL", "") or provider.get("options", {}).get(
            "baseURL", ""
        )
        if not base_url or not base_url.strip():
            errors.append("缺少 API 地址 (baseURL)")

        # 检查 apiKey
        api_key = provider.get("apiKey", "") or provider.get("options", {}).get(
            "apiKey", ""
        )
        if not api_key or not api_key.strip():
            errors.append("缺少 API 密钥 (apiKey)")

        # 检查 Model 配置
        models = provider.get("models", {})
        if not models:
            warnings.append("未配置任何模型")

        if errors:
            return ValidationResult.failure(errors, warnings)
        return ValidationResult(valid=True, errors=[], warnings=warnings)

    def export_to_claude(self, provider: Dict, model: str) -> ExportResult:
        """导出到 Claude Code

        Args:
            provider: OpenCode Provider 配置
            model: 默认模型 ID

        Returns:
            ExportResult
        """
        cli_type = "claude"
        backup_path = None

        try:
            # 验证 Provider
            validation = self.validate_provider(provider)
            if not validation.valid:
                return ExportResult.fail(cli_type, "; ".join(validation.errors))

            # 创建备份
            backup_path = self.backup_manager.create_backup(cli_type)

            # 生成配置
            config = self.config_generator.generate_claude_config(provider, model)

            # 写入配置
            self.config_writer.write_claude_settings(config)

            settings_path = CLIConfigWriter.get_claude_dir() / "settings.json"
            return ExportResult.ok(cli_type, [settings_path], backup_path)

        except CLIExportError as e:
            return ExportResult.fail(cli_type, str(e), backup_path)
        except Exception as e:
            return ExportResult.fail(cli_type, f"导出失败: {e}", backup_path)

    def export_to_codex(self, provider: Dict, model: str) -> ExportResult:
        """导出到 Codex CLI

        Args:
            provider: OpenCode Provider 配置
            model: 默认模型 ID

        Returns:
            ExportResult
        """
        cli_type = "codex"
        backup_path = None

        try:
            # 验证 Provider
            validation = self.validate_provider(provider)
            if not validation.valid:
                return ExportResult.fail(cli_type, "; ".join(validation.errors))

            # 创建备份
            backup_path = self.backup_manager.create_backup(cli_type)

            # 生成配置
            auth = self.config_generator.generate_codex_auth(provider)
            config_toml = self.config_generator.generate_codex_config(provider, model)

            # 写入配置
            self.config_writer.write_codex_auth(auth)
            self.config_writer.write_codex_config(config_toml)

            codex_dir = CLIConfigWriter.get_codex_dir()
            return ExportResult.ok(
                cli_type,
                [codex_dir / "auth.json", codex_dir / "config.toml"],
                backup_path,
            )

        except CLIExportError as e:
            return ExportResult.fail(cli_type, str(e), backup_path)
        except Exception as e:
            return ExportResult.fail(cli_type, f"导出失败: {e}", backup_path)

    def export_to_gemini(self, provider: Dict, model: str) -> ExportResult:
        """导出到 Gemini CLI

        Args:
            provider: OpenCode Provider 配置
            model: 默认模型 ID

        Returns:
            ExportResult
        """
        cli_type = "gemini"
        backup_path = None

        try:
            # 验证 Provider
            validation = self.validate_provider(provider)
            if not validation.valid:
                return ExportResult.fail(cli_type, "; ".join(validation.errors))

            # 创建备份
            backup_path = self.backup_manager.create_backup(cli_type)

            # 生成配置
            env_map = self.config_generator.generate_gemini_env(provider, model)
            settings = self.config_generator.generate_gemini_settings()

            # 写入配置
            self.config_writer.write_gemini_env(env_map)
            self.config_writer.write_gemini_settings(settings)

            gemini_dir = CLIConfigWriter.get_gemini_dir()
            return ExportResult.ok(
                cli_type,
                [gemini_dir / ".env", gemini_dir / "settings.json"],
                backup_path,
            )

        except CLIExportError as e:
            return ExportResult.fail(cli_type, str(e), backup_path)
        except Exception as e:
            return ExportResult.fail(cli_type, f"导出失败: {e}", backup_path)

    def batch_export(
        self, provider: Dict, models: Dict[str, str], targets: List[str]
    ) -> BatchExportResult:
        """批量导出到多个 CLI 工具

        Args:
            provider: OpenCode Provider 配置
            models: {cli_type: model_id} 字典
            targets: 要导出的 CLI 类型列表

        Returns:
            BatchExportResult
        """
        results = []

        for cli_type in targets:
            model = models.get(cli_type, "")

            try:
                if cli_type == "claude":
                    result = self.export_to_claude(provider, model)
                elif cli_type == "codex":
                    result = self.export_to_codex(provider, model)
                elif cli_type == "gemini":
                    result = self.export_to_gemini(provider, model)
                else:
                    result = ExportResult.fail(cli_type, f"未知的 CLI 类型: {cli_type}")
            except Exception as e:
                result = ExportResult.fail(cli_type, f"导出异常: {e}")

            results.append(result)

        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful

        return BatchExportResult(
            total=len(results), successful=successful, failed=failed, results=results
        )

    def validate_exported_config(self, cli_type: str) -> ValidationResult:
        """验证导出后的配置

        Args:
            cli_type: CLI 类型

        Returns:
            ValidationResult
        """
        errors = []
        warnings = []

        cli_dir = CLIConfigWriter.get_cli_dir(cli_type)

        if cli_type == "claude":
            settings_path = cli_dir / "settings.json"
            if not settings_path.exists():
                errors.append("settings.json 文件不存在")
            else:
                try:
                    with open(settings_path, "r", encoding="utf-8") as f:
                        config = json.load(f)
                    if "env" not in config:
                        errors.append("settings.json 缺少 env 字段")
                    else:
                        env = config["env"]
                        if "ANTHROPIC_BASE_URL" not in env:
                            errors.append("缺少 ANTHROPIC_BASE_URL")
                        if "ANTHROPIC_AUTH_TOKEN" not in env:
                            errors.append("缺少 ANTHROPIC_AUTH_TOKEN")
                except json.JSONDecodeError as e:
                    errors.append(f"settings.json 格式错误: {e}")
                except Exception as e:
                    errors.append(f"读取 settings.json 失败: {e}")

        elif cli_type == "codex":
            auth_path = cli_dir / "auth.json"
            config_path = cli_dir / "config.toml"

            if not auth_path.exists():
                errors.append("auth.json 文件不存在")
            else:
                try:
                    with open(auth_path, "r", encoding="utf-8") as f:
                        auth = json.load(f)
                    if "OPENAI_API_KEY" not in auth:
                        errors.append("auth.json 缺少 OPENAI_API_KEY")
                except json.JSONDecodeError as e:
                    errors.append(f"auth.json 格式错误: {e}")
                except Exception as e:
                    errors.append(f"读取 auth.json 失败: {e}")

            if not config_path.exists():
                errors.append("config.toml 文件不存在")
            else:
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    if "model_provider" not in content:
                        errors.append("config.toml 缺少 model_provider")
                    if "model =" not in content:
                        errors.append("config.toml 缺少 model")
                except Exception as e:
                    errors.append(f"读取 config.toml 失败: {e}")

        elif cli_type == "gemini":
            env_path = cli_dir / ".env"
            settings_path = cli_dir / "settings.json"

            if not env_path.exists():
                errors.append(".env 文件不存在")
            else:
                try:
                    with open(env_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    if "GEMINI_API_KEY" not in content:
                        errors.append(".env 缺少 GEMINI_API_KEY")
                    if "GOOGLE_GEMINI_BASE_URL" not in content:
                        errors.append(".env 缺少 GOOGLE_GEMINI_BASE_URL")
                except Exception as e:
                    errors.append(f"读取 .env 失败: {e}")

            if not settings_path.exists():
                warnings.append("settings.json 文件不存在")
            else:
                try:
                    with open(settings_path, "r", encoding="utf-8") as f:
                        config = json.load(f)
                    if "security" not in config:
                        warnings.append("settings.json 缺少 security 字段")
                except json.JSONDecodeError as e:
                    errors.append(f"settings.json 格式错误: {e}")
                except Exception as e:
                    errors.append(f"读取 settings.json 失败: {e}")

        if errors:
            return ValidationResult.failure(errors, warnings)
        return ValidationResult(valid=True, errors=[], warnings=warnings)


class ConfigValidator:
    """配置文件验证器 - 检查 OpenCode 配置格式是否正确"""

    @staticmethod
    def _is_blank(value: Any) -> bool:
        if value is None:
            return True
        if isinstance(value, str):
            return value.strip() == ""
        return False

    # Provider 必需字段
    PROVIDER_REQUIRED_FIELDS = ["npm", "options"]
    # Provider options 必需字段
    PROVIDER_OPTIONS_REQUIRED = ["baseURL", "apiKey"]
    # Model 推荐字段
    MODEL_RECOMMENDED_FIELDS = ["name", "limit"]
    # Oh My OpenCode 必需字段
    OHMY_AGENT_REQUIRED_FIELDS = ["model"]
    OHMY_CATEGORY_REQUIRED_FIELDS = ["model"]
    # 有效的 npm 包
    VALID_NPM_PACKAGES = [
        "@ai-sdk/anthropic",
        "@ai-sdk/openai",
        "@ai-sdk/google",
        "@ai-sdk/azure",
        "@ai-sdk/amazon-bedrock",
        "@ai-sdk/google-vertex",
        "@ai-sdk/mistral",
        "@ai-sdk/xai",
        "@ai-sdk/togetherai",
        "@ai-sdk/cohere",
        "@ai-sdk/deepseek",
    ]

    @staticmethod
    def validate_opencode_config(config: Dict) -> List[Dict]:
        """
        验证 OpenCode 配置文件
        返回问题列表: [{"level": "error/warning", "path": "provider.xxx", "message": "..."}]
        """
        issues = []
        if not config:
            issues.append(
                {"level": "error", "path": "root", "message": "配置文件为空或无法解析"}
            )
            return issues
        if not isinstance(config, dict):
            issues.append(
                {"level": "error", "path": "root", "message": "配置根必须是对象类型"}
            )
            return issues

        # 验证 $schema
        schema = config.get("$schema")
        if schema != "https://opencode.ai/config.json":
            issues.append(
                {
                    "level": "warning",
                    "path": "$schema",
                    "message": "建议设置 $schema 为 https://opencode.ai/config.json",
                }
            )

        # 验证 provider 部分
        providers = config.get("provider", {})
        if not providers:
            issues.append(
                {
                    "level": "warning",
                    "path": "provider",
                    "message": "未配置任何 Provider",
                }
            )
        if not isinstance(providers, dict):
            issues.append(
                {
                    "level": "error",
                    "path": "provider",
                    "message": "provider 必须是对象类型",
                }
            )
            return issues

        for provider_name, provider_data in providers.items():
            provider_path = f"provider.{provider_name}"

            # 检查 provider 值是否为字典
            if not isinstance(provider_data, dict):
                issues.append(
                    {
                        "level": "error",
                        "path": provider_path,
                        "message": f"Provider '{provider_name}' 的值必须是对象，当前是 {type(provider_data).__name__}",
                    }
                )
                continue

            # 检查必需字段
            for field in ConfigValidator.PROVIDER_REQUIRED_FIELDS:
                if field not in provider_data:
                    issues.append(
                        {
                            "level": "error",
                            "path": f"{provider_path}.{field}",
                            "message": f"Provider '{provider_name}' 缺少必需字段 '{field}'",
                        }
                    )
                elif ConfigValidator._is_blank(provider_data.get(field)):
                    issues.append(
                        {
                            "level": "error",
                            "path": f"{provider_path}.{field}",
                            "message": f"Provider '{provider_name}' 的 '{field}' 为空",
                        }
                    )

            # 检查 npm 包是否有效
            npm = provider_data.get("npm", "")
            if npm and npm not in ConfigValidator.VALID_NPM_PACKAGES:
                issues.append(
                    {
                        "level": "warning",
                        "path": f"{provider_path}.npm",
                        "message": f"Provider '{provider_name}' 的 npm 包 '{npm}' 不在已知列表中",
                    }
                )

            # 检查 options
            options = provider_data.get("options", {})
            if not isinstance(options, dict):
                issues.append(
                    {
                        "level": "error",
                        "path": f"{provider_path}.options",
                        "message": f"Provider '{provider_name}' 的 options 必须是对象",
                    }
                )
            else:
                for opt_field in ConfigValidator.PROVIDER_OPTIONS_REQUIRED:
                    if opt_field not in options:
                        issues.append(
                            {
                                "level": "warning",
                                "path": f"{provider_path}.options.{opt_field}",
                                "message": f"Provider '{provider_name}' 的 options 缺少 '{opt_field}'",
                            }
                        )
                    elif ConfigValidator._is_blank(options.get(opt_field)):
                        issues.append(
                            {
                                "level": "warning",
                                "path": f"{provider_path}.options.{opt_field}",
                                "message": f"Provider '{provider_name}' 的 options.{opt_field} 为空",
                            }
                        )

            # 检查 models
            models = provider_data.get("models", {})
            if not isinstance(models, dict):
                issues.append(
                    {
                        "level": "error",
                        "path": f"{provider_path}.models",
                        "message": f"Provider '{provider_name}' 的 models 必须是对象",
                    }
                )
            else:
                if not models:
                    issues.append(
                        {
                            "level": "warning",
                            "path": f"{provider_path}.models",
                            "message": f"Provider '{provider_name}' 没有配置任何模型",
                        }
                    )
                for model_id, model_data in models.items():
                    model_path = f"{provider_path}.models.{model_id}"
                    if ConfigValidator._is_blank(model_id):
                        issues.append(
                            {
                                "level": "error",
                                "path": model_path,
                                "message": f"Provider '{provider_name}' 存在空模型ID",
                            }
                        )
                        continue
                    if not isinstance(model_data, dict):
                        issues.append(
                            {
                                "level": "error",
                                "path": model_path,
                                "message": f"Model '{model_id}' 的值必须是对象",
                            }
                        )
                        continue

                    # 检查 limit 字段
                    limit = model_data.get("limit", {})
                    if not isinstance(limit, dict):
                        issues.append(
                            {
                                "level": "warning",
                                "path": f"{model_path}.limit",
                                "message": f"Model '{model_id}' 的 limit 应该是对象",
                            }
                        )
                    elif limit:
                        context = limit.get("context")
                        output = limit.get("output")
                        if context is not None and not isinstance(context, int):
                            issues.append(
                                {
                                    "level": "warning",
                                    "path": f"{model_path}.limit.context",
                                    "message": f"Model '{model_id}' 的 context 应该是整数",
                                }
                            )
                        if output is not None and not isinstance(output, int):
                            issues.append(
                                {
                                    "level": "warning",
                                    "path": f"{model_path}.limit.output",
                                    "message": f"Model '{model_id}' 的 output 应该是整数",
                                }
                            )

        # 验证 mcp 部分
        mcp = config.get("mcp", {})
        if mcp and not isinstance(mcp, dict):
            issues.append(
                {"level": "error", "path": "mcp", "message": "mcp 必须是对象类型"}
            )
        elif isinstance(mcp, dict):
            for mcp_name, mcp_data in mcp.items():
                mcp_path = f"mcp.{mcp_name}"
                if not isinstance(mcp_data, dict):
                    issues.append(
                        {
                            "level": "error",
                            "path": mcp_path,
                            "message": f"MCP '{mcp_name}' 的值必须是对象",
                        }
                    )
                    continue

                mcp_type = mcp_data.get("type")
                if mcp_type == "local" and "command" not in mcp_data:
                    issues.append(
                        {
                            "level": "warning",
                            "path": f"{mcp_path}.command",
                            "message": f"Local MCP '{mcp_name}' 缺少 command 字段",
                        }
                    )
                elif mcp_type == "remote" and "url" not in mcp_data:
                    issues.append(
                        {
                            "level": "warning",
                            "path": f"{mcp_path}.url",
                            "message": f"Remote MCP '{mcp_name}' 缺少 url 字段",
                        }
                    )

        # 验证 agent 部分
        agent = config.get("agent", {})
        if agent and not isinstance(agent, dict):
            issues.append(
                {"level": "error", "path": "agent", "message": "agent 必须是对象类型"}
            )

        return issues

    @staticmethod
    def validate_ohmyopencode_config(config: Dict) -> List[Dict]:
        """
        验证 Oh My OpenCode 配置文件
        返回问题列表: [{"level": "error/warning", "path": "agents.xxx", "message": "..."}]
        """
        issues = []
        if not config:
            issues.append(
                {"level": "error", "path": "root", "message": "配置文件为空或无法解析"}
            )
            return issues
        if not isinstance(config, dict):
            issues.append(
                {"level": "error", "path": "root", "message": "配置根必须是对象类型"}
            )
            return issues

        agents = config.get("agents", {})
        if not agents:
            issues.append(
                {"level": "warning", "path": "agents", "message": "未配置任何 Agent"}
            )
        if agents and not isinstance(agents, dict):
            issues.append(
                {"level": "error", "path": "agents", "message": "agents 必须是对象类型"}
            )
            return issues

        if isinstance(agents, dict):
            for agent_name, agent_data in agents.items():
                agent_path = f"agents.{agent_name}"
                if ConfigValidator._is_blank(agent_name):
                    issues.append(
                        {
                            "level": "error",
                            "path": agent_path,
                            "message": "Agent 名称为空",
                        }
                    )
                    continue
                if not isinstance(agent_data, dict):
                    issues.append(
                        {
                            "level": "error",
                            "path": agent_path,
                            "message": f"Agent '{agent_name}' 的值必须是对象",
                        }
                    )
                    continue
                for field in ConfigValidator.OHMY_AGENT_REQUIRED_FIELDS:
                    if field not in agent_data:
                        issues.append(
                            {
                                "level": "error",
                                "path": f"{agent_path}.{field}",
                                "message": f"Agent '{agent_name}' 缺少必需字段 '{field}'",
                            }
                        )
                    elif ConfigValidator._is_blank(agent_data.get(field)):
                        issues.append(
                            {
                                "level": "error",
                                "path": f"{agent_path}.{field}",
                                "message": f"Agent '{agent_name}' 的 '{field}' 为空",
                            }
                        )
                if "description" in agent_data and ConfigValidator._is_blank(
                    agent_data.get("description")
                ):
                    issues.append(
                        {
                            "level": "warning",
                            "path": f"{agent_path}.description",
                            "message": f"Agent '{agent_name}' 的 description 为空",
                        }
                    )

        categories = config.get("categories", {})
        if not categories:
            issues.append(
                {
                    "level": "warning",
                    "path": "categories",
                    "message": "未配置任何 Category",
                }
            )
        if categories and not isinstance(categories, dict):
            issues.append(
                {
                    "level": "error",
                    "path": "categories",
                    "message": "categories 必须是对象类型",
                }
            )
            return issues

        if isinstance(categories, dict):
            for category_name, category_data in categories.items():
                category_path = f"categories.{category_name}"
                if ConfigValidator._is_blank(category_name):
                    issues.append(
                        {
                            "level": "error",
                            "path": category_path,
                            "message": "Category 名称为空",
                        }
                    )
                    continue
                if not isinstance(category_data, dict):
                    issues.append(
                        {
                            "level": "error",
                            "path": category_path,
                            "message": f"Category '{category_name}' 的值必须是对象",
                        }
                    )
                    continue
                for field in ConfigValidator.OHMY_CATEGORY_REQUIRED_FIELDS:
                    if field not in category_data:
                        issues.append(
                            {
                                "level": "error",
                                "path": f"{category_path}.{field}",
                                "message": f"Category '{category_name}' 缺少必需字段 '{field}'",
                            }
                        )
                    elif ConfigValidator._is_blank(category_data.get(field)):
                        issues.append(
                            {
                                "level": "error",
                                "path": f"{category_path}.{field}",
                                "message": f"Category '{category_name}' 的 '{field}' 为空",
                            }
                        )

                temperature = category_data.get("temperature")
                if temperature is not None and not isinstance(
                    temperature, (int, float)
                ):
                    issues.append(
                        {
                            "level": "warning",
                            "path": f"{category_path}.temperature",
                            "message": f"Category '{category_name}' 的 temperature 应该是数字",
                        }
                    )
                if "description" in category_data and ConfigValidator._is_blank(
                    category_data.get("description")
                ):
                    issues.append(
                        {
                            "level": "warning",
                            "path": f"{category_path}.description",
                            "message": f"Category '{category_name}' 的 description 为空",
                        }
                    )

        return issues

    @staticmethod
    def fix_provider_structure(config: Dict) -> Tuple[Dict, List[str]]:
        """
        修复 Provider 结构问题
        返回: (修复后的配置, 修复日志列表)
        """
        fixes = []
        if not config:
            return config, fixes

        providers = config.get("provider", {})
        if not isinstance(providers, dict):
            return config, fixes

        fixed_providers = {}
        for provider_name, provider_data in providers.items():
            if not isinstance(provider_data, dict):
                fixes.append(f"跳过无效 Provider '{provider_name}' (值不是对象)")
                continue

            # 确保必需字段存在
            fixed_provider = dict(provider_data)

            # 确保 npm 字段存在
            if "npm" not in fixed_provider:
                fixed_provider["npm"] = "@ai-sdk/openai"
                fixes.append(f"Provider '{provider_name}': 添加默认 npm 字段")

            # 确保 options 字段存在且为对象
            if "options" not in fixed_provider or not isinstance(
                fixed_provider.get("options"), dict
            ):
                fixed_provider["options"] = fixed_provider.get("options", {})
                if not isinstance(fixed_provider["options"], dict):
                    fixed_provider["options"] = {}
                fixes.append(f"Provider '{provider_name}': 修复 options 字段")

            # 确保 options 中有 baseURL 和 apiKey
            if "baseURL" not in fixed_provider["options"]:
                fixed_provider["options"]["baseURL"] = ""
                fixes.append(f"Provider '{provider_name}': 添加空 baseURL")
            if "apiKey" not in fixed_provider["options"]:
                fixed_provider["options"]["apiKey"] = ""
                fixes.append(f"Provider '{provider_name}': 添加空 apiKey")

            # 确保 models 字段存在且为对象
            if "models" not in fixed_provider:
                fixed_provider["models"] = {}
                fixes.append(f"Provider '{provider_name}': 添加空 models 字段")
            elif not isinstance(fixed_provider.get("models"), dict):
                fixed_provider["models"] = {}
                fixes.append(f"Provider '{provider_name}': 修复 models 字段为对象")

            # 规范化字段顺序: npm, name, options, models
            ordered_provider = {}
            if "npm" in fixed_provider:
                ordered_provider["npm"] = fixed_provider["npm"]
            if "name" in fixed_provider:
                ordered_provider["name"] = fixed_provider["name"]
            if "options" in fixed_provider:
                ordered_provider["options"] = fixed_provider["options"]
            if "models" in fixed_provider:
                ordered_provider["models"] = fixed_provider["models"]
            # 保留其他字段
            for k, v in fixed_provider.items():
                if k not in ordered_provider:
                    ordered_provider[k] = v

            fixed_providers[provider_name] = ordered_provider

        config["provider"] = fixed_providers
        return config, fixes

    @staticmethod
    def get_issues_summary(issues: List[Dict]) -> str:
        """生成问题摘要"""
        errors = [i for i in issues if i["level"] == "error"]
        warnings = [i for i in issues if i["level"] == "warning"]

        lines = []
        if errors:
            lines.append(f"❌ {len(errors)} 个错误:")
            for e in errors[:5]:  # 最多显示5个
                lines.append(f"  • {e['message']}")
            if len(errors) > 5:
                lines.append(f"  ... 还有 {len(errors) - 5} 个错误")

        if warnings:
            lines.append(f"⚠️ {len(warnings)} 个警告:")
            for w in warnings[:5]:
                lines.append(f"  • {w['message']}")
            if len(warnings) > 5:
                lines.append(f"  ... 还有 {len(warnings) - 5} 个警告")

        return "\n".join(lines) if lines else "✅ 配置格式正确"


class ModelRegistry:
    """模型注册表 - 管理所有已配置的模型"""

    def __init__(
        self,
        opencode_config: Optional[Dict],
        auth_manager: Optional[AuthManager] = None,
    ):
        self.config = opencode_config or {}
        self.auth_manager = auth_manager or AuthManager()
        self.models: Dict[str, bool] = {}
        self.native_providers: Dict[str, bool] = {}  # 已配置的原生 Provider
        self.refresh()

    def refresh(self):
        self.models = {}
        self.native_providers = {}

        # 获取自定义 Provider 的模型
        providers = self.config.get("provider", {})
        for provider_name, provider_data in providers.items():
            if not isinstance(provider_data, dict):
                continue
            models = provider_data.get("models", {})
            for model_id in models.keys():
                full_ref = f"{provider_name}/{model_id}"
                self.models[full_ref] = True

        # 获取已配置的原生 Provider
        try:
            auth_data = self.auth_manager.read_auth()
            for provider_id in auth_data:
                if auth_data[provider_id]:  # 有认证数据
                    self.native_providers[provider_id] = True
        except Exception:
            pass

    def get_all_models(self) -> List[str]:
        return list(self.models.keys())

    def get_configured_native_providers(self) -> List[str]:
        """获取已配置的原生 Provider ID 列表"""
        return list(self.native_providers.keys())

    def is_native_provider_configured(self, provider_id: str) -> bool:
        """检查原生 Provider 是否已配置"""
        return provider_id in self.native_providers


class ImportService:
    """外部配置导入服务 - 支持Claude Code、Codex、Gemini、cc-switch等配置格式"""

    @staticmethod
    def _first_existing_path(paths: List[Path]) -> Path:
        for path in paths:
            if path.exists():
                return path
        return paths[0]

    @staticmethod
    def _parse_toml_value(value: str):
        lower_value = value.lower()
        if lower_value in {"true", "false"}:
            return lower_value == "true"
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            return value[1:-1]
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            return value

    def _parse_toml_string(self, content: str) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        current_section: Dict[str, Any] = result
        for line in content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("[") and line.endswith("]"):
                section = line[1:-1]
                current_section = result
                for part in section.split("."):
                    current_section = current_section.setdefault(part, {})
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = self._parse_toml_value(value.strip())
                current_section[key] = value
        return result

    @staticmethod
    def _normalize_base_url(base_url: str, require_v1: bool) -> str:
        if not base_url:
            return ""
        trimmed = base_url.rstrip("/")
        if require_v1 and not trimmed.endswith("/v1"):
            trimmed = f"{trimmed}/v1"
        return trimmed

    @staticmethod
    def _sanitize_provider_key(name: str) -> str:
        cleaned = re.sub(r"[^a-z0-9-]+", "-", name.strip().lower())
        return cleaned.strip("-") or "provider"

    @staticmethod
    def _unique_provider_key(base: str, used_keys: set) -> str:
        candidate = base
        index = 2
        while candidate in used_keys:
            candidate = f"{base}-{index}"
            index += 1
        used_keys.add(candidate)
        return candidate

    def scan_external_configs(self) -> Dict:
        """扫描所有支持的外部配置文件"""
        results = {}
        test_root = Path(__file__).parent / "test"

        # Claude Code配置
        claude_settings = ConfigPaths.get_import_path("claude")
        if claude_settings is None:
            claude_settings = ConfigPaths.get_claude_settings()
            if not claude_settings.exists() and test_root.exists():
                test_path = test_root / ".claude" / "settings.json"
                if test_path.exists():
                    claude_settings = test_path
        results["Claude Code Settings"] = {
            "path": str(claude_settings),
            "exists": claude_settings.exists(),
            "data": ConfigManager.load_json(claude_settings)
            if claude_settings.exists()
            else None,
            "type": "claude",
        }

        claude_providers = ConfigPaths.get_import_path("claude_providers")
        if claude_providers is None:
            claude_providers = ConfigPaths.get_claude_providers()
            if not claude_providers.exists() and test_root.exists():
                test_path = test_root / ".claude" / "providers.json"
                if test_path.exists():
                    claude_providers = test_path
        results["Claude Providers"] = {
            "path": str(claude_providers),
            "exists": claude_providers.exists(),
            "data": ConfigManager.load_json(claude_providers)
            if claude_providers.exists()
            else None,
            "type": "claude_providers",
        }

        # Codex配置 (TOML格式)
        codex_config = ConfigPaths.get_import_path("codex")
        if codex_config is None:
            codex_config = Path.home() / ".codex" / "config.toml"
            if not codex_config.exists() and test_root.exists():
                test_path = test_root / ".codex" / "config.toml"
                if test_path.exists():
                    codex_config = test_path
        results["Codex Config"] = {
            "path": str(codex_config),
            "exists": codex_config.exists(),
            "data": self._parse_toml(codex_config) if codex_config.exists() else None,
            "type": "codex",
        }

        # Gemini配置
        gemini_dir = Path.home() / ".gemini"
        gemini_config = ConfigPaths.get_import_path("gemini")
        if gemini_config is None:
            gemini_config = self._first_existing_path(
                [gemini_dir / "config.json", gemini_dir / "settings.json"]
            )
            if not gemini_config.exists() and test_root.exists():
                test_path = test_root / ".gemini" / "settings.json"
                if test_path.exists():
                    gemini_config = test_path
        results["Gemini Config"] = {
            "path": str(gemini_config),
            "exists": gemini_config.exists(),
            "data": ConfigManager.load_json(gemini_config)
            if gemini_config.exists()
            else None,
            "type": "gemini",
        }

        # cc-switch配置
        ccswitch_dir = Path.home() / ".cc-switch"
        ccswitch_config = ConfigPaths.get_import_path("ccswitch")
        if ccswitch_config is None:
            ccswitch_config = self._first_existing_path(
                [
                    ccswitch_dir / "config.json.migrated",
                    ccswitch_dir / "config.json.bak",
                    ccswitch_dir / "config.json",
                ]
            )
            if not ccswitch_config.exists() and test_root.exists():
                test_path = test_root / ".cc-switch" / "config.json.migrated"
                if test_path.exists():
                    ccswitch_config = test_path
        results["CC-Switch Config"] = {
            "path": str(ccswitch_config),
            "exists": ccswitch_config.exists(),
            "data": ConfigManager.load_json(ccswitch_config)
            if ccswitch_config.exists()
            else None,
            "type": "ccswitch",
        }

        return results

    def _parse_toml(self, path: Path) -> Optional[Dict]:
        """简易TOML解析器"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            return self._parse_toml_string(content)
        except Exception as e:
            print(f"TOML parse failed: {e}")
            return None

    @staticmethod
    def _extract_from_env(env: Dict[str, Any]) -> Dict[str, str]:
        if not isinstance(env, dict):
            return {}
        api_key = env.get("ANTHROPIC_AUTH_TOKEN") or env.get("ANTHROPIC_API_TOKEN")
        base_url = env.get("ANTHROPIC_BASE_URL") or ""
        default_model = env.get("ANTHROPIC_MODEL")
        return {
            "api_key": api_key or "",
            "base_url": base_url or "",
            "default_model": default_model or "",
        }

    @staticmethod
    def _extract_provider_items(source_data: Any) -> List[Dict[str, Any]]:
        if isinstance(source_data, list):
            return [item for item in source_data if isinstance(item, dict)]
        if isinstance(source_data, dict):
            if "providers" in source_data and isinstance(
                source_data["providers"], dict
            ):
                items = []
                for item in source_data["providers"].values():
                    if isinstance(item, dict):
                        items.append(item)
                return items
            return [source_data]
        return []

    @staticmethod
    def _collect_model_ids(*values: Any) -> List[str]:
        model_ids: List[str] = []

        def add_value(value: Any) -> None:
            if value is None:
                return
            if isinstance(value, str):
                cleaned = value.strip()
                if cleaned:
                    model_ids.append(cleaned)
                return
            if isinstance(value, list):
                for item in value:
                    add_value(item)
                return
            if isinstance(value, dict):
                for key, item in value.items():
                    key_upper = str(key).upper()
                    if "MODEL" in key_upper:
                        add_value(item)
                for key in (
                    "model",
                    "default_model",
                    "defaultModel",
                    "model_id",
                    "modelId",
                    "id",
                    "name",
                ):
                    if key in value:
                        add_value(value.get(key))
                if "models" in value:
                    add_value(value.get("models"))

        for value in values:
            add_value(value)

        seen = set()
        deduped: List[str] = []
        for item in model_ids:
            lowered = item.lower()
            if lowered in {"opus", "sonnet", "haiku"}:
                continue
            if re.fullmatch(
                r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", lowered
            ):
                continue
            if item not in seen:
                seen.add(item)
                deduped.append(item)
        return deduped

    def convert_to_opencode(
        self, source_type: str, source_data: Dict
    ) -> Optional[Dict]:
        """将外部配置转换为OpenCode格式"""
        if not source_data:
            return None

        result = {"provider": {}, "permission": {}}
        used_keys: set = set()

        def add_provider(
            key: str,
            display_name: str,
            npm: str,
            api_key: str,
            base_url: str,
            require_v1: bool = False,
            model_ids: Optional[List[str]] = None,
        ) -> None:
            provider_key = self._unique_provider_key(key, used_keys)
            normalized_url = self._normalize_base_url(base_url, require_v1)
            models: Dict[str, Any] = {}
            if model_ids:
                for model_id in model_ids:
                    if model_id and isinstance(model_id, str):
                        models[model_id] = {"name": model_id}
            result["provider"][provider_key] = {
                "npm": npm,
                "name": display_name,
                "options": {
                    "apiKey": api_key or "",
                    "baseURL": normalized_url,
                },
                "models": models,
            }

        if source_type == "claude":
            env = source_data.get("env", source_data)
            extracted = self._extract_from_env(env)
            model_ids = self._collect_model_ids(
                extracted.get("default_model"),
                source_data.get("model"),
                source_data.get("default_model"),
                source_data.get("defaultModel"),
            )
            if extracted["api_key"] or extracted["base_url"] or model_ids:
                add_provider(
                    "anthropic",
                    "Anthropic (Claude)",
                    "@ai-sdk/anthropic",
                    extracted["api_key"],
                    extracted["base_url"],
                    require_v1=False,
                    model_ids=model_ids or None,
                )
            if "permissions" in source_data:
                for tool, perm in source_data.get("permissions", {}).items():
                    result["permission"][tool] = perm

        elif source_type == "claude_providers":
            for provider_data in self._extract_provider_items(source_data):
                display_name = provider_data.get("name") or provider_data.get("id")
                display_name = display_name or "Anthropic (Claude)"
                provider_key = self._sanitize_provider_key(display_name)
                api_key = provider_data.get("api_key") or provider_data.get(
                    "auth_token"
                )
                base_url = provider_data.get("base_url") or ""
                model_ids = self._collect_model_ids(
                    provider_data.get("models"),
                    provider_data.get("model"),
                    provider_data.get("default_model"),
                    provider_data.get("defaultModel"),
                )
                add_provider(
                    provider_key,
                    display_name,
                    "@ai-sdk/anthropic",
                    api_key or "",
                    base_url,
                    require_v1=False,
                    model_ids=model_ids or None,
                )

        elif source_type == "codex":
            model_providers = source_data.get("model_providers", {})
            provider_name = source_data.get("model_provider")
            provider_config = None
            if provider_name and isinstance(model_providers, dict):
                provider_config = model_providers.get(provider_name)
            if provider_config is None and isinstance(model_providers, dict):
                provider_name = next(iter(model_providers.keys()), None)
                provider_config = (
                    model_providers.get(provider_name) if provider_name else None
                )
            model_ids = self._collect_model_ids(
                source_data.get("model"),
                source_data.get("default_model"),
                source_data.get("defaultModel"),
                provider_config,
            )
            if isinstance(provider_config, dict):
                display_name = provider_config.get("name") or provider_name or "Codex"
                provider_key = self._sanitize_provider_key(
                    provider_name or display_name
                )
                base_url = provider_config.get("base_url", "")
                add_provider(
                    provider_key,
                    display_name,
                    "@ai-sdk/openai",
                    "",
                    base_url,
                    require_v1=True,
                    model_ids=model_ids or None,
                )
            elif model_ids:
                add_provider(
                    "codex",
                    "Codex",
                    "@ai-sdk/openai",
                    "",
                    "",
                    require_v1=True,
                    model_ids=model_ids,
                )

        elif source_type == "gemini":
            env = source_data.get("env", source_data)
            api_key = ""
            if isinstance(env, dict):
                api_key = env.get("GOOGLE_API_KEY") or env.get("GEMINI_API_KEY")
            api_key = api_key or source_data.get("apiKey") or ""
            base_url = source_data.get("baseURL") or source_data.get("base_url") or ""
            if api_key or base_url:
                add_provider(
                    "google",
                    "Google (Gemini)",
                    "@ai-sdk/google",
                    api_key,
                    base_url,
                    require_v1=False,
                )

        elif source_type == "ccswitch":
            claude = source_data.get("claude", {})
            claude_providers = claude.get("providers", {})
            if isinstance(claude_providers, dict):
                for provider_data in claude_providers.values():
                    if not isinstance(provider_data, dict):
                        continue
                    settings = provider_data.get("settingsConfig", {})
                    extracted = self._extract_from_env(settings.get("env", {}))
                    model_ids = self._collect_model_ids(
                        settings.get("env", {}),
                        settings.get("config", {}),
                        provider_data,
                        claude,
                    )
                    if not (extracted["api_key"] or extracted["base_url"] or model_ids):
                        continue
                    display_name = provider_data.get("name", "Anthropic (Claude)")
                    provider_key = self._sanitize_provider_key(display_name)
                    add_provider(
                        provider_key,
                        display_name,
                        "@ai-sdk/anthropic",
                        extracted["api_key"],
                        extracted["base_url"],
                        require_v1=False,
                        model_ids=model_ids or None,
                    )

            codex = source_data.get("codex", {})
            codex_providers = codex.get("providers", {})
            if isinstance(codex_providers, dict):
                for provider_data in codex_providers.values():
                    if not isinstance(provider_data, dict):
                        continue
                    settings = provider_data.get("settingsConfig", {})
                    auth = settings.get("auth", {})
                    config = settings.get("config", {})
                    if isinstance(config, str):
                        config = self._parse_toml_string(config)
                    api_key = ""
                    if isinstance(auth, dict):
                        api_key = auth.get("OPENAI_API_KEY") or ""
                    base_url = ""
                    if isinstance(config, dict):
                        base_url = config.get("base_url", "")
                    model_ids = self._collect_model_ids(
                        auth,
                        config,
                        settings.get("env", {}),
                        provider_data,
                        codex,
                    )
                    if not (api_key or base_url or model_ids):
                        continue
                    display_name = provider_data.get("name", "Codex")
                    provider_key = self._sanitize_provider_key(display_name)
                    require_v1 = True
                    if "/v1/" in base_url or base_url.rstrip("/").endswith("/v1"):
                        require_v1 = False
                    add_provider(
                        provider_key,
                        display_name,
                        "@ai-sdk/openai",
                        api_key,
                        base_url,
                        require_v1=require_v1,
                        model_ids=model_ids or None,
                    )

        return result


class ModelFetchService(QObject):
    """模型列表获取服务"""

    fetch_finished = pyqtSignal(str, list, str)  # provider_name, model_ids, error

    def __init__(self, parent=None):
        super().__init__(parent)

    def fetch_async(self, provider_name: str, options: Dict[str, Any]) -> None:
        thread = threading.Thread(
            target=self._fetch_models, args=(provider_name, options), daemon=True
        )
        thread.start()

    def _build_urls(self, options: Dict[str, Any]) -> List[str]:
        base_url = (options.get("baseURL") or "").strip()
        model_list_url = (options.get("modelListUrl") or "").strip()
        urls: List[str] = []

        if model_list_url:
            if model_list_url.startswith("http://") or model_list_url.startswith(
                "https://"
            ):
                urls.append(model_list_url)
            elif base_url:
                urls.append(base_url.rstrip("/") + "/" + model_list_url.lstrip("/"))
            return urls

        if not base_url:
            return urls

        if base_url.rstrip("/").endswith("/v1"):
            urls.append(base_url.rstrip("/") + "/models")
            return urls

        urls.append(base_url.rstrip("/") + "/v1/models")
        urls.append(base_url.rstrip("/") + "/models")
        return urls

    def _extract_model_ids(self, data: Any) -> List[str]:
        model_ids: List[str] = []
        if isinstance(data, dict):
            items = None
            if isinstance(data.get("data"), list):
                items = data.get("data")
            elif isinstance(data.get("models"), list):
                items = data.get("models")
            elif isinstance(data.get("result"), list):
                items = data.get("result")
            if items is not None:
                for item in items:
                    if isinstance(item, dict):
                        model_id = item.get("id") or item.get("name") or ""
                        if model_id:
                            model_ids.append(str(model_id))
                    elif isinstance(item, str):
                        model_ids.append(item)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    model_id = item.get("id") or item.get("name") or ""
                    if model_id:
                        model_ids.append(str(model_id))
                elif isinstance(item, str):
                    model_ids.append(item)
        return model_ids

    def _fetch_models(self, provider_name: str, options: Dict[str, Any]) -> None:
        urls = self._build_urls(options)
        if not urls:
            self.fetch_finished.emit(provider_name, [], "未配置模型列表地址")
            return

        api_key = (options.get("apiKey") or "").strip()
        headers = {"User-Agent": "OpenCode-Config-Manager"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        last_error = ""
        for url in urls:
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = json.loads(response.read().decode("utf-8"))
                model_ids = self._extract_model_ids(data)
                if model_ids:
                    self.fetch_finished.emit(provider_name, model_ids, "")
                    return
                last_error = "未返回可用模型列表"
            except Exception as e:
                last_error = str(e)

        self.fetch_finished.emit(provider_name, [], last_error or "获取失败")


class VersionChecker(QObject):
    """GitHub 版本检查服务 - 线程安全 + 速率限制处理"""

    # 信号：在主线程中安全地更新 UI
    update_available = pyqtSignal(str, str)  # (latest_version, release_url)

    def __init__(self, callback=None, parent=None):
        super().__init__(parent)
        self.callback = callback
        self.latest_version: Optional[str] = None
        self.release_url: Optional[str] = None
        self.checking = False
        self.last_check_time = 0  # 上次检查时间戳
        self.check_interval = 3600  # 检查间隔（秒），默认1小时
        # 连接信号到回调
        if callback:
            self.update_available.connect(callback)

    def check_update_async(self):
        """异步检查更新 - 带速率限制保护"""
        if self.checking:
            return

        # 检查是否在冷却期内
        current_time = time.time()
        if current_time - self.last_check_time < self.check_interval:
            print(
                f"Version check skipped: within cooldown period ({self.check_interval}s)"
            )
            return

        self.checking = True
        thread = threading.Thread(target=self._check_update, daemon=True)
        thread.start()

    def _check_update(self):
        """检查 GitHub 最新版本 - 带错误处理和速率限制"""
        try:
            req = urllib.request.Request(
                GITHUB_RELEASES_API,
                headers={
                    "User-Agent": "OpenCode-Config-Manager",
                    "Accept": "application/vnd.github.v3+json",
                },
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                tag_name = data.get("tag_name", "")
                version_match = re.search(r"v?(\d+\.\d+\.\d+)", tag_name)
                if version_match:
                    self.latest_version = version_match.group(1)
                    self.release_url = data.get("html_url", GITHUB_URL + "/releases")
                    # 更新最后检查时间
                    self.last_check_time = time.time()
                    # 通过信号在主线程中安全地调用回调
                    self.update_available.emit(self.latest_version, self.release_url)
        except urllib.error.HTTPError as e:
            if e.code == 403:
                # GitHub API 速率限制
                print(f"Version check failed: GitHub API rate limit exceeded (403)")
                # 增加冷却时间到 6 小时
                self.check_interval = 21600
            else:
                print(f"Version check failed: HTTP {e.code} - {e.reason}")
        except urllib.error.URLError as e:
            print(f"Version check failed: Network error - {e.reason}")
        except Exception as e:
            print(f"Version check failed: {e}")
        finally:
            self.checking = False

    @staticmethod
    def compare_versions(current: str, latest: str) -> bool:
        """比较版本号，返回 True 如果有新版本"""
        try:
            current_parts = [int(x) for x in current.split(".")]
            latest_parts = [int(x) for x in latest.split(".")]
            return latest_parts > current_parts
        except:
            return False


# ==================== 基础页面类 ====================
class BaseDialog(QDialog):
    """对话框基类 - 所有对话框继承此类，自动适配主题"""

    def __init__(self, parent=None):
        super().__init__(parent)
        # 监听主题变化
        qconfig.themeChanged.connect(self._apply_theme)

    def showEvent(self, event):
        """显示时应用当前主题"""
        super().showEvent(event)
        self._apply_theme()

    def _apply_theme(self):
        """根据当前主题应用样式"""
        if isDarkTheme():
            # 深色主题
            self.setStyleSheet("""
                QDialog {
                    background-color: #202020;
                    color: #E0E0E0;
                }
                QLabel {
                    color: #E0E0E0;
                }
                SubtitleLabel {
                    color: #FFFFFF;
                }
                QTableWidget {
                    background-color: #0d1117;
                    color: #E0E0E0;
                    gridline-color: #30363d;
                    border: 1px solid #30363d;
                }
                QTableWidget::item {
                    padding: 6px;
                }
                QTableWidget::item:selected {
                    background-color: #0078D4;
                }
                QHeaderView::section {
                    background-color: #161b22;
                    color: #B0B0B0;
                    border: none;
                    border-bottom: 1px solid #30363d;
                    padding: 8px;
                    font-weight: bold;
                }
                QTextEdit, TextEdit {
                    background-color: #0d1117;
                    color: #E0E0E0;
                    border: 1px solid #30363d;
                }
            """)
        else:
            # 浅色主题 - 奶白色背景（参考左侧软件）
            self.setStyleSheet("""
                QDialog {
                    background-color: #F7F8FA;
                    color: #1A1A1A;
                }
                QLabel {
                    color: #1A1A1A;
                }
                SubtitleLabel {
                    color: #000000;
                }
                QTableWidget {
                    background-color: #FFFFFF;
                    color: #1A1A1A;
                    gridline-color: #E8E8E8;
                    border: 1px solid #E0E0E0;
                }
                QTableWidget::item {
                    padding: 6px;
                }
                QTableWidget::item:selected {
                    background-color: #2979FF;
                    color: #FFFFFF;
                }
                QHeaderView::section {
                    background-color: #F0F1F3;
                    color: #505050;
                    border: none;
                    border-bottom: 1px solid #E0E0E0;
                    padding: 8px;
                    font-weight: bold;
                }
                QTextEdit, TextEdit {
                    background-color: #FFFFFF;
                    color: #1A1A1A;
                    border: 1px solid #E0E0E0;
                }
            """)


class BasePage(QWidget):
    """页面基类 - 所有页面继承此类"""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName(title.replace(" ", "_").lower())
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(36, 20, 36, 20)
        self._layout.setSpacing(16)

        # 页面标题
        self.title_label = TitleLabel(title, self)
        self._layout.addWidget(self.title_label)
        self.setLayout(self._layout)

    def add_card(self, title: Optional[str] = None) -> SimpleCardWidget:
        """添加一个卡片容器"""
        card = SimpleCardWidget(self)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(12)

        if title:
            card_title = SubtitleLabel(title, card)
            card_layout.addWidget(card_title)

        self._layout.addWidget(card)
        return card

    def show_success(self, title: str, content: str):
        """显示成功提示"""
        InfoBar.success(
            title=title,
            content=content,
            orient=QtCore.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self,
        )

    def show_error(self, title: str, content: str):
        """显示错误提示"""
        InfoBar.error(
            title=title,
            content=content,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self,
        )

    def show_warning(self, title: str, content: str):
        """显示警告提示"""
        InfoBar.warning(
            title=title,
            content=content,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=4000,
            parent=self,
        )


# ==================== 首页 ====================
class HomePage(BasePage):
    """首页 - 显示配置文件路径、统计信息、工具栏"""

    def __init__(self, main_window, parent=None):
        super().__init__(tr("home.title"), parent)
        self.main_window = main_window
        # 隐藏页面标题
        self.title_label.hide()
        self._setup_ui()
        self._load_stats()
        # 连接配置变更信号
        self.main_window.config_changed.connect(self._on_config_changed)

    def _on_config_changed(self):
        """配置变更时刷新统计"""
        self._load_stats()

    def _setup_ui(self):
        # ===== 关于卡片 (无标题) =====
        about_card = self.add_card()
        about_layout = about_card.layout()
        if about_layout is None:
            about_layout = QVBoxLayout(about_card)

        # 顶部布局：左侧 Logo，右侧标题与按钮
        hero_layout = QHBoxLayout()
        hero_layout.setSpacing(16)

        # Logo 图片 - 保持原始比例，设置固定尺寸确保完整显示
        logo_path = get_resource_path("assets/logo1.png")
        logo_label = QLabel(about_card)
        logo_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path))
            # 缩放到高度 100，保持比例 (原始 383x146，缩放后约 262x100)
            scaled_pixmap = pixmap.scaledToHeight(100, Qt.SmoothTransformation)  # type: ignore[attr-defined]
            logo_label.setPixmap(scaled_pixmap)
            # 设置固定尺寸确保完整显示
            logo_label.setFixedSize(scaled_pixmap.width(), scaled_pixmap.height())
        else:
            logo_label.setText("{ }")
            logo_label.setStyleSheet(
                "font-size: 36px; font-weight: bold; color: #3498DB;"
            )
        hero_layout.addWidget(logo_label)

        right_layout = QVBoxLayout()
        right_layout.setSpacing(6)

        title_label = TitleLabel(f"OpenCode Config Manager v{APP_VERSION}", about_card)
        title_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #e6edf3;")
        right_layout.addWidget(title_label)

        right_layout.addWidget(
            BodyLabel(
                tr("home.welcome"),
                about_card,
            )
        )

        # 链接按钮
        link_layout = QHBoxLayout()
        github_btn = PrimaryPushButton(FIF.GITHUB, tr("help.github"), about_card)
        github_btn.clicked.connect(lambda: webbrowser.open(GITHUB_URL))
        link_layout.addWidget(github_btn)

        author_btn = PushButton(
            FIF.PEOPLE, f"{tr('help.author')}: {AUTHOR_NAME}", about_card
        )
        author_btn.clicked.connect(lambda: webbrowser.open(AUTHOR_GITHUB))
        link_layout.addWidget(author_btn)

        link_layout.addStretch()
        right_layout.addLayout(link_layout)

        right_layout.addStretch()
        hero_layout.addLayout(right_layout, 1)
        about_layout.addLayout(hero_layout)

        # ===== 配置文件路径卡片 =====
        paths_card = self.add_card(tr("home.config_path"))
        paths_layout = paths_card.layout()

        # 路径标签样式
        def create_path_label(text):
            label = StrongBodyLabel(text)
            label.setStyleSheet("color: #58a6ff; min-width: 120px;")
            return label

        # OpenCode 配置路径
        oc_layout = QHBoxLayout()
        oc_layout.addWidget(create_path_label("OpenCode:"))
        self.oc_path_label = CaptionLabel(
            str(ConfigPaths.get_opencode_config()), paths_card
        )
        self.oc_path_label.setToolTip(str(ConfigPaths.get_opencode_config()))
        oc_layout.addWidget(self.oc_path_label, 1)

        oc_copy_btn = ToolButton(FIF.COPY, paths_card)
        oc_copy_btn.setToolTip(tr("common.copy"))
        oc_copy_btn.clicked.connect(
            lambda: self._copy_to_clipboard(self.oc_path_label.text())
        )
        oc_layout.addWidget(oc_copy_btn)

        oc_browse_btn = ToolButton(FIF.FOLDER, paths_card)
        oc_browse_btn.setToolTip(tr("home.select_config"))
        oc_browse_btn.clicked.connect(lambda: self._browse_config("opencode"))
        oc_layout.addWidget(oc_browse_btn)

        self.oc_reset_btn = ToolButton(FIF.SYNC, paths_card)
        self.oc_reset_btn.setToolTip(tr("home.reset_path"))
        self.oc_reset_btn.clicked.connect(lambda: self._reset_config_path("opencode"))
        self.oc_reset_btn.setVisible(ConfigPaths.is_custom_path("opencode"))
        oc_layout.addWidget(self.oc_reset_btn)

        paths_layout.addLayout(oc_layout)

        # Oh My OpenCode 配置路径
        ohmy_layout = QHBoxLayout()
        ohmy_layout.addWidget(create_path_label("Oh My OpenCode:"))
        self.ohmy_path_label = CaptionLabel(
            str(ConfigPaths.get_ohmyopencode_config()), paths_card
        )
        self.ohmy_path_label.setToolTip(str(ConfigPaths.get_ohmyopencode_config()))
        ohmy_layout.addWidget(self.ohmy_path_label, 1)

        ohmy_copy_btn = ToolButton(FIF.COPY, paths_card)
        ohmy_copy_btn.setToolTip(tr("common.copy"))
        ohmy_copy_btn.clicked.connect(
            lambda: self._copy_to_clipboard(self.ohmy_path_label.text())
        )
        ohmy_layout.addWidget(ohmy_copy_btn)

        ohmy_browse_btn = ToolButton(FIF.FOLDER, paths_card)
        ohmy_browse_btn.setToolTip(tr("home.select_config"))
        ohmy_browse_btn.clicked.connect(lambda: self._browse_config("ohmyopencode"))
        ohmy_layout.addWidget(ohmy_browse_btn)

        self.ohmy_reset_btn = ToolButton(FIF.SYNC, paths_card)
        self.ohmy_reset_btn.setToolTip(tr("home.reset_path"))
        self.ohmy_reset_btn.clicked.connect(
            lambda: self._reset_config_path("ohmyopencode")
        )
        self.ohmy_reset_btn.setVisible(ConfigPaths.is_custom_path("ohmyopencode"))
        ohmy_layout.addWidget(self.ohmy_reset_btn)

        paths_layout.addLayout(ohmy_layout)

        # 备份目录路径
        backup_layout = QHBoxLayout()
        backup_layout.addWidget(create_path_label(tr("home.backup_path") + ":"))
        self.backup_path_label = CaptionLabel(
            str(ConfigPaths.get_backup_dir()), paths_card
        )
        self.backup_path_label.setToolTip(str(ConfigPaths.get_backup_dir()))
        backup_layout.addWidget(self.backup_path_label, 1)

        backup_copy_btn = ToolButton(FIF.COPY, paths_card)
        backup_copy_btn.setToolTip(tr("common.copy"))
        backup_copy_btn.clicked.connect(
            lambda: self._copy_to_clipboard(self.backup_path_label.text())
        )
        backup_layout.addWidget(backup_copy_btn)

        backup_browse_btn = ToolButton(FIF.FOLDER, paths_card)
        backup_browse_btn.setToolTip(tr("home.select_backup_dir"))
        backup_browse_btn.clicked.connect(self._browse_backup_dir)
        backup_layout.addWidget(backup_browse_btn)

        self.backup_reset_btn = ToolButton(FIF.SYNC, paths_card)
        self.backup_reset_btn.setToolTip(tr("home.reset_path"))
        self.backup_reset_btn.clicked.connect(self._reset_backup_dir)
        self.backup_reset_btn.setVisible(ConfigPaths.is_custom_path("backup"))
        backup_layout.addWidget(self.backup_reset_btn)

        paths_layout.addLayout(backup_layout)

        # ===== 统计信息卡片 =====
        stats_card = self.add_card(tr("home.config_stats"))
        stats_layout = stats_card.layout()

        stats_row = QHBoxLayout()
        stats_row.setSpacing(24)

        # 统计项 - 横向显示，数值加粗变色
        def create_stat_item(label_text, parent):
            container = QWidget(parent)
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(6)

            label = CaptionLabel(label_text, container)
            label.setStyleSheet("color: #7d8590;")
            layout.addWidget(label)

            value = StrongBodyLabel("0", container)
            value.setStyleSheet("font-size: 14px; color: #58a6ff;")
            layout.addWidget(value)

            return container, value

        self.provider_count_label = None
        self.model_count_label = None
        self.mcp_count_label = None
        self.agent_count_label = None
        self.ohmy_agent_count_label = None
        self.category_count_label = None

        stats_items = [
            ("Provider:", "provider_count_label"),
            ("Model:", "model_count_label"),
            ("MCP:", "mcp_count_label"),
            ("Agent:", "agent_count_label"),
            ("Oh My Agent:", "ohmy_agent_count_label"),
            ("Category:", "category_count_label"),
        ]

        for label_text, attr_name in stats_items:
            container, value_label = create_stat_item(label_text, stats_card)
            setattr(self, attr_name, value_label)
            stats_row.addWidget(container)

        stats_row.addStretch()
        stats_layout.addLayout(stats_row)

        # ===== 操作按钮卡片 =====
        action_card = self.add_card(tr("home.quick_actions"))
        action_layout = action_card.layout()

        btn_layout = QHBoxLayout()

        reload_btn = PrimaryPushButton(FIF.SYNC, tr("home.reload_config"), action_card)
        reload_btn.clicked.connect(self._on_reload)
        btn_layout.addWidget(reload_btn)

        backup_btn = PushButton(FIF.SAVE, tr("home.backup_now"), action_card)
        backup_btn.clicked.connect(self._on_backup)
        btn_layout.addWidget(backup_btn)

        self.validate_btn = PushButton(
            FIF.SEARCH, tr("home.validate_config"), action_card
        )
        self.validate_btn.clicked.connect(self._on_validate_config)
        btn_layout.addWidget(self.validate_btn)

        btn_layout.addStretch()
        action_layout.addLayout(btn_layout)

        # ===== 配置检测详情卡片 =====
        validate_card = self.add_card(tr("home.validation_details"))
        validate_layout = validate_card.layout()
        self.validation_details = PlainTextEdit(validate_card)
        self.validation_details.setReadOnly(True)
        self.validation_details.setPlaceholderText(tr("home.no_validation_yet"))
        self.validation_details.setMinimumHeight(120)
        self.validation_details.setMaximumHeight(200)
        self.validation_details.setStyleSheet("""
            PlainTextEdit {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 8px;
                font-family: "Consolas", "Monaco", monospace;
                font-size: 12px;
                color: #e6edf3;
            }
        """)
        validate_layout.addWidget(self.validation_details)

        self._layout.addStretch()

    def _format_validation_details(self, issues: List[Dict]) -> str:
        if not issues:
            return tr("home.validation_no_issues")
        lines = []
        for index, issue in enumerate(issues, start=1):
            level_label = (
                tr("home.validation_error_label")
                if issue.get("level") == "error"
                else tr("home.validation_warning_label")
            )
            path = issue.get("path", "")
            message = issue.get("message", "")
            lines.append(f"{index}. [{level_label}] {path} - {message}")
        return "\n".join(lines)

    def _on_validate_config(self):
        """手动配置检测"""
        oc_issues = ConfigValidator.validate_opencode_config(
            self.main_window.opencode_config or {}
        )
        ohmy_issues = ConfigValidator.validate_ohmyopencode_config(
            self.main_window.ohmyopencode_config or {}
        )
        issues = []
        for issue in oc_issues:
            issue_copy = dict(issue)
            issue_copy["path"] = f"OpenCode.{issue_copy.get('path', '')}".rstrip(".")
            issues.append(issue_copy)
        for issue in ohmy_issues:
            issue_copy = dict(issue)
            issue_copy["path"] = f"OhMy.{issue_copy.get('path', '')}".rstrip(".")
            issues.append(issue_copy)

        errors = [i for i in issues if i.get("level") == "error"]
        warnings = [i for i in issues if i.get("level") == "warning"]
        if not issues:
            self.show_success(
                tr("home.validation_complete"), tr("home.validation_no_issues_msg")
            )
        elif errors:
            self.show_error(
                tr("home.validation_complete"),
                tr(
                    "home.validation_errors_warnings",
                    error_count=len(errors),
                    warning_count=len(warnings),
                ),
            )
        else:
            self.show_warning(
                tr("home.validation_complete"),
                tr("home.validation_warnings_only", warning_count=len(warnings)),
            )

        self.validation_details.setPlainText(self._format_validation_details(issues))

    def _copy_to_clipboard(self, text: str):
        """复制文本到剪贴板"""
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        self.show_success(tr("common.success"), tr("home.copy_success"))

    def _browse_config(self, config_type: str):
        """浏览并选择配置文件"""
        title = (
            tr("home.select_opencode_config")
            if config_type == "opencode"
            else tr("home.select_ohmyopencode_config")
        )
        file_filter = tr("home.json_filter")

        # 获取当前路径作为起始目录
        if config_type == "opencode":
            start_path = str(ConfigPaths.get_opencode_config().parent)
        else:
            start_path = str(ConfigPaths.get_ohmyopencode_config().parent)

        file_path, _ = QFileDialog.getOpenFileName(self, title, start_path, file_filter)

        if file_path:
            path = Path(file_path)
            # 验证文件是否为有效的 JSON/JSONC
            config_data = ConfigManager.load_json(path)
            if config_data is None:
                self.show_error(tr("common.error"), tr("home.invalid_config"))
                return

            # 设置自定义路径
            if config_type == "opencode":
                ConfigPaths.set_opencode_config(path)
                self.oc_path_label.setText(str(path))
                self.oc_path_label.setToolTip(str(path))
                self.oc_reset_btn.setVisible(True)
                # 重新加载配置
                self.main_window.opencode_config = config_data
            else:
                ConfigPaths.set_ohmyopencode_config(path)
                self.ohmy_path_label.setText(str(path))
                self.ohmy_path_label.setToolTip(str(path))
                self.ohmy_reset_btn.setVisible(True)
                # 重新加载配置
                self.main_window.ohmyopencode_config = config_data

            self._load_stats()
            self.show_success(
                tr("common.success"), tr("home.switched_to_custom", filename=path.name)
            )

    def _reset_config_path(self, config_type: str):
        """重置为默认配置路径"""
        ConfigPaths.reset_to_default(config_type)

        if config_type == "opencode":
            default_path = ConfigPaths.get_opencode_config()
            self.oc_path_label.setText(str(default_path))
            self.oc_path_label.setToolTip(str(default_path))
            self.oc_reset_btn.setVisible(False)
            # 重新加载默认配置
            self.main_window.opencode_config = (
                ConfigManager.load_json(default_path) or {}
            )
        else:
            default_path = ConfigPaths.get_ohmyopencode_config()
            self.ohmy_path_label.setText(str(default_path))
            self.ohmy_path_label.setToolTip(str(default_path))
            self.ohmy_reset_btn.setVisible(False)
            # 重新加载默认配置
            self.main_window.ohmyopencode_config = (
                ConfigManager.load_json(default_path) or {}
            )

        self._load_stats()
        self.show_success(tr("common.success"), tr("home.reset_to_default"))

    def _browse_backup_dir(self):
        """浏览并选择备份目录"""
        start_path = str(ConfigPaths.get_backup_dir())
        dir_path = QFileDialog.getExistingDirectory(
            self, tr("home.select_backup_dir_title"), start_path
        )

        if dir_path:
            path = Path(dir_path)
            ConfigPaths.set_backup_dir(path)
            self.backup_path_label.setText(str(path))
            self.backup_path_label.setToolTip(str(path))
            self.backup_reset_btn.setVisible(True)
            # 更新备份管理器的目录
            self.main_window.backup_manager.backup_dir = path
            path.mkdir(parents=True, exist_ok=True)
            self.show_success(
                tr("common.success"),
                tr("home.switched_to_custom_backup", dirname=path.name),
            )

    def _reset_backup_dir(self):
        """重置为默认备份目录"""
        ConfigPaths.reset_to_default("backup")
        default_path = ConfigPaths.get_backup_dir()
        self.backup_path_label.setText(str(default_path))
        self.backup_path_label.setToolTip(str(default_path))
        self.backup_reset_btn.setVisible(False)
        # 更新备份管理器的目录
        self.main_window.backup_manager.backup_dir = default_path
        self.show_success(tr("common.success"), tr("home.reset_to_default_backup"))

    def _update_path_labels(self):
        """更新路径标签显示"""
        oc_path = str(ConfigPaths.get_opencode_config())
        ohmy_path = str(ConfigPaths.get_ohmyopencode_config())

        self.oc_path_label.setText(oc_path)
        self.oc_path_label.setToolTip(oc_path)
        self.oc_reset_btn.setVisible(ConfigPaths.is_custom_path("opencode"))

        self.ohmy_path_label.setText(ohmy_path)
        self.ohmy_path_label.setToolTip(ohmy_path)
        self.ohmy_reset_btn.setVisible(ConfigPaths.is_custom_path("ohmyopencode"))

    def _load_stats(self):
        """加载统计信息"""
        oc_config = self.main_window.opencode_config or {}
        ohmy_config = self.main_window.ohmyopencode_config or {}

        # Provider 数量
        providers = oc_config.get("provider", {})
        self.provider_count_label.setText(str(len(providers)))

        # Model 数量
        model_count = 0
        for provider_data in providers.values():
            if isinstance(provider_data, dict):
                model_count += len(provider_data.get("models", {}))
        self.model_count_label.setText(str(model_count))

        # MCP 数量 - MCP 配置直接在 mcp 下，不是 mcp.servers
        mcp_count = len(oc_config.get("mcp", {}))
        self.mcp_count_label.setText(str(mcp_count))

        # OpenCode Agent 数量
        agent_count = len(oc_config.get("agent", {}))
        self.agent_count_label.setText(str(agent_count))

        # Oh My Agent 数量
        ohmy_agent_count = len(ohmy_config.get("agents", {}))
        self.ohmy_agent_count_label.setText(str(ohmy_agent_count))

        # Category 数量
        category_count = len(ohmy_config.get("categories", {}))
        self.category_count_label.setText(str(category_count))

    def _on_reload(self):
        """重新加载配置"""
        self.main_window.opencode_config = ConfigManager.load_json(
            ConfigPaths.get_opencode_config()
        )
        self.main_window.ohmyopencode_config = ConfigManager.load_json(
            ConfigPaths.get_ohmyopencode_config()
        )

        if self.main_window.opencode_config is None:
            self.main_window.opencode_config = {}
        if self.main_window.ohmyopencode_config is None:
            self.main_window.ohmyopencode_config = {}

        self.main_window._refresh_file_hashes()
        self._load_stats()
        self.show_success(tr("common.success"), tr("home.config_reloaded"))

    def _on_backup(self):
        """备份配置"""
        backup_manager = self.main_window.backup_manager
        oc_file_path = ConfigPaths.get_opencode_config()
        ohmy_file_path = ConfigPaths.get_ohmyopencode_config()

        oc_path = backup_manager.backup_data(
            oc_file_path, self.main_window.opencode_config, tag="manual-memory"
        )
        ohmy_path = backup_manager.backup_data(
            ohmy_file_path, self.main_window.ohmyopencode_config, tag="manual-memory"
        )
        backup_manager.backup(oc_file_path, tag="manual-file")
        backup_manager.backup(ohmy_file_path, tag="manual-file")

        if oc_path and ohmy_path:
            self.show_success(tr("common.success"), tr("home.backup_success"))
        else:
            self.show_error(tr("common.error"), tr("home.backup_failed"))


# ==================== Provider 页面 ====================
class ProviderPage(BasePage):
    """Provider 管理页面"""

    def __init__(self, main_window, parent=None):
        super().__init__(tr("provider.title"), parent)
        self.main_window = main_window
        self._setup_ui()
        self._load_data()
        # 连接配置变更信号
        self.main_window.config_changed.connect(self._on_config_changed)

    def _on_models_fetched(self, provider_name: str, model_ids: List[str], error: str):
        if error:
            self.show_warning(
                tr("common.info"), tr("provider.fetch_failed", error=error)
            )
            return

        if not model_ids:
            self.show_warning(tr("common.info"), tr("provider.no_models_found"))
            return

        dialog = ModelSelectDialog(
            self.main_window, provider_name, model_ids, parent=self
        )
        if not dialog.exec_():
            return

        selected = dialog.get_selected_model_ids()
        if not selected:
            self.show_warning(tr("common.info"), tr("provider.no_models_selected"))
            return

        batch_config = dialog.get_batch_config()
        self._add_models(provider_name, selected, batch_config)

    def _add_models(
        self,
        provider_name: str,
        model_ids: List[str],
        batch_config: Dict[str, Any] | None = None,
    ) -> None:
        config = self.main_window.opencode_config or {}
        provider = config.get("provider", {}).get(provider_name)
        if not isinstance(provider, dict):
            self.show_warning(tr("common.info"), tr("provider.provider_not_exist"))
            return

        models = provider.setdefault("models", {})
        added = 0
        for model_id in model_ids:
            if model_id in models:
                continue
            category = self._resolve_model_category(model_id)
            model_data = {"name": model_id}
            if batch_config:
                model_data.update(self._apply_batch_config(category, batch_config))
            models[model_id] = model_data
            added += 1

        self.main_window.save_opencode_config()
        self._load_data()
        if added:
            self.show_success(
                tr("common.success"), tr("provider.models_added", count=added)
            )
        else:
            self.show_warning(tr("common.info"), tr("provider.models_exist"))

    def _resolve_model_category(self, model_id: str) -> str:
        lower = model_id.lower()
        if "claude" in lower:
            return tr("provider.claude_series")
        if "gemini" in lower:
            return tr("provider.gemini_series")
        if any(token in lower for token in ("gpt", "openai", "codex", "o1")):
            return tr("provider.openai_series")
        return tr("provider.other_models")

    def _get_preset_for_category(
        self, category: str, preset_name: str
    ) -> Dict[str, Any]:
        custom = MODEL_PRESET_CUSTOM.get(category, {})
        if preset_name in custom:
            return copy.deepcopy(custom[preset_name])
        presets = MODEL_PRESET_PACKS.get(category, {})
        if preset_name in presets:
            return copy.deepcopy(presets[preset_name])
        return {
            "attachment": False,
            "modalities": {"input": ["text"], "output": ["text"]},
            "limit": {"context": 64000, "output": 8192},
            "options": {},
            "variants": {},
        }

    def _apply_batch_config(
        self, category: str, batch_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        support = {
            "attachment": True,
            "modalities": True,
            "limit": True,
            "options": False,
            "thinking": False,
            "variants": False,
        }
        if category == tr("provider.claude_series_short"):
            support["thinking"] = True
            support["variants"] = True
        elif category == tr("provider.openai_series_short"):
            support["options"] = True
            support["variants"] = True
        elif category == tr("provider.gemini_series_short"):
            support["thinking"] = True
            support["variants"] = True

        result: Dict[str, Any] = {}
        if not batch_config:
            return result

        base_preset = self._get_preset_for_category(
            category, MODEL_PRESET_DEFAULT.get(category, "基础")
        )

        for key in (
            "attachment",
            "modalities",
            "limit",
            "options",
            "thinking",
            "variants",
        ):
            config = batch_config.get(key)
            if not config or not config.get("enabled"):
                continue
            if not support.get(key, False):
                continue
            if key == "attachment":
                result["attachment"] = True
                continue
            if key == "modalities":
                result["modalities"] = {"input": ["text", "image"], "output": ["text"]}
                continue

            if key == "limit":
                value = config.get("value")
                limit_map = {
                    "4k": {"context": 64000, "output": 4096},
                    "8k": {"context": 128000, "output": 8192},
                    "16k": {"context": 200000, "output": 16384},
                    "32k": {"context": 256000, "output": 32768},
                    "64k": {"context": 256000, "output": 65536},
                }
                if value in limit_map:
                    result["limit"] = limit_map[value]
                continue
            if key == "thinking":
                value = config.get("value")
                if category == tr("provider.claude_series_short"):
                    result["options"] = {
                        "thinking": {"type": "enabled", "budgetTokens": 64000}
                    }
                    thinking_map = {
                        "8k": 8000,
                        "16k": 16000,
                        "32k": 32000,
                        "64k": 64000,
                    }
                    if value in thinking_map:
                        result["options"]["thinking"]["budgetTokens"] = thinking_map[
                            value
                        ]
                elif category == tr("provider.gemini_series_short"):
                    result["options"] = {"thinkingConfig": {"thinkingBudget": 32000}}
                    thinking_map = {
                        "8k": 8000,
                        "16k": 16000,
                        "32k": 32000,
                        "64k": 64000,
                    }
                    if value in thinking_map:
                        result["options"]["thinkingConfig"]["thinkingBudget"] = (
                            thinking_map[value]
                        )
                continue
            if key == "options":
                value = config.get("value")
                if value:
                    result["options"] = {"reasoningEffort": value}
                continue
            if key == "variants":
                value = config.get("value")
                if value == "high/medium/low":
                    result["variants"] = {
                        "high": {"reasoningEffort": "high"},
                        "medium": {"reasoningEffort": "medium"},
                        "low": {"reasoningEffort": "low"},
                    }
                elif value == "high/low":
                    result["variants"] = {
                        "high": {"reasoningEffort": "high"},
                        "low": {"reasoningEffort": "low"},
                    }
                continue
        return result

    def _on_config_changed(self):
        """配置变更时刷新数据"""
        self._load_data()

    def _setup_ui(self):
        # 工具栏
        toolbar = QHBoxLayout()

        self.add_btn = PrimaryPushButton(FIF.ADD, tr("provider.add_provider"), self)
        self.add_btn.clicked.connect(self._on_add)
        toolbar.addWidget(self.add_btn)

        self.edit_btn = PushButton(FIF.EDIT, tr("common.edit"), self)
        self.edit_btn.clicked.connect(self._on_edit)
        toolbar.addWidget(self.edit_btn)

        self.delete_btn = PushButton(FIF.DELETE, tr("common.delete"), self)
        self.delete_btn.clicked.connect(self._on_delete)
        toolbar.addWidget(self.delete_btn)

        self.fetch_models_btn = PushButton(FIF.SYNC, tr("provider.fetch_models"), self)
        self.fetch_models_btn.clicked.connect(self._on_fetch_models)
        toolbar.addWidget(self.fetch_models_btn)

        self.export_cli_btn = PushButton(FIF.SEND, tr("provider.export_to_cli"), self)
        self.export_cli_btn.clicked.connect(self._on_export_to_cli)
        toolbar.addWidget(self.export_cli_btn)

        self.query_balance_btn = PushButton(
            FIF.MARKET, tr("provider.query_balance"), self
        )
        self.query_balance_btn.clicked.connect(self._on_query_balance)
        toolbar.addWidget(self.query_balance_btn)

        toolbar.addStretch()
        self._layout.addLayout(toolbar)

        # Provider 列表
        self.table = TableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            [
                tr("common.name"),
                tr("provider.display_name"),
                "SDK",
                tr("provider.api_address"),
                tr("provider.model_count"),
            ]
        )
        # 调整列宽：名称15字符，模型数5字符，SDK22字符，剩余均分
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.resizeSection(0, 120)  # 名称 15字符约120px
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # 显示名称 均分
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.resizeSection(2, 180)  # SDK 22字符约180px
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # API地址 均分
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.resizeSection(4, 60)  # 模型数 5字符约60px
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.doubleClicked.connect(self._on_edit)
        self._layout.addWidget(self.table)

    def _load_data(self):
        """加载 Provider 数据"""
        self.table.setRowCount(0)
        config = self.main_window.opencode_config or {}
        providers = config.get("provider", {})

        for name, data in providers.items():
            if not isinstance(data, dict):
                continue
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(data.get("name", "")))
            self.table.setItem(row, 2, QTableWidgetItem(data.get("npm", "")))
            # API地址添加tooltip显示全部
            api_url = data.get("options", {}).get("baseURL", "")
            api_item = QTableWidgetItem(api_url)
            api_item.setToolTip(
                api_url if api_url else tr("provider.use_default_address")
            )
            self.table.setItem(row, 3, api_item)
            self.table.setItem(
                row, 4, QTableWidgetItem(str(len(data.get("models", {}))))
            )

    def _on_add(self):
        """添加 Provider"""
        dialog = ProviderDialog(self.main_window, parent=self)
        if dialog.exec_():
            self._load_data()
            self.show_success(tr("common.success"), tr("provider.added_success"))

    def _on_edit(self):
        """编辑 Provider"""
        row = self.table.currentRow()
        if row < 0:
            self.show_warning(tr("common.info"), tr("provider.select_first"))
            return

        name = self.table.item(row, 0).text()
        dialog = ProviderDialog(self.main_window, provider_name=name, parent=self)
        if dialog.exec_():
            self._load_data()
            self.show_success(tr("common.success"), tr("provider.updated_success"))

    def _on_delete(self):
        """删除 Provider"""
        row = self.table.currentRow()
        if row < 0:
            self.show_warning(tr("common.info"), tr("provider.select_first"))
            return

        name = self.table.item(row, 0).text()
        w = FluentMessageBox(
            tr("provider.delete_confirm_title"),
            tr("provider.delete_confirm", name=name),
            self,
        )
        if w.exec_():
            config = self.main_window.opencode_config or {}
            if "provider" in config and name in config["provider"]:
                del config["provider"][name]
                self.main_window.save_opencode_config()
                self._load_data()
                self.show_success(
                    tr("common.success"), tr("provider.deleted_success", name=name)
                )

    def _on_fetch_models(self):
        """拉取模型列表"""
        row = self.table.currentRow()
        if row < 0:
            self.show_warning(tr("common.info"), tr("provider.select_first"))
            return

        provider_name = self.table.item(row, 0).text()
        config = self.main_window.opencode_config or {}
        provider = config.get("provider", {}).get(provider_name, {})
        options = provider.get("options", {}) if isinstance(provider, dict) else {}
        if not options.get("baseURL") and not options.get("modelListUrl"):
            self.show_warning(tr("common.info"), tr("provider.no_base_url"))
            return

        self._fetch_models_for_provider(provider_name, options)

    def _fetch_models_for_provider(self, provider_name: str, options: Dict[str, Any]):
        if not hasattr(self, "_model_fetch_service"):
            self._model_fetch_service = ModelFetchService(self)
            self._model_fetch_service.fetch_finished.connect(self._on_models_fetched)

        self.show_warning(
            tr("common.info"), tr("provider.fetch_models_hint", name=provider_name)
        )
        self._model_fetch_service.fetch_async(provider_name, options)

    def _on_export_to_cli(self):
        """导出到 CLI 工具"""
        row = self.table.currentRow()
        if row < 0:
            self.show_warning(tr("common.info"), tr("provider.select_first"))
            return

        provider_name = self.table.item(row, 0).text()

        # 切换到 CLI 导出页面
        if hasattr(self.main_window, "cli_export_page"):
            self.main_window.switchTo(self.main_window.cli_export_page)
            # 预选当前 Provider
            cli_page = self.main_window.cli_export_page
            index = cli_page.provider_combo.findText(provider_name)
            if index >= 0:
                cli_page.provider_combo.setCurrentIndex(index)
        else:
            self.show_warning(tr("common.info"), tr("provider.cli_page_unavailable"))

    def _on_query_balance(self):
        """查询余额"""
        row = self.table.currentRow()
        if row < 0:
            self.show_warning(tr("common.info"), tr("provider.select_first"))
            return

        provider_name = self.table.item(row, 0).text()
        config = self.main_window.opencode_config or {}
        provider = config.get("provider", {}).get(provider_name, {})

        if not isinstance(provider, dict):
            self.show_warning(tr("common.info"), tr("provider.provider_not_exist"))
            return

        # 获取 baseURL 和 apiKey
        options = provider.get("options", {})
        base_url = options.get("baseURL", "")
        api_key = options.get("apiKey", "")

        if not base_url:
            self.show_warning(tr("common.info"), tr("provider.no_base_url"))
            return

        if not api_key:
            self.show_warning(tr("common.info"), tr("provider.no_api_key"))
            return

        # 显示加载提示
        state_tooltip = StateToolTip(
            tr("provider.querying_balance"), tr("provider.please_wait"), self.window()
        )
        state_tooltip.move(state_tooltip.getSuitablePos())
        state_tooltip.show()

        # 在后台线程查询余额
        def query_thread():
            try:
                usage_data = self._query_provider_usage(base_url, api_key)
                # 在主线程显示结果
                QMetaObject.invokeMethod(
                    self,
                    "_show_balance_result",
                    Qt.QueuedConnection,
                    Q_ARG(str, provider_name),
                    Q_ARG(object, usage_data),
                    Q_ARG(str, api_key),
                    Q_ARG(object, state_tooltip),
                )
            except Exception as e:
                # 在主线程显示错误
                QMetaObject.invokeMethod(
                    self,
                    "_show_balance_error",
                    Qt.QueuedConnection,
                    Q_ARG(str, str(e)),
                    Q_ARG(object, state_tooltip),
                )

        thread = threading.Thread(target=query_thread, daemon=True)
        thread.start()

    def _query_provider_usage(self, base_url: str, api_key: str) -> Dict[str, Any]:
        """查询 Provider 用量（支持 OpenAI API 和 NewAPI）"""
        import json
        from datetime import datetime, timedelta

        # 规范化 base_url - 移除末尾斜杠
        base_url = base_url.rstrip("/")

        # 先尝试 NewAPI 接口
        try:
            return self._query_newapi_usage(base_url, api_key)
        except Exception as newapi_error:
            # NewAPI 失败，尝试 OpenAI API
            pass

        # 尝试 OpenAI API 接口
        try:
            return self._query_openai_usage(base_url, api_key)
        except Exception as openai_error:
            # 两种方式都失败，抛出错误
            raise Exception(
                f"余额查询失败。NewAPI: {str(newapi_error)[:50]}... OpenAI API: {str(openai_error)[:50]}..."
            )

    def _query_newapi_usage(self, base_url: str, api_key: str) -> Dict[str, Any]:
        """查询 NewAPI 用量"""
        import json

        # NewAPI 余额查询端点
        balance_url = f"{base_url}/api/usage/token"
        req = urllib.request.Request(balance_url)
        req.add_header("Authorization", f"Bearer {api_key}")
        req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                response_data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            raise Exception(f"NewAPI 查询失败: {e.code} - {error_body}")
        except Exception as e:
            raise Exception(f"NewAPI 请求失败: {str(e)}")

        # 解析 NewAPI 响应
        if not response_data.get("code") or "data" not in response_data:
            raise Exception("NewAPI 响应格式不正确")

        usage_data = response_data["data"]

        # NewAPI 返回的是积分，需要转换为美元
        # 转换比例: 500,000 积分 = $1
        CONVERSION_RATE = 500000.0

        total_granted_points = usage_data.get("total_granted", 0)
        total_used_points = usage_data.get("total_used", 0)
        total_available_points = usage_data.get("total_available", 0)

        # 转换为美元
        total_balance = total_granted_points / CONVERSION_RATE
        used_balance = total_used_points / CONVERSION_RATE
        remaining_balance = total_available_points / CONVERSION_RATE

        # 判断是否为无限额度
        is_unlimited = usage_data.get("unlimited_quota", False)

        return {
            "api_type": "newapi",
            "token_name": usage_data.get("name", ""),
            "total_balance": total_balance,
            "used_balance": used_balance,
            "remaining_balance": remaining_balance,
            "is_unlimited": is_unlimited,
            "access_until": usage_data.get("expires_at", 0),
            "query_start_date": "",
            "query_end_date": "",
        }

    def _query_openai_usage(self, base_url: str, api_key: str) -> Dict[str, Any]:
        """查询 OpenAI API 用量"""
        import json
        from datetime import datetime, timedelta

        # 规范化 base_url - 移除末尾斜杠
        base_url = base_url.rstrip("/")

        # 智能处理 /v1 路径 - 如果已经包含 /v1，就不再添加
        if base_url.endswith("/v1"):
            api_base = base_url
        else:
            api_base = f"{base_url}/v1"

        # 1. 查询订阅信息
        subscription_url = f"{api_base}/dashboard/billing/subscription"
        req = urllib.request.Request(subscription_url)
        req.add_header("Authorization", f"Bearer {api_key}")
        req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                subscription_data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            raise Exception(f"订阅信息查询失败: {e.code} - {error_body}")
        except Exception as e:
            raise Exception(f"请求订阅信息失败: {str(e)}")

        total_balance = subscription_data.get("hard_limit_usd", 0.0)
        access_until = subscription_data.get("access_until", 0)
        is_unlimited = total_balance >= 100000000.0

        # 2. 查询使用情况（最近100天）
        now = datetime.now()
        start = now - timedelta(days=100)
        start_date = start.strftime("%Y-%m-%d")
        end_date = now.strftime("%Y-%m-%d")

        usage_url = f"{api_base}/dashboard/billing/usage?start_date={start_date}&end_date={end_date}"
        req = urllib.request.Request(usage_url)
        req.add_header("Authorization", f"Bearer {api_key}")
        req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                usage_data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            raise Exception(f"使用情况查询失败: {e.code} - {error_body}")
        except Exception as e:
            raise Exception(f"请求使用情况失败: {str(e)}")

        # total_usage 是以美分为单位，需要除以100转换为美元
        total_usage_cents = usage_data.get("total_usage", 0.0)
        used_balance = total_usage_cents / 100.0

        # 计算剩余额度
        remaining_balance = (
            float("inf") if is_unlimited else (total_balance - used_balance)
        )

        return {
            "api_type": "openai",
            "token_name": "",
            "total_balance": total_balance,
            "used_balance": used_balance,
            "remaining_balance": remaining_balance,
            "is_unlimited": is_unlimited,
            "access_until": access_until,
            "query_start_date": start_date,
            "query_end_date": end_date,
        }

        # 1. 查询订阅信息
        subscription_url = f"{api_base}/dashboard/billing/subscription"
        req = urllib.request.Request(subscription_url)
        req.add_header("Authorization", f"Bearer {api_key}")
        req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                subscription_data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            raise Exception(f"订阅信息查询失败: {e.code} - {error_body}")
        except Exception as e:
            raise Exception(f"请求订阅信息失败: {str(e)}")

        total_balance = subscription_data.get("hard_limit_usd", 0.0)
        access_until = subscription_data.get("access_until", 0)
        is_unlimited = total_balance >= 100000000.0

        # 2. 查询使用情况（最近100天）
        now = datetime.now()
        start = now - timedelta(days=100)
        start_date = start.strftime("%Y-%m-%d")
        end_date = now.strftime("%Y-%m-%d")

        usage_url = f"{api_base}/dashboard/billing/usage?start_date={start_date}&end_date={end_date}"
        req = urllib.request.Request(usage_url)
        req.add_header("Authorization", f"Bearer {api_key}")
        req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                usage_data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            raise Exception(f"使用情况查询失败: {e.code} - {error_body}")
        except Exception as e:
            raise Exception(f"请求使用情况失败: {str(e)}")

        # total_usage 是以美分为单位，需要除以100转换为美元
        total_usage_cents = usage_data.get("total_usage", 0.0)
        used_balance = total_usage_cents / 100.0

        # 计算剩余额度
        remaining_balance = (
            float("inf") if is_unlimited else (total_balance - used_balance)
        )

        return {
            "total_balance": total_balance,
            "used_balance": used_balance,
            "remaining_balance": remaining_balance,
            "is_unlimited": is_unlimited,
            "access_until": access_until,
            "query_start_date": start_date,
            "query_end_date": end_date,
        }

    @pyqtSlot(str, object, str, object)
    def _show_balance_result(
        self,
        provider_name: str,
        usage_data: Dict[str, Any],
        api_key: str,
        state_tooltip,
    ):
        """显示余额查询结果"""
        state_tooltip.setContent(tr("provider.query_complete"))
        state_tooltip.setState(True)
        state_tooltip.close()

        # 创建结果对话框
        dialog = BalanceResultDialog(provider_name, usage_data, api_key, self)
        dialog.exec_()

    @pyqtSlot(str, object)
    def _show_balance_error(self, error_msg: str, state_tooltip):
        """显示余额查询错误"""
        state_tooltip.setContent(tr("provider.query_failed"))
        state_tooltip.setState(False)
        state_tooltip.close()

        self.show_error(
            tr("common.error"), tr("provider.query_balance_error", error=error_msg)
        )


class BalanceResultDialog(BaseDialog):
    """余额查询结果对话框"""

    def __init__(
        self,
        provider_name: str,
        usage_data: Dict[str, Any],
        api_key: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self.provider_name = provider_name
        self.usage_data = usage_data
        self.api_key = api_key
        self.setWindowTitle(tr("provider.balance_info"))
        self.setMinimumSize(500, 400)
        self._setup_ui()

    def _mask_api_key(self, api_key: str) -> str:
        """遮挡 API Key 中间部分"""
        if not api_key or len(api_key) < 10:
            return "***"
        # 显示前4个字符和后4个字符，中间用 *** 代替
        return f"{api_key[:4]}***{api_key[-4:]}"

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # 标题
        title = TitleLabel(tr("provider.balance_info"), self)
        layout.addWidget(title)

        # Provider 名称和 Key
        provider_key_layout = QHBoxLayout()
        provider_label = BodyLabel(
            f"{tr('provider.provider_name')}: {self.provider_name}", self
        )
        provider_key_layout.addWidget(provider_label)

        # 显示遮挡的 API Key
        if self.api_key:
            masked_key = self._mask_api_key(self.api_key)
            key_label = CaptionLabel(f"Key: {masked_key}", self)
            key_label.setStyleSheet("color: #888888; margin-left: 10px;")
            provider_key_layout.addWidget(key_label)

        provider_key_layout.addStretch()
        layout.addLayout(provider_key_layout)

        # API 类型（如果是 NewAPI）
        api_type = self.usage_data.get("api_type", "openai")
        if api_type == "newapi":
            api_type_label = CaptionLabel(f"API 类型: NewAPI / One-API", self)
            api_type_label.setStyleSheet("color: #888888;")
            layout.addWidget(api_type_label)

            # Token 名称
            token_name = self.usage_data.get("token_name", "")
            if token_name:
                token_label = CaptionLabel(f"Token 名称: {token_name}", self)
                token_label.setStyleSheet("color: #888888;")
                layout.addWidget(token_label)

        # 余额信息卡片
        card = QWidget(self)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(16)

        # 判断是否为无限额度
        is_unlimited = self.usage_data.get("is_unlimited", False)

        # ========== Key 额度信息区域 ==========
        quota_section = QWidget(self)
        quota_layout = QVBoxLayout(quota_section)
        quota_layout.setSpacing(8)
        quota_layout.setContentsMargins(0, 0, 0, 0)

        # 区域标题
        quota_title = StrongBodyLabel(tr("provider.key_quota_info"), self)
        quota_layout.addWidget(quota_title)

        # Key 额度
        key_quota_layout = QHBoxLayout()
        key_quota_layout.addWidget(BodyLabel(tr("provider.key_quota") + ":", self))
        if is_unlimited:
            key_quota_value = BodyLabel("🔓 无限", self)
            key_quota_value.setStyleSheet(
                "font-weight: bold; color: #107c10; font-size: 15px;"
            )
        else:
            key_quota_value = BodyLabel(
                self._format_currency(self.usage_data["total_balance"]), self
            )
            key_quota_value.setStyleSheet(
                "font-weight: bold; color: #0078d4; font-size: 15px;"
            )
        key_quota_layout.addWidget(key_quota_value)
        key_quota_layout.addStretch()
        quota_layout.addLayout(key_quota_layout)

        # Key 余额
        key_balance_layout = QHBoxLayout()
        key_balance_layout.addWidget(BodyLabel(tr("provider.key_balance") + ":", self))
        if is_unlimited:
            key_balance_value = BodyLabel("🔓 无限", self)
            key_balance_value.setStyleSheet(
                "font-weight: bold; color: #107c10; font-size: 15px;"
            )
        else:
            remaining = self.usage_data["remaining_balance"]
            key_balance_value = BodyLabel(self._format_currency(remaining), self)
            color = "#107c10" if remaining > 10 else "#d13438"
            key_balance_value.setStyleSheet(
                f"font-weight: bold; color: {color}; font-size: 15px;"
            )
        key_balance_layout.addWidget(key_balance_value)
        key_balance_layout.addStretch()
        quota_layout.addLayout(key_balance_layout)

        card_layout.addWidget(quota_section)

        # 分隔线
        separator1 = QWidget(self)
        separator1.setFixedHeight(1)
        separator1.setStyleSheet("background-color: #e0e0e0;")
        card_layout.addWidget(separator1)

        # ========== 使用详情区域 ==========
        usage_section = QWidget(self)
        usage_layout = QVBoxLayout(usage_section)
        usage_layout.setSpacing(8)
        usage_layout.setContentsMargins(0, 0, 0, 0)

        # 区域标题
        usage_title = StrongBodyLabel(tr("provider.usage_details"), self)
        usage_layout.addWidget(usage_title)

        # 已使用
        used_layout = QHBoxLayout()
        used_layout.addWidget(BodyLabel(tr("provider.used") + ":", self))
        used_value = BodyLabel(
            self._format_currency(self.usage_data["used_balance"]), self
        )
        used_value.setStyleSheet("font-weight: bold; color: #d13438;")
        used_layout.addWidget(used_value)
        used_layout.addStretch()
        usage_layout.addLayout(used_layout)

        # 使用率（仅对有限额度显示）
        if not is_unlimited and self.usage_data["total_balance"] > 0:
            usage_rate = (
                self.usage_data["used_balance"] / self.usage_data["total_balance"]
            ) * 100
            usage_rate_layout = QHBoxLayout()
            usage_rate_layout.addWidget(
                BodyLabel(tr("provider.usage_rate") + ":", self)
            )
            usage_rate_value = BodyLabel(f"{usage_rate:.2f}%", self)
            usage_rate_value.setStyleSheet("font-weight: bold; color: #888888;")
            usage_rate_layout.addWidget(usage_rate_value)
            usage_rate_layout.addStretch()
            usage_layout.addLayout(usage_rate_layout)

        card_layout.addWidget(usage_section)

        # 分隔线
        separator2 = QWidget(self)
        separator2.setFixedHeight(1)
        separator2.setStyleSheet("background-color: #e0e0e0;")
        card_layout.addWidget(separator2)

        # ========== 其他信息区域 ==========
        other_section = QWidget(self)
        other_layout = QVBoxLayout(other_section)
        other_layout.setSpacing(8)
        other_layout.setContentsMargins(0, 0, 0, 0)

        # 有效期
        if self.usage_data["access_until"] > 0:
            expiry_layout = QHBoxLayout()
            expiry_layout.addWidget(BodyLabel(tr("provider.access_until") + ":", self))
            expiry_date = datetime.fromtimestamp(self.usage_data["access_until"])
            expiry_value = BodyLabel(expiry_date.strftime("%Y-%m-%d %H:%M:%S"), self)
            expiry_layout.addWidget(expiry_value)
            expiry_layout.addStretch()
            other_layout.addLayout(expiry_layout)
        else:
            # 永不过期
            expiry_layout = QHBoxLayout()
            expiry_layout.addWidget(BodyLabel(tr("provider.expiry") + ":", self))
            expiry_value = BodyLabel(tr("provider.never_expire"), self)
            expiry_value.setStyleSheet("color: #107c10;")
            expiry_layout.addWidget(expiry_value)
            expiry_layout.addStretch()
            other_layout.addLayout(expiry_layout)

        # 查询时间范围（仅对 OpenAI API 显示）
        if api_type == "openai" and self.usage_data["query_start_date"]:
            date_range_layout = QHBoxLayout()
            date_range_layout.addWidget(
                BodyLabel(tr("provider.query_period") + ":", self)
            )
            date_range_value = CaptionLabel(
                f"{self.usage_data['query_start_date']} ~ {self.usage_data['query_end_date']}",
                self,
            )
            date_range_layout.addWidget(date_range_value)
            date_range_layout.addStretch()
            other_layout.addLayout(date_range_layout)

        card_layout.addWidget(other_section)

        # 添加说明文本
        note_label = CaptionLabel(
            tr("provider.balance_note"),
            self,
        )
        note_label.setStyleSheet("color: #888888; font-style: italic;")
        card_layout.addWidget(note_label)

        layout.addWidget(card)
        layout.addStretch()

        # 关闭按钮
        close_btn = PrimaryPushButton(tr("common.close"), self)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _format_currency(self, value: float) -> str:
        """格式化货币"""
        if value == float("inf"):
            return tr("provider.unlimited")
        return f"${value:.2f}"


class ModelPresetCustomDialog(BaseDialog):
    """模型配置包自定义弹窗"""

    def __init__(self, category: str, preset_name: str = "", parent=None):
        super().__init__(parent)
        self.category = category
        self.preset_name = preset_name
        self._preset: Dict[str, Any] = {}

        self.setWindowTitle(tr("provider.custom_preset"))
        self.setMinimumSize(560, 420)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        layout.addWidget(TitleLabel(tr("provider.custom_preset"), self))
        layout.addWidget(BodyLabel(tr("provider.category") + " " + self.category, self))

        name_layout = QHBoxLayout()
        name_layout.addWidget(BodyLabel(tr("provider.custom_preset_name"), self))
        self.name_edit = LineEdit(self)
        self.name_edit.setPlaceholderText(tr("provider.custom_preset_placeholder"))
        if self.preset_name:
            self.name_edit.setText(self.preset_name)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        layout.addWidget(
            BodyLabel(
                tr("provider.custom_preset_config"),
                self,
            )
        )
        self.config_edit = PlainTextEdit(self)
        self.config_edit.setPlaceholderText(
            tr("provider.custom_preset_json_placeholder")
        )
        self.config_edit.setPlainText(
            json.dumps(
                {
                    "attachment": False,
                    "modalities": {"input": ["text"], "output": ["text"]},
                    "limit": {"context": 200000, "output": 16000},
                    "options": {},
                    "variants": {},
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        layout.addWidget(self.config_edit, 1)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.save_btn = PrimaryPushButton(tr("common.save"), self)
        self.save_btn.clicked.connect(self._on_add)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)

        # 初始化
        self._on_series_changed(self.series_combo.currentText())

    def _on_series_changed(self, series: str):
        self.model_list.clear()
        # 将显示名称转换回原始键
        original_key = self._series_map.get(series, series)
        if original_key in PRESET_MODEL_CONFIGS:
            models = PRESET_MODEL_CONFIGS[original_key]["models"]
            for model_id, data in models.items():
                self.model_list.addItem(f"{model_id} - {data.get('name', '')}")

    def _on_add(self):
        selected = self.model_list.selectedItems()
        if not selected:
            InfoBar.warning(
                tr("common.hint"), tr("dialog.select_at_least_one_model"), parent=self
            )
            return

        series = self.series_combo.currentText()
        # 将显示名称转换回原始键
        original_key = self._series_map.get(series, series)
        series_data = PRESET_MODEL_CONFIGS.get(original_key, {})
        models_data = series_data.get("models", {})

        config = self.main_window.opencode_config
        if config is None:
            config = {}
            self.main_window.opencode_config = config

        if "provider" not in config:
            config["provider"] = {}

        # 验证 Provider 是否存在且结构完整
        if self.provider_name not in config["provider"]:
            InfoBar.error(
                "错误",
                f'Provider "{self.provider_name}" 不存在，请先在 Provider 管理页面创建',
                parent=self,
            )
            return

        provider = config["provider"][self.provider_name]

        # 检查 Provider 结构是否完整
        if "npm" not in provider or "options" not in provider:
            InfoBar.error(
                "错误",
                f'Provider "{self.provider_name}" 配置不完整，请先在 Provider 管理页面完善配置',
                parent=self,
            )
            return

        # 确保 models 字段存在
        if "models" not in provider:
            provider["models"] = {}

        models = provider["models"]
        added = 0

        for item in selected:
            model_id = item.text().split(" - ")[0]
            if model_id in models_data:
                preset = models_data[model_id]
                models[model_id] = {
                    "name": preset.get("name", ""),
                    "attachment": preset.get("attachment", False),
                    "limit": preset.get("limit", {}),
                    "options": preset.get("options", {}),
                    "variants": preset.get("variants", {}),
                }
                added += 1

        self.main_window.save_opencode_config()
        InfoBar.success(
            tr("common.success"), tr("dialog.models_added", count=added), parent=self
        )
        self.accept()


# ==================== MCP 页面 ====================
class NativeProviderPage(BasePage):
    """原生 Provider 配置页面 - 管理 OpenCode 官方支持的原生 AI 服务提供商"""

    def __init__(self, main_window, parent=None):
        super().__init__(tr("native_provider.title"), parent)
        self.main_window = main_window
        self.auth_manager = AuthManager()
        self.env_detector = EnvVarDetector()
        self._setup_ui()
        self._load_data()
        # 连接配置变更信号
        self.main_window.config_changed.connect(self._on_config_changed)

    def _on_config_changed(self):
        """配置变更时刷新列表"""
        self._load_data()

    def _setup_ui(self):
        """初始化 UI 布局"""
        # 工具栏
        toolbar = QHBoxLayout()

        self.config_btn = PrimaryPushButton(
            FIF.SETTING, tr("native_provider.config_provider"), self
        )
        self.config_btn.clicked.connect(self._on_config)
        toolbar.addWidget(self.config_btn)

        self.test_btn = PushButton(
            FIF.WIFI, tr("native_provider.test_connection"), self
        )
        self.test_btn.clicked.connect(self._on_test)
        toolbar.addWidget(self.test_btn)

        self.delete_btn = PushButton(
            FIF.DELETE, tr("native_provider.delete_config"), self
        )
        self.delete_btn.clicked.connect(self._on_delete)
        toolbar.addWidget(self.delete_btn)

        self.query_balance_btn = PushButton(
            FIF.MARKET, tr("provider.query_balance"), self
        )
        self.query_balance_btn.clicked.connect(self._on_query_balance)
        toolbar.addWidget(self.query_balance_btn)

        toolbar.addStretch()
        self._layout.addLayout(toolbar)

        # Provider 列表表格
        self.table = TableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            [
                "Provider",
                "SDK",
                tr("native_provider.status"),
                tr("native_provider.env_vars"),
            ]
        )

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.resizeSection(0, 160)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.resizeSection(2, 80)
        header.setSectionResizeMode(3, QHeaderView.Stretch)

        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.doubleClicked.connect(self._on_config)
        self._layout.addWidget(self.table)

    def _load_data(self):
        """加载 Provider 数据"""
        self.table.setRowCount(0)

        # 读取已配置的认证
        auth_data = {}
        try:
            auth_data = self.auth_manager.read_auth()
        except Exception:
            pass

        for provider in NATIVE_PROVIDERS:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Provider 名称
            name_item = QTableWidgetItem(provider.name)
            name_item.setData(Qt.UserRole, provider.id)
            self.table.setItem(row, 0, name_item)

            # SDK
            self.table.setItem(row, 1, QTableWidgetItem(provider.sdk))

            # 状态
            is_configured = provider.id in auth_data and auth_data[provider.id]
            status_text = (
                tr("native_provider.configured")
                if is_configured
                else tr("native_provider.not_configured")
            )
            status_item = QTableWidgetItem(status_text)
            if is_configured:
                status_item.setForeground(QColor("#4CAF50"))
            else:
                status_item.setForeground(QColor("#9E9E9E"))
            self.table.setItem(row, 2, status_item)

            # 环境变量
            env_vars = ", ".join(provider.env_vars) if provider.env_vars else "-"
            env_item = QTableWidgetItem(env_vars)
            env_item.setToolTip(env_vars)
            self.table.setItem(row, 3, env_item)

    def _get_selected_provider(self) -> Optional[NativeProviderConfig]:
        """获取当前选中的 Provider"""
        row = self.table.currentRow()
        if row < 0:
            return None
        provider_id = self.table.item(row, 0).data(Qt.UserRole)
        return get_native_provider(provider_id)

    def _on_config(self):
        """配置 Provider"""
        provider = self._get_selected_provider()
        if not provider:
            self.show_warning(
                tr("common.info"), tr("common.please_select_first", item="Provider")
            )
            return

        dialog = NativeProviderDialog(
            self.main_window,
            provider,
            self.auth_manager,
            self.env_detector,
            parent=self,
        )
        if dialog.exec_():
            self._load_data()
            self.show_success(
                tr("common.success"),
                tr("native_provider.config_saved", name=provider.name),
            )

    def _on_test(self):
        """测试连接"""
        provider = self._get_selected_provider()
        if not provider:
            self.show_warning(
                tr("common.info"), tr("common.please_select_first", item="Provider")
            )
            return

        if not provider.test_endpoint:
            self.show_warning(
                tr("common.info"), tr("native_provider.test_not_supported")
            )
            return

        # 获取认证信息
        auth_data = self.auth_manager.get_provider_auth(provider.id)
        if not auth_data:
            self.show_error(
                tr("provider.test_failed"), tr("provider.please_configure_provider")
            )
            return

        api_key = auth_data.get("apiKey", "")
        if api_key:
            api_key = _resolve_env_value(api_key)

        if not api_key:
            self.show_error(
                tr("provider.test_failed"), tr("provider.api_key_not_found")
            )
            return

        # 获取 baseURL
        config = self.main_window.opencode_config or {}
        provider_options = (
            config.get("provider", {}).get(provider.id, {}).get("options", {})
        )
        base_url = provider_options.get("baseURL", "")

        if not base_url:
            default_urls = {
                "anthropic": "https://api.anthropic.com",
                "openai": "https://api.openai.com",
                "gemini": "https://generativelanguage.googleapis.com",
                "xai": "https://api.x.ai",
                "groq": "https://api.groq.com",
                "openrouter": "https://openrouter.ai/api",
                "deepseek": "https://api.deepseek.com",
                "opencode": "https://api.opencode.ai",
            }
            base_url = default_urls.get(provider.id, "")

        if not base_url:
            self.show_error(
                tr("provider.test_failed"), tr("provider.cannot_determine_api_address")
            )
            return

        test_url = base_url.rstrip("/") + provider.test_endpoint

        # 执行测试
        self.show_warning("测试中", "正在测试连接...")

        start_time = time.time()
        try:
            req = urllib.request.Request(test_url)
            req.add_header("Authorization", f"Bearer {api_key}")
            req.add_header("x-api-key", api_key)
            with urllib.request.urlopen(req, timeout=10) as resp:
                elapsed = int((time.time() - start_time) * 1000)
                self.show_success(
                    tr("provider.connection_success"),
                    f"{tr('provider.response_time')}: {elapsed}ms",
                )
        except urllib.error.HTTPError as e:
            self.show_error(
                tr("provider.connection_failed"), f"HTTP {e.code}: {e.reason}"
            )
        except Exception as e:
            self.show_error(tr("provider.connection_failed"), str(e))

    def _on_delete(self):
        """删除配置"""
        provider = self._get_selected_provider()
        if not provider:
            self.show_warning(
                tr("common.info"), tr("common.please_select_first", item="Provider")
            )
            return

        # 检查是否已配置
        auth_data = self.auth_manager.get_provider_auth(provider.id)
        if not auth_data:
            self.show_warning(
                tr("common.info"), tr("native_provider.provider_not_configured")
            )
            return

        # 确认删除
        msg_box = FluentMessageBox(
            "确认删除",
            f"确定要删除 {provider.name} 的配置吗？\n这将删除认证信息和选项配置。",
            self,
        )
        if msg_box.exec_() != QMessageBox.Yes:
            return

        # 删除认证
        try:
            self.auth_manager.delete_provider_auth(provider.id)
        except Exception as e:
            self.show_error("删除失败", f"无法删除认证配置: {e}")
            return

        # 删除选项
        config = self.main_window.opencode_config or {}
        if "provider" in config and provider.id in config["provider"]:
            if "options" in config["provider"][provider.id]:
                del config["provider"][provider.id]["options"]
                if not config["provider"][provider.id]:
                    del config["provider"][provider.id]
                self.main_window.opencode_config = config
                self.main_window.save_opencode_config()

        self.show_success("删除成功", f"{provider.name} 配置已删除")
        self._load_data()

    def _on_query_balance(self):
        """查询余额"""
        provider = self._get_selected_provider()
        if not provider:
            self.show_warning(
                tr("common.info"), tr("common.please_select_first", item="Provider")
            )
            return

        # 获取认证信息
        auth_data = self.auth_manager.get_provider_auth(provider.id)
        if not auth_data:
            self.show_warning(
                tr("common.info"), tr("native_provider.provider_not_configured")
            )
            return

        # 获取 API Key
        api_key = auth_data.get("apiKey", "")
        if not api_key:
            self.show_warning(tr("common.info"), tr("provider.no_api_key"))
            return

        # 获取 baseURL
        config = self.main_window.opencode_config or {}
        provider_config = config.get("provider", {}).get(provider.id, {})
        options = provider_config.get("options", {})
        base_url = options.get("baseURL", provider.default_base_url)

        if not base_url:
            self.show_warning(tr("common.info"), tr("provider.no_base_url"))
            return

        # 显示加载提示
        state_tooltip = StateToolTip(
            tr("provider.querying_balance"), tr("provider.please_wait"), self.window()
        )
        state_tooltip.move(state_tooltip.getSuitablePos())
        state_tooltip.show()

        # 在后台线程查询余额
        def query_thread():
            try:
                usage_data = self._query_provider_usage(base_url, api_key)
                # 在主线程显示结果
                QMetaObject.invokeMethod(
                    self,
                    "_show_balance_result",
                    Qt.QueuedConnection,
                    Q_ARG(str, provider.name),
                    Q_ARG(object, usage_data),
                    Q_ARG(object, state_tooltip),
                )
            except Exception as e:
                # 在主线程显示错误
                QMetaObject.invokeMethod(
                    self,
                    "_show_balance_error",
                    Qt.QueuedConnection,
                    Q_ARG(str, str(e)),
                    Q_ARG(object, state_tooltip),
                )

        thread = threading.Thread(target=query_thread, daemon=True)
        thread.start()

    def _query_provider_usage(self, base_url: str, api_key: str) -> Dict[str, Any]:
        """查询 Provider 用量（支持 OpenAI API 和 NewAPI）"""
        import json
        from datetime import datetime, timedelta

        # 规范化 base_url - 移除末尾斜杠
        base_url = base_url.rstrip("/")

        # 先尝试 NewAPI 接口
        try:
            return self._query_newapi_usage(base_url, api_key)
        except Exception as newapi_error:
            # NewAPI 失败，尝试 OpenAI API
            pass

        # 尝试 OpenAI API 接口
        try:
            return self._query_openai_usage(base_url, api_key)
        except Exception as openai_error:
            # 两种方式都失败，抛出错误
            raise Exception(
                f"余额查询失败。NewAPI: {str(newapi_error)[:50]}... OpenAI API: {str(openai_error)[:50]}..."
            )

    def _query_newapi_usage(self, base_url: str, api_key: str) -> Dict[str, Any]:
        """查询 NewAPI 用量"""
        import json

        # NewAPI 余额查询端点
        balance_url = f"{base_url}/api/usage/token"
        req = urllib.request.Request(balance_url)
        req.add_header("Authorization", f"Bearer {api_key}")
        req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                response_data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            raise Exception(f"NewAPI 查询失败: {e.code} - {error_body}")
        except Exception as e:
            raise Exception(f"NewAPI 请求失败: {str(e)}")

        # 解析 NewAPI 响应
        if not response_data.get("code") or "data" not in response_data:
            raise Exception("NewAPI 响应格式不正确")

        usage_data = response_data["data"]

        # NewAPI 返回的是积分，需要转换为美元
        # 转换比例: 500,000 积分 = $1
        CONVERSION_RATE = 500000.0

        total_granted_points = usage_data.get("total_granted", 0)
        total_used_points = usage_data.get("total_used", 0)
        total_available_points = usage_data.get("total_available", 0)

        # 转换为美元
        total_balance = total_granted_points / CONVERSION_RATE
        used_balance = total_used_points / CONVERSION_RATE
        remaining_balance = total_available_points / CONVERSION_RATE

        # 判断是否为无限额度
        is_unlimited = usage_data.get("unlimited_quota", False)

        return {
            "api_type": "newapi",
            "token_name": usage_data.get("name", ""),
            "total_balance": total_balance,
            "used_balance": used_balance,
            "remaining_balance": remaining_balance,
            "is_unlimited": is_unlimited,
            "access_until": usage_data.get("expires_at", 0),
            "query_start_date": "",
            "query_end_date": "",
        }

    def _query_openai_usage(self, base_url: str, api_key: str) -> Dict[str, Any]:
        """查询 OpenAI API 用量"""
        import json
        from datetime import datetime, timedelta

        # 智能处理 /v1 路径 - 如果已经包含 /v1，就不再添加
        if base_url.endswith("/v1"):
            api_base = base_url
        else:
            api_base = f"{base_url}/v1"

        # 1. 查询订阅信息
        subscription_url = f"{api_base}/dashboard/billing/subscription"
        req = urllib.request.Request(subscription_url)
        req.add_header("Authorization", f"Bearer {api_key}")
        req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                subscription_data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            raise Exception(f"订阅信息查询失败: {e.code} - {error_body}")
        except Exception as e:
            raise Exception(f"请求订阅信息失败: {str(e)}")

        total_balance = subscription_data.get("hard_limit_usd", 0.0)
        access_until = subscription_data.get("access_until", 0)
        is_unlimited = total_balance >= 100000000.0

        # 2. 查询使用情况（最近100天）
        now = datetime.now()
        start = now - timedelta(days=100)
        start_date = start.strftime("%Y-%m-%d")
        end_date = now.strftime("%Y-%m-%d")

        usage_url = f"{api_base}/dashboard/billing/usage?start_date={start_date}&end_date={end_date}"
        req = urllib.request.Request(usage_url)
        req.add_header("Authorization", f"Bearer {api_key}")
        req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                usage_data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            raise Exception(f"使用情况查询失败: {e.code} - {error_body}")
        except Exception as e:
            raise Exception(f"请求使用情况失败: {str(e)}")

        # total_usage 是以美分为单位，需要除以100转换为美元
        total_usage_cents = usage_data.get("total_usage", 0.0)
        used_balance = total_usage_cents / 100.0

        # 计算剩余额度
        remaining_balance = (
            float("inf") if is_unlimited else (total_balance - used_balance)
        )

        return {
            "api_type": "openai",
            "token_name": "",
            "total_balance": total_balance,
            "used_balance": used_balance,
            "remaining_balance": remaining_balance,
            "is_unlimited": is_unlimited,
            "access_until": access_until,
            "query_start_date": start_date,
            "query_end_date": end_date,
        }

    @pyqtSlot(str, object, str, object)
    def _show_balance_result(
        self,
        provider_name: str,
        usage_data: Dict[str, Any],
        api_key: str,
        state_tooltip,
    ):
        """显示余额查询结果"""
        state_tooltip.setContent(tr("provider.query_complete"))
        state_tooltip.setState(True)
        state_tooltip.close()

        # 创建结果对话框
        dialog = BalanceResultDialog(provider_name, usage_data, api_key, self)
        dialog.exec_()

    @pyqtSlot(str, object)
    def _show_balance_error(self, error_msg: str, state_tooltip):
        """显示余额查询错误"""
        state_tooltip.setContent(tr("provider.query_failed"))
        state_tooltip.setState(False)
        state_tooltip.close()

        self.show_error(
            tr("common.error"), tr("provider.query_balance_error", error=error_msg)
        )


class ModelSelectDialog(BaseDialog):
    """模型选择对话框"""

    def __init__(
        self, main_window, provider_name: str, model_ids: List[str], parent=None
    ):
        super().__init__(parent)
        self.main_window = main_window
        self.provider_name = provider_name
        self.model_ids = list(dict.fromkeys(model_ids or []))
        self._selected: List[str] = []
        self._items = []
        self._row_widgets: Dict[str, Dict[str, Any]] = {}
        self._visible_model_ids: List[str] = []
        self._bulk_controls: Dict[str, Dict[str, Any]] = {}
        self._batch_config: Dict[str, Any] = {}

        self.setWindowTitle(tr("provider.model_select_title"))
        self.setMinimumSize(900, 560)
        self._setup_ui()
        self._load_categories()
        self._refresh_models()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        layout.addWidget(TitleLabel(tr("provider.model_select_title"), self))
        layout.addWidget(BodyLabel(tr("provider.model_list_hint"), self))

        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(8)

        filter_layout.addWidget(BodyLabel(tr("provider.group_mode"), self))
        self.group_mode_combo = ComboBox(self)
        self.group_mode_combo.addItems(
            [
                tr("provider.group_vendor"),
                tr("provider.group_prefix"),
                tr("provider.group_letter"),
            ]
        )
        self.group_mode_combo.currentTextChanged.connect(self._on_group_mode_changed)
        filter_layout.addWidget(self.group_mode_combo)

        filter_layout.addWidget(BodyLabel(tr("provider.filter_mode"), self))
        self.match_mode_combo = ComboBox(self)
        self.match_mode_combo.addItems(
            [
                tr("provider.filter_contains"),
                tr("provider.filter_prefix"),
                tr("provider.filter_regex"),
            ]
        )
        self.match_mode_combo.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.match_mode_combo)

        self.keyword_edit = LineEdit(self)
        self.keyword_edit.setPlaceholderText(tr("provider.keyword_filter"))
        self.keyword_edit.textChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.keyword_edit, 1)

        self.clear_btn = PushButton(tr("provider.clear_filter"), self)
        self.clear_btn.clicked.connect(self._clear_filters)
        filter_layout.addWidget(self.clear_btn)

        layout.addLayout(filter_layout)

        self.batch_layout = QHBoxLayout()
        self.batch_layout.setSpacing(8)
        self.batch_layout.addWidget(BodyLabel(tr("provider.batch_config") + ":", self))
        layout.addLayout(self.batch_layout)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(12)

        self.category_list = ListWidget(self)
        self.category_list.setFixedWidth(200)
        self.category_list.currentTextChanged.connect(self._on_category_list_changed)
        content_layout.addWidget(self.category_list)

        self.model_list = ListWidget(self)
        self.model_list.setSpacing(6)
        self.model_list.setUniformItemSizes(True)
        self.model_list.setSelectionMode(QAbstractItemView.NoSelection)
        content_layout.addWidget(self.model_list, 1)

        layout.addLayout(content_layout, 1)

        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(8)

        self.select_all_check = CheckBox(tr("common.select_all"), self)
        self.select_all_check.stateChanged.connect(self._on_select_all_changed)
        self.select_all_check.setTristate(False)
        footer_layout.addWidget(self.select_all_check)

        self.count_label = CaptionLabel(
            tr("provider.selected_count", selected=0, total=0), self
        )
        footer_layout.addWidget(self.count_label)

        self.empty_label = CaptionLabel(tr("provider.no_models_to_add"), self)
        self.empty_label.setVisible(False)
        footer_layout.addWidget(self.empty_label)

        footer_layout.addStretch()

        self.cancel_btn = PushButton(tr("common.cancel"), self)
        self.cancel_btn.clicked.connect(self.reject)
        footer_layout.addWidget(self.cancel_btn)

        self.confirm_btn = PrimaryPushButton(tr("provider.add_selected"), self)
        self.confirm_btn.clicked.connect(self._on_confirm)
        footer_layout.addWidget(self.confirm_btn)

        layout.addLayout(footer_layout)

    def _build_batch_controls(self):
        self._batch_config = {}
        self._bulk_controls = {}
        while self.batch_layout.count() > 1:
            item = self.batch_layout.takeAt(1)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)

    def _load_categories(self):
        self._rebuild_categories()
        self._build_batch_controls()
        self._add_batch_control("attachment", tr("provider.attachment"), [])
        self._add_batch_control("modalities", tr("provider.image"), [])
        self._add_batch_control(
            "limit", tr("provider.output_length"), ["4k", "8k", "16k", "32k", "64k"]
        )
        self._add_batch_control(
            "options", "Options", ["fast", "medium", "high", "xhigh"]
        )
        self._add_batch_control("thinking", "Thinking", ["8k", "16k", "32k", "64k"])
        self._add_batch_control("variants", "Variants", ["high/medium/low", "high/low"])

    def _add_batch_control(
        self,
        key: str,
        label: str,
        choices: List[str],
    ):
        container = QWidget(self)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        checkbox = CheckBox(label, container)
        checkbox.stateChanged.connect(
            lambda state, k=key: self._on_batch_check_changed(k, state)
        )
        layout.addWidget(checkbox)

        combo = None
        if choices:
            combo = ComboBox(container)
            combo.addItems(choices)
            combo.currentTextChanged.connect(
                lambda text, k=key: self._on_batch_combo_changed(k, text)
            )
            metrics = QFontMetrics(combo.font())
            max_text_width = max(metrics.horizontalAdvance(text) for text in choices)
            combo.setMinimumWidth(max_text_width + 18)
            layout.addWidget(combo)

        self.batch_layout.addWidget(container)
        self._bulk_controls[key] = {
            "container": container,
            "checkbox": checkbox,
            "combo": combo,
        }
        self._batch_config[key] = {"enabled": False, "value": None}

    def _on_batch_check_changed(self, key: str, state: int):
        config = self._batch_config.get(key)
        if config is None:
            return
        config["enabled"] = state == Qt.Checked

    def _on_batch_combo_changed(self, key: str, text: str):
        config = self._batch_config.get(key)
        if config is None:
            return
        config["value"] = text

    def _on_group_mode_changed(self):
        self._rebuild_categories()
        self._refresh_models()

    def _on_category_list_changed(self, text: str):
        self._refresh_models()
        self._update_batch_controls()

    def _on_filter_changed(self):
        self._refresh_models()

    def _clear_filters(self):
        self.group_mode_combo.setCurrentIndex(0)
        self.match_mode_combo.setCurrentIndex(0)
        self.keyword_edit.clear()

    def _rebuild_categories(self):
        self.category_list.blockSignals(True)
        self.category_list.clear()
        self.category_list.addItem(tr("provider.all_categories"))

        groups = self._group_models()
        for group in sorted(groups.keys(), key=str.lower):
            if group != tr("provider.all_categories"):
                self.category_list.addItem(group)

        self.category_list.setCurrentRow(0)
        self.category_list.blockSignals(False)

    def _group_models(self) -> Dict[str, List[str]]:
        mode = self.group_mode_combo.currentText()
        groups: Dict[str, List[str]] = {}
        for model_id in self.model_ids:
            key = self._get_group_key(model_id, mode)
            groups.setdefault(key, []).append(model_id)
        return groups

    def _get_group_key(self, model_id: str, mode: str) -> str:
        lower = model_id.lower()
        if mode == "前缀分组":
            if "-" in model_id:
                return model_id.split("-", 1)[0]
            if "/" in model_id:
                return model_id.split("/", 1)[0]
            return model_id[:1].upper() if model_id else "其他"
        if mode == "首字母":
            return model_id[:1].upper() if model_id else "其他"
        # 厂商识别
        if "claude" in lower:
            return tr("provider.claude_series_short")
        if "gemini" in lower:
            return tr("provider.gemini_series_short")
        if any(token in lower for token in ("gpt", "openai", "codex", "o1")):
            return tr("provider.openai_series_short")
        return tr("provider.other_models_short")

    def _resolve_category_for_preset(self, model_id: str) -> str:
        return self._get_group_key(model_id, "厂商识别")

    def _refresh_preset_combo(self):
        return

    def _get_preset_names(self, category: str) -> List[str]:
        names = list(MODEL_PRESET_PACKS.get(category, {}).keys())
        names += list(MODEL_PRESET_CUSTOM.get(category, {}).keys())
        if not names:
            names.append("基础")
        return names

    def _get_default_preset_for_category(self, category: str) -> Dict[str, Any]:
        preset_name = MODEL_PRESET_DEFAULT.get(category, "基础")
        return self._get_preset(category, preset_name)

    def _get_bulk_category(self) -> str:
        if not self._visible_model_ids:
            return tr("provider.other_models_short")
        return self._resolve_category_for_preset(self._visible_model_ids[0])

    def _get_category_bulk_support(self, category: str) -> Dict[str, bool]:
        support = {
            "attachment": True,
            "modalities": True,
            "limit": True,
            "options": False,
            "thinking": False,
            "variants": False,
        }
        if category == tr("provider.claude_series_short"):
            support["thinking"] = True
            support["variants"] = True
        elif category == tr("provider.openai_series_short"):
            support["options"] = True
            support["variants"] = True
        elif category == tr("provider.gemini_series_short"):
            support["thinking"] = True
            support["variants"] = True
        return support

    def _update_batch_controls(self):
        if not self._bulk_controls:
            return
        category = self._get_bulk_category()
        support = self._get_category_bulk_support(category)
        for key, meta in self._bulk_controls.items():
            checkbox = meta.get("checkbox")
            combo = meta.get("combo")
            enabled = support.get(key, False)
            if checkbox is not None:
                checkbox.setEnabled(enabled)
                if not enabled:
                    checkbox.setChecked(False)
                    config = self._batch_config.get(key)
                    if config is not None:
                        config["enabled"] = False
            if combo is not None:
                combo.setEnabled(enabled)

    def _get_preset(self, category: str, preset_name: str) -> Dict[str, Any]:
        if preset_name in MODEL_PRESET_CUSTOM.get(category, {}):
            return MODEL_PRESET_CUSTOM[category][preset_name]
        presets = MODEL_PRESET_PACKS.get(category, {})
        if preset_name in presets:
            return presets[preset_name]
        return {
            "attachment": False,
            "modalities": {"input": ["text"], "output": ["text"]},
            "limit": {"context": 64000, "output": 8192},
            "options": {},
            "variants": {},
        }

    def _on_model_check_changed(self, model_id: str, state: int):
        if state == Qt.Checked:
            if model_id not in self._selected:
                self._selected.append(model_id)
        else:
            if model_id in self._selected:
                self._selected.remove(model_id)
        self._update_count_label()
        self._sync_select_all_state()

    def _toggle_model_check(self, model_id: str):
        row = self._row_widgets.get(model_id)
        if not row:
            return
        checkbox = row.get("checkbox")
        if checkbox is None:
            return
        checkbox.setChecked(not checkbox.isChecked())

    def _build_model_row(self, model_id: str):
        row_widget = QWidget(self.model_list)
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(6, 4, 6, 4)
        row_layout.setSpacing(8)

        check = CheckBox("", row_widget)
        check.setChecked(model_id in self._selected)
        check.stateChanged.connect(
            lambda state, mid=model_id: self._on_model_check_changed(mid, state)
        )
        row_layout.addWidget(check)

        name_label = BodyLabel(model_id, row_widget)
        name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        name_label.mousePressEvent = (
            lambda event, mid=model_id: self._toggle_model_check(mid)
        )
        row_layout.addWidget(name_label, 1)

        row_widget.mousePressEvent = (
            lambda event, mid=model_id: self._toggle_model_check(mid)
        )

        item = QListWidgetItem(self.model_list)
        item.setSizeHint(row_widget.sizeHint())
        self.model_list.setItemWidget(item, row_widget)

        self._row_widgets[model_id] = {
            "item": item,
            "checkbox": check,
        }
        self._items.append(model_id)

    def _refresh_models(self):
        self.model_list.blockSignals(True)
        self.model_list.clear()
        self._items = []
        self._visible_model_ids = []
        self._row_widgets = {}
        self.model_list.setFocusPolicy(Qt.NoFocus)

        group = (
            self.category_list.currentItem().text()
            if self.category_list.currentItem()
            else tr("provider.all_categories")
        )
        keyword = self.keyword_edit.text().strip()
        match_mode = self.match_mode_combo.currentText()
        pattern = keyword.lower()
        regex = None
        if pattern and match_mode == "正则":
            try:
                regex = re.compile(pattern, re.IGNORECASE)
            except re.error:
                regex = None

        for model_id in self.model_ids:
            if group != tr("provider.all_categories"):
                if (
                    self._get_group_key(model_id, self.group_mode_combo.currentText())
                    != group
                ):
                    continue
            if pattern:
                if match_mode == "包含":
                    if pattern not in model_id.lower():
                        continue
                elif match_mode == "前缀":
                    if not model_id.lower().startswith(pattern):
                        continue
                elif match_mode == "正则":
                    if not regex or not regex.search(model_id):
                        continue
            self._build_model_row(model_id)
            self._visible_model_ids.append(model_id)

        self.model_list.blockSignals(False)
        self._update_count_label()
        self._sync_select_all_state()
        self._update_batch_controls()

        if not self._items:
            self.empty_label.setVisible(True)
        else:
            self.empty_label.setVisible(False)

    def _on_select_all_changed(self, state):
        if not self._items:
            return
        target_state = state == Qt.Checked
        for model_id, row in self._row_widgets.items():
            checkbox = row.get("checkbox")
            if checkbox is None:
                continue
            checkbox.blockSignals(True)
            checkbox.setChecked(target_state)
            checkbox.blockSignals(False)
            if target_state:
                if model_id not in self._selected:
                    self._selected.append(model_id)
            else:
                if model_id in self._selected:
                    self._selected.remove(model_id)
        self._update_count_label()

    def _sync_select_all_state(self):
        if not self._items:
            self.select_all_check.setChecked(False)
            return
        checked = sum(1 for model_id in self._items if model_id in self._selected)
        if checked == len(self._items):
            self.select_all_check.setChecked(True)
        else:
            self.select_all_check.setChecked(False)

    def _update_count_label(self):
        total = len(self._items)
        selected = len(self._selected)
        self.count_label.setText(
            tr("provider.selected_count", selected=selected, total=total)
        )

    def _on_confirm(self):
        selected = [model_id for model_id in self._items if model_id in self._selected]
        self._selected = selected
        self.accept()

    def get_selected_model_ids(self) -> List[str]:
        return list(self._selected)

    def get_batch_config(self) -> Dict[str, Any]:
        return dict(self._batch_config)


class ProviderDialog(BaseDialog):
    """Provider 编辑对话框"""

    def __init__(self, main_window, provider_name: str = None, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.provider_name = provider_name
        self.is_edit = provider_name is not None

        self.setWindowTitle(
            tr("provider.edit_provider")
            if self.is_edit
            else tr("provider.add_provider")
        )
        self.setMinimumWidth(520)
        self._setup_ui()

        if self.is_edit:
            self._load_provider_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Provider 名称
        name_layout = QHBoxLayout()
        name_label = BodyLabel(tr("provider.provider_key") + ":", self)
        name_label.setMinimumWidth(90)
        name_layout.addWidget(name_label)
        self.name_edit = LineEdit(self)
        self.name_edit.setPlaceholderText(tr("provider.placeholder_key"))
        self.name_edit.setToolTip(get_tooltip("provider_name"))
        self.name_edit.setMinimumHeight(36)
        if self.is_edit:
            self.name_edit.setEnabled(False)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        # 显示名称
        display_layout = QHBoxLayout()
        display_label = BodyLabel(tr("provider.display_name") + ":", self)
        display_label.setMinimumWidth(90)
        display_layout.addWidget(display_label)
        self.display_edit = LineEdit(self)
        self.display_edit.setPlaceholderText(tr("provider.placeholder_display"))
        self.display_edit.setToolTip(get_tooltip("provider_display"))
        self.display_edit.setMinimumHeight(36)
        display_layout.addWidget(self.display_edit)
        layout.addLayout(display_layout)

        # SDK
        sdk_layout = QHBoxLayout()
        sdk_label = BodyLabel("SDK:", self)
        sdk_label.setMinimumWidth(90)
        sdk_layout.addWidget(sdk_label)
        self.sdk_combo = ComboBox(self)
        self.sdk_combo.addItems(PRESET_SDKS)
        self.sdk_combo.setToolTip(get_tooltip("provider_sdk"))
        self.sdk_combo.setMinimumHeight(36)
        sdk_layout.addWidget(self.sdk_combo)
        layout.addLayout(sdk_layout)

        # API 地址
        url_layout = QHBoxLayout()
        url_label = BodyLabel(tr("provider.base_url") + ":", self)
        url_label.setMinimumWidth(90)
        url_layout.addWidget(url_label)
        self.url_edit = LineEdit(self)
        self.url_edit.setPlaceholderText(tr("provider.placeholder_base_url"))
        self.url_edit.setToolTip(get_tooltip("provider_url"))
        self.url_edit.setMinimumHeight(36)
        url_layout.addWidget(self.url_edit)
        layout.addLayout(url_layout)

        # API 密钥
        key_layout = QHBoxLayout()
        key_label = BodyLabel(tr("provider.api_key") + ":", self)
        key_label.setMinimumWidth(90)
        key_layout.addWidget(key_label)
        self.key_edit = LineEdit(self)
        self.key_edit.setPlaceholderText(tr("provider.placeholder_api_key"))
        self.key_edit.setToolTip(get_tooltip("provider_apikey"))
        self.key_edit.setMinimumHeight(36)
        key_layout.addWidget(self.key_edit)
        layout.addLayout(key_layout)

        # 模型列表地址
        model_list_layout = QHBoxLayout()
        model_list_label = BodyLabel(tr("provider.model_list_url") + ":", self)
        model_list_label.setMinimumWidth(90)
        model_list_layout.addWidget(model_list_label)
        self.model_list_url_edit = LineEdit(self)
        self.model_list_url_edit.setPlaceholderText(
            tr("provider.placeholder_model_list")
        )
        self.model_list_url_edit.setToolTip(get_tooltip("provider_model_list_url"))
        self.model_list_url_edit.setMinimumHeight(36)
        model_list_layout.addWidget(self.model_list_url_edit)
        layout.addLayout(model_list_layout)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = PushButton(tr("common.cancel"), self)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.save_btn = PrimaryPushButton(tr("common.save"), self)
        self.save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)

    def _load_provider_data(self):
        config = self.main_window.opencode_config or {}
        provider = config.get("provider", {}).get(self.provider_name, {})

        self.name_edit.setText(self.provider_name)
        self.display_edit.setText(provider.get("name", ""))
        self.sdk_combo.setCurrentText(provider.get("npm", ""))

        options = provider.get("options", {}) if isinstance(provider, dict) else {}
        self.url_edit.setText(options.get("baseURL", ""))
        self.key_edit.setText(options.get("apiKey", ""))
        self.model_list_url_edit.setText(options.get("modelListUrl", ""))

    def _on_save(self):
        name = self.name_edit.text().strip()
        if not name:
            InfoBar.error(tr("common.error"), tr("provider.enter_name"), parent=self)
            return

        config = self.main_window.opencode_config
        if config is None:
            config = {}
            self.main_window.opencode_config = config

        if "provider" not in config:
            config["provider"] = {}

        if not self.is_edit and name in config["provider"]:
            InfoBar.error(
                tr("common.error"),
                tr("provider.provider_exists", name=name),
                parent=self,
            )
            return

        provider_data = config["provider"].get(name, {"models": {}})
        provider_data["npm"] = self.sdk_combo.currentText()
        provider_data["name"] = self.display_edit.text().strip()
        provider_data["options"] = {
            "baseURL": self.url_edit.text().strip(),
            "apiKey": self.key_edit.text().strip(),
            "modelListUrl": self.model_list_url_edit.text().strip(),
        }

        config["provider"][name] = provider_data
        self.main_window.save_opencode_config()

        options = provider_data.get("options", {})
        if options.get("baseURL") or options.get("modelListUrl"):
            if not hasattr(self.main_window, "_model_fetch_service"):
                self.main_window._model_fetch_service = ModelFetchService(
                    self.main_window
                )

            service = self.main_window._model_fetch_service
            if hasattr(self.main_window, "provider_page") and not getattr(
                service, "_provider_page_connected", False
            ):
                service.fetch_finished.connect(
                    self.main_window.provider_page._on_models_fetched
                )
                service._provider_page_connected = True

            service.fetch_async(name, options)
        else:
            InfoBar.warning(
                tr("common.info"),
                tr("provider.no_base_url") + "，跳过自动拉取",
                parent=self,
            )

        self.accept()


# ==================== 原生 Provider 页面 ====================
class NativeProviderDialog(BaseDialog):
    """原生 Provider 配置对话框"""

    def __init__(
        self,
        main_window,
        provider: NativeProviderConfig,
        auth_manager: AuthManager,
        env_detector: EnvVarDetector,
        parent=None,
    ):
        super().__init__(parent)
        self.main_window = main_window
        self.provider = provider
        self.auth_manager = auth_manager
        self.env_detector = env_detector
        self.auth_inputs: Dict[str, QWidget] = {}
        self.option_inputs: Dict[str, QWidget] = {}
        self._setup_ui()

    def _setup_ui(self):
        """初始化对话框 UI"""
        self.setWindowTitle(tr("provider.configure_provider", name=self.provider.name))
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Provider 信息
        info_label = CaptionLabel(f"SDK: {self.provider.sdk}", self)
        layout.addWidget(info_label)

        # 环境变量检测提示
        detected_env = self.env_detector.detect_env_vars(self.provider.id)
        if detected_env:
            env_hint = CaptionLabel(
                f"✓ {tr('native_provider.detected_env_vars')}: {', '.join(detected_env.keys())}",
                self,
            )
            env_hint.setStyleSheet("color: #4CAF50;")
            layout.addWidget(env_hint)

        # 认证配置卡片
        auth_card = SimpleCardWidget(self)
        auth_card_layout = QVBoxLayout(auth_card)
        auth_card_layout.setContentsMargins(16, 16, 16, 16)
        auth_card_layout.setSpacing(12)

        auth_title = StrongBodyLabel(tr("native_provider.auth_config"), auth_card)
        auth_card_layout.addWidget(auth_title)

        current_auth = self.auth_manager.get_provider_auth(self.provider.id) or {}

        for field in self.provider.auth_fields:
            field_layout = QHBoxLayout()

            label = BodyLabel(
                f"{field.label}{'*' if field.required else ''}", auth_card
            )
            label.setMinimumWidth(120)
            field_layout.addWidget(label)

            if field.field_type == "password":
                input_widget = LineEdit(auth_card)
                input_widget.setEchoMode(LineEdit.Password)
            else:
                input_widget = LineEdit(auth_card)

            input_widget.setPlaceholderText(field.placeholder)
            if field.key in current_auth:
                input_widget.setText(str(current_auth[field.key]))

            field_layout.addWidget(input_widget, 1)

            # 环境变量导入按钮
            env_var = self._get_env_var_for_field(field.key)
            if env_var and env_var in detected_env:
                import_btn = ToolButton(FIF.DOWNLOAD, auth_card)
                import_btn.setToolTip(
                    tr("native_provider.import_env_var", env_var=env_var)
                )
                import_btn.clicked.connect(
                    partial(self._import_env_var, input_widget, env_var)
                )
                field_layout.addWidget(import_btn)

            self.auth_inputs[field.key] = input_widget
            auth_card_layout.addLayout(field_layout)

        layout.addWidget(auth_card)

        # 选项配置卡片
        if self.provider.option_fields:
            option_card = SimpleCardWidget(self)
            option_card_layout = QVBoxLayout(option_card)
            option_card_layout.setContentsMargins(16, 16, 16, 16)
            option_card_layout.setSpacing(12)

            option_title = StrongBodyLabel(
                tr("native_provider.provider_options"), option_card
            )
            option_card_layout.addWidget(option_title)

            config = self.main_window.opencode_config or {}
            current_options = (
                config.get("provider", {}).get(self.provider.id, {}).get("options", {})
            )

            for field in self.provider.option_fields:
                field_layout = QHBoxLayout()

                label = BodyLabel(field.label, option_card)
                label.setMinimumWidth(120)
                field_layout.addWidget(label)

                if field.field_type == "select" and field.options:
                    input_widget = ComboBox(option_card)
                    input_widget.addItems(field.options)
                    current_value = current_options.get(field.key, field.default)
                    if current_value in field.options:
                        input_widget.setCurrentText(current_value)
                else:
                    input_widget = LineEdit(option_card)
                    input_widget.setPlaceholderText(field.default or "可选")
                    input_widget.setText(str(current_options.get(field.key, "")))

                field_layout.addWidget(input_widget, 1)
                self.option_inputs[field.key] = input_widget
                option_card_layout.addLayout(field_layout)

            layout.addWidget(option_card)

        layout.addStretch()

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = PushButton(tr("common.cancel"), self)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = PrimaryPushButton(tr("common.save"), self)
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _get_env_var_for_field(self, field_key: str) -> Optional[str]:
        """获取字段对应的环境变量名"""
        for env_var, auth_field in self.env_detector.ENV_TO_AUTH_FIELD.items():
            if auth_field == field_key:
                provider_vars = self.env_detector.PROVIDER_ENV_VARS.get(
                    self.provider.id, []
                )
                if env_var in provider_vars:
                    return env_var
        return None

    def _import_env_var(self, input_widget: LineEdit, env_var: str):
        """导入环境变量引用"""
        ref = self.env_detector.format_env_reference(env_var)
        input_widget.setText(ref)

    def _on_save(self):
        """保存配置"""
        # 检查重复
        config = self.main_window.opencode_config or {}
        custom_providers = config.get("provider", {})
        if self.provider.id in custom_providers:
            if custom_providers[self.provider.id].get("npm"):
                msg_box = FluentMessageBox(
                    "配置冲突",
                    f"已存在同名的自定义 Provider '{self.provider.id}'。\n继续保存？",
                    self,
                )
                if msg_box.exec_() != QMessageBox.Yes:
                    return

        # 收集认证数据
        auth_data = {}
        for field in self.provider.auth_fields:
            input_widget = self.auth_inputs.get(field.key)
            if input_widget:
                value = input_widget.text().strip()
                if value:
                    auth_data[field.key] = value
                elif field.required:
                    QMessageBox.warning(self, "验证失败", f"{field.label} 是必填项")
                    return

        # 保存认证
        try:
            self.auth_manager.set_provider_auth(self.provider.id, auth_data)
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"无法保存认证配置: {e}")
            return

        # 保存选项
        if self.option_inputs:
            options = {}
            for field in self.provider.option_fields:
                input_widget = self.option_inputs.get(field.key)
                if input_widget:
                    if isinstance(input_widget, ComboBox):
                        value = input_widget.currentText()
                    else:
                        value = input_widget.text().strip()
                    if value:
                        options[field.key] = value

            if options:
                if "provider" not in config:
                    config["provider"] = {}
                if self.provider.id not in config["provider"]:
                    config["provider"][self.provider.id] = {}
                config["provider"][self.provider.id]["options"] = options
                self.main_window.opencode_config = config
                self.main_window.save_opencode_config()

        self.accept()


# ==================== Model 页面 ====================


class ModelPage(BasePage):
    """Model 管理页面"""

    def __init__(self, main_window, parent=None):
        super().__init__(tr("model.title"), parent)
        self.main_window = main_window
        self._setup_ui()
        self._load_providers()
        # 连接配置变更信号
        self.main_window.config_changed.connect(self._on_config_changed)

    def _on_config_changed(self):
        """配置变更时刷新 Provider 列表和模型"""
        current_provider = self.provider_combo.currentText()
        self._load_providers()
        # 尝试恢复之前选中的 Provider
        idx = self.provider_combo.findText(current_provider)
        if idx >= 0:
            self.provider_combo.setCurrentIndex(idx)
        elif self.provider_combo.count() > 0:
            self.provider_combo.setCurrentIndex(0)

    def _setup_ui(self):
        # Provider 选择
        provider_layout = QHBoxLayout()
        provider_layout.addWidget(BodyLabel(tr("model.select_provider"), self))
        self.provider_combo = ComboBox(self)
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        provider_layout.addWidget(self.provider_combo)
        provider_layout.addStretch()
        self._layout.addLayout(provider_layout)

        # 工具栏
        toolbar = QHBoxLayout()

        self._bulk_models_owner = "model"

        self.add_btn = PrimaryPushButton(FIF.ADD, tr("model.add_model"), self)
        self.add_btn.clicked.connect(self._on_add)
        toolbar.addWidget(self.add_btn)

        self.preset_btn = PushButton(FIF.LIBRARY, tr("model.add_from_preset"), self)
        self.preset_btn.clicked.connect(self._on_add_preset)
        toolbar.addWidget(self.preset_btn)

        self.edit_btn = PushButton(FIF.EDIT, tr("common.edit"), self)
        self.edit_btn.clicked.connect(self._on_edit)
        toolbar.addWidget(self.edit_btn)

        self.delete_btn = PushButton(FIF.DELETE, tr("common.delete"), self)
        self.delete_btn.clicked.connect(self._on_delete)
        toolbar.addWidget(self.delete_btn)

        toolbar.addStretch()
        self._layout.addLayout(toolbar)

        # Agent 列表
        self.table = TableWidget(self)

        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            [
                tr("model.model_id"),
                tr("model.model_name"),
                tr("model.context"),
                tr("model.output"),
                tr("model.attachment"),
            ]
        )
        # 调整列宽：模型ID和显示名称加宽，上下文/输出/附件各10字符(约80px)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # 模型ID 均分
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # 显示名称 均分
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.resizeSection(2, 120)  # 上下文 15字符
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.resizeSection(3, 80)  # 输出 10字符
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.resizeSection(4, 60)  # 附件 10字符
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.doubleClicked.connect(self._on_edit)
        self._layout.addWidget(self.table)

    def _load_providers(self):
        """加载 Provider 列表"""
        self.provider_combo.clear()
        config = self.main_window.opencode_config or {}
        providers = config.get("provider", {})
        for name in providers.keys():
            self.provider_combo.addItem(name)

    def _on_provider_changed(self, provider_name: str):
        """Provider 切换时刷新模型列表"""
        self._load_models(provider_name)

    def _load_models(self, provider_name: str):
        """加载指定 Provider 的模型列表"""
        self.table.setRowCount(0)
        if not provider_name:
            return

        config = self.main_window.opencode_config or {}
        provider = config.get("provider", {}).get(provider_name, {})
        if not isinstance(provider, dict):
            return
        models = provider.get("models", {})

        for model_id, data in models.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(model_id))
            self.table.setItem(row, 1, QTableWidgetItem(data.get("name", "")))
            limit = data.get("limit", {})
            self.table.setItem(row, 2, QTableWidgetItem(str(limit.get("context", ""))))
            self.table.setItem(row, 3, QTableWidgetItem(str(limit.get("output", ""))))
            self.table.setItem(
                row, 4, QTableWidgetItem("✓" if data.get("attachment") else "")
            )

    def _on_add(self):
        """添加模型"""
        provider = self.provider_combo.currentText()
        if not provider:
            self.show_warning(tr("common.info"), tr("model.select_provider_first"))
            return
        dialog = ModelDialog(self.main_window, provider, parent=self)
        if dialog.exec_():
            self._load_models(provider)
            self.show_success(tr("common.success"), tr("model.added_success"))

    def _on_add_preset(self):
        """从预设添加模型"""
        provider = self.provider_combo.currentText()
        if not provider:
            self.show_warning(tr("common.info"), tr("model.select_provider_first"))
            return
        dialog = PresetModelDialog(self.main_window, provider, parent=self)
        if dialog.exec_():
            self._load_models(provider)
            self.show_success(tr("common.success"), tr("model.preset_added_success"))

    def _on_edit(self):
        """编辑模型"""
        provider = self.provider_combo.currentText()
        row = self.table.currentRow()
        if row < 0:
            self.show_warning(tr("common.info"), tr("model.select_model_first"))
            return
        model_id = self.table.item(row, 0).text()
        dialog = ModelDialog(self.main_window, provider, model_id=model_id, parent=self)
        if dialog.exec_():
            self._load_models(provider)
            self.show_success(tr("common.success"), tr("model.updated_success"))

    def _on_delete(self):
        """删除模型"""
        provider = self.provider_combo.currentText()
        row = self.table.currentRow()
        if row < 0:
            self.show_warning(tr("common.info"), tr("model.select_model_first"))
            return

        model_id = self.table.item(row, 0).text()
        w = FluentMessageBox(
            tr("model.delete_confirm_title"),
            tr("model.delete_confirm", name=model_id),
            self,
        )
        if w.exec_():
            config = self.main_window.opencode_config or {}
            if "provider" in config and provider in config["provider"]:
                models = config["provider"][provider].get("models", {})
                if model_id in models:
                    del models[model_id]
                    self.main_window.save_opencode_config()
                    self._load_models(provider)

                    # 修复焦点问题：删除后自动选中下一行或上一行
                    new_row_count = self.table.rowCount()
                    if new_row_count > 0:
                        # 如果删除的不是最后一行，选中原位置的行（现在是下一行）
                        # 如果删除的是最后一行，选中新的最后一行
                        new_row = min(row, new_row_count - 1)
                        self.table.selectRow(new_row)
                        self.table.setCurrentCell(new_row, 0)

                    self.show_success(
                        tr("common.success"), tr("model.deleted_success", name=model_id)
                    )


class ModelDialog(BaseDialog):
    """模型编辑对话框 - 完整版本，包含 Options/Variants Tab"""

    def __init__(
        self, main_window, provider_name: str, model_id: str = None, parent=None
    ):
        super().__init__(parent)
        self.main_window = main_window
        self.provider_name = provider_name
        self.model_id = model_id
        self.is_edit = model_id is not None
        self.current_model_data = {"options": {}, "variants": {}}

        self.setWindowTitle(
            tr("model.edit_model") if self.is_edit else tr("model.add_model")
        )
        self.setMinimumSize(750, 750)
        self._setup_ui()
        self._apply_enhanced_style()

        if self.is_edit:
            self._load_model_data()

    def _apply_enhanced_style(self):
        """应用增强样式 - 增加层叠感"""
        if isDarkTheme():
            self.setStyleSheet(
                self.styleSheet()
                + """
                /* Tab/Pivot 样式增强 */
                Pivot {
                    background-color: #161b22;
                    border-radius: 6px;
                    padding: 4px;
                }
                /* 卡片样式增强 */
                CardWidget {
                    background-color: #161b22;
                    border: 1px solid #30363d;
                    border-radius: 8px;
                    margin: 4px 0;
                }
                /* 表格样式增强 - Antigravity 风格 */
                QTableWidget, TableWidget {
                    background-color: #0d1117;
                    border: none;
                    border-radius: 8px;
                    gridline-color: transparent;
                    outline: none;
                }
                QTableWidget::item, TableWidget::item {
                    padding: 12px 16px;
                    border: none;
                    border-bottom: 1px solid #21262d;
                    color: #e6edf3;
                }
                QTableWidget::item:selected, TableWidget::item:selected {
                    background-color: #1f6feb;
                    color: #ffffff;
                }
                QTableWidget::item:hover, TableWidget::item:hover {
                    background-color: #161b22;
                }
                QHeaderView::section {
                    background-color: #0d1117;
                    color: #7d8590;
                    border: none;
                    border-bottom: 1px solid #21262d;
                    padding: 12px 16px;
                    font-weight: 600;
                    font-size: 12px;
                }
                QHeaderView {
                    background-color: #0d1117;
                }
                /* 滚动条样式 */
                QScrollBar:vertical {
                    background-color: #0d1117;
                    width: 8px;
                    border-radius: 4px;
                }
                QScrollBar::handle:vertical {
                    background-color: #30363d;
                    border-radius: 4px;
                    min-height: 30px;
                }
                QScrollBar::handle:vertical:hover {
                    background-color: #484f58;
                }
                /* 分组标题样式 */
                CaptionLabel {
                    color: #58a6ff;
                    font-weight: bold;
                    padding: 4px 0;
                }
            """
            )

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # ===== 基本信息区域 =====
        basic_card = CardWidget(self)
        basic_layout = QVBoxLayout(basic_card)
        basic_layout.setSpacing(10)
        basic_layout.setContentsMargins(16, 12, 16, 12)

        # 标题
        basic_layout.addWidget(SubtitleLabel(tr("model.basic_info"), basic_card))

        # 模型ID
        id_layout = QHBoxLayout()
        id_layout.addWidget(BodyLabel(tr("model.model_id") + ":", self))
        self.id_edit = LineEdit(self)
        self.id_edit.setPlaceholderText("如: claude-sonnet-4-5-20250929")
        self.id_edit.setToolTip(get_tooltip("model_id"))
        if self.is_edit:
            self.id_edit.setEnabled(False)
        id_layout.addWidget(self.id_edit)
        basic_layout.addLayout(id_layout)

        # 显示名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(BodyLabel(tr("model.model_name") + ":", self))
        self.name_edit = LineEdit(self)
        self.name_edit.setToolTip(get_tooltip("model_name"))
        name_layout.addWidget(self.name_edit)
        basic_layout.addLayout(name_layout)

        # 支持附件
        self.attachment_check = CheckBox(tr("model.support_attachment"), self)
        self.attachment_check.setToolTip(get_tooltip("model_attachment"))
        basic_layout.addWidget(self.attachment_check)

        # Modalities 输入/输出模态
        modalities_layout = QHBoxLayout()
        modalities_layout.addWidget(BodyLabel(tr("model.input_modality") + ":", self))
        self.input_text_check = CheckBox("text", self)
        self.input_text_check.setChecked(True)
        modalities_layout.addWidget(self.input_text_check)
        self.input_image_check = CheckBox("image", self)
        modalities_layout.addWidget(self.input_image_check)
        self.input_audio_check = CheckBox("audio", self)
        modalities_layout.addWidget(self.input_audio_check)
        self.input_video_check = CheckBox("video", self)
        modalities_layout.addWidget(self.input_video_check)
        modalities_layout.addSpacing(20)
        modalities_layout.addWidget(BodyLabel(tr("model.output_modality") + ":", self))
        self.output_text_check = CheckBox("text", self)
        self.output_text_check.setChecked(True)
        modalities_layout.addWidget(self.output_text_check)
        self.output_image_check = CheckBox("image", self)
        modalities_layout.addWidget(self.output_image_check)
        self.output_audio_check = CheckBox("audio", self)
        modalities_layout.addWidget(self.output_audio_check)
        modalities_layout.addStretch()
        basic_layout.addLayout(modalities_layout)

        # 上下文窗口和最大输出
        limit_layout = QHBoxLayout()
        limit_layout.addWidget(BodyLabel(tr("model.context") + ":", self))
        self.context_spin = SpinBox(self)
        self.context_spin.setRange(0, 10000000)
        self.context_spin.setValue(200000)
        self.context_spin.setMinimumWidth(120)
        self.context_spin.setToolTip(get_tooltip("model_context"))
        limit_layout.addWidget(self.context_spin)
        limit_layout.addSpacing(20)
        limit_layout.addWidget(BodyLabel(tr("model.output") + ":", self))
        self.output_spin = SpinBox(self)
        self.output_spin.setRange(0, 1000000)
        self.output_spin.setValue(16000)
        self.output_spin.setMinimumWidth(100)
        self.output_spin.setToolTip(get_tooltip("model_output"))
        limit_layout.addWidget(self.output_spin)
        basic_layout.addLayout(limit_layout)

        layout.addWidget(basic_card)

        # ===== Tab 切换区域 =====
        tab_container = CardWidget(self)
        tab_layout = QVBoxLayout(tab_container)
        tab_layout.setContentsMargins(12, 8, 12, 12)

        self.pivot = Pivot(self)
        self.stacked_widget = QStackedWidget(self)

        # Options Tab
        self.options_widget = QWidget()
        self._setup_options_tab(self.options_widget)
        self.stacked_widget.addWidget(self.options_widget)
        self.pivot.addItem(routeKey="options", text=tr("model.options_tab"))

        # Variants Tab
        self.variants_widget = QWidget()
        self._setup_variants_tab(self.variants_widget)
        self.stacked_widget.addWidget(self.variants_widget)
        self.pivot.addItem(routeKey="variants", text=tr("model.variants_tab"))

        self.pivot.currentItemChanged.connect(
            lambda k: self.stacked_widget.setCurrentIndex(0 if k == "options" else 1)
        )
        self.pivot.setCurrentItem("options")

        tab_layout.addWidget(self.pivot)
        tab_layout.addWidget(self.stacked_widget, 1)

        layout.addWidget(tab_container, 1)

        # ===== 按钮区域 =====
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = PushButton(tr("common.cancel"), self)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.save_btn = PrimaryPushButton(tr("common.save"), self)
        self.save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)

    def _setup_options_tab(self, parent):
        """设置 Options Tab - 使用 ScrollArea 解决空间不足问题"""
        # 主布局
        main_layout = QVBoxLayout(parent)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 创建滚动区域
        scroll_area = QScrollArea(parent)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
        )

        # 滚动内容容器
        scroll_content = QWidget()
        scroll_content.setStyleSheet("QWidget { background: transparent; }")
        layout = QVBoxLayout(scroll_content)
        layout.setSpacing(10)
        layout.setContentsMargins(4, 8, 4, 8)

        # Claude Thinking 快捷按钮
        claude_card = CardWidget(scroll_content)
        claude_layout = QVBoxLayout(claude_card)
        claude_layout.setContentsMargins(8, 6, 8, 6)
        claude_layout.setSpacing(6)
        claude_layout.addWidget(
            CaptionLabel(tr("model.claude_thinking_config"), claude_card)
        )
        claude_btn_layout = QHBoxLayout()
        claude_btn_layout.setSpacing(6)

        btn_thinking_type = PushButton("type=enabled", claude_card)
        btn_thinking_type.setToolTip(get_tooltip("option_thinking_type"))
        btn_thinking_type.setFixedHeight(32)
        btn_thinking_type.clicked.connect(
            lambda: self._add_thinking_config("type", "enabled")
        )
        claude_btn_layout.addWidget(btn_thinking_type)

        btn_budget = PushButton("budget=16000", claude_card)
        btn_budget.setToolTip(get_tooltip("option_thinking_budget"))
        btn_budget.setFixedHeight(32)
        btn_budget.clicked.connect(
            lambda: self._add_thinking_config("budgetTokens", 16000)
        )
        claude_btn_layout.addWidget(btn_budget)

        btn_full = PrimaryPushButton(tr("model.one_click_add"), claude_card)
        btn_full.setFixedHeight(32)
        btn_full.clicked.connect(self._add_full_thinking_config)
        claude_btn_layout.addWidget(btn_full)

        claude_layout.addLayout(claude_btn_layout)
        layout.addWidget(claude_card)

        # OpenAI 推理快捷按钮
        openai_card = CardWidget(scroll_content)
        openai_layout = QVBoxLayout(openai_card)
        openai_layout.setContentsMargins(8, 6, 8, 6)
        openai_layout.setSpacing(6)
        openai_layout.addWidget(
            CaptionLabel(tr("model.openai_reasoning_config"), openai_card)
        )
        openai_btn_layout = QHBoxLayout()
        openai_btn_layout.setSpacing(6)

        openai_presets = [
            ("reasoning", "high", "option_reasoningEffort"),
            ("verbosity", "low", "option_textVerbosity"),
            ("summary", "auto", "option_reasoningSummary"),
        ]
        for key, val, tooltip_key in openai_presets:
            btn = PushButton(f"{key}={val}", openai_card)
            btn.setToolTip(get_tooltip(tooltip_key))
            btn.setFixedHeight(32)
            btn.clicked.connect(
                lambda checked, k=key, v=val: self._add_option_preset(k, v)
            )
            openai_btn_layout.addWidget(btn)

        openai_layout.addLayout(openai_btn_layout)
        layout.addWidget(openai_card)

        # Gemini Thinking 快捷按钮
        gemini_card = CardWidget(scroll_content)
        gemini_layout = QVBoxLayout(gemini_card)
        gemini_layout.setContentsMargins(8, 6, 8, 6)
        gemini_layout.setSpacing(6)
        gemini_layout.addWidget(
            CaptionLabel(tr("model.gemini_thinking_config"), gemini_card)
        )
        gemini_btn_layout = QHBoxLayout()
        gemini_btn_layout.setSpacing(6)

        btn_gemini_8k = PushButton("budget=8000", gemini_card)
        btn_gemini_8k.setToolTip(get_tooltip("option_thinking_budget"))
        btn_gemini_8k.setFixedHeight(32)
        btn_gemini_8k.clicked.connect(lambda: self._add_gemini_thinking_config(8000))
        gemini_btn_layout.addWidget(btn_gemini_8k)

        btn_gemini_16k = PushButton("budget=16000", gemini_card)
        btn_gemini_16k.setToolTip(get_tooltip("option_thinking_budget"))
        btn_gemini_16k.setFixedHeight(32)
        btn_gemini_16k.clicked.connect(lambda: self._add_gemini_thinking_config(16000))
        gemini_btn_layout.addWidget(btn_gemini_16k)

        gemini_layout.addLayout(gemini_btn_layout)
        layout.addWidget(gemini_card)

        # Options 列表
        options_label = BodyLabel(
            tr("model.options_key_value_list_label"), scroll_content
        )
        options_label.setToolTip(get_tooltip("model_options"))
        layout.addWidget(options_label)

        self.options_table = TableWidget(scroll_content)
        self.options_table.setColumnCount(2)
        self.options_table.setHorizontalHeaderLabels(
            [tr("model.key"), tr("model.value")]
        )
        self.options_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.options_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.options_table.setMinimumHeight(100)
        self.options_table.setMaximumHeight(150)
        self.options_table.verticalHeader().setDefaultSectionSize(28)
        self.options_table.horizontalHeader().setFixedHeight(35)
        self.options_table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        layout.addWidget(self.options_table)

        # 键值输入 - 单行紧凑布局
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)

        key_label = BodyLabel(tr("model.key") + ":", scroll_content)
        key_label.setFixedWidth(24)
        input_layout.addWidget(key_label)

        self.option_key_edit = LineEdit(scroll_content)
        self.option_key_edit.setPlaceholderText("temperature")
        self.option_key_edit.setFixedHeight(32)
        input_layout.addWidget(self.option_key_edit, 1)

        value_label = BodyLabel(tr("model.value") + ":", scroll_content)
        value_label.setFixedWidth(24)
        input_layout.addWidget(value_label)

        self.option_value_edit = LineEdit(scroll_content)
        self.option_value_edit.setPlaceholderText("0.7")
        self.option_value_edit.setFixedHeight(32)
        input_layout.addWidget(self.option_value_edit, 1)

        layout.addLayout(input_layout)

        # 添加/删除按钮
        opt_btn_layout = QHBoxLayout()
        opt_btn_layout.setSpacing(8)
        add_opt_btn = PrimaryPushButton(tr("model.add"), scroll_content)
        add_opt_btn.setFixedHeight(32)
        add_opt_btn.clicked.connect(self._add_option)
        opt_btn_layout.addWidget(add_opt_btn)
        del_opt_btn = PushButton(tr("model.delete_selected"), scroll_content)
        del_opt_btn.setFixedHeight(32)
        del_opt_btn.clicked.connect(self._delete_option)
        opt_btn_layout.addWidget(del_opt_btn)
        opt_btn_layout.addStretch()
        layout.addLayout(opt_btn_layout)

        # 添加弹性空间
        layout.addStretch()

        # 设置滚动区域内容
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

    def _setup_variants_tab(self, parent):
        """设置 Variants Tab"""
        layout = QVBoxLayout(parent)
        layout.setSpacing(12)
        layout.setContentsMargins(4, 8, 4, 8)

        variants_label = BodyLabel(tr("model.variants_config_label"), parent)
        variants_label.setToolTip(get_tooltip("model_variants"))
        layout.addWidget(variants_label)

        # Variants 列表
        self.variants_table = TableWidget(parent)
        self.variants_table.setColumnCount(2)
        self.variants_table.setHorizontalHeaderLabels(
            [tr("model.variant_name"), tr("model.config")]
        )
        self.variants_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.variants_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.variants_table.setMinimumHeight(120)
        self.variants_table.verticalHeader().setDefaultSectionSize(36)
        self.variants_table.horizontalHeader().setMinimumHeight(32)
        self.variants_table.itemSelectionChanged.connect(self._on_variant_select)
        layout.addWidget(self.variants_table)

        # 变体名称输入
        name_layout = QHBoxLayout()
        name_layout.setSpacing(8)
        name_label = BodyLabel(tr("model.variant_name_label"), parent)
        name_label.setMinimumWidth(50)
        name_layout.addWidget(name_label)
        self.variant_name_edit = LineEdit(parent)
        self.variant_name_edit.setPlaceholderText("high, low, thinking")
        self.variant_name_edit.setMinimumHeight(36)
        name_layout.addWidget(self.variant_name_edit)
        layout.addLayout(name_layout)

        # 预设名称按钮
        preset_layout = QHBoxLayout()
        preset_layout.setSpacing(6)
        preset_layout.addWidget(CaptionLabel(tr("model.preset_label") + ":", parent))
        for name in ["high", "low", "thinking", "fast", "default"]:
            btn = PushButton(name, parent)
            btn.setMinimumHeight(30)
            btn.clicked.connect(
                lambda checked, n=name: self.variant_name_edit.setText(n)
            )
            preset_layout.addWidget(btn)
        preset_layout.addStretch()
        layout.addLayout(preset_layout)

        # JSON 配置编辑器
        layout.addWidget(BodyLabel(tr("model.config_json_label"), parent))
        self.variant_config_edit = TextEdit(parent)
        self.variant_config_edit.setPlaceholderText('{"reasoningEffort": "high"}')
        self.variant_config_edit.setMinimumHeight(80)
        self.variant_config_edit.setMaximumHeight(100)
        layout.addWidget(self.variant_config_edit)

        # 添加/删除按钮
        var_btn_layout = QHBoxLayout()
        var_btn_layout.setSpacing(8)
        add_var_btn = PrimaryPushButton(tr("model.add_variant"), parent)
        add_var_btn.setMinimumHeight(36)
        add_var_btn.clicked.connect(self._add_variant)
        var_btn_layout.addWidget(add_var_btn)
        del_var_btn = PushButton(tr("model.delete_variant"), parent)
        del_var_btn.setMinimumHeight(36)
        del_var_btn.clicked.connect(self._delete_variant)
        var_btn_layout.addWidget(del_var_btn)
        var_btn_layout.addStretch()
        layout.addLayout(var_btn_layout)

        layout.addStretch()

    # ===== Options 辅助方法 =====
    def _add_thinking_config(self, param, value):
        """添加 Claude thinking 配置参数"""
        options = self.current_model_data.setdefault("options", {})
        thinking = options.setdefault("thinking", {})
        thinking[param] = value
        self._refresh_options_table()

    def _add_full_thinking_config(self):
        """一键添加完整的 Claude thinking 配置"""
        options = self.current_model_data.setdefault("options", {})
        options["thinking"] = {"type": "enabled", "budgetTokens": 16000}
        self._refresh_options_table()
        InfoBar.success(
            "成功", "已添加 Claude Thinking 配置", parent=self, duration=2000
        )

    def _add_gemini_thinking_config(self, budget):
        """添加 Gemini thinking 配置"""
        options = self.current_model_data.setdefault("options", {})
        options["thinkingConfig"] = {"thinkingBudget": budget}
        self._refresh_options_table()

    def _add_option_preset(self, key, value):
        """添加预设 option"""
        self.option_key_edit.setText(key)
        self.option_value_edit.setText(str(value))

    def _add_option(self):
        """添加自定义 option"""
        key = self.option_key_edit.text().strip()
        value = self.option_value_edit.text().strip()
        if not key:
            return
        # 尝试转换值类型
        try:
            if value.lower() == "true":
                value = True
            elif value.lower() == "false":
                value = False
            elif value.isdigit():
                value = int(value)
            elif value.replace(".", "", 1).isdigit():
                value = float(value)
        except Exception:
            pass
        self.current_model_data.setdefault("options", {})[key] = value
        self._refresh_options_table()
        self.option_key_edit.clear()
        self.option_value_edit.clear()

    def _delete_option(self):
        """删除选中的 option"""
        selected = self.options_table.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        key = self.options_table.item(row, 0).text()
        options = self.current_model_data.get("options", {})
        if key in options:
            del options[key]
            self._refresh_options_table()

    def _refresh_options_table(self):
        """刷新 options 表格"""
        self.options_table.setRowCount(0)
        options = self.current_model_data.get("options", {})
        for key, value in options.items():
            row = self.options_table.rowCount()
            self.options_table.insertRow(row)
            self.options_table.setItem(row, 0, QTableWidgetItem(str(key)))
            self.options_table.setItem(row, 1, QTableWidgetItem(str(value)))

    # ===== Variants 辅助方法 =====
    def _on_variant_select(self):
        """选中变体时加载配置"""
        selected = self.variants_table.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        name = self.variants_table.item(row, 0).text()
        variants = self.current_model_data.get("variants", {})
        if name in variants:
            self.variant_name_edit.setText(name)
            self.variant_config_edit.setPlainText(
                json.dumps(variants[name], indent=2, ensure_ascii=False)
            )

    def _add_variant(self):
        """添加变体"""
        name = self.variant_name_edit.text().strip()
        if not name:
            InfoBar.warning(
                tr("common.info"), tr("model.enter_variant_name"), parent=self
            )
            return
        try:
            config = json.loads(self.variant_config_edit.toPlainText().strip() or "{}")
        except json.JSONDecodeError as e:
            InfoBar.error("错误", f"JSON 格式错误: {e}", parent=self)
            return
        self.current_model_data.setdefault("variants", {})[name] = config
        self._refresh_variants_table()
        self.variant_name_edit.clear()

    def _delete_variant(self):
        """删除选中的变体"""
        selected = self.variants_table.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        name = self.variants_table.item(row, 0).text()
        variants = self.current_model_data.get("variants", {})
        if name in variants:
            del variants[name]
            self._refresh_variants_table()

    def _refresh_variants_table(self):
        """刷新 variants 表格"""
        self.variants_table.setRowCount(0)
        variants = self.current_model_data.get("variants", {})
        for name, config in variants.items():
            row = self.variants_table.rowCount()
            self.variants_table.insertRow(row)
            self.variants_table.setItem(row, 0, QTableWidgetItem(name))
            config_str = json.dumps(config, ensure_ascii=False)
            if len(config_str) > 50:
                config_str = config_str[:50] + "..."
            self.variants_table.setItem(row, 1, QTableWidgetItem(config_str))

    def _load_model_data(self):
        """加载模型数据"""
        config = self.main_window.opencode_config or {}
        provider = config.get("provider", {}).get(self.provider_name, {})
        if not isinstance(provider, dict):
            return
        model = provider.get("models", {}).get(self.model_id, {})

        self.id_edit.setText(self.model_id)
        self.name_edit.setText(model.get("name", ""))
        self.attachment_check.setChecked(model.get("attachment", False))

        # 加载 modalities
        modalities = model.get("modalities", {})
        input_modalities = modalities.get("input", ["text"])
        output_modalities = modalities.get("output", ["text"])
        self.input_text_check.setChecked("text" in input_modalities)
        self.input_image_check.setChecked("image" in input_modalities)
        self.input_audio_check.setChecked("audio" in input_modalities)
        self.input_video_check.setChecked("video" in input_modalities)
        self.output_text_check.setChecked("text" in output_modalities)
        self.output_image_check.setChecked("image" in output_modalities)
        self.output_audio_check.setChecked("audio" in output_modalities)

        limit = model.get("limit", {})
        self.context_spin.setValue(limit.get("context", 200000))
        self.output_spin.setValue(limit.get("output", 16000))

        # 加载 options 和 variants
        self.current_model_data["options"] = model.get("options", {}).copy()
        self.current_model_data["variants"] = model.get("variants", {}).copy()
        self._refresh_options_table()
        self._refresh_variants_table()

    def _on_save(self):
        """保存模型"""
        model_id = self.id_edit.text().strip()
        if not model_id:
            InfoBar.error("错误", "请输入模型 ID", parent=self)
            return

        config = self.main_window.opencode_config
        if config is None:
            config = {}
            self.main_window.opencode_config = config

        if "provider" not in config:
            config["provider"] = {}

        # 验证 Provider 是否存在且结构完整
        if self.provider_name not in config["provider"]:
            InfoBar.error(
                "错误",
                f'Provider "{self.provider_name}" 不存在，请先在 Provider 管理页面创建',
                parent=self,
            )
            return

        provider = config["provider"][self.provider_name]

        # 检查 Provider 结构是否完整
        if "npm" not in provider or "options" not in provider:
            InfoBar.error(
                "错误",
                f'Provider "{self.provider_name}" 配置不完整，请先在 Provider 管理页面完善配置',
                parent=self,
            )
            return

        # 确保 models 字段存在
        if "models" not in provider:
            provider["models"] = {}

        models = provider["models"]

        # 检查名称冲突
        if not self.is_edit and model_id in models:
            InfoBar.error("错误", f'模型 "{model_id}" 已存在', parent=self)
            return

        # 保存数据
        model_data = {
            "name": self.name_edit.text().strip(),
            "attachment": self.attachment_check.isChecked(),
            "limit": {
                "context": self.context_spin.value(),
                "output": self.output_spin.value(),
            },
        }

        # 保存 modalities
        input_modalities = []
        if self.input_text_check.isChecked():
            input_modalities.append("text")
        if self.input_image_check.isChecked():
            input_modalities.append("image")
        if self.input_audio_check.isChecked():
            input_modalities.append("audio")
        if self.input_video_check.isChecked():
            input_modalities.append("video")
        output_modalities = []
        if self.output_text_check.isChecked():
            output_modalities.append("text")
        if self.output_image_check.isChecked():
            output_modalities.append("image")
        if self.output_audio_check.isChecked():
            output_modalities.append("audio")
        if input_modalities or output_modalities:
            model_data["modalities"] = {
                "input": input_modalities if input_modalities else ["text"],
                "output": output_modalities if output_modalities else ["text"],
            }

        # 保存前进行配置校验，避免写入错误结构
        temp_provider = dict(provider)
        temp_models = dict(temp_provider.get("models", {}))
        temp_models[model_id] = model_data
        temp_provider["models"] = temp_models
        temp_config = dict(config)
        temp_providers = dict(temp_config.get("provider", {}))
        temp_providers[self.provider_name] = temp_provider
        temp_config["provider"] = temp_providers
        issues = ConfigValidator.validate_opencode_config(temp_config)
        errors = [i for i in issues if i["level"] == "error"]
        if errors:
            msg = "\n".join(f"• {e['message']}" for e in errors[:8])
            if len(errors) > 8:
                msg += f"\n... 还有 {len(errors) - 8} 个错误"
            InfoBar.error("错误", f"配置校验失败：\n{msg}", parent=self)
            return

        options = self.current_model_data.get("options", {})
        if options:
            model_data["options"] = options
        variants = self.current_model_data.get("variants", {})
        if variants:
            model_data["variants"] = variants

        models[model_id] = model_data
        self.main_window.save_opencode_config()
        self.accept()


class PresetModelDialog(BaseDialog):
    """预设模型选择对话框"""

    def __init__(self, main_window, provider_name: str, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.provider_name = provider_name

        self.setWindowTitle(tr("model.add_from_preset_title"))
        self.setMinimumSize(500, 400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 模型系列选择
        series_layout = QHBoxLayout()
        series_layout.addWidget(BodyLabel(tr("model.model_series") + ":", self))
        self.series_combo = ComboBox(self)
        # 添加翻译后的系列名称
        self._series_map = {}
        for key in PRESET_MODEL_CONFIGS.keys():
            if key == "Claude 系列":
                display_name = tr("provider.claude_series_short")
            elif key == "OpenAI/Codex 系列":
                display_name = tr("provider.openai_series_short")
            elif key == "Gemini 系列":
                display_name = tr("provider.gemini_series_short")
            elif key == "其他模型":
                display_name = tr("provider.other_models_short")
            else:
                display_name = key
            self._series_map[display_name] = key
            self.series_combo.addItem(display_name)
        self.series_combo.currentTextChanged.connect(self._on_series_changed)
        series_layout.addWidget(self.series_combo)
        layout.addLayout(series_layout)

        # 模型列表
        layout.addWidget(BodyLabel(tr("cli_export.select_model") + ":", self))
        self.model_list = ListWidget(self)
        self.model_list.setSelectionMode(QAbstractItemView.MultiSelection)
        layout.addWidget(self.model_list)

        # 模型描述
        self.desc_label = CaptionLabel("", self)
        self.desc_label.setWordWrap(True)
        layout.addWidget(self.desc_label)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = PushButton(tr("common.cancel"), self)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.save_btn = PrimaryPushButton(tr("common.save"), self)
        self.save_btn.clicked.connect(self._on_add)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)

        # 初始化
        self._on_series_changed(self.series_combo.currentText())

    def _on_series_changed(self, series: str):
        self.model_list.clear()
        # 将显示名称转换回原始键
        original_key = self._series_map.get(series, series)
        if original_key in PRESET_MODEL_CONFIGS:
            models = PRESET_MODEL_CONFIGS[original_key]["models"]
            for model_id, data in models.items():
                self.model_list.addItem(f"{model_id} - {data.get('name', '')}")

    def _on_add(self):
        selected = self.model_list.selectedItems()
        if not selected:
            InfoBar.warning(
                tr("common.info"), tr("model.select_at_least_one"), parent=self
            )
            return

        series = self.series_combo.currentText()
        # 将显示名称转换回原始键
        original_key = self._series_map.get(series, series)
        series_data = PRESET_MODEL_CONFIGS.get(original_key, {})
        models_data = series_data.get("models", {})

        config = self.main_window.opencode_config
        if config is None:
            config = {}
            self.main_window.opencode_config = config

        if "provider" not in config:
            config["provider"] = {}

        # 验证 Provider 是否存在且结构完整
        if self.provider_name not in config["provider"]:
            InfoBar.error(
                "错误",
                f'Provider "{self.provider_name}" 不存在，请先在 Provider 管理页面创建',
                parent=self,
            )
            return

        provider = config["provider"][self.provider_name]

        # 检查 Provider 结构是否完整
        if "npm" not in provider or "options" not in provider:
            InfoBar.error(
                "错误",
                f'Provider "{self.provider_name}" 配置不完整，请先在 Provider 管理页面完善配置',
                parent=self,
            )
            return

        # 确保 models 字段存在
        if "models" not in provider:
            provider["models"] = {}

        models = provider["models"]
        added = 0

        for item in selected:
            model_id = item.text().split(" - ")[0]
            if model_id in models_data:
                preset = models_data[model_id]
                models[model_id] = {
                    "name": preset.get("name", ""),
                    "attachment": preset.get("attachment", False),
                    "limit": preset.get("limit", {}),
                    "options": preset.get("options", {}),
                    "variants": preset.get("variants", {}),
                }
                added += 1

        self.main_window.save_opencode_config()
        InfoBar.success(
            tr("common.success"), tr("provider.models_added", count=added), parent=self
        )
        self.accept()


# ==================== MCP 页面 ====================


class MCPPage(BasePage):
    """MCP 服务器管理页面"""

    def __init__(self, main_window, parent=None):
        super().__init__(tr("mcp.title"), parent)
        self.main_window = main_window
        self._setup_ui()
        self._load_data()
        # 连接配置变更信号
        self.main_window.config_changed.connect(self._on_config_changed)

    def _on_config_changed(self):
        """配置变更时刷新数据"""
        self._load_data()

    def _setup_ui(self):
        # 工具栏
        toolbar = QHBoxLayout()

        self.add_local_btn = PrimaryPushButton(FIF.ADD, tr("mcp.add_local"), self)
        self.add_local_btn.clicked.connect(lambda: self._on_add("local"))
        toolbar.addWidget(self.add_local_btn)

        self.add_remote_btn = PushButton(FIF.CLOUD, tr("mcp.add_remote"), self)
        self.add_remote_btn.clicked.connect(lambda: self._on_add("remote"))
        toolbar.addWidget(self.add_remote_btn)

        self.edit_btn = PushButton(FIF.EDIT, tr("common.edit"), self)
        self.edit_btn.clicked.connect(self._on_edit)
        toolbar.addWidget(self.edit_btn)

        self.delete_btn = PushButton(FIF.DELETE, tr("common.delete"), self)
        self.delete_btn.clicked.connect(self._on_delete)
        toolbar.addWidget(self.delete_btn)

        self.awesome_btn = PushButton(FIF.LIBRARY, tr("mcp.awesome_mcp"), self)
        self.awesome_btn.setToolTip(tr("mcp.awesome_mcp_tooltip"))
        self.awesome_btn.clicked.connect(self._open_awesome_mcp)
        toolbar.addWidget(self.awesome_btn)

        self.ohmy_mcp_btn = PushButton(FIF.ROBOT, tr("mcp.oh_my_mcp"), self)
        self.ohmy_mcp_btn.setToolTip(tr("mcp.oh_my_mcp_tooltip"))
        self.ohmy_mcp_btn.clicked.connect(self._on_ohmy_mcp)
        toolbar.addWidget(self.ohmy_mcp_btn)

        toolbar.addStretch()
        self._layout.addLayout(toolbar)

        # Agent 列表
        self.table = TableWidget(self)

        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            [
                tr("mcp.server_name"),
                tr("mcp.server_type"),
                tr("mcp.enabled"),
                tr("mcp.timeout"),
                tr("mcp.command_url"),
            ]
        )
        # 列宽设置: 名称自适应, 类型15字符(120px), 启用8字符(64px), 超时10字符(80px), 命令/URL自适应
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # 名称
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.resizeSection(1, 120)  # 类型 15字符
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.resizeSection(2, 64)  # 启用 8字符
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.resizeSection(3, 80)  # 超时 10字符
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # 命令/URL
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.doubleClicked.connect(self._on_edit)
        self._layout.addWidget(self.table)

    def _load_data(self):
        self.table.setRowCount(0)
        config = self.main_window.opencode_config or {}
        mcps = config.get("mcp", {})

        # 添加类型检查，防止 mcp 字段为非字典类型时崩溃
        if not isinstance(mcps, dict):
            mcps = {}

        for name, data in mcps.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(name))

            mcp_type = "remote" if "url" in data else "local"
            self.table.setItem(row, 1, QTableWidgetItem(mcp_type))

            enabled = data.get("enabled", True)
            self.table.setItem(row, 2, QTableWidgetItem("✓" if enabled else "✗"))
            self.table.setItem(row, 3, QTableWidgetItem(str(data.get("timeout", 5000))))

            if mcp_type == "local":
                cmd = data.get("command", [])
                self.table.setItem(
                    row,
                    4,
                    QTableWidgetItem(
                        " ".join(cmd) if isinstance(cmd, list) else str(cmd)
                    ),
                )
            else:
                self.table.setItem(row, 4, QTableWidgetItem(data.get("url", "")))

    def _open_awesome_mcp(self):
        webbrowser.open("https://github.com/punkpeye/awesome-mcp-servers")

    def _on_ohmy_mcp(self):
        """打开 Oh My OpenCode MCP 管理对话框"""
        dialog = OhMyMCPDialog(self.main_window, parent=self)
        if dialog.exec_():
            self.show_success(tr("common.success"), tr("mcp.ohmy_updated_success"))

    def _on_add(self, mcp_type: str):
        dialog = MCPDialog(self.main_window, mcp_type=mcp_type, parent=self)
        if dialog.exec_():
            self._load_data()
            self.show_success(tr("common.success"), tr("mcp.added_success"))

    def _on_edit(self):
        row = self.table.currentRow()
        if row < 0:
            self.show_warning(tr("common.info"), tr("mcp.select_first"))
            return

        name = self.table.item(row, 0).text()
        mcp_type = self.table.item(row, 1).text()
        dialog = MCPDialog(
            self.main_window, mcp_name=name, mcp_type=mcp_type, parent=self
        )
        if dialog.exec_():
            self._load_data()
            self.show_success(tr("common.success"), tr("mcp.updated_success"))

    def _on_delete(self):
        row = self.table.currentRow()
        if row < 0:
            self.show_warning(tr("common.info"), tr("mcp.select_first"))
            return

        name = self.table.item(row, 0).text()
        w = FluentMessageBox(
            tr("mcp.delete_confirm_title"), tr("mcp.delete_confirm", name=name), self
        )
        if w.exec_():
            config = self.main_window.opencode_config or {}
            if "mcp" in config and name in config["mcp"]:
                del config["mcp"][name]
                self.main_window.save_opencode_config()
                self._load_data()
                self.show_success(
                    tr("common.success"), tr("mcp.deleted_success", name=name)
                )


class OhMyMCPDialog(BaseDialog):
    """Oh My OpenCode MCP 管理对话框"""

    # Oh My OpenCode 自带的 MCP 服务器
    OHMY_MCPS = {
        "websearch": {
            "name": "websearch",
            "description": "websearch_desc",
            "type": "remote",
            "enabled_by_default": True,
        },
        "context7": {
            "name": "context7",
            "description": "context7_desc",
            "type": "remote",
            "enabled_by_default": True,
        },
        "grep_app": {
            "name": "grep_app",
            "description": "grep_app_desc",
            "type": "remote",
            "enabled_by_default": True,
        },
    }

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setWindowTitle(tr("mcp.ohmy_dialog.title"))
        self.setMinimumWidth(700)
        self.setMinimumHeight(400)
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # 说明文字
        info_label = BodyLabel(
            tr("mcp.ohmy_dialog.info_text"),
            self,
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # MCP 列表
        self.table = TableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            [
                tr("mcp.ohmy_dialog.table_name"),
                tr("mcp.ohmy_dialog.table_type"),
                tr("mcp.ohmy_dialog.table_status"),
                tr("mcp.ohmy_dialog.table_description"),
            ]
        )

        # 列宽设置
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.resizeSection(0, 120)  # 名称
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.resizeSection(1, 80)  # 类型
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.resizeSection(2, 100)  # 状态 - 增宽以显示完整的"✓ 启用"
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # 描述

        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.table)

        # 操作按钮
        btn_layout = QHBoxLayout()

        self.toggle_btn = PushButton(tr("mcp.ohmy_dialog.toggle_button"), self)
        self.toggle_btn.setToolTip(tr("mcp.ohmy_dialog.toggle_tooltip"))
        self.toggle_btn.clicked.connect(self._on_toggle)
        btn_layout.addWidget(self.toggle_btn)

        self.enable_all_btn = PushButton(tr("mcp.ohmy_dialog.enable_all"), self)
        self.enable_all_btn.clicked.connect(self._on_enable_all)
        btn_layout.addWidget(self.enable_all_btn)

        self.disable_all_btn = PushButton(tr("mcp.ohmy_dialog.disable_all"), self)
        self.disable_all_btn.clicked.connect(self._on_disable_all)
        btn_layout.addWidget(self.disable_all_btn)

        btn_layout.addStretch()

        self.close_btn = PrimaryPushButton(tr("common.close"), self)
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)

    def _load_data(self):
        """加载 Oh My MCP 数据 - 从配置文件动态读取"""
        self.table.setRowCount(0)

        # 读取 Oh My OpenCode 配置
        config = self.main_window.ohmyopencode_config or {}

        # 获取 MCP 配置
        mcps = config.get("mcp", {})
        if not isinstance(mcps, dict):
            mcps = {}

        # 获取禁用列表
        disabled_mcps = config.get("disabled_mcps", [])
        if not isinstance(disabled_mcps, list):
            disabled_mcps = []

        # 如果配置中没有 MCP，显示提示信息
        if not mcps:
            InfoBar.info(
                tr("common.info"),
                tr("mcp.ohmy_dialog.no_mcp_info"),
                parent=self,
            )
            # 显示默认的 3 个 MCP
            mcps = self.OHMY_MCPS

        # 填充表格
        for mcp_name, mcp_data in mcps.items():
            row = self.table.rowCount()
            self.table.insertRow(row)

            # 名称
            self.table.setItem(row, 0, QTableWidgetItem(mcp_name))

            # 类型 - 从配置中读取或使用默认值
            if isinstance(mcp_data, dict):
                mcp_type = "remote" if "url" in mcp_data else "local"
                description = mcp_data.get("description", "")
            else:
                # 如果是预设的 MCP，使用预设信息
                mcp_type = (
                    mcp_data.get("type", "remote")
                    if isinstance(mcp_data, dict)
                    else "remote"
                )
                description = (
                    mcp_data.get("description", "")
                    if isinstance(mcp_data, dict)
                    else ""
                )

            self.table.setItem(row, 1, QTableWidgetItem(mcp_type))

            # 状态
            is_enabled = mcp_name not in disabled_mcps
            status_text = (
                tr("mcp.ohmy_dialog.status_enabled")
                if is_enabled
                else tr("mcp.ohmy_dialog.status_disabled")
            )
            status_item = QTableWidgetItem(status_text)
            if is_enabled:
                status_item.setForeground(QColor("#4CAF50"))  # 绿色
            else:
                status_item.setForeground(QColor("#F44336"))  # 红色
            self.table.setItem(row, 2, status_item)

            # 描述 - 使用翻译
            if not description:
                description = tr("mcp.ohmy_dialog.default_desc", name=mcp_name)
            elif description in ["websearch_desc", "context7_desc", "grep_app_desc"]:
                # 如果是预设的描述键，使用翻译
                description = tr(f"mcp.ohmy_dialog.{description}")
            desc_item = QTableWidgetItem(description)
            desc_item.setToolTip(description)
            self.table.setItem(row, 3, desc_item)

    def _on_toggle(self):
        """切换选中 MCP 的状态"""
        row = self.table.currentRow()
        if row < 0:
            InfoBar.warning(
                tr("common.warning"),
                tr("mcp.ohmy_dialog.select_first_warning"),
                parent=self,
            )
            return

        mcp_name = self.table.item(row, 0).text()
        self._toggle_mcp(mcp_name)
        self._load_data()

    def _on_enable_all(self):
        """启用所有 MCP"""
        config = self.main_window.ohmyopencode_config
        if config is None:
            config = {}
            self.main_window.ohmyopencode_config = config

        # 清空 disabled_mcps 列表
        config["disabled_mcps"] = []
        self.main_window.save_ohmyopencode_config()
        self._load_data()
        InfoBar.success(
            tr("common.success"), tr("mcp.ohmy_dialog.enable_all_success"), parent=self
        )

    def _on_disable_all(self):
        """禁用所有 MCP"""
        config = self.main_window.ohmyopencode_config
        if config is None:
            config = {}
            self.main_window.ohmyopencode_config = config

        # 获取所有 MCP 名称
        mcps = config.get("mcp", {})
        if not isinstance(mcps, dict):
            mcps = {}

        # 如果没有配置 MCP，使用默认的 3 个
        if not mcps:
            mcps = self.OHMY_MCPS

        # 将所有 MCP 添加到 disabled_mcps 列表
        config["disabled_mcps"] = list(mcps.keys())
        self.main_window.save_ohmyopencode_config()
        self._load_data()
        InfoBar.success(
            tr("common.success"), tr("dialog.disabled_all_ohmymcp"), parent=self
        )

    def _toggle_mcp(self, mcp_name: str):
        """切换指定 MCP 的启用状态"""
        config = self.main_window.ohmyopencode_config
        if config is None:
            config = {}
            self.main_window.ohmyopencode_config = config

        disabled_mcps = config.get("disabled_mcps", [])
        if not isinstance(disabled_mcps, list):
            disabled_mcps = []

        if mcp_name in disabled_mcps:
            # 当前是禁用状态，启用它
            disabled_mcps.remove(mcp_name)
            InfoBar.success(
                tr("common.success"),
                tr("dialog.mcp_enabled", name=mcp_name),
                parent=self,
            )
        else:
            # 当前是启用状态，禁用它
            disabled_mcps.append(mcp_name)
            InfoBar.success(
                tr("common.success"),
                tr("dialog.mcp_disabled", name=mcp_name),
                parent=self,
            )

        config["disabled_mcps"] = disabled_mcps
        self.main_window.save_ohmyopencode_config()


class MCPDialog(BaseDialog):
    """MCP 编辑对话框"""

    PRESET_MCP_TEMPLATES = {
        "fetch": {
            "name": "mcp-server-fetch",
            "type": "local",
            "command": ["uvx", "mcp-server-fetch"],
            "environment": {},
            "description": "抓取网页内容与资源的基础 MCP 服务器",
            "tags": ["stdio", "http", "web"],
            "homepage": "https://github.com/modelcontextprotocol/servers",
            "docs": "https://github.com/modelcontextprotocol/servers/tree/main/src/fetch",
        },
        "time": {
            "name": "@modelcontextprotocol/server-time",
            "type": "local",
            "command": ["npx", "-y", "@modelcontextprotocol/server-time"],
            "environment": {},
            "description": "提供时间相关工具的轻量 MCP 服务器",
            "tags": ["stdio", "time", "utility"],
            "homepage": "https://github.com/modelcontextprotocol/servers",
            "docs": "https://github.com/modelcontextprotocol/servers/tree/main/src/time",
        },
        "memory": {
            "name": "@modelcontextprotocol/server-memory",
            "type": "local",
            "command": ["npx", "-y", "@modelcontextprotocol/server-memory"],
            "environment": {},
            "description": "提供记忆图谱能力的 MCP 服务器",
            "tags": ["stdio", "memory", "graph"],
            "homepage": "https://github.com/modelcontextprotocol/servers",
            "docs": "https://github.com/modelcontextprotocol/servers/tree/main/src/memory",
        },
        "sequential-thinking": {
            "name": "@modelcontextprotocol/server-sequential-thinking",
            "type": "local",
            "command": [
                "npx",
                "-y",
                "@modelcontextprotocol/server-sequential-thinking",
            ],
            "environment": {},
            "description": "结构化推理与分步思考的 MCP 服务器",
            "tags": ["stdio", "thinking", "reasoning"],
            "homepage": "https://github.com/modelcontextprotocol/servers",
            "docs": "https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking",
        },
        "context7": {
            "name": "@upstash/context7-mcp",
            "type": "local",
            "command": ["npx", "-y", "@upstash/context7-mcp"],
            "environment": {},
            "description": "提供最新文档检索的 Context7 MCP",
            "tags": ["stdio", "docs", "search"],
            "homepage": "https://context7.com",
            "docs": "https://github.com/upstash/context7/blob/master/README.md",
        },
        "chrome-devtools": {
            "name": "chrome-devtools-mcp",
            "type": "local",
            "command": ["npx", "-y", "chrome-devtools-mcp@latest"],
            "environment": {},
            "description": "连接 Chrome DevTools 的调试 MCP 服务器",
            "tags": ["stdio", "browser", "devtools"],
            "homepage": "https://github.com/ChromeDevTools/chrome-devtools-mcp",
            "docs": "https://github.com/ChromeDevTools/chrome-devtools-mcp",
        },
        "open-web-mcp": {
            "name": "open-web-mcp",
            "type": "local",
            "command": ["npx", "-y", "open-web-mcp"],
            "environment": {},
            "description": "开放网页搜索与打开页面的 MCP 服务器",
            "tags": ["stdio", "web", "search"],
            "homepage": "https://github.com/modelcontextprotocol/servers",
            "docs": "https://github.com/modelcontextprotocol/servers",
        },
        "serena": {
            "name": "serena",
            "type": "local",
            "command": [
                "uvx",
                "--from",
                "git+https://github.com/oraios/serena",
                "serena",
                "start-mcp-server",
                "--context",
                "ide-assistant",
            ],
            "environment": {},
            "description": "提供本地项目理解与指令执行的 Serena MCP",
            "tags": ["stdio", "local", "automation"],
            "homepage": "https://github.com/oraios/serena",
            "docs": "https://oraios.github.io/serena/",
        },
    }

    def __init__(
        self, main_window, mcp_name: str = None, mcp_type: str = "local", parent=None
    ):
        super().__init__(parent)
        self.main_window = main_window
        self.mcp_name = mcp_name
        self.mcp_type = mcp_type
        self.is_edit = mcp_name is not None

        if self.is_edit:
            self.setWindowTitle(tr("mcp.dialog.edit_title"))
        else:
            title = (
                tr("mcp.dialog.add_local_title")
                if mcp_type == "local"
                else tr("mcp.dialog.add_remote_title")
            )
            self.setWindowTitle(title)
        self.setMinimumWidth(550)
        self._setup_ui()

        if self.is_edit:
            self._load_mcp_data()
        self._update_preview()

        # 监听语言切换事件
        _lang_manager.language_changed.connect(self._on_language_changed)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        preset_layout = QHBoxLayout()
        preset_layout.setSpacing(6)
        preset_layout.addWidget(BodyLabel(tr("mcp.dialog.preset_label"), self))
        self.preset_buttons = {}
        current_type_label = (
            tr("mcp.remote") if self.mcp_type == "remote" else tr("mcp.local")
        )
        for preset_name in self.PRESET_MCP_TEMPLATES.keys():
            preset_data = self._get_preset_data(preset_name)
            preset_type = preset_data.get("type", "local")
            preset_type_label = (
                tr("mcp.remote") if preset_type == "remote" else tr("mcp.local")
            )
            preset_btn = PushButton(preset_name, self)
            preset_btn.clicked.connect(partial(self._on_preset_clicked, preset_name))
            if preset_type != self.mcp_type:
                preset_btn.setEnabled(False)
                preset_btn.setToolTip(
                    tr("mcp.dialog.preset_disabled_tooltip").format(
                        current=current_type_label, preset=preset_type_label
                    )
                )
            else:
                preset_btn.setToolTip(tr("mcp.dialog.preset_tooltip"))
            preset_layout.addWidget(preset_btn)
            self.preset_buttons[preset_name] = preset_btn
        preset_layout.addStretch()
        layout.addLayout(preset_layout)

        # MCP 名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(BodyLabel(tr("mcp.dialog.mcp_name_label"), self))
        self.name_edit = LineEdit(self)
        self.name_edit.setPlaceholderText(tr("mcp.dialog.mcp_name_placeholder"))
        self.name_edit.setToolTip(get_tooltip("mcp_name"))
        if self.is_edit:
            self.name_edit.setEnabled(False)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        # 启用状态
        self.enabled_check = CheckBox(tr("mcp.dialog.enable_checkbox"), self)
        self.enabled_check.setChecked(True)
        self.enabled_check.setToolTip(get_tooltip("mcp_enabled"))
        layout.addWidget(self.enabled_check)

        if self.mcp_type == "local":
            # 启动命令
            cmd_label = BodyLabel(tr("mcp.dialog.command_label"), self)
            cmd_label.setToolTip(get_tooltip("mcp_command"))
            layout.addWidget(cmd_label)
            self.command_edit = TextEdit(self)
            self.command_edit.setPlaceholderText(tr("mcp.dialog.command_placeholder"))
            self.command_edit.setMaximumHeight(80)
            layout.addWidget(self.command_edit)

            # 环境变量
            env_label = BodyLabel(tr("mcp.dialog.env_label"), self)
            env_label.setToolTip(get_tooltip("mcp_environment"))
            layout.addWidget(env_label)
            self.env_edit = TextEdit(self)
            self.env_edit.setPlaceholderText(tr("mcp.dialog.env_placeholder"))
            self.env_edit.setMaximumHeight(80)
            layout.addWidget(self.env_edit)
        else:
            # URL
            url_layout = QHBoxLayout()
            url_layout.addWidget(BodyLabel(tr("mcp.dialog.url_label"), self))
            self.url_edit = LineEdit(self)
            self.url_edit.setPlaceholderText(tr("mcp.dialog.url_placeholder"))
            self.url_edit.setToolTip(get_tooltip("mcp_url"))
            url_layout.addWidget(self.url_edit)
            layout.addLayout(url_layout)

            # Headers
            headers_label = BodyLabel(tr("mcp.dialog.headers_label"), self)
            headers_label.setToolTip(get_tooltip("mcp_headers"))
            layout.addWidget(headers_label)
            self.headers_edit = TextEdit(self)
            self.headers_edit.setPlaceholderText(tr("mcp.dialog.headers_placeholder"))
            self.headers_edit.setMaximumHeight(80)
            layout.addWidget(self.headers_edit)

        # 超时
        timeout_layout = QHBoxLayout()
        timeout_layout.addWidget(BodyLabel(tr("mcp.dialog.timeout_label"), self))
        self.timeout_spin = SpinBox(self)
        self.timeout_spin.setRange(1000, 300000)
        self.timeout_spin.setValue(5000)
        self.timeout_spin.setToolTip(get_tooltip("mcp_timeout"))
        timeout_layout.addWidget(self.timeout_spin)
        layout.addLayout(timeout_layout)

        # 附加信息（默认收起）
        self.extra_group = QGroupBox(tr("mcp.additional_info"), self)
        self.extra_group.setCheckable(True)
        self.extra_group.setChecked(False)
        self.extra_group.setToolTip(tr("dialog.tooltip_toggle_expand"))
        self.extra_group.toggled.connect(self._on_extra_group_toggled)
        group_layout = QVBoxLayout(self.extra_group)
        group_layout.setSpacing(0)

        self.extra_content = QWidget(self.extra_group)
        extra_layout = QVBoxLayout(self.extra_content)
        extra_layout.setSpacing(8)

        desc_label = BodyLabel(tr("skill.description") + ":", self.extra_group)
        self.desc_edit = TextEdit(self.extra_group)
        self.desc_edit.setPlaceholderText(tr("dialog.placeholder_mcp_desc"))
        self.desc_edit.setMaximumHeight(80)
        extra_layout.addWidget(desc_label)
        extra_layout.addWidget(self.desc_edit)

        tags_layout = QHBoxLayout()
        tags_layout.addWidget(BodyLabel(tr("mcp.tags") + ":", self.extra_group))
        self.tags_edit = LineEdit(self.extra_group)
        self.tags_edit.setPlaceholderText(tr("dialog.placeholder_mcp_tags"))
        tags_layout.addWidget(self.tags_edit)
        extra_layout.addLayout(tags_layout)

        homepage_layout = QHBoxLayout()
        homepage_layout.addWidget(
            BodyLabel(tr("mcp.homepage_link") + ":", self.extra_group)
        )
        self.homepage_edit = LineEdit(self.extra_group)
        self.homepage_edit.setPlaceholderText("https://github.com/xxx")
        homepage_layout.addWidget(self.homepage_edit)
        extra_layout.addLayout(homepage_layout)

        docs_layout = QHBoxLayout()
        docs_layout.addWidget(BodyLabel(tr("mcp.docs_link") + ":", self.extra_group))
        self.docs_edit = LineEdit(self.extra_group)
        self.docs_edit.setPlaceholderText("https://docs.example.com")
        docs_layout.addWidget(self.docs_edit)
        extra_layout.addLayout(docs_layout)

        group_layout.addWidget(self.extra_content)
        self.extra_content.setVisible(False)
        layout.addWidget(self.extra_group)

        # JSON 预览
        self.preview_group = QGroupBox(tr("mcp.full_json_preview"), self)
        preview_layout = QVBoxLayout(self.preview_group)
        preview_layout.setSpacing(8)

        preview_header = QHBoxLayout()
        preview_header.addWidget(
            BodyLabel(tr("mcp.full_mcp_config_preview"), self.preview_group)
        )
        self.preview_wrap_check = CheckBox(
            tr("mcp.include_wrapper"), self.preview_group
        )
        self.preview_wrap_check.setChecked(False)
        self.preview_wrap_check.stateChanged.connect(lambda: self._update_preview())
        preview_header.addWidget(self.preview_wrap_check)
        preview_header.addStretch()
        self.format_btn = PushButton(tr("cli_export.format_json"), self.preview_group)
        self.format_btn.clicked.connect(self._on_format_preview)
        preview_header.addWidget(self.format_btn)
        preview_layout.addLayout(preview_header)

        self.preview_edit = TextEdit(self.preview_group)
        self.preview_edit.setReadOnly(True)
        self.preview_edit.setMinimumHeight(180)
        self.preview_edit.setLineWrapMode(QTextEdit.NoWrap)
        self.preview_edit.setFont(QFont("Consolas", 10))
        preview_layout.addWidget(self.preview_edit)
        layout.addWidget(self.preview_group)

        self._preview_highlighter = JsonTomlHighlighter(
            self.preview_edit.document(), isDarkTheme()
        )
        self.preview_edit.cursorPositionChanged.connect(
            lambda: apply_bracket_match_highlight(self.preview_edit, isDarkTheme())
        )

        self._bind_preview_signals()
        if self.mcp_type == "remote":
            self.preview_wrap_check.setChecked(True)
        self._update_preview()

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = PushButton(tr("common.cancel"), self)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.save_btn = PrimaryPushButton(tr("common.save"), self)
        self.save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)

    @classmethod
    def register_preset(cls, name: str, data: Dict[str, Any]) -> None:
        """注册或更新 MCP 预设模板"""
        if not name or not isinstance(data, dict):
            return
        cls.PRESET_MCP_TEMPLATES[name] = data

    def _get_preset_data(self, preset_key: str) -> Dict[str, Any]:
        data = self.PRESET_MCP_TEMPLATES.get(preset_key, {})
        if not isinstance(data, dict):
            return {}
        return {
            "name": data.get("name") or preset_key,
            "type": data.get("type", "local"),
            "command": data.get("command", []),
            "environment": data.get("environment", {}),
            "description": data.get("description", ""),
            "tags": data.get("tags", []),
            "homepage": data.get("homepage", ""),
            "docs": data.get("docs", ""),
        }

    def _on_preset_clicked(self, preset_key: str) -> None:
        preset = self._get_preset_data(preset_key)
        if not preset:
            InfoBar.warning(
                tr("common.hint"), tr("dialog.preset_data_unavailable"), parent=self
            )
            return
        if preset.get("type") != self.mcp_type:
            InfoBar.warning(
                tr("common.hint"), tr("dialog.preset_type_mismatch"), parent=self
            )
            return
        # 使用预设的键名作为 MCP 名称，而不是 name 字段（name 字段可能包含特殊字符）
        if self.name_edit.isEnabled():
            self.name_edit.setText(preset_key)
        if self.mcp_type == "local":
            command = preset.get("command", [])
            env = preset.get("environment", {})
            self.command_edit.setPlainText(
                json.dumps(command, ensure_ascii=False) if command else ""
            )
            self.env_edit.setPlainText(
                json.dumps(env, indent=2, ensure_ascii=False) if env else ""
            )
        self._apply_extra_info(preset)
        self._update_preview()

    def _load_mcp_data(self):
        config = self.main_window.opencode_config or {}
        mcp = config.get("mcp", {}).get(self.mcp_name, {})

        self.name_edit.setText(self.mcp_name)
        self.enabled_check.setChecked(mcp.get("enabled", True))
        self.timeout_spin.setValue(mcp.get("timeout", 5000))

        if self.mcp_type == "local":
            cmd = mcp.get("command", [])
            if cmd:
                self.command_edit.setPlainText(json.dumps(cmd, ensure_ascii=False))
            env = mcp.get("environment", {})
            if env:
                self.env_edit.setPlainText(
                    json.dumps(env, indent=2, ensure_ascii=False)
                )
        else:
            self.url_edit.setText(mcp.get("url", ""))
            headers = mcp.get("headers", {})
            if headers:
                self.headers_edit.setPlainText(
                    json.dumps(headers, indent=2, ensure_ascii=False)
                )

        extra_info = {
            "description": mcp.get("description", ""),
            "tags": mcp.get("tags", []),
            "homepage": mcp.get("homepage", ""),
            "docs": mcp.get("docs", ""),
        }
        self._apply_extra_info(extra_info)
        self._update_preview()

    def _on_save(self):
        name = self.name_edit.text().strip()
        if not name:
            InfoBar.error(
                tr("common.error"), tr("mcp.dialog.name_required"), parent=self
            )
            return

        self._update_preview()

        config = self.main_window.opencode_config
        if config is None:
            config = {}
            self.main_window.opencode_config = config

        if "mcp" not in config:
            config["mcp"] = {}

        if not self.is_edit and name in config["mcp"]:
            InfoBar.error(tr("common.error"), tr("mcp.dialog.name_exists"), parent=self)
            return

        mcp_data = {
            "type": self.mcp_type,
            "enabled": self.enabled_check.isChecked(),
            "timeout": self.timeout_spin.value(),
        }

        if self.mcp_type == "local":
            cmd_text = self.command_edit.toPlainText().strip()
            if cmd_text:
                try:
                    mcp_data["command"] = json.loads(cmd_text)
                except json.JSONDecodeError as e:
                    InfoBar.error(
                        tr("common.error"),
                        tr("mcp.dialog.command_invalid").format(error=str(e)),
                        parent=self,
                    )
                    return

            env_text = self.env_edit.toPlainText().strip()
            if env_text:
                try:
                    mcp_data["environment"] = json.loads(env_text)
                except json.JSONDecodeError as e:
                    InfoBar.error(
                        tr("common.error"),
                        tr("mcp.dialog.env_invalid").format(error=str(e)),
                        parent=self,
                    )
                    return
        else:
            url = self.url_edit.text().strip()
            if not url:
                InfoBar.error(
                    tr("common.error"), tr("mcp.dialog.url_required"), parent=self
                )
                return
            mcp_data["url"] = url

            headers_text = self.headers_edit.toPlainText().strip()
            if headers_text:
                try:
                    mcp_data["headers"] = json.loads(headers_text)
                except json.JSONDecodeError as e:
                    InfoBar.error(
                        tr("common.error"),
                        tr("mcp.dialog.headers_invalid").format(error=str(e)),
                        parent=self,
                    )
                    return

        self._update_extra_info(mcp_data)
        config["mcp"][name] = mcp_data
        self.main_window.save_opencode_config()
        self.accept()

    def _apply_extra_info(self, data: Dict[str, Any]) -> None:
        description = (data.get("description") or "").strip()
        tags = data.get("tags", [])
        homepage = (data.get("homepage") or "").strip()
        docs = (data.get("docs") or "").strip()

        self.desc_edit.setPlainText(description)
        if isinstance(tags, list):
            tags_text = ", ".join(str(tag).strip() for tag in tags if str(tag).strip())
        else:
            tags_text = str(tags).strip()
        self.tags_edit.setText(tags_text)
        self.homepage_edit.setText(homepage)
        self.docs_edit.setText(docs)

    def _update_extra_info(self, mcp_data: Dict[str, Any]) -> None:
        """更新额外信息到 MCP 数据

        注意：根据 OpenCode 官方文档，MCP 配置只能包含固定的标准字段：
        - Local MCP: type, command, environment, enabled, timeout
        - Remote MCP: type, url, headers, oauth, enabled, timeout

        description、tags、homepage、docs 等字段仅用于 UI 显示，不应写入配置文件。
        """
        # 不再写入非标准字段，保持配置文件符合 OpenCode 规范
        pass

    def _bind_preview_signals(self) -> None:
        self.name_edit.textChanged.connect(lambda: self._update_preview())
        self.enabled_check.stateChanged.connect(lambda: self._update_preview())
        self.timeout_spin.valueChanged.connect(lambda: self._update_preview())
        self.desc_edit.textChanged.connect(lambda: self._update_preview())
        self.tags_edit.textChanged.connect(lambda: self._update_preview())
        self.homepage_edit.textChanged.connect(lambda: self._update_preview())
        self.docs_edit.textChanged.connect(lambda: self._update_preview())

        if self.mcp_type == "local":
            self.command_edit.textChanged.connect(lambda: self._update_preview())
            self.env_edit.textChanged.connect(lambda: self._update_preview())
        else:
            self.url_edit.textChanged.connect(lambda: self._update_preview())
            self.headers_edit.textChanged.connect(lambda: self._update_preview())

    def _on_extra_group_toggled(self, checked: bool) -> None:
        self.extra_content.setVisible(checked)

    def _parse_json_text(self, text: str, default_value: Any) -> Any:
        if not text:
            return default_value
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text

    def _collect_preview_data(self) -> Dict[str, Any]:
        tags_text = self.tags_edit.text().strip()
        tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]

        data = {
            "type": self.mcp_type,
            "enabled": self.enabled_check.isChecked(),
            "timeout": self.timeout_spin.value(),
        }

        description = self.desc_edit.toPlainText().strip()
        if description:
            data["description"] = description

        if tags:
            data["tags"] = tags

        homepage = self.homepage_edit.text().strip()
        if homepage:
            data["homepage"] = homepage

        docs = self.docs_edit.text().strip()
        if docs:
            data["docs"] = docs

        if self.mcp_type == "local":
            command_text = self.command_edit.toPlainText().strip()
            env_text = self.env_edit.toPlainText().strip()
            data["command"] = self._parse_json_text(command_text, [])
            data["environment"] = self._parse_json_text(env_text, {})
        else:
            data["url"] = self.url_edit.text().strip()
            headers_text = self.headers_edit.toPlainText().strip()
            data["headers"] = self._parse_json_text(headers_text, {})

        return data

    def _update_preview(self) -> None:
        data = self._collect_preview_data()
        if self.preview_wrap_check.isChecked():
            data = {"mcpServers": {self.name_edit.text().strip() or "server": data}}
        preview_text = json.dumps(data, indent=2, ensure_ascii=False)
        self.preview_edit.setPlainText(preview_text)
        apply_bracket_match_highlight(self.preview_edit, isDarkTheme())

    def _on_format_preview(self) -> None:
        self._update_preview()
        self.preview_edit.moveCursor(QTextCursor.Start)

    def _on_language_changed(self, lang_code: str) -> None:
        """处理语言切换事件"""
        # 更新窗口标题
        if self.is_edit:
            self.setWindowTitle(tr("mcp.dialog.edit_title"))
        else:
            title = (
                tr("mcp.dialog.add_local_title")
                if self.mcp_type == "local"
                else tr("mcp.dialog.add_remote_title")
            )
            self.setWindowTitle(title)

        # 更新 QGroupBox 标题
        self.extra_group.setTitle(tr("mcp.additional_info"))
        self.preview_group.setTitle(tr("mcp.full_json_preview"))

        # 更新 CheckBox 文本
        self.preview_wrap_check.setText(tr("mcp.include_wrapper"))
        self.enabled_check.setText(tr("mcp.dialog.enable_checkbox"))

        # 更新按钮文本
        self.cancel_btn.setText(tr("common.cancel"))
        self.save_btn.setText(tr("common.save"))
        self.format_btn.setText(tr("cli_export.format_json"))


# ==================== OpenCode Agent 页面 ====================
class OpenCodeAgentPage(BasePage):
    """OpenCode 原生 Agent 配置页面"""

    def __init__(self, main_window, parent=None):
        super().__init__(tr("agent.title"), parent)
        self.main_window = main_window
        self._setup_ui()
        self._load_data()
        # 连接配置变更信号
        self.main_window.config_changed.connect(self._on_config_changed)

    def _on_config_changed(self):
        """配置变更时刷新数据"""
        self._load_data()

    def _setup_ui(self):
        # 工具栏
        toolbar = QHBoxLayout()

        self.add_btn = PrimaryPushButton(FIF.ADD, tr("agent.add_agent"), self)
        self.add_btn.clicked.connect(self._on_add)
        toolbar.addWidget(self.add_btn)

        self.preset_btn = PushButton(FIF.LIBRARY, tr("model.add_from_preset"), self)
        self.preset_btn.clicked.connect(self._on_add_preset)
        toolbar.addWidget(self.preset_btn)

        self.edit_btn = PushButton(FIF.EDIT, tr("common.edit"), self)
        self.edit_btn.clicked.connect(self._on_edit)
        toolbar.addWidget(self.edit_btn)

        self.delete_btn = PushButton(FIF.DELETE, tr("common.delete"), self)
        self.delete_btn.clicked.connect(self._on_delete)
        toolbar.addWidget(self.delete_btn)

        toolbar.addStretch()
        self._layout.addLayout(toolbar)

        # Agent 列表
        self.table = TableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            [
                tr("common.name"),
                tr("agent.mode"),
                tr("agent.temperature"),
                tr("common.description"),
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.doubleClicked.connect(self._on_edit)
        self._layout.addWidget(self.table)

    def _load_data(self):
        self.table.setRowCount(0)
        config = self.main_window.opencode_config or {}
        agents = config.get("agent", {})

        # 添加类型检查，防止 agent 字段为非字典类型时崩溃
        if not isinstance(agents, dict):
            agents = {}

        for name, data in agents.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(data.get("mode", "subagent")))
            self.table.setItem(
                row, 2, QTableWidgetItem(str(data.get("temperature", "")))
            )
            desc = data.get("description", "")
            if not desc:
                desc = PRESET_OPENCODE_AGENTS.get(name, {}).get("description", "")
            desc_item = QTableWidgetItem(desc[:50] + "..." if len(desc) > 50 else desc)
            desc_item.setToolTip(desc)
            self.table.setItem(row, 3, desc_item)

    def _on_add(self):
        dialog = OpenCodeAgentDialog(self.main_window, parent=self)
        if dialog.exec_():
            self._load_data()
            self.show_success(tr("common.success"), tr("agent.added_success"))

    def _on_add_preset(self):
        dialog = PresetOpenCodeAgentDialog(self.main_window, parent=self)
        if dialog.exec_():
            self._load_data()
            self.show_success(tr("common.success"), tr("agent.preset_added_success"))

    def _on_edit(self):
        row = self.table.currentRow()
        if row < 0:
            self.show_warning(tr("common.info"), tr("agent.select_first"))
            return

        name = self.table.item(row, 0).text()
        dialog = OpenCodeAgentDialog(self.main_window, agent_name=name, parent=self)
        if dialog.exec_():
            self._load_data()
            self.show_success(tr("common.success"), tr("agent.updated_success"))

    def _on_delete(self):
        row = self.table.currentRow()
        if row < 0:
            self.show_warning(tr("common.info"), tr("agent.select_first"))
            return

        name = self.table.item(row, 0).text()
        w = FluentMessageBox(
            tr("common.confirm_delete_title"),
            tr("dialog.confirm_delete_agent", name=name),
            self,
        )
        if w.exec_():
            config = self.main_window.opencode_config or {}
            if "agent" in config and name in config["agent"]:
                del config["agent"][name]
                self.main_window.save_opencode_config()
                self._load_data()
                self.show_success(
                    tr("common.success"), tr("dialog.agent_deleted", name=name)
                )


class OpenCodeAgentDialog(BaseDialog):
    """OpenCode Agent 编辑对话框 - 完整版本"""

    def __init__(self, main_window, agent_name: str = None, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.agent_name = agent_name
        self.is_edit = agent_name is not None

        self.setWindowTitle(
            tr("agent.dialog.edit_title")
            if self.is_edit
            else tr("agent.dialog.add_title")
        )
        self.setMinimumSize(600, 700)
        self._setup_ui()
        self._apply_scroll_style()

        if self.is_edit:
            self._load_agent_data()

    def _apply_scroll_style(self):
        """应用滚动区域内部样式"""
        if isDarkTheme():
            # 确保滚动区域内部也是深色
            self.setStyleSheet(
                self.styleSheet()
                + """
                QScrollArea { background-color: #0d1117; border: none; }
                QScrollArea > QWidget > QWidget { background-color: #0d1117; }
                QWidget { background-color: transparent; }
                CardWidget { background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; }
            """
            )

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 使用滚动区域
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content.setObjectName("scrollContent")
        if isDarkTheme():
            content.setStyleSheet(
                "QWidget#scrollContent { background-color: #0d1117; }"
            )
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(10)

        # ===== 基本信息 =====
        basic_card = CardWidget(content)
        basic_layout = QVBoxLayout(basic_card)
        basic_layout.setSpacing(10)
        basic_layout.addWidget(
            SubtitleLabel(tr("agent.dialog.agent_key_label"), basic_card)
        )

        # Agent 名称
        name_layout = QHBoxLayout()
        name_layout.setSpacing(8)
        name_label = BodyLabel(tr("agent.dialog.agent_key_label"), basic_card)
        name_label.setMinimumWidth(80)
        name_layout.addWidget(name_label)
        self.name_edit = LineEdit(basic_card)
        self.name_edit.setPlaceholderText(tr("agent.dialog.agent_key_placeholder"))
        self.name_edit.setMinimumHeight(36)
        self.name_edit.setToolTip(get_tooltip("agent_name"))
        if self.is_edit:
            self.name_edit.setEnabled(False)
        name_layout.addWidget(self.name_edit)
        basic_layout.addLayout(name_layout)

        # 描述
        desc_layout = QHBoxLayout()
        desc_layout.setSpacing(8)
        desc_label = BodyLabel(tr("common.description") + ":", basic_card)
        desc_label.setMinimumWidth(80)
        desc_layout.addWidget(desc_label)
        self.desc_edit = LineEdit(basic_card)
        self.desc_edit.setPlaceholderText(tr("dialog.placeholder_agent_desc"))
        self.desc_edit.setMinimumHeight(36)
        self.desc_edit.setToolTip(get_tooltip("agent_description"))
        desc_layout.addWidget(self.desc_edit)
        basic_layout.addLayout(desc_layout)

        # 模式
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(8)
        mode_label = BodyLabel(tr("agent.dialog.mode_label"), basic_card)
        mode_label.setMinimumWidth(80)
        mode_layout.addWidget(mode_label)
        self.mode_combo = ComboBox(basic_card)
        self.mode_combo.addItems(["primary", "subagent", "all"])
        self.mode_combo.setMinimumHeight(36)
        self.mode_combo.setToolTip(get_tooltip("opencode_agent_mode"))
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        basic_layout.addLayout(mode_layout)

        # 模型 (可选)
        model_layout = QHBoxLayout()
        model_layout.setSpacing(8)
        model_label = BodyLabel(tr("agent.dialog.model_optional_label"), basic_card)
        model_label.setMinimumWidth(80)
        model_layout.addWidget(model_label)
        self.model_edit = LineEdit(basic_card)
        self.model_edit.setPlaceholderText("claude-sonnet-4-5-20250929")
        self.model_edit.setMinimumHeight(36)
        self.model_edit.setToolTip(get_tooltip("agent_model"))
        model_layout.addWidget(self.model_edit)
        basic_layout.addLayout(model_layout)

        content_layout.addWidget(basic_card)

        # ===== 参数配置 =====
        param_card = CardWidget(content)
        param_layout = QVBoxLayout(param_card)
        param_layout.setSpacing(10)
        param_layout.addWidget(
            SubtitleLabel(tr("agent.dialog.param_config_title"), param_card)
        )

        # Temperature
        temp_layout = QHBoxLayout()
        temp_layout.setSpacing(8)
        temp_layout.addWidget(
            BodyLabel(tr("agent.dialog.temperature_label"), param_card)
        )
        self.temp_slider = Slider(Qt.Orientation.Horizontal, param_card)
        self.temp_slider.setRange(0, 200)
        self.temp_slider.setValue(30)
        self.temp_slider.setToolTip(get_tooltip("opencode_agent_temperature"))
        self.temp_label = BodyLabel("0.3", param_card)
        self.temp_slider.valueChanged.connect(
            lambda v: self.temp_label.setText(f"{v / 100:.1f}")
        )
        temp_layout.addWidget(self.temp_slider)
        temp_layout.addWidget(self.temp_label)
        param_layout.addLayout(temp_layout)

        # 最大步数
        steps_layout = QHBoxLayout()
        steps_layout.setSpacing(8)
        steps_layout.addWidget(
            BodyLabel(tr("agent.dialog.max_steps_label"), param_card)
        )
        self.maxsteps_spin = SpinBox(param_card)
        self.maxsteps_spin.setRange(0, 1000)
        self.maxsteps_spin.setValue(0)
        self.maxsteps_spin.setSpecialValueText(tr("agent.dialog.max_steps_unlimited"))
        self.maxsteps_spin.setMinimumHeight(36)
        self.maxsteps_spin.setToolTip(get_tooltip("opencode_agent_maxSteps"))
        steps_layout.addWidget(self.maxsteps_spin)
        steps_layout.addStretch()
        param_layout.addLayout(steps_layout)

        # 复选框
        check_layout = QHBoxLayout()
        check_layout.setSpacing(16)
        self.hidden_check = CheckBox(tr("agent.dialog.hidden_checkbox"), param_card)
        self.hidden_check.setToolTip(get_tooltip("opencode_agent_hidden"))
        check_layout.addWidget(self.hidden_check)
        self.disable_check = CheckBox(tr("agent.dialog.disable_checkbox"), param_card)
        self.disable_check.setToolTip(get_tooltip("opencode_agent_disable"))
        check_layout.addWidget(self.disable_check)
        check_layout.addStretch()
        param_layout.addLayout(check_layout)

        content_layout.addWidget(param_card)

        # ===== 工具和权限配置 =====
        tools_card = CardWidget(content)
        tools_layout = QVBoxLayout(tools_card)
        tools_layout.setSpacing(8)
        tools_layout.addWidget(
            SubtitleLabel(tr("agent.dialog.tools_permission_title"), tools_card)
        )

        # 工具配置 (JSON)
        tools_label = BodyLabel(tr("agent.dialog.tools_label"), tools_card)
        tools_label.setToolTip(get_tooltip("opencode_agent_tools"))
        tools_layout.addWidget(tools_label)
        self.tools_edit = TextEdit(tools_card)
        self.tools_edit.setPlaceholderText(tr("agent.dialog.tools_placeholder"))
        self.tools_edit.setMinimumHeight(100)
        self.tools_edit.setMaximumHeight(150)
        tools_layout.addWidget(self.tools_edit)

        # 权限配置 (JSON)
        perm_label = BodyLabel(tr("agent.dialog.permission_label"), tools_card)
        perm_label.setToolTip(get_tooltip("opencode_agent_permission"))
        tools_layout.addWidget(perm_label)
        self.permission_edit = TextEdit(tools_card)
        self.permission_edit.setPlaceholderText('{"edit": "allow", "bash": "ask"}')
        self.permission_edit.setMinimumHeight(150)
        self.permission_edit.setMaximumHeight(160)
        tools_layout.addWidget(self.permission_edit)
        tools_layout.addWidget(self.permission_edit, stretch=1)
        content_layout.addWidget(tools_card)

        # ===== 系统提示词 =====
        prompt_card = CardWidget(content)
        prompt_layout = QVBoxLayout(prompt_card)
        prompt_layout.setSpacing(8)
        prompt_label = SubtitleLabel(
            tr("agent.dialog.system_prompt_title"), prompt_card
        )
        prompt_label.setToolTip(get_tooltip("opencode_agent_prompt"))
        prompt_layout.addWidget(prompt_label)
        self.prompt_edit = TextEdit(prompt_card)
        self.prompt_edit.setPlaceholderText(tr("dialog.placeholder_custom_prompt"))
        self.prompt_edit.setMinimumHeight(80)
        prompt_layout.addWidget(self.prompt_edit)

        content_layout.addWidget(prompt_card)
        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        # ===== 按钮 =====
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = PushButton(tr("common.cancel"), self)
        self.cancel_btn.setMinimumHeight(36)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.save_btn = PrimaryPushButton(tr("common.save"), self)
        self.save_btn.setMinimumHeight(36)
        self.save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)

    def _load_agent_data(self):
        config = self.main_window.opencode_config or {}
        agent = config.get("agent", {}).get(self.agent_name, {})

        self.name_edit.setText(self.agent_name)
        self.desc_edit.setText(agent.get("description", ""))

        mode = agent.get("mode", "subagent")
        self.mode_combo.setCurrentText(mode)

        self.model_edit.setText(agent.get("model", ""))

        temp = agent.get("temperature", 0.3)
        self.temp_slider.setValue(int(temp * 100))

        maxsteps = agent.get("maxSteps", 0)
        self.maxsteps_spin.setValue(maxsteps if maxsteps else 0)

        self.hidden_check.setChecked(agent.get("hidden", False))
        self.disable_check.setChecked(agent.get("disable", False))

        tools = agent.get("tools", {})
        if tools:
            self.tools_edit.setPlainText(
                json.dumps(tools, indent=2, ensure_ascii=False)
            )

        permission = agent.get("permission", {})
        if permission:
            self.permission_edit.setPlainText(
                json.dumps(permission, indent=2, ensure_ascii=False)
            )

        self.prompt_edit.setPlainText(agent.get("prompt", ""))

    def _on_save(self):
        name = self.name_edit.text().strip()
        if not name:
            InfoBar.error(
                tr("common.error"), tr("agent.dialog.key_required"), parent=self
            )
            return

        desc = self.desc_edit.text().strip()
        if not desc:
            InfoBar.error(tr("common.error"), "请输入 Agent 描述", parent=self)
            return

        config = self.main_window.opencode_config
        if config is None:
            config = {}
            self.main_window.opencode_config = config

        if "agent" not in config:
            config["agent"] = {}

        if not self.is_edit and name in config["agent"]:
            InfoBar.error(
                tr("common.error"), tr("agent.dialog.key_exists"), parent=self
            )
            return

        agent_data = {
            "description": desc,
            "mode": self.mode_combo.currentText(),
        }

        # 模型
        model = self.model_edit.text().strip()
        if model:
            agent_data["model"] = model

        # Temperature (只有非默认值才保存)
        temp = self.temp_slider.value() / 100
        if temp != 0.3:
            agent_data["temperature"] = temp

        # 最大步数
        maxsteps = self.maxsteps_spin.value()
        if maxsteps > 0:
            agent_data["maxSteps"] = maxsteps

        # 复选框
        if self.hidden_check.isChecked():
            agent_data["hidden"] = True
        if self.disable_check.isChecked():
            agent_data["disable"] = True

        # 工具配置
        tools_text = self.tools_edit.toPlainText().strip()
        if tools_text:
            try:
                tools = json.loads(tools_text)
                if tools:
                    agent_data["tools"] = tools
            except json.JSONDecodeError as e:
                InfoBar.error(
                    tr("common.error"),
                    tr("agent.dialog.tools_invalid").format(error=str(e)),
                    parent=self,
                )
                return

        # 权限配置
        perm_text = self.permission_edit.toPlainText().strip()
        if perm_text:
            try:
                permission = json.loads(perm_text)
                if permission:
                    agent_data["permission"] = permission
            except json.JSONDecodeError as e:
                InfoBar.error(
                    tr("common.error"), f"权限配置 JSON 格式错误: {e}", parent=self
                )
                return

        # 系统提示词
        prompt = self.prompt_edit.toPlainText().strip()
        if prompt:
            agent_data["prompt"] = prompt

        config["agent"][name] = agent_data
        self.main_window.save_opencode_config()
        self.accept()


class PresetOpenCodeAgentDialog(BaseDialog):
    """预设 OpenCode Agent 选择对话框"""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window

        self.setWindowTitle(tr("agent.preset_dialog.title"))
        self.setMinimumSize(450, 350)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        layout.addWidget(BodyLabel(tr("agent.preset_dialog.select_label"), self))

        self.agent_list = ListWidget(self)
        self.agent_list.setSelectionMode(QAbstractItemView.MultiSelection)
        for name, data in PRESET_OPENCODE_AGENTS.items():
            self.agent_list.addItem(f"{name} - {data.get('description', '')[:40]}")
        layout.addWidget(self.agent_list)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = PushButton(tr("common.cancel"), self)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.add_btn = PrimaryPushButton(tr("agent.preset_dialog.add_selected"), self)
        self.add_btn.clicked.connect(self._on_add)
        btn_layout.addWidget(self.add_btn)

        layout.addLayout(btn_layout)

    def _on_add(self):
        selected = self.agent_list.selectedItems()
        if not selected:
            InfoBar.warning(
                tr("common.hint"), tr("dialog.select_at_least_one_agent"), parent=self
            )
            return

        config = self.main_window.opencode_config
        if config is None:
            config = {}
            self.main_window.opencode_config = config

        if "agent" not in config:
            config["agent"] = {}

        added = 0
        for item in selected:
            name = item.text().split(" - ")[0]
            if name in PRESET_OPENCODE_AGENTS:
                preset = PRESET_OPENCODE_AGENTS[name]
                config["agent"][name] = {
                    "mode": preset.get("mode", "subagent"),
                    "description": preset.get("description", ""),
                }
                if "tools" in preset:
                    config["agent"][name]["tools"] = preset["tools"]
                if "permission" in preset:
                    config["agent"][name]["permission"] = preset["permission"]
                added += 1

        self.main_window.save_opencode_config()
        InfoBar.success(
            tr("common.success"), tr("dialog.agents_added", count=added), parent=self
        )
        self.accept()


# ==================== Permission 页面 ====================
class PermissionPage(BasePage):
    """权限管理页面"""

    def __init__(self, main_window, parent=None):
        super().__init__(tr("permission.title"), parent)
        self.main_window = main_window
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        # 工具栏
        toolbar = QHBoxLayout()

        self.add_btn = PrimaryPushButton(FIF.ADD, tr("permission.add_permission"), self)
        self.add_btn.clicked.connect(self._on_add)
        toolbar.addWidget(self.add_btn)

        self.edit_btn = PushButton(FIF.EDIT, tr("common.edit"), self)
        self.edit_btn.clicked.connect(self._on_edit)
        toolbar.addWidget(self.edit_btn)

        self.delete_btn = PushButton(FIF.DELETE, tr("common.delete"), self)
        self.delete_btn.clicked.connect(self._on_delete)
        toolbar.addWidget(self.delete_btn)

        toolbar.addStretch()

        # 快捷按钮
        for tool in ["Bash", "Read", "Write", "Edit", "WebFetch"]:
            btn = PushButton(tool, self)
            btn.clicked.connect(lambda checked, t=tool: self._quick_add(t))
            toolbar.addWidget(btn)

        self._layout.addLayout(toolbar)

        # 权限列表
        self.table = TableWidget(self)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(
            [tr("permission.tool_name"), tr("permission.permission_level")]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.doubleClicked.connect(self._on_edit)
        self._layout.addWidget(self.table)

    def _load_data(self):
        self.table.setRowCount(0)
        config = self.main_window.opencode_config or {}
        permissions = config.get("permission", {})

        # 添加类型检查，防止 permission 字段为非字典类型时崩溃
        if not isinstance(permissions, dict):
            permissions = {}

        for tool, level in permissions.items():
            # 跳过 skill 子配置
            if tool == "skill":
                continue
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(tool))
            self.table.setItem(row, 1, QTableWidgetItem(str(level)))

    def _on_add(self):
        dialog = PermissionDialog(self.main_window, parent=self)
        if dialog.exec_():
            self._load_data()
            self.show_success(tr("common.success"), tr("permission.permission_saved"))

    def _on_edit(self):
        row = self.table.currentRow()
        if row < 0:
            self.show_warning(tr("common.warning"), tr("common.select_item_first"))
            return

        tool = self.table.item(row, 0).text()
        level = self.table.item(row, 1).text()
        dialog = PermissionDialog(self.main_window, tool=tool, level=level, parent=self)
        if dialog.exec_():
            self._load_data()
            self.show_success(tr("common.success"), tr("permission.permission_saved"))

    def _quick_add(self, tool: str):
        config = self.main_window.opencode_config
        if config is None:
            config = {}
            self.main_window.opencode_config = config

        if "permission" not in config:
            config["permission"] = {}

        config["permission"][tool] = "allow"
        self.main_window.save_opencode_config()
        self._load_data()
        self.show_success(
            tr("common.success"),
            tr("permission.permission_added", tool=tool, level="allow"),
        )

    def _on_delete(self):
        row = self.table.currentRow()
        if row < 0:
            self.show_warning(tr("common.warning"), tr("common.select_item_first"))
            return

        tool = self.table.item(row, 0).text()
        config = self.main_window.opencode_config or {}
        if "permission" in config and tool in config["permission"]:
            del config["permission"][tool]
            self.main_window.save_opencode_config()
            self._load_data()
            self.show_success(
                tr("common.success"), tr("permission.permission_deleted_msg", tool=tool)
            )


class PermissionDialog(BaseDialog):
    """权限编辑对话框"""

    def __init__(self, main_window, tool: str = None, level: str = None, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.original_tool = tool
        self.is_edit = tool is not None

        self.setWindowTitle(
            tr("permission.edit_permission")
            if self.is_edit
            else tr("permission.add_permission")
        )
        self.setMinimumWidth(400)
        self._setup_ui()

        if self.is_edit:
            self.tool_edit.setText(tool)
            self.tool_edit.setEnabled(False)
            if level:
                self.level_combo.setCurrentText(level)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 工具名称
        tool_layout = QHBoxLayout()
        tool_layout.addWidget(BodyLabel(tr("permission.tool_name") + ":", self))
        self.tool_edit = LineEdit(self)
        self.tool_edit.setPlaceholderText(tr("dialog.placeholder_tool_names"))
        self.tool_edit.setToolTip(get_tooltip("permission_tool"))
        tool_layout.addWidget(self.tool_edit)
        layout.addLayout(tool_layout)

        # 权限级别
        level_layout = QHBoxLayout()
        level_layout.addWidget(BodyLabel(tr("permission.permission_level") + ":", self))
        self.level_combo = ComboBox(self)
        self.level_combo.addItems(
            [tr("permission.allow"), tr("permission.ask"), tr("permission.deny")]
        )
        self.level_combo.setToolTip(get_tooltip("permission_level"))
        level_layout.addWidget(self.level_combo)
        layout.addLayout(level_layout)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = PushButton(tr("common.cancel"), self)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.save_btn = PrimaryPushButton(tr("common.save"), self)
        self.save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)

    def _on_save(self):
        tool = self.tool_edit.text().strip()
        if not tool:
            InfoBar.error(tr("common.error"), tr("dialog.enter_tool_name"), parent=self)
            return

        config = self.main_window.opencode_config
        if config is None:
            config = {}
            self.main_window.opencode_config = config

        if "permission" not in config:
            config["permission"] = {}

        config["permission"][tool] = self.level_combo.currentText()
        self.main_window.save_opencode_config()
        self.accept()


# ==================== Help 页面 ====================
class HelpPage(BasePage):
    """帮助页面"""

    def __init__(self, main_window, parent=None):
        super().__init__(tr("help.title"), parent)
        self.main_window = main_window
        # 隐藏页面标题
        self.title_label.hide()
        self._setup_ui()

    def _setup_ui(self):
        # ===== 关于卡片 - 左右布局 =====
        about_card = SimpleCardWidget(self)
        about_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        about_card_layout = QHBoxLayout(about_card)
        about_card_layout.setContentsMargins(20, 16, 20, 16)
        about_card_layout.setSpacing(16)

        # 左侧 Logo
        logo_path = get_resource_path("assets/logo1.png")
        logo_label = QLabel(about_card)
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path))
            logo_label.setPixmap(pixmap.scaledToHeight(80, Qt.SmoothTransformation))
        else:
            logo_label.setText("{ }")
            logo_label.setStyleSheet(
                "font-size: 36px; font-weight: bold; color: #9B59B6;"
            )
        about_card_layout.addWidget(logo_label)

        # 右侧信息
        right_layout = QVBoxLayout()
        right_layout.setSpacing(6)

        # 标题行
        title_layout = QHBoxLayout()
        occm_label = TitleLabel("OCCM", about_card)
        occm_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #9B59B6;")
        title_layout.addWidget(occm_label)

        version_label = SubtitleLabel(
            f"OpenCode Config Manager v{APP_VERSION}", about_card
        )
        title_layout.addWidget(version_label)
        title_layout.addStretch()
        right_layout.addLayout(title_layout)

        right_layout.addWidget(
            BodyLabel(
                tr("help.about_description"),
                about_card,
            )
        )

        # 按钮行
        link_layout = QHBoxLayout()
        github_btn = PrimaryPushButton(
            FIF.GITHUB, tr("help.github_homepage"), about_card
        )
        github_btn.clicked.connect(lambda: webbrowser.open(GITHUB_URL))
        link_layout.addWidget(github_btn)

        author_btn = PushButton(
            FIF.PEOPLE, f"{tr('help.author')}: {AUTHOR_NAME}", about_card
        )
        author_btn.clicked.connect(lambda: webbrowser.open(AUTHOR_GITHUB))
        link_layout.addWidget(author_btn)
        link_layout.addStretch()
        right_layout.addLayout(link_layout)

        about_card_layout.addLayout(right_layout, 1)
        self._layout.addWidget(about_card)

        # ===== Tab 切换区域 - 占满剩余空间 =====
        tab_container = CardWidget(self)
        tab_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        tab_layout = QVBoxLayout(tab_container)
        tab_layout.setContentsMargins(12, 8, 12, 12)

        self.pivot = Pivot(self)
        self.stacked_widget = QStackedWidget(self)
        self.stacked_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 配置优先级 Tab
        priority_widget = QWidget()
        priority_layout = QVBoxLayout(priority_widget)
        priority_layout.addWidget(
            SubtitleLabel(tr("help.priority_title"), priority_widget)
        )
        priority_content = tr("help.priority_content")
        priority_text = PlainTextEdit(priority_widget)
        priority_text.setPlainText(priority_content.strip())
        priority_text.setReadOnly(True)
        priority_layout.addWidget(priority_text, 1)
        self.stacked_widget.addWidget(priority_widget)
        self.pivot.addItem(routeKey="priority", text=tr("help.tab_priority"))

        # 使用说明 Tab
        usage_widget = QWidget()
        usage_layout = QVBoxLayout(usage_widget)
        usage_layout.addWidget(SubtitleLabel(tr("help.usage_title"), usage_widget))
        usage_content = tr("help.usage_content")
        usage_text = PlainTextEdit(usage_widget)
        usage_text.setPlainText(usage_content.strip())
        usage_text.setReadOnly(True)
        usage_layout.addWidget(usage_text, 1)
        self.stacked_widget.addWidget(usage_widget)
        self.pivot.addItem(routeKey="usage", text=tr("help.tab_usage"))

        # Options vs Variants Tab
        options_widget = QWidget()
        options_layout = QVBoxLayout(options_widget)
        options_layout.addWidget(
            SubtitleLabel(tr("help.options_title"), options_widget)
        )
        options_content = tr("help.options_content")
        options_text = PlainTextEdit(options_widget)
        options_text.setPlainText(options_content.strip())
        options_text.setReadOnly(True)
        options_layout.addWidget(options_text, 1)
        self.stacked_widget.addWidget(options_widget)
        self.pivot.addItem(routeKey="options", text=tr("help.tab_options"))

        # Tab 切换连接
        def on_tab_changed(key):
            index_map = {"priority": 0, "usage": 1, "options": 2}
            self.stacked_widget.setCurrentIndex(index_map.get(key, 0))

        self.pivot.currentItemChanged.connect(on_tab_changed)
        self.pivot.setCurrentItem("priority")

        tab_layout.addWidget(self.pivot)
        tab_layout.addWidget(self.stacked_widget, 1)

        self._layout.addWidget(tab_container, 1)


# ==================== 主窗口 ====================
class MainWindow(FluentWindow):
    """主窗口"""

    # 配置变更信号 - 用于跨页面数据同步
    config_changed = pyqtSignal()

    def __init__(self):
        super().__init__()

        # 加载语言偏好
        lang_code = _lang_manager._load_language_preference()
        _lang_manager.set_language(lang_code)

        # 备份管理器（需要在冲突检测之前初始化）
        self.backup_manager = BackupManager()

        # 检测配置文件冲突（同时存在 .json 和 .jsonc）
        self._check_config_conflicts()

        # 加载配置
        self.opencode_config = ConfigManager.load_json(
            ConfigPaths.get_opencode_config()
        )
        self.ohmyopencode_config = ConfigManager.load_json(
            ConfigPaths.get_ohmyopencode_config()
        )

        if self.opencode_config is None:
            self.opencode_config = {}
        if self.ohmyopencode_config is None:
            self.ohmyopencode_config = {}

        # 初始化文件指纹
        self._refresh_file_hashes()

        # 启动时验证配置
        self._validate_config_on_startup()

        # 版本检查器
        self.version_checker = VersionChecker(
            callback=self._on_version_check, parent=self
        )
        self.latest_version = None
        self.release_url = None
        self._version_info_bar = None

        # 外部修改检测（记录文件指纹）
        self._opencode_file_hash = None
        self._ohmy_file_hash = None
        self._external_change_pending: Dict[str, Optional[str]] = {}

        self._init_window()
        self._init_navigation()

        # 版本检查定时器
        if STARTUP_VERSION_CHECK_ENABLED:
            # 启动后延迟首次检查
            QTimer.singleShot(
                IMMEDIATE_VERSION_CHECK_MS, self.version_checker.check_update_async
            )
        # 30分钟定时检查
        self._version_update_timer = QTimer(self)
        self._version_update_timer.setInterval(UPDATE_INTERVAL_MS)
        self._version_update_timer.timeout.connect(
            self.version_checker.check_update_async
        )
        self._version_update_timer.start()

        # 外部修改检测定时器
        self._file_watch_timer = QTimer(self)
        self._file_watch_timer.setInterval(10000)
        self._file_watch_timer.timeout.connect(self._check_external_file_changes)
        self._file_watch_timer.start()

    def _init_window(self):
        self.setWindowTitle(f"OCCM - OpenCode Config Manager v{APP_VERSION}")
        self.setMinimumSize(900, 600)  # 减小最小高度
        self.resize(UIConfig.WINDOW_WIDTH, UIConfig.WINDOW_HEIGHT)

        # 将窗口移动到主屏幕中央
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            x = (screen_geometry.width() - self.width()) // 2 + screen_geometry.x()
            y = (screen_geometry.height() - self.height()) // 2 + screen_geometry.y()
            # 确保窗口在屏幕范围内
            x = max(
                screen_geometry.x(),
                min(x, screen_geometry.x() + screen_geometry.width() - self.width()),
            )
            y = max(
                screen_geometry.y(),
                min(y, screen_geometry.y() + screen_geometry.height() - self.height()),
            )
            self.move(x, y)

        # 立即应用深色背景
        self._apply_dark_background()

        # 监听主题变化
        qconfig.themeChanged.connect(self._apply_dark_background)

        # 创建系统主题监听器
        self.themeListener = SystemThemeListener(self)
        self.themeListener.start()

        # 设置窗口图标 - 使用 assets/icon.png
        icon_path = get_resource_path("assets/icon.png")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        else:
            # 备用 icon.ico
            icon_path = get_resource_path("assets/icon.ico")
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
            else:
                self.setWindowIcon(FIF.CODE.icon())

        # 设置导航栏可折叠，自适应窗口大小
        self.navigationInterface.setExpandWidth(220)  # 增加宽度以适应英文菜单
        self.navigationInterface.setCollapsible(True)  # 允许折叠

        # 设置导航栏字体（正常粗细）
        nav_font = QFont()
        nav_font.setWeight(QFont.Normal)  # 正常粗细
        self.navigationInterface.setFont(nav_font)

        # 导航栏样式 - 紧凑布局
        self._update_nav_style()

        # 添加语言切换按钮到标题栏
        self._add_language_switcher()

    def _update_nav_style(self):
        """根据窗口高度更新导航栏样式"""
        height = self.height()
        # 根据窗口高度计算菜单项高度 (600px -> 24px, 900px -> 32px)
        item_height = max(24, min(32, int(height / 28)))
        font_size = max(11, min(13, int(height / 70)))

        self.navigationInterface.setStyleSheet(f"""
            * {{
                font-weight: normal;
            }}
            NavigationTreeWidget {{
                font-family: {UIConfig.FONT_FAMILY_SANS};
                font-size: {font_size}px;
                font-weight: normal;
            }}
            NavigationTreeWidget::item {{
                height: {item_height}px;
                margin: 0px 4px;
                padding: 0px 6px;
                border-radius: 4px;
                font-weight: 900;
            }}
            NavigationTreeWidget::item QLabel {{
                font-weight: 900;
            }}
            QLabel {{
                font-weight: 900;
            }}
            NavigationSeparator {{
                height: 1px;
                margin: 1px 8px;
            }}
        """)

    def resizeEvent(self, event):
        """窗口大小改变时更新导航栏"""
        super().resizeEvent(event)
        self._update_nav_style()

    def _apply_dark_background(self):
        """应用自定义背景样式"""
        if isDarkTheme():
            # 深色主题 - 应用自定义深黑色背景
            if hasattr(self, "stackedWidget"):
                self.stackedWidget.setStyleSheet(f"""
                    StackedWidget {{
                        background-color: {UIConfig.DARK_BG};
                        border: 1px solid {UIConfig.DARK_BORDER};
                        border-right: none;
                        border-bottom: none;
                        border-top-left-radius: 10px;
                    }}
                """)

            # 导航栏背景
            if hasattr(self, "navigationInterface"):
                self._update_nav_style()
        else:
            # 浅色主题 - 清除自定义样式，使用默认
            if hasattr(self, "stackedWidget"):
                self.stackedWidget.setStyleSheet("")
            if hasattr(self, "navigationInterface"):
                self._update_nav_style()

        # 更新监控页面统计卡片样式
        if hasattr(self, "monitor_page") and hasattr(
            self.monitor_page, "_apply_stat_card_theme"
        ):
            self.monitor_page._apply_stat_card_theme()

    def _add_language_switcher(self):
        """添加语言切换按钮"""
        # 创建语言切换按钮 - 使用 TransparentToolButton 以居中显示图标
        self.lang_button = TransparentToolButton(FIF.GLOBE, self)
        self.lang_button.setFixedSize(40, 36)
        self.lang_button.setIconSize(QSize(18, 18))
        self.lang_button.setText("")  # 不显示文本，只显示图标
        self.lang_button.setToolTip(tr("settings.language"))
        self.lang_button.clicked.connect(self._on_language_switch)

        # 添加到标题栏右侧，在最小化按钮的左侧
        # FluentWindow 标题栏布局：[图标][标题][Stretch][自定义按钮区][最小化][最大化][关闭]
        # 窗口控制按钮（最小化、最大化、关闭）通常在最后3个位置
        # 我们需要插入到倒数第3个位置（最小化按钮之前）
        layout = self.titleBar.hBoxLayout
        count = layout.count()
        insert_pos = max(0, count - 3)  # 在最小化按钮之前插入
        layout.insertWidget(insert_pos, self.lang_button)

    def _on_language_switch(self):
        """切换语言（优化版 - 无闪烁过渡）"""
        current_lang = _lang_manager.get_current_language()
        new_lang = "en_US" if current_lang == "zh_CN" else "zh_CN"

        # 切换语言
        _lang_manager.set_language(new_lang)

        # 保存当前窗口状态
        geometry = self.geometry()

        # 隐藏当前窗口（避免闪烁）
        self.hide()

        # 创建新窗口
        new_window = MainWindow()
        new_window.setGeometry(geometry)

        # 显示新窗口
        new_window.show()
        new_window.raise_()
        new_window.activateWindow()

        # 关闭当前窗口
        self.close()

    def _init_navigation(self):
        # ===== 顶部工具栏区域 =====
        # 添加首页/状态页面
        self.home_page = HomePage(self)
        self.addSubInterface(self.home_page, FIF.HOME, tr("menu.home"))

        # ===== OpenCode 配置分组 =====
        # Provider 页面
        self.provider_page = ProviderPage(self)
        self.addSubInterface(self.provider_page, FIF.PEOPLE, tr("menu.provider"))

        # 原生 Provider 页面
        self.native_provider_page = NativeProviderPage(self)
        self.addSubInterface(
            self.native_provider_page, FIF.GLOBE, tr("menu.native_provider")
        )

        # Model 页面
        self.model_page = ModelPage(self)
        self.addSubInterface(self.model_page, FIF.ROBOT, tr("menu.model"))

        # MCP 页面
        self.mcp_page = MCPPage(self)
        self.addSubInterface(self.mcp_page, FIF.CLOUD, tr("menu.mcp"))

        # OpenCode Agent 页面
        self.opencode_agent_page = OpenCodeAgentPage(self)
        self.addSubInterface(
            self.opencode_agent_page, FIF.COMMAND_PROMPT, tr("menu.agent")
        )

        # Permission 页面
        self.permission_page = PermissionPage(self)
        self.addSubInterface(
            self.permission_page, FIF.CERTIFICATE, tr("menu.permission")
        )

        # Skill 页面
        self.skill_page = SkillPage(self)
        self.addSubInterface(self.skill_page, FIF.BOOK_SHELF, tr("menu.skill"))

        # Rules 页面
        self.rules_page = RulesPage(self)
        self.addSubInterface(self.rules_page, FIF.DOCUMENT, tr("menu.rules"))

        # Compaction 页面
        self.compaction_page = CompactionPage(self)
        self.addSubInterface(
            self.compaction_page, FIF.ZIP_FOLDER, tr("menu.compaction")
        )

        # ===== Oh My OpenCode 配置分组 =====
        # Oh My Agent 页面
        self.ohmy_agent_page = OhMyAgentPage(self)
        self.addSubInterface(
            self.ohmy_agent_page, FIF.EMOJI_TAB_SYMBOLS, tr("menu.ohmyagent")
        )

        # Category 页面
        self.category_page = CategoryPage(self)
        self.addSubInterface(self.category_page, FIF.TAG, tr("menu.category"))

        # ===== 工具分组 =====
        # Import 页面
        self.import_page = ImportPage(self)
        self.addSubInterface(self.import_page, FIF.DOWNLOAD, tr("menu.import"))

        # CLI 导出页面
        self.cli_export_page = CLIExportPage(self)
        self.addSubInterface(self.cli_export_page, FIF.SEND, tr("menu.export"))

        # 监控页面
        self.monitor_page = MonitorPage(self)
        self.addSubInterface(self.monitor_page, FIF.SPEED_HIGH, tr("menu.monitor"))

        # ===== 工具菜单 =====
        self.navigationInterface.addSeparator()

        # 主题切换按钮
        self.navigationInterface.addItem(
            routeKey="theme",
            icon=FIF.CONSTRACT,
            text=tr("menu.theme"),
            onClick=self._toggle_theme,
        )

        # Backup 按钮
        self.navigationInterface.addItem(
            routeKey="backup",
            icon=FIF.HISTORY,
            text=tr("menu.backup"),
            onClick=self._show_backup_dialog,
        )

        # Help 页面
        self.help_page = HelpPage(self)
        self.addSubInterface(self.help_page, FIF.HELP, tr("menu.help"))

    def _show_backup_dialog(self):
        """显示备份管理对话框"""
        dialog = BackupDialog(self, parent=self)
        dialog.exec_()

    def save_opencode_config(self):
        """保存 OpenCode 配置"""
        success, jsonc_warning = ConfigManager.save_json(
            ConfigPaths.get_opencode_config(),
            self.opencode_config,
            backup_manager=self.backup_manager,
        )
        if success:
            self.notify_config_changed()
            if jsonc_warning and not getattr(self, "_opencode_jsonc_warned", False):
                self._opencode_jsonc_warned = True
                InfoBar.warning(
                    title="JSONC 注释已丢失",
                    content="原配置文件包含注释，保存后注释已丢失。已自动备份原文件。",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=8000,
                    parent=self,
                )
            return True
        return False

    def save_ohmyopencode_config(self):
        """保存 Oh My OpenCode 配置"""
        success, jsonc_warning = ConfigManager.save_json(
            ConfigPaths.get_ohmyopencode_config(),
            self.ohmyopencode_config,
            backup_manager=self.backup_manager,
        )
        if success:
            self.notify_config_changed()
            if jsonc_warning and not getattr(self, "_ohmyopencode_jsonc_warned", False):
                self._ohmyopencode_jsonc_warned = True
                InfoBar.warning(
                    title="JSONC 注释已丢失",
                    content="原配置文件包含注释，保存后注释已丢失。已自动备份原文件。",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=8000,
                    parent=self,
                )
            return True
        return False

    def notify_config_changed(self):
        """通知所有页面配置已变更"""
        self.config_changed.emit()

    def _on_version_check(self, latest_version: str, release_url: str):
        """版本检查回调"""
        if VersionChecker.compare_versions(APP_VERSION, latest_version):
            self.latest_version = latest_version
            self.release_url = release_url
            if self._version_info_bar:
                self._version_info_bar.close()

            info_bar = InfoBar(
                InfoBarIcon.INFORMATION,
                tr("dialog.new_version_found"),
                tr("dialog.new_version_available", version=latest_version),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                duration=-1,
                position=InfoBarPosition.TOP_RIGHT,
                parent=self,
            )
            info_bar.setCursor(Qt.PointingHandCursor)

            if isDarkTheme():
                info_bar.setCustomBackgroundColor("#E3F2FD", "#1A237E")
                info_bar.setStyleSheet(
                    """
                    InfoBar {
                        border: 1px solid #283593;
                        border-radius: 6px;
                    }
                    InfoBar > QLabel#titleLabel {
                        color: #BBDEFB;
                        font-weight: bold;
                    }
                    InfoBar > QLabel#contentLabel {
                        color: #E3F2FD;
                    }
                    """
                )
            else:
                info_bar.setCustomBackgroundColor("#FFF8E1", "#3E2723")
                info_bar.setStyleSheet(
                    """
                    InfoBar {
                        border: 1px solid #FFB74D;
                        border-radius: 6px;
                    }
                    InfoBar > QLabel#titleLabel {
                        color: #E65100;
                        font-weight: bold;
                    }
                    InfoBar > QLabel#contentLabel {
                        color: #BF360C;
                    }
                    """
                )

            def _open_release(event):
                # 点击提示条直接打开发布页面
                if event.button() == Qt.LeftButton:
                    self._open_release_url()

            def _clear_info_bar():
                if self._version_info_bar is info_bar:
                    self._version_info_bar = None

            info_bar.mousePressEvent = _open_release
            info_bar.closedSignal.connect(_clear_info_bar)
            info_bar.show()
            self._version_info_bar = info_bar

    def _open_release_url(self):
        """打开版本发布页面"""
        release_url = self.release_url or f"{GITHUB_URL}/releases"
        if release_url:
            QDesktopServices.openUrl(QUrl(release_url))

    def _refresh_file_hashes(self):
        """刷新当前配置文件哈希"""
        self._opencode_file_hash = BackupManager.file_hash(
            ConfigPaths.get_opencode_config()
        )
        self._ohmy_file_hash = BackupManager.file_hash(
            ConfigPaths.get_ohmyopencode_config()
        )

    def _check_external_file_changes(self):
        """检测配置文件是否被外部修改"""
        oc_path = ConfigPaths.get_opencode_config()
        ohmy_path = ConfigPaths.get_ohmyopencode_config()
        current_oc_hash = BackupManager.file_hash(oc_path)
        current_ohmy_hash = BackupManager.file_hash(ohmy_path)

        if (
            self._opencode_file_hash
            and current_oc_hash
            and current_oc_hash != self._opencode_file_hash
        ):
            pending = self._external_change_pending.get("opencode")
            if pending == current_oc_hash:
                self._external_change_pending["opencode"] = None
                self._handle_external_change("OpenCode", oc_path)
            else:
                self._external_change_pending["opencode"] = current_oc_hash
        if (
            self._ohmy_file_hash
            and current_ohmy_hash
            and current_ohmy_hash != self._ohmy_file_hash
        ):
            pending = self._external_change_pending.get("ohmy")
            if pending == current_ohmy_hash:
                self._external_change_pending["ohmy"] = None
                self._handle_external_change("Oh My OpenCode", ohmy_path)
            else:
                self._external_change_pending["ohmy"] = current_ohmy_hash

        self._opencode_file_hash = current_oc_hash
        self._ohmy_file_hash = current_ohmy_hash

    def _handle_external_change(self, config_name: str, path: Path):
        """处理外部修改提示"""
        msg = (
            f"检测到 {config_name} 配置文件已被外部修改。\n\n"
            "请选择如何处理：\n"
            "• 点击【确定】重新加载文件内容（可能覆盖当前界面数据）\n"
            "• 点击【取消】保留当前界面数据（文件保持外部修改）"
        )
        dialog = FluentMessageBox(tr("dialog.config_file_changed"), msg, self)
        if dialog.exec_():
            # 重新加载并刷新哈希
            if config_name == "OpenCode":
                new_config = ConfigManager.load_json(path) or {}
                issues = ConfigValidator.validate_opencode_config(new_config)
                errors = [i for i in issues if i["level"] == "error"]
                if errors:
                    msg = "\n".join(f"• {e['message']}" for e in errors[:8])
                    if len(errors) > 8:
                        msg += f"\n... 还有 {len(errors) - 8} 个错误"
                    InfoBar.error(
                        tr("common.error"),
                        tr("dialog.reload_failed", msg=msg),
                        parent=self,
                    )
                    return
                self.opencode_config = new_config
            else:
                self.ohmyopencode_config = ConfigManager.load_json(path) or {}
            self._refresh_file_hashes()
            self.notify_config_changed()
            if hasattr(self, "home_page"):
                self.home_page._load_stats()
            InfoBar.success(
                title="已重新加载",
                content=f"已加载 {config_name} 最新配置",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=5000,
                parent=self,
            )
        else:
            # 保持当前内存态，同时备份内存数据
            if config_name == "OpenCode":
                self.backup_manager.backup_data(
                    path, self.opencode_config, tag="external-keep"
                )
            else:
                self.backup_manager.backup_data(
                    path, self.ohmyopencode_config, tag="external-keep"
                )
            InfoBar.warning(
                title="保持当前数据",
                content=f"未重新加载 {config_name}，当前界面数据保持不变",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=6000,
                parent=self,
            )

    def _toggle_theme(self):
        """切换深浅色主题 (手动切换会停止跟随系统)"""
        if isDarkTheme():
            setTheme(Theme.LIGHT)
        else:
            setTheme(Theme.DARK)
        # 切换后重新应用自定义背景
        QTimer.singleShot(50, self._apply_dark_background)

    def closeEvent(self, e):
        """关闭窗口时停止主题监听器"""
        if hasattr(self, "themeListener"):
            self.themeListener.terminate()
            self.themeListener.deleteLater()
        super().closeEvent(e)

    def _check_config_conflicts(self):
        """检测配置文件冲突（同时存在 .json 和 .jsonc）"""
        conflicts = []

        # 检查 opencode 配置
        opencode_conflict = ConfigPaths.check_config_conflict("opencode")
        if opencode_conflict:
            conflicts.append(("OpenCode", "opencode", opencode_conflict))

        # 检查 oh-my-opencode 配置
        ohmy_conflict = ConfigPaths.check_config_conflict("oh-my-opencode")
        if ohmy_conflict:
            conflicts.append(("Oh My OpenCode", "oh-my-opencode", ohmy_conflict))

        if not conflicts:
            return

        # 延迟显示对话框，等窗口完全初始化
        # 使用 lambda 捕获 conflicts
        QTimer.singleShot(200, lambda: self._show_conflict_dialog(conflicts))

    def _show_conflict_dialog(self, conflicts: list):
        """显示配置文件冲突对话框"""
        for config_name, base_name, (json_path, jsonc_path) in conflicts:
            json_info = ConfigPaths.get_config_file_info(json_path)
            jsonc_info = ConfigPaths.get_config_file_info(jsonc_path)

            msg = f"""检测到 {config_name} 同时存在两个配置文件：

📄 {json_path.name}
   大小: {json_info.get("size_str", "未知")}
   修改时间: {json_info.get("mtime_str", "未知")}

📄 {jsonc_path.name}
   大小: {jsonc_info.get("size_str", "未知")}
   修改时间: {jsonc_info.get("mtime_str", "未知")}

⚠️ 当前程序会优先加载 .jsonc 文件。

请选择要使用的配置文件：
• 点击「确定」使用 .json 文件（删除 .jsonc）
• 点击「取消」使用 .jsonc 文件（保持现状）"""

            dialog = FluentMessageBox(
                tr("dialog.config_file_conflict", config_name=config_name), msg, self
            )

            if dialog.exec_():
                # 用户选择使用 .json，删除 .jsonc
                try:
                    # 先备份 .jsonc
                    self.backup_manager.backup(jsonc_path, tag="conflict-backup")
                    # 删除 .jsonc
                    jsonc_path.unlink()
                    InfoBar.success(
                        title="已切换配置",
                        content=f"已删除 {jsonc_path.name}，将使用 {json_path.name}",
                        orient=Qt.Orientation.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP_RIGHT,
                        duration=5000,
                        parent=self,
                    )
                except Exception as e:
                    InfoBar.error(
                        title="删除失败",
                        content=f"无法删除 {jsonc_path.name}: {e}",
                        orient=Qt.Orientation.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP_RIGHT,
                        duration=5000,
                        parent=self,
                    )
            else:
                # 用户选择保持现状（使用 .jsonc）
                InfoBar.info(
                    title="保持现状",
                    content=f"将继续使用 {jsonc_path.name}",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3000,
                    parent=self,
                )

    def _validate_config_on_startup(self):
        """启动时验证配置文件"""
        issues = ConfigValidator.validate_opencode_config(self.opencode_config)
        errors = [i for i in issues if i["level"] == "error"]
        warnings = [i for i in issues if i["level"] == "warning"]

        if not errors and not warnings:
            return  # 配置正常，无需提示

        # 延迟显示对话框，等窗口完全初始化
        QTimer.singleShot(500, lambda: self._show_validation_dialog(issues))

    def _show_validation_dialog(self, issues: List[Dict]):
        """显示配置验证结果对话框"""
        errors = [i for i in issues if i["level"] == "error"]
        warnings = [i for i in issues if i["level"] == "warning"]

        # 构建消息
        msg_lines = [tr("dialog.config_issues_detected") + "\n"]

        if errors:
            msg_lines.append(f"❌ {len(errors)} {tr('dialog.errors_count')}")
            for e in errors[:8]:
                msg_lines.append(f"  • {e['message']}")
            if len(errors) > 8:
                msg_lines.append(tr("dialog.more_errors").format(count=len(errors) - 8))
            msg_lines.append("")

        if warnings:
            msg_lines.append(f"⚠️ {len(warnings)} {tr('dialog.warnings_count')}")
            for w in warnings[:8]:
                msg_lines.append(f"  • {w['message']}")
            if len(warnings) > 8:
                msg_lines.append(
                    tr("dialog.more_warnings").format(count=len(warnings) - 8)
                )

        msg_lines.append("\n" + tr("dialog.auto_fix_prompt"))

        # 创建对话框
        dialog = FluentMessageBox(
            tr("dialog.config_format_check"), "\n".join(msg_lines), self
        )

        if dialog.exec_():
            # 用户点击确认，执行修复
            self._fix_config()
        else:
            # 用户取消，显示警告
            InfoBar.warning(
                title=tr("dialog.config_issues_not_fixed"),
                content=tr("dialog.config_issues_warning"),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=8000,
                parent=self,
            )

    def _fix_config(self):
        """修复配置文件"""
        # 先备份
        self.backup_manager.backup(ConfigPaths.get_opencode_config(), tag="before-fix")

        # 执行修复
        fixed_config, fixes = ConfigValidator.fix_provider_structure(
            self.opencode_config
        )

        if fixes:
            self.opencode_config = fixed_config
            self.save_opencode_config()

            # 显示修复结果
            fix_msg = f"已完成 {len(fixes)} 项修复：\n" + "\n".join(
                f"• {f}" for f in fixes[:10]
            )
            if len(fixes) > 10:
                fix_msg += f"\n... 还有 {len(fixes) - 10} 项"

            InfoBar.success(
                title="配置已修复",
                content=fix_msg,
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=10000,
                parent=self,
            )

            # 刷新首页统计
            if hasattr(self, "home_page"):
                self.home_page._load_stats()
        else:
            InfoBar.info(
                title="无需修复",
                content="配置结构已经正确",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=5000,
                parent=self,
            )


# ==================== Oh My Agent 页面 ====================
class OhMyAgentPage(BasePage):
    """Oh My OpenCode Agent 管理页面"""

    def __init__(self, main_window, parent=None):
        super().__init__(tr("ohmyagent.title"), parent)
        self.main_window = main_window
        self._setup_ui()
        self._load_data()
        # 连接配置变更信号
        self.main_window.config_changed.connect(self._on_config_changed)

    def _on_config_changed(self):
        """配置变更时刷新数据"""
        self._load_data()

    def _setup_ui(self):
        # 工具栏
        toolbar = QHBoxLayout()

        self.add_btn = PrimaryPushButton(FIF.ADD, tr("ohmyagent.add_agent"), self)
        self.add_btn.clicked.connect(self._on_add)
        toolbar.addWidget(self.add_btn)

        self.preset_btn = PushButton(FIF.LIBRARY, tr("common.add_from_preset"), self)
        self.preset_btn.clicked.connect(self._on_add_preset)
        toolbar.addWidget(self.preset_btn)

        self.edit_btn = PushButton(FIF.EDIT, tr("common.edit"), self)
        self.edit_btn.clicked.connect(self._on_edit)
        toolbar.addWidget(self.edit_btn)

        self.delete_btn = PushButton(FIF.DELETE, tr("common.delete"), self)
        self.delete_btn.clicked.connect(self._on_delete)
        toolbar.addWidget(self.delete_btn)

        self.bulk_model_label = BodyLabel(tr("ohmyagent.bulk_model"), self)
        toolbar.addWidget(self.bulk_model_label)
        self.bulk_model_combo = ComboBox(self)
        self.bulk_model_combo.setMinimumWidth(220)
        self.bulk_model_combo.currentIndexChanged.connect(self._on_bulk_model_changed)
        toolbar.addWidget(self.bulk_model_combo)

        toolbar.addStretch()
        self._layout.addLayout(toolbar)

        # Agent 列表
        self.table = TableWidget(self)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(
            [tr("common.name"), tr("ohmyagent.model"), tr("common.description")]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.doubleClicked.connect(self._on_edit)
        self._layout.addWidget(self.table)

    def _load_data(self):
        """加载 Agent 数据"""
        self.table.setRowCount(0)
        config = self.main_window.ohmyopencode_config or {}
        agents = config.get("agents", {})

        # 添加类型检查，防止 agents 字段为非字典类型时崩溃
        if not isinstance(agents, dict):
            agents = {}

        models = self._get_available_models()
        self._refresh_bulk_model_combo(models)

        for name, data in agents.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(name))

            model_combo = ComboBox(self.table)
            model_combo.addItems(models)
            current_model = data.get("model", "")
            if current_model:
                model_combo.setCurrentText(current_model)
            model_combo.currentIndexChanged.connect(
                partial(self._on_row_model_changed, name, model_combo)
            )
            self.table.setCellWidget(row, 1, model_combo)

            # 描述列添加 tooltip 显示全部
            desc = data.get("description", "")
            if not desc:
                desc = PRESET_AGENTS.get(name, "")
            desc_item = QTableWidgetItem(desc[:50] + "..." if len(desc) > 50 else desc)
            desc_item.setToolTip(desc)
            self.table.setItem(row, 2, desc_item)

    def _get_available_models(self) -> List[str]:
        registry = ModelRegistry(self.main_window.opencode_config)
        return registry.get_all_models()

    def _refresh_bulk_model_combo(self, models: List[str]) -> None:
        current = self.bulk_model_combo.currentText()
        self.bulk_model_combo.blockSignals(True)
        self.bulk_model_combo.clear()
        self.bulk_model_combo.addItem(tr("common.keep_all"))
        self.bulk_model_combo.addItems(models)
        if current:
            self.bulk_model_combo.setCurrentText(current)
        self.bulk_model_combo.blockSignals(False)

    def _on_row_model_changed(self, agent_name: str, combo: ComboBox) -> None:
        config = self.main_window.ohmyopencode_config
        if config is None:
            config = {}
            self.main_window.ohmyopencode_config = config
        agents = config.setdefault("agents", {})
        if agent_name not in agents:
            return
        agents[agent_name]["model"] = combo.currentText()
        self.main_window.save_ohmyopencode_config()

    def _on_bulk_model_changed(self) -> None:
        model = self.bulk_model_combo.currentText()
        if model == tr("common.keep_all"):
            return
        config = self.main_window.ohmyopencode_config
        if config is None:
            config = {}
            self.main_window.ohmyopencode_config = config
        agents = config.setdefault("agents", {})
        if not agents:
            return
        for name in agents.keys():
            agents[name]["model"] = model
        self.main_window.save_ohmyopencode_config()
        self._load_data()

    def _on_add(self):
        """添加 Agent"""
        dialog = OhMyAgentDialog(self.main_window, parent=self)
        if dialog.exec_():
            self._load_data()
            self.show_success(
                self.tr("common.success"), self.tr("ohmyagent.agent_added")
            )

    def _on_add_preset(self):
        """从预设添加 Agent"""
        dialog = PresetOhMyAgentDialog(self.main_window, parent=self)
        if dialog.exec_():
            self._load_data()
            self.show_success(
                self.tr("common.success"), self.tr("ohmyagent.preset_agent_added")
            )

    def _on_edit(self):
        """编辑 Agent"""
        row = self.table.currentRow()
        if row < 0:
            self.show_warning(
                tr("common.info"), tr("common.please_select_first", item="Agent")
            )
            return

        name = self.table.item(row, 0).text()
        dialog = OhMyAgentDialog(self.main_window, agent_name=name, parent=self)
        if dialog.exec_():
            self._load_data()
            self.show_success(
                self.tr("common.success"), self.tr("ohmyagent.agent_updated")
            )

    def _on_delete(self):
        """删除 Agent"""
        row = self.table.currentRow()
        if row < 0:
            self.show_warning(
                tr("common.info"), tr("common.please_select_first", item="Agent")
            )
            return

        name = self.table.item(row, 0).text()
        w = FluentMessageBox(
            tr("common.confirm_delete_title"),
            tr("dialog.confirm_delete_agent", name=name),
            self,
        )
        if w.exec_():
            config = self.main_window.ohmyopencode_config or {}
            if "agents" in config and name in config["agents"]:
                del config["agents"][name]
                self.main_window.save_ohmyopencode_config()
                self._load_data()
                self.show_success(
                    tr("common.success"), tr("dialog.agent_deleted", name=name)
                )


class OhMyAgentDialog(BaseDialog):
    """Oh My Agent 编辑对话框"""

    def __init__(self, main_window, agent_name: str = None, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.agent_name = agent_name
        self.is_edit = agent_name is not None

        self.setWindowTitle(
            tr("ohmyagent.dialog.edit_title")
            if self.is_edit
            else tr("ohmyagent.dialog.add_title")
        )
        self.setMinimumWidth(450)
        self._setup_ui()

        if self.is_edit:
            self._load_agent_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Agent 名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(BodyLabel(tr("ohmyagent.dialog.agent_key_label"), self))
        self.name_edit = LineEdit(self)
        self.name_edit.setPlaceholderText(tr("ohmyagent.dialog.agent_key_placeholder"))
        self.name_edit.setToolTip(get_tooltip("ohmyopencode_agent_name"))
        if self.is_edit:
            self.name_edit.setEnabled(False)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        # 绑定模型
        model_layout = QHBoxLayout()
        model_layout.addWidget(BodyLabel(tr("ohmyagent.dialog.model_label"), self))
        self.model_combo = ComboBox(self)
        self.model_combo.setToolTip(get_tooltip("ohmyopencode_agent_model"))
        self._load_models()
        model_layout.addWidget(self.model_combo)
        layout.addLayout(model_layout)

        # 描述
        desc_label = BodyLabel(tr("common.description") + ":", self)
        desc_label.setToolTip(get_tooltip("ohmyopencode_agent_description"))
        layout.addWidget(desc_label)
        self.desc_edit = TextEdit(self)
        self.desc_edit.setPlaceholderText(tr("dialog.placeholder_agent_desc_detail"))
        self.desc_edit.setMaximumHeight(100)
        layout.addWidget(self.desc_edit)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = PushButton(tr("common.cancel"), self)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.save_btn = PrimaryPushButton(tr("common.save"), self)
        self.save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)

    def _load_models(self):
        """加载可用模型列表"""
        self.model_combo.clear()
        registry = ModelRegistry(self.main_window.opencode_config)
        models = registry.get_all_models()
        self.model_combo.addItems(models)

    def _load_agent_data(self):
        config = self.main_window.ohmyopencode_config or {}
        agent = config.get("agents", {}).get(self.agent_name, {})

        self.name_edit.setText(self.agent_name)

        model = agent.get("model", "")
        if model:
            self.model_combo.setCurrentText(model)

        self.desc_edit.setPlainText(agent.get("description", ""))

    def _on_save(self):
        name = self.name_edit.text().strip()
        if not name:
            InfoBar.error(
                tr("common.error"), tr("ohmyagent.dialog.key_required"), parent=self
            )
            return

        config = self.main_window.ohmyopencode_config
        if config is None:
            config = {}
            self.main_window.ohmyopencode_config = config

        if "agents" not in config:
            config["agents"] = {}

        if not self.is_edit and name in config["agents"]:
            InfoBar.error(
                tr("common.error"), tr("ohmyagent.dialog.key_exists"), parent=self
            )
            return

        config["agents"][name] = {
            "model": self.model_combo.currentText(),
            "description": self.desc_edit.toPlainText().strip(),
        }

        self.main_window.save_ohmyopencode_config()
        self.accept()


class PresetOhMyAgentDialog(BaseDialog):
    """预设 Oh My Agent 选择对话框"""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window

        self.setWindowTitle(tr("ohmyagent.preset_dialog.title"))
        self.setMinimumWidth(500)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        layout.addWidget(SubtitleLabel(tr("ohmyagent.preset_dialog.subtitle"), self))

        # 预设列表
        self.list_widget = ListWidget(self)
        for name, desc in PRESET_AGENTS.items():
            self.list_widget.addItem(f"{name} - {desc}")
        layout.addWidget(self.list_widget)

        # 绑定模型
        model_layout = QHBoxLayout()
        model_layout.addWidget(BodyLabel(tr("ohmyagent.dialog.model_label"), self))
        self.model_combo = ComboBox(self)
        self._load_models()
        model_layout.addWidget(self.model_combo)
        layout.addLayout(model_layout)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = PushButton(tr("common.cancel"), self)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.add_btn = PrimaryPushButton(tr("common.add"), self)
        self.add_btn.clicked.connect(self._on_add)
        btn_layout.addWidget(self.add_btn)

        layout.addLayout(btn_layout)

    def _load_models(self):
        self.model_combo.clear()
        registry = ModelRegistry(self.main_window.opencode_config)
        models = registry.get_all_models()
        self.model_combo.addItems(models)

    def _on_add(self):
        current = self.list_widget.currentItem()
        if not current:
            InfoBar.warning(
                tr("common.warning"),
                tr("ohmyagent.preset_dialog.select_preset"),
                parent=self,
            )
            return

        # 解析选中的预设
        text = current.text()
        name = text.split(" - ")[0]
        desc = PRESET_AGENTS.get(name, "")

        config = self.main_window.ohmyopencode_config
        if config is None:
            config = {}
            self.main_window.ohmyopencode_config = config

        if "agents" not in config:
            config["agents"] = {}

        if name in config["agents"]:
            InfoBar.warning(
                tr("common.warning"),
                tr("ohmyagent.preset_dialog.agent_exists", name=name),
                parent=self,
            )
            return

        config["agents"][name] = {
            "model": self.model_combo.currentText(),
            "description": desc,
        }

        self.main_window.save_ohmyopencode_config()
        self.accept()


# ==================== Category 页面 ====================
class CategoryPage(BasePage):
    """Category 管理页面"""

    def __init__(self, main_window, parent=None):
        super().__init__(tr("category.title"), parent)
        self.main_window = main_window
        self._setup_ui()
        self._load_data()
        # 连接配置变更信号
        self.main_window.config_changed.connect(self._on_config_changed)

    def _on_config_changed(self):
        """配置变更时刷新数据"""
        self._load_data()

    def _setup_ui(self):
        # 工具栏
        toolbar = QHBoxLayout()

        self.add_btn = PrimaryPushButton(FIF.ADD, tr("category.add_category"), self)
        self.add_btn.clicked.connect(self._on_add)
        toolbar.addWidget(self.add_btn)

        self.preset_btn = PushButton(FIF.LIBRARY, tr("common.add_from_preset"), self)
        self.preset_btn.clicked.connect(self._on_add_preset)
        toolbar.addWidget(self.preset_btn)

        self.edit_btn = PushButton(FIF.EDIT, tr("common.edit"), self)
        self.edit_btn.clicked.connect(self._on_edit)
        toolbar.addWidget(self.edit_btn)

        self.delete_btn = PushButton(FIF.DELETE, tr("common.delete"), self)
        self.delete_btn.clicked.connect(self._on_delete)
        toolbar.addWidget(self.delete_btn)

        self.bulk_model_label = BodyLabel(tr("ohmyagent.bulk_model"), self)
        toolbar.addWidget(self.bulk_model_label)
        self.bulk_model_combo = ComboBox(self)
        self.bulk_model_combo.setMinimumWidth(220)
        self.bulk_model_combo.currentIndexChanged.connect(self._on_bulk_model_changed)
        toolbar.addWidget(self.bulk_model_combo)

        toolbar.addStretch()
        self._layout.addLayout(toolbar)

        # Category 列表
        self.table = TableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            [
                tr("common.name"),
                tr("category.bind_model").rstrip(":"),
                "Temperature",
                tr("common.description"),
            ]
        )
        # 调整列宽：名称20字符，Temperature12字符，剩余均分
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.resizeSection(0, 160)  # 名称 20字符约160px
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # 绑定模型 均分
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.resizeSection(2, 100)  # Temperature 12字符约100px
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # 描述 均分
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.doubleClicked.connect(self._on_edit)
        self._layout.addWidget(self.table)

    def _load_data(self):
        """加载 Category 数据"""
        self.table.setRowCount(0)
        config = self.main_window.ohmyopencode_config or {}
        categories = config.get("categories", {})

        # 添加类型检查，防止 categories 字段为非字典类型时崩溃
        if not isinstance(categories, dict):
            categories = {}

        models = self._get_available_models()
        self._refresh_bulk_model_combo(models)

        for name, data in categories.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(name))

            model_combo = ComboBox(self.table)
            model_combo.addItems(models)
            current_model = data.get("model", "")
            if current_model:
                model_combo.setCurrentText(current_model)
            model_combo.currentIndexChanged.connect(
                partial(self._on_row_model_changed, name, model_combo)
            )
            self.table.setCellWidget(row, 1, model_combo)

            self.table.setItem(
                row, 2, QTableWidgetItem(str(data.get("temperature", 0.7)))
            )
            # 描述列添加 tooltip 显示全部
            desc = data.get("description", "")
            if not desc:
                desc = PRESET_CATEGORIES.get(name, {}).get("description", "")
            desc_item = QTableWidgetItem(desc[:30] + "..." if len(desc) > 30 else desc)
            desc_item.setToolTip(desc)
            self.table.setItem(row, 3, desc_item)

    def _get_available_models(self) -> List[str]:
        registry = ModelRegistry(self.main_window.opencode_config)
        return registry.get_all_models()

    def _refresh_bulk_model_combo(self, models: List[str]) -> None:
        current = self.bulk_model_combo.currentText()
        self.bulk_model_combo.blockSignals(True)
        self.bulk_model_combo.clear()
        self.bulk_model_combo.addItem(tr("common.keep_all"))
        self.bulk_model_combo.addItems(models)
        if current:
            self.bulk_model_combo.setCurrentText(current)
        self.bulk_model_combo.blockSignals(False)

    def _on_row_model_changed(self, category_name: str, combo: ComboBox) -> None:
        config = self.main_window.ohmyopencode_config
        if config is None:
            config = {}
            self.main_window.ohmyopencode_config = config
        categories = config.setdefault("categories", {})
        if category_name not in categories:
            return
        categories[category_name]["model"] = combo.currentText()
        self.main_window.save_ohmyopencode_config()

    def _on_bulk_model_changed(self) -> None:
        model = self.bulk_model_combo.currentText()
        if model == tr("common.keep_all"):
            return
        config = self.main_window.ohmyopencode_config
        if config is None:
            config = {}
            self.main_window.ohmyopencode_config = config
        categories = config.setdefault("categories", {})
        if not categories:
            return
        for name in categories.keys():
            categories[name]["model"] = model
        self.main_window.save_ohmyopencode_config()
        self._load_data()

    def _on_add(self):
        dialog = CategoryDialog(self.main_window, parent=self)
        if dialog.exec_():
            self._load_data()
            self.show_success(
                self.tr("common.success"), self.tr("category.category_added")
            )

    def _on_add_preset(self):
        dialog = PresetCategoryDialog(self.main_window, parent=self)
        if dialog.exec_():
            self._load_data()
            self.show_success(
                self.tr("common.success"), self.tr("category.preset_category_added")
            )

    def _on_edit(self):
        row = self.table.currentRow()
        if row < 0:
            self.show_warning(
                tr("common.info"), tr("common.please_select_first", item="Category")
            )
            return

        name = self.table.item(row, 0).text()
        dialog = CategoryDialog(self.main_window, category_name=name, parent=self)
        if dialog.exec_():
            self._load_data()
            self.show_success(
                self.tr("common.success"), self.tr("category.category_updated")
            )

    def _on_delete(self):
        row = self.table.currentRow()
        if row < 0:
            self.show_warning(
                tr("common.info"), tr("common.please_select_first", item="Category")
            )
            return

        name = self.table.item(row, 0).text()
        w = FluentMessageBox(
            tr("common.confirm_delete_title"),
            tr("dialog.confirm_delete_category", name=name),
            self,
        )
        if w.exec_():
            config = self.main_window.ohmyopencode_config or {}
            if "categories" in config and name in config["categories"]:
                del config["categories"][name]
                self.main_window.save_ohmyopencode_config()
                self._load_data()
                self.show_success(
                    tr("common.success"), tr("dialog.category_deleted", name=name)
                )


class CategoryDialog(BaseDialog):
    """Category 编辑对话框"""

    def __init__(self, main_window, category_name: str = None, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.category_name = category_name
        self.is_edit = category_name is not None

        self.setWindowTitle(
            "编辑 Category" if self.is_edit else tr("category.add_category")
        )
        self.setMinimumWidth(450)
        self._setup_ui()

        if self.is_edit:
            self._load_category_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Category 名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(BodyLabel(tr("category.category_name") + ":", self))
        self.name_edit = LineEdit(self)
        self.name_edit.setPlaceholderText(tr("dialog.placeholder_category_tags"))
        self.name_edit.setToolTip(get_tooltip("category_name"))
        if self.is_edit:
            self.name_edit.setEnabled(False)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        # 绑定模型
        model_layout = QHBoxLayout()
        model_layout.addWidget(BodyLabel(tr("category.bind_model"), self))
        self.model_combo = ComboBox(self)
        self.model_combo.setToolTip(get_tooltip("category_model"))
        self._load_models()
        model_layout.addWidget(self.model_combo)
        layout.addLayout(model_layout)

        # Temperature 滑块
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(BodyLabel("Temperature:", self))
        self.temp_slider = Slider(Qt.Horizontal, self)
        self.temp_slider.setRange(0, 200)  # 0.0 - 2.0
        self.temp_slider.setValue(70)  # 默认 0.7
        self.temp_slider.setToolTip(get_tooltip("category_temperature"))
        self.temp_slider.valueChanged.connect(self._on_temp_changed)
        temp_layout.addWidget(self.temp_slider)
        self.temp_label = BodyLabel("0.7", self)
        self.temp_label.setMinimumWidth(40)
        temp_layout.addWidget(self.temp_label)
        layout.addLayout(temp_layout)

        # 描述
        desc_label = BodyLabel(tr("skill.description") + ":", self)
        desc_label.setToolTip(get_tooltip("category_description"))
        layout.addWidget(desc_label)
        self.desc_edit = TextEdit(self)
        self.desc_edit.setPlaceholderText(tr("dialog.placeholder_category_desc"))
        self.desc_edit.setMaximumHeight(80)
        layout.addWidget(self.desc_edit)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = PushButton(tr("common.cancel"), self)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.save_btn = PrimaryPushButton(tr("common.save"), self)
        self.save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)

    def _on_temp_changed(self, value):
        self.temp_label.setText(f"{value / 100:.1f}")

    def _load_models(self):
        self.model_combo.clear()
        registry = ModelRegistry(self.main_window.opencode_config)
        models = registry.get_all_models()
        self.model_combo.addItems(models)

    def _load_category_data(self):
        config = self.main_window.ohmyopencode_config or {}
        category = config.get("categories", {}).get(self.category_name, {})

        self.name_edit.setText(self.category_name)

        model = category.get("model", "")
        if model:
            self.model_combo.setCurrentText(model)

        temp = category.get("temperature", 0.7)
        self.temp_slider.setValue(int(temp * 100))
        self.temp_label.setText(f"{temp:.1f}")

        self.desc_edit.setPlainText(category.get("description", ""))

    def _on_save(self):
        name = self.name_edit.text().strip()
        if not name:
            InfoBar.error(
                tr("common.error"), tr("dialog.enter_category_name"), parent=self
            )
            return

        config = self.main_window.ohmyopencode_config
        if config is None:
            config = {}
            self.main_window.ohmyopencode_config = config

        if "categories" not in config:
            config["categories"] = {}

        if not self.is_edit and name in config["categories"]:
            InfoBar.error("错误", f'Category "{name}" 已存在', parent=self)
            return

        config["categories"][name] = {
            "model": self.model_combo.currentText(),
            "temperature": round(self.temp_slider.value() / 100, 1),
            "description": self.desc_edit.toPlainText().strip(),
        }

        self.main_window.save_ohmyopencode_config()
        self.accept()


class PresetCategoryDialog(BaseDialog):
    """预设 Category 选择对话框"""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window

        self.setWindowTitle(tr("category.preset_dialog_title"))
        self.setMinimumWidth(500)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        layout.addWidget(SubtitleLabel(tr("category.select_preset_category"), self))

        # 预设列表
        self.list_widget = ListWidget(self)
        for name, data in PRESET_CATEGORIES.items():
            temp = data.get("temperature", 0.7)
            desc = data.get("description", "")
            self.list_widget.addItem(f"{name} (temp={temp}) - {desc}")
        layout.addWidget(self.list_widget)

        # 绑定模型
        model_layout = QHBoxLayout()
        model_layout.addWidget(BodyLabel(tr("category.bind_model"), self))
        self.model_combo = ComboBox(self)
        self._load_models()
        model_layout.addWidget(self.model_combo)
        layout.addLayout(model_layout)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = PushButton(tr("common.cancel"), self)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.add_btn = PrimaryPushButton(tr("model.add"), self)
        self.add_btn.clicked.connect(self._on_add)
        btn_layout.addWidget(self.add_btn)

        layout.addLayout(btn_layout)

    def _load_models(self):
        self.model_combo.clear()
        registry = ModelRegistry(self.main_window.opencode_config)
        models = registry.get_all_models()
        self.model_combo.addItems(models)

    def _on_add(self):
        current = self.list_widget.currentItem()
        if not current:
            InfoBar.warning(
                tr("common.hint"), tr("dialog.select_preset_category"), parent=self
            )
            return

        text = current.text()
        name = text.split(" (temp=")[0]
        preset = PRESET_CATEGORIES.get(name, {})

        config = self.main_window.ohmyopencode_config
        if config is None:
            config = {}
            self.main_window.ohmyopencode_config = config

        if "categories" not in config:
            config["categories"] = {}

        if name in config["categories"]:
            InfoBar.warning(
                tr("common.info"),
                tr("category.category_exists", name=name),
                parent=self,
            )
            return

        config["categories"][name] = {
            "model": self.model_combo.currentText(),
            "temperature": preset.get("temperature", 0.7),
            "description": preset.get("description", ""),
        }

        self.main_window.save_ohmyopencode_config()
        self.accept()


# ==================== Skill 发现器 ====================
@dataclass
class DiscoveredSkill:
    """发现的 Skill 信息"""

    name: str
    description: str
    path: Path
    source: (
        str  # 'opencode-global', 'opencode-project', 'claude-global', 'claude-project'
    )
    license_info: Optional[str] = None
    compatibility: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None
    content: str = ""


class SkillDiscovery:
    """Skill 发现器 - 扫描所有路径发现已有的 Skill"""

    # Skill 搜索路径配置
    SKILL_PATHS = {
        "opencode-global": Path.home() / ".config" / "opencode" / "skills",
        "claude-global": Path.home() / ".claude" / "skills",
    }

    @staticmethod
    def get_project_paths() -> Dict[str, Path]:
        """获取项目级别的 Skill 路径"""
        cwd = Path.cwd()
        return {
            "opencode-project": cwd / ".opencode" / "skills",
            "claude-project": cwd / ".claude" / "skills",
        }

    @staticmethod
    def validate_skill_name(name: str) -> Tuple[bool, str]:
        """验证 Skill 名称是否符合规范

        规则：
        - 1-64 字符
        - 小写字母数字 + 单连字符分隔
        - 不能以 - 开头或结尾
        - 不能有连续 --

        Returns:
            (是否有效, 错误信息)
        """
        if not name:
            return False, "名称不能为空"
        if len(name) > 64:
            return False, "名称不能超过 64 字符"
        if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", name):
            return False, "名称格式错误：只能使用小写字母、数字、单连字符分隔"
        return True, ""

    @staticmethod
    def validate_description(desc: str) -> Tuple[bool, str]:
        """验证描述是否符合规范

        规则：1-1024 字符
        """
        if not desc:
            return False, "描述不能为空"
        if len(desc) > 1024:
            return False, "描述不能超过 1024 字符"
        return True, ""

    @staticmethod
    def parse_skill_file(skill_path: Path) -> Optional[DiscoveredSkill]:
        """解析 SKILL.md 文件

        Args:
            skill_path: SKILL.md 文件路径

        Returns:
            解析后的 DiscoveredSkill 对象，解析失败返回 None
        """
        if not skill_path.exists():
            return None

        try:
            content = skill_path.read_text(encoding="utf-8")
        except Exception:
            return None

        # 解析 frontmatter
        frontmatter = {}
        body = content

        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    # 简单的 YAML 解析（不依赖 pyyaml）
                    yaml_content = parts[1].strip()
                    for line in yaml_content.split("\n"):
                        line = line.strip()
                        if ":" in line and not line.startswith("#"):
                            key, value = line.split(":", 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            # 处理 metadata 子对象
                            if key == "metadata":
                                frontmatter["metadata"] = {}
                            elif key.startswith("  ") and "metadata" in frontmatter:
                                # metadata 子项
                                sub_key = key.strip()
                                frontmatter["metadata"][sub_key] = value
                            else:
                                frontmatter[key] = value
                    body = parts[2].strip()
                except Exception:
                    pass

        name = frontmatter.get("name", "")
        description = frontmatter.get("description", "")

        if not name or not description:
            return None

        # 确定来源
        skill_dir = skill_path.parent
        source = "unknown"
        for src, base_path in SkillDiscovery.SKILL_PATHS.items():
            try:
                if skill_dir.is_relative_to(base_path):
                    source = src
                    break
            except (ValueError, TypeError):
                pass

        if source == "unknown":
            for src, base_path in SkillDiscovery.get_project_paths().items():
                try:
                    if skill_dir.is_relative_to(base_path):
                        source = src
                        break
                except (ValueError, TypeError):
                    pass

        return DiscoveredSkill(
            name=name,
            description=description,
            path=skill_path,
            source=source,
            license_info=frontmatter.get("license"),
            compatibility=frontmatter.get("compatibility"),
            metadata=frontmatter.get("metadata")
            if isinstance(frontmatter.get("metadata"), dict)
            else None,
            content=body,
        )

    @classmethod
    def discover_all(cls) -> List[DiscoveredSkill]:
        """发现所有 Skill

        Returns:
            发现的 Skill 列表
        """
        skills = []
        seen_names = set()

        # 合并所有搜索路径
        all_paths = {**cls.SKILL_PATHS, **cls.get_project_paths()}

        for source, base_path in all_paths.items():
            if not base_path.exists():
                continue

            # 遍历 skills 目录下的子目录
            try:
                for skill_dir in base_path.iterdir():
                    if not skill_dir.is_dir():
                        continue

                    # 尝试查找 SKILL.md 或 SKILL.txt
                    skill_file = None
                    for filename in ["SKILL.md", "SKILL.txt"]:
                        potential_file = skill_dir / filename
                        if potential_file.exists():
                            skill_file = potential_file
                            break

                    if not skill_file:
                        continue

                    try:
                        skill = cls.parse_skill_file(skill_file)
                        if skill and skill.name not in seen_names:
                            skills.append(skill)
                            seen_names.add(skill.name)
                    except Exception as e:
                        # 解析单个skill失败，记录但继续处理其他skills
                        print(f"解析 skill 失败 {skill_dir.name}: {e}")
                        continue
            except Exception as e:
                # 遍历目录失败，记录但继续处理其他路径
                print(f"遍历目录失败 {base_path}: {e}")
                continue

        return skills

    @classmethod
    def get_skill_by_name(cls, name: str) -> Optional[DiscoveredSkill]:
        """根据名称获取 Skill"""
        for skill in cls.discover_all():
            if skill.name == name:
                return skill
        return None


# ==================== Skill 市场 ====================
class SkillMarket:
    """Skill 市场 - 内置常用 Skills 列表"""

    # 内置 Skill 列表（仅 Anthropic 官方 Skills - 已验证可用）
    FEATURED_SKILLS = [
        # UI/UX 和设计类
        {
            "name": "ui-ux-pro-max",
            "repo": "nextlevelbuilder/ui-ux-pro-max-skill",
            "description": "ui_ux_pro_max_desc",
            "category": "ui_ux",
            "tags": ["ui", "ux", "design", "frontend"],
            "path": ".opencode/skills/ui-ux-pro-max",
        },
        {
            "name": "canvas-design",
            "repo": "anthropics/skills",
            "description": "canvas_design_desc",
            "category": "ui_ux",
            "tags": ["design", "canvas", "art"],
            "path": "skills/canvas-design",
        },
        {
            "name": "theme-factory",
            "repo": "anthropics/skills",
            "description": "theme_factory_desc",
            "category": "ui_ux",
            "tags": ["theme", "styling", "design"],
            "path": "skills/theme-factory",
        },
        {
            "name": "web-artifacts-builder",
            "repo": "anthropics/skills",
            "description": "web_artifacts_builder_desc",
            "category": "ui_ux",
            "tags": ["web", "react", "frontend"],
            "path": "skills/web-artifacts-builder",
        },
        # 开发工具类
        {
            "name": "mcp-builder",
            "repo": "anthropics/skills",
            "description": "mcp_builder_desc",
            "category": "dev_tools",
            "tags": ["mcp", "server", "protocol"],
            "path": "skills/mcp-builder",
        },
        {
            "name": "webapp-testing",
            "repo": "anthropics/skills",
            "description": "webapp_testing_desc",
            "category": "testing",
            "tags": ["testing", "webapp", "automation"],
            "path": "skills/webapp-testing",
        },
        {
            "name": "skill-creator",
            "repo": "anthropics/skills",
            "description": "skill_creator_desc",
            "category": "dev_tools",
            "tags": ["skill", "creator", "development"],
            "path": "skills/skill-creator",
        },
        # 创意和媒体类
        {
            "name": "algorithmic-art",
            "repo": "anthropics/skills",
            "description": "algorithmic_art_desc",
            "category": "creative",
            "tags": ["art", "generative", "creative"],
            "path": "skills/algorithmic-art",
        },
        {
            "name": "slack-gif-creator",
            "repo": "anthropics/skills",
            "description": "slack_gif_creator_desc",
            "category": "creative",
            "tags": ["slack", "gif", "creative"],
            "path": "skills/slack-gif-creator",
        },
        # 文档和沟通类
        {
            "name": "doc-coauthoring",
            "repo": "anthropics/skills",
            "description": "doc_coauthoring_desc",
            "category": "documentation",
            "tags": ["documentation", "collaboration", "writing"],
            "path": "skills/doc-coauthoring",
        },
        {
            "name": "brand-guidelines",
            "repo": "anthropics/skills",
            "description": "brand_guidelines_desc",
            "category": "documentation",
            "tags": ["brand", "guidelines", "design"],
            "path": "skills/brand-guidelines",
        },
        {
            "name": "internal-comms",
            "repo": "anthropics/skills",
            "description": "internal_comms_desc",
            "category": "documentation",
            "tags": ["communication", "internal", "team"],
            "path": "skills/internal-comms",
        },
    ]

    @classmethod
    def get_all_skills(cls) -> List[Dict[str, Any]]:
        """获取所有市场 Skills（翻译后）"""
        return [cls._translate_skill(s) for s in cls.FEATURED_SKILLS]

    @classmethod
    def _translate_skill(cls, skill: Dict[str, Any]) -> Dict[str, Any]:
        """翻译 Skill 数据"""
        translated = skill.copy()
        translated["description"] = tr(f"skill.market_skills.{skill['description']}")
        translated["category"] = tr(f"skill.categories.{skill['category']}")
        return translated

    @classmethod
    def search_skills(cls, query: str) -> List[Dict[str, Any]]:
        """搜索 Skills"""
        query = query.lower()
        results = []
        for skill in cls.FEATURED_SKILLS:
            translated = cls._translate_skill(skill)
            if (
                query in skill["name"].lower()
                or query in translated["description"].lower()
                or any(query in tag for tag in skill["tags"])
            ):
                results.append(translated)
        return results

    @classmethod
    def get_by_category(cls, category: str) -> List[Dict[str, Any]]:
        """按分类获取 Skills"""
        all_skills = cls.get_all_skills()
        return [s for s in all_skills if s["category"] == category]

    @classmethod
    def get_categories(cls) -> List[str]:
        """获取所有分类（翻译后）"""
        category_keys = set(s["category"] for s in cls.FEATURED_SKILLS)
        translated_categories = [tr(f"skill.categories.{key}") for key in category_keys]
        return sorted(translated_categories)


# ==================== Skill 市场对话框 ====================
class SkillMarketDialog(MessageBoxBase):
    """Skill 市场对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel(tr("skill.market_dialog.title"), self)
        self.selected_skill = None

        # 搜索框
        search_layout = QHBoxLayout()
        self.search_edit = LineEdit(self.widget)
        self.search_edit.setPlaceholderText(
            tr("skill.market_dialog.search_placeholder")
        )
        self.search_edit.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_edit)

        search_btn = PushButton(FIF.SEARCH, tr("common.search"), self.widget)
        search_btn.clicked.connect(self._on_search)
        search_layout.addWidget(search_btn)

        # 分类筛选
        self.category_combo = ComboBox(self.widget)
        self.category_combo.addItem(tr("skill.market_dialog.category_all"))
        self.category_combo.addItems(SkillMarket.get_categories())
        self.category_combo.currentTextChanged.connect(self._on_category_changed)
        search_layout.addWidget(self.category_combo)

        # Skills 表格
        self.table = TableWidget(self.widget)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            [
                tr("common.name"),
                tr("common.description"),
                tr("skill.market_dialog.category_label"),
                tr("skill.market_dialog.repo_label"),
            ]
        )
        # 设置列宽：名称自适应，描述拉伸，分类和仓库固定宽度
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setColumnWidth(2, 100)  # 分类列固定 100px
        self.table.setColumnWidth(3, 200)  # 仓库列固定 200px
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setMinimumHeight(400)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)

        # 填充数据
        self._load_skills(SkillMarket.get_all_skills())

        # 添加"浏览更多技能"链接
        browse_more_layout = QHBoxLayout()
        browse_more_layout.addStretch()

        # SkillsMP 链接
        skillsmp_label = HyperlinkLabel(self.widget)
        skillsmp_label.setUrl("https://skillsmp.com/")
        skillsmp_label.setText("🌐 SkillsMP.com")
        skillsmp_label.setToolTip("访问 SkillsMP.com 浏览更多社区技能")
        browse_more_layout.addWidget(skillsmp_label)

        browse_more_layout.addSpacing(20)

        # ComposioHQ 链接
        composio_label = HyperlinkLabel(self.widget)
        composio_label.setUrl("https://github.com/ComposioHQ/awesome-claude-skills")
        composio_label.setText("🌐 ComposioHQ Skills")
        composio_label.setToolTip("访问 ComposioHQ 浏览更多社区技能")
        browse_more_layout.addWidget(composio_label)

        browse_more_layout.addStretch()

        # 布局
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addLayout(search_layout)
        self.viewLayout.addWidget(self.table)
        self.viewLayout.addLayout(browse_more_layout)

        self.yesButton.setText(tr("skill.market_dialog.install_button"))
        self.yesButton.setEnabled(False)
        self.cancelButton.setText(tr("common.cancel"))

        self.widget.setMinimumWidth(800)
        self.widget.setMinimumHeight(600)

    def _load_skills(self, skills: List[Dict[str, Any]]):
        """加载 Skills 到表格"""
        self.table.setRowCount(0)
        for skill in skills:
            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 0, QTableWidgetItem(skill["name"]))
            self.table.setItem(row, 1, QTableWidgetItem(skill["description"]))
            self.table.setItem(row, 2, QTableWidgetItem(skill["category"]))
            self.table.setItem(row, 3, QTableWidgetItem(skill["repo"]))

    def _on_search(self):
        """搜索 Skills"""
        query = self.search_edit.text().strip()
        if query:
            skills = SkillMarket.search_skills(query)
        else:
            skills = SkillMarket.get_all_skills()
        self._load_skills(skills)

    def _on_category_changed(self, category: str):
        """分类筛选"""
        if category == tr("skill.market_dialog.category_all"):
            skills = SkillMarket.get_all_skills()
        else:
            skills = SkillMarket.get_by_category(category)
        self._load_skills(skills)

    def _on_selection_changed(self):
        """选择变化"""
        selected = self.table.selectedItems()
        if selected:
            row = selected[0].row()
            repo = self.table.item(row, 3).text()
            # 从市场列表中找到对应的 skill
            for skill in SkillMarket.get_all_skills():
                if skill["repo"] == repo:
                    self.selected_skill = skill
                    break
            self.yesButton.setEnabled(True)
        else:
            self.selected_skill = None
            self.yesButton.setEnabled(False)

    def get_selected_skill(self) -> Optional[Dict[str, Any]]:
        """获取选中的 Skill"""
        return self.selected_skill


# ==================== 安全扫描器 ====================
class SkillSecurityScanner:
    """Skill 安全扫描器 - 检测可疑代码模式"""

    # 危险模式列表
    DANGEROUS_PATTERNS = [
        {
            "pattern": r"os\.system\(",
            "level": "high",
            "description_key": "skill.security_dialog.risk_os_system",
        },
        {
            "pattern": r"subprocess\.(call|run|Popen)",
            "level": "high",
            "description_key": "skill.security_dialog.risk_subprocess",
        },
        {
            "pattern": r"eval\(",
            "level": "critical",
            "description_key": "skill.security_dialog.risk_eval",
        },
        {
            "pattern": r"exec\(",
            "level": "critical",
            "description_key": "skill.security_dialog.risk_exec",
        },
        {
            "pattern": r"__import__\(",
            "level": "medium",
            "description_key": "skill.security_dialog.risk_import",
        },
        {
            "pattern": r"os\.remove\(",
            "level": "high",
            "description_key": "skill.security_dialog.risk_remove",
        },
        {
            "pattern": r"shutil\.rmtree\(",
            "level": "high",
            "description_key": "skill.security_dialog.risk_rmtree",
        },
        {
            "pattern": r"requests\.(get|post|put|delete)",
            "level": "low",
            "description_key": "skill.security_dialog.risk_requests",
        },
        {
            "pattern": r"socket\.",
            "level": "medium",
            "description_key": "skill.security_dialog.risk_socket",
        },
    ]

    @classmethod
    def scan_skill(cls, skill_path: Path) -> Dict[str, Any]:
        """扫描 Skill 的安全风险"""
        import re

        issues = []
        score = 100

        try:
            content = skill_path.read_text(encoding="utf-8")
            lines = content.split("\n")

            for pattern_info in cls.DANGEROUS_PATTERNS:
                pattern = pattern_info["pattern"]
                level = pattern_info["level"]
                description_key = pattern_info["description_key"]

                for line_num, line in enumerate(lines, 1):
                    if re.search(pattern, line):
                        issues.append(
                            {
                                "line": line_num,
                                "code": line.strip(),
                                "level": level,
                                "description_key": description_key,
                            }
                        )

                        # 扣分
                        if level == "critical":
                            score -= 30
                        elif level == "high":
                            score -= 20
                        elif level == "medium":
                            score -= 10
                        elif level == "low":
                            score -= 5

            score = max(0, score)

            return {
                "score": score,
                "issues": issues,
                "level": cls._get_risk_level(score),
            }

        except Exception as e:
            return {
                "score": 0,
                "issues": [
                    {
                        "line": 0,
                        "code": "",
                        "level": "critical",
                        "description": f"扫描失败: {str(e)}",
                    }
                ],
                "level": "unknown",
            }

    @staticmethod
    def _get_risk_level(score: int) -> str:
        """根据分数获取风险等级"""
        if score >= 90:
            return "safe"
        elif score >= 70:
            return "low"
        elif score >= 50:
            return "medium"
        elif score >= 30:
            return "high"
        else:
            return "critical"


# ==================== 安全扫描对话框 ====================
class SecurityScanDialog(MessageBoxBase):
    """安全扫描结果对话框"""

    def __init__(self, scan_result: Dict[str, Any], skill_name: str, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel(
            f"{tr('skill.security_dialog.title')} - {skill_name}", self
        )

        score = scan_result["score"]
        level = scan_result["level"]
        issues = scan_result["issues"]

        # 分数和等级
        score_layout = QHBoxLayout()
        score_label = TitleLabel(
            f"{tr('skill.security_dialog.score_label')} {score}/100", self.widget
        )
        score_layout.addWidget(score_label)

        level_colors = {
            "safe": "#4CAF50",
            "low": "#8BC34A",
            "medium": "#FF9800",
            "high": "#FF5722",
            "critical": "#F44336",
            "unknown": "#9E9E9E",
        }
        level_names = {
            "safe": tr("skill.security_dialog.level_safe"),
            "low": tr("skill.security_dialog.level_low"),
            "medium": tr("skill.security_dialog.level_medium"),
            "high": tr("skill.security_dialog.level_high"),
            "critical": tr("skill.security_dialog.level_critical"),
            "unknown": tr("skill.security_dialog.level_unknown"),
        }

        level_label = StrongBodyLabel(
            level_names.get(level, tr("skill.security_dialog.level_unknown")),
            self.widget,
        )
        level_label.setStyleSheet(f"color: {level_colors.get(level, '#9E9E9E')};")
        score_layout.addWidget(level_label)
        score_layout.addStretch()

        # 问题列表
        if issues:
            issues_label = BodyLabel(
                f"{tr('skill.security_dialog.issues_found')} {len(issues)} {tr('skill.security_dialog.issues_count')}",
                self.widget,
            )
        else:
            issues_label = BodyLabel(tr("skill.security_dialog.no_issues"), self.widget)

        # 问题表格
        self.table = TableWidget(self.widget)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            [
                tr("skill.security_dialog.table_line"),
                tr("skill.security_dialog.table_risk"),
                tr("skill.security_dialog.table_description"),
                tr("skill.security_dialog.table_code"),
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setMinimumHeight(300)

        for issue in issues:
            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 0, QTableWidgetItem(str(issue["line"])))
            self.table.setItem(row, 1, QTableWidgetItem(issue["level"]))
            # 使用翻译键获取描述
            description = tr(issue.get("description_key", ""))
            self.table.setItem(row, 2, QTableWidgetItem(description))
            self.table.setItem(row, 3, QTableWidgetItem(issue["code"]))

        # 布局
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addLayout(score_layout)
        self.viewLayout.addWidget(issues_label)
        self.viewLayout.addWidget(self.table)

        self.yesButton.setText(tr("skill.security_dialog.close_button"))
        self.cancelButton.hide()

        self.widget.setMinimumWidth(900)
        self.widget.setMinimumHeight(600)


# ==================== Skill 安装器 ====================
class SkillInstaller:
    """Skill 安装器 - 支持从 GitHub 和本地安装"""

    @staticmethod
    def detect_default_branch(owner: str, repo: str) -> str:
        """检测GitHub仓库的默认分支

        Args:
            owner: GitHub 用户名
            repo: 仓库名

        Returns:
            默认分支名（main 或 master），如果检测失败返回 "main"
        """
        import requests

        try:
            # 尝试通过 GitHub API 获取仓库信息
            api_url = f"https://api.github.com/repos/{owner}/{repo}"
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("default_branch", "main")
        except Exception:
            pass

        # API 失败时，尝试检测 main 和 master 分支
        for branch in ["main", "master"]:
            try:
                test_url = (
                    f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
                )
                response = requests.head(test_url, timeout=5)
                if response.status_code == 200:
                    return branch
            except Exception:
                continue

        # 默认返回 main
        return "main"

    @staticmethod
    def parse_source(source: str) -> Tuple[str, Dict[str, str]]:
        """解析安装源

        Args:
            source: GitHub URL / shorthand / 本地路径

        Returns:
            (类型, 详情字典)
            类型: 'github', 'local'
        """
        import re

        # GitHub shorthand: user/repo
        if re.match(r"^[\w-]+/[\w-]+$", source):
            owner, repo = source.split("/")
            return "github", {
                "owner": owner,
                "repo": repo,
                "branch": "main",
                "url": f"https://github.com/{owner}/{repo}",
            }

        # 完整 GitHub URL
        if source.startswith("https://github.com/"):
            match = re.match(r"https://github\.com/([\w-]+)/([\w-]+)", source)
            if match:
                owner, repo = match.groups()
                return "github", {
                    "owner": owner,
                    "repo": repo,
                    "branch": "main",
                    "url": source,
                }

        # 本地路径
        if os.path.exists(source):
            return "local", {"path": source}

        raise ValueError(f"无法识别的来源格式: {source}")

    @staticmethod
    def install_from_github(
        owner: str,
        repo: str,
        branch: str,
        target_dir: Path,
        subdir: str = None,
        progress_callback=None,
    ) -> Tuple[bool, str]:
        """从 GitHub 安装 Skill

        Args:
            owner: GitHub 用户名
            repo: 仓库名
            branch: 分支名
            target_dir: 目标目录（skills 根目录）
            subdir: 子目录路径（如 "skills/mcp-builder"）
            progress_callback: 进度回调函数

        Returns:
            (是否成功, 消息)
        """
        import requests
        import zipfile
        import tempfile
        from datetime import datetime

        try:
            # 1. 下载 ZIP
            if progress_callback:
                progress_callback("正在下载...")

            zip_url = (
                f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
            )
            response = requests.get(zip_url, stream=True, timeout=30)

            # 如果404，尝试检测并使用正确的分支
            if response.status_code == 404:
                if progress_callback:
                    progress_callback("检测分支...")
                detected_branch = SkillInstaller.detect_default_branch(owner, repo)
                if detected_branch != branch:
                    if progress_callback:
                        progress_callback(f"使用分支: {detected_branch}")
                    branch = detected_branch
                    zip_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
                    response = requests.get(zip_url, stream=True, timeout=30)

            response.raise_for_status()

            # 2. 解压到临时目录
            if progress_callback:
                progress_callback("正在解压...")

            with tempfile.TemporaryDirectory() as temp_dir:
                zip_path = Path(temp_dir) / "skill.zip"
                with open(zip_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(temp_dir)

                # 3. 查找 SKILL.md 或 SKILL.txt
                extracted_dir = Path(temp_dir) / f"{repo}-{branch}"

                # 如果指定了子目录，则在子目录中查找
                if subdir:
                    skill_dir = extracted_dir / subdir
                    if not skill_dir.exists():
                        return False, f"子目录不存在: {subdir}"
                else:
                    skill_dir = extracted_dir

                # 尝试查找 SKILL.md 或 SKILL.txt
                skill_file = None
                for filename in ["SKILL.md", "SKILL.txt"]:
                    potential_file = skill_dir / filename
                    if potential_file.exists():
                        skill_file = potential_file
                        break

                if not skill_file:
                    return (
                        False,
                        f"未找到 SKILL.md 或 SKILL.txt 文件{f' (在 {subdir} 中)' if subdir else ''}",
                    )

                # 4. 解析 Skill 名称
                skill = SkillDiscovery.parse_skill_file(skill_file)
                if not skill:
                    return False, "SKILL 文件格式错误"

                # 5. 复制到目标目录
                if progress_callback:
                    progress_callback("正在安装...")

                skill_target = target_dir / skill.name
                if skill_target.exists():
                    shutil.rmtree(skill_target)

                shutil.copytree(skill_dir, skill_target)

                # 6. 获取最新 commit hash
                commit_hash = None
                try:
                    api_url = (
                        f"https://api.github.com/repos/{owner}/{repo}/commits/{branch}"
                    )
                    commit_response = requests.get(api_url, timeout=10)
                    if commit_response.status_code == 200:
                        commit_hash = commit_response.json()["sha"]
                except Exception:
                    pass

                # 7. 保存元数据
                meta = {
                    "source": "github",
                    "owner": owner,
                    "repo": repo,
                    "branch": branch,
                    "url": f"https://github.com/{owner}/{repo}",
                    "installed_at": datetime.now().isoformat(),
                    "commit_hash": commit_hash,
                }

                # 如果有子目录，记录下来
                if subdir:
                    meta["subdir"] = subdir

                meta_file = skill_target / ".skill-meta.json"
                with open(meta_file, "w", encoding="utf-8") as f:
                    json.dump(meta, f, indent=2, ensure_ascii=False)

                if progress_callback:
                    progress_callback("安装完成！")

                return True, f"Skill '{skill.name}' 安装成功"

        except requests.exceptions.RequestException as e:
            return False, f"网络错误: {str(e)}"
        except Exception as e:
            return False, f"安装失败: {str(e)}"

    @staticmethod
    def install_from_local(
        source_path: str, target_dir: Path, progress_callback=None
    ) -> Tuple[bool, str]:
        """从本地路径安装 Skill

        Args:
            source_path: 本地 Skill 目录路径
            target_dir: 目标目录（skills 根目录）
            progress_callback: 进度回调函数

        Returns:
            (是否成功, 消息)
        """
        from datetime import datetime

        try:
            source = Path(source_path)
            if not source.exists():
                return False, f"路径不存在: {source_path}"

            # 查找 SKILL.md
            skill_md = source / "SKILL.md"
            if not skill_md.exists():
                return False, "未找到 SKILL.md 文件"

            # 解析 Skill
            skill = SkillDiscovery.parse_skill_file(skill_md)
            if not skill:
                return False, "SKILL.md 格式错误"

            # 复制到目标目录
            if progress_callback:
                progress_callback("正在复制...")

            skill_target = target_dir / skill.name
            if skill_target.exists():
                shutil.rmtree(skill_target)

            shutil.copytree(source, skill_target)

            # 保存元数据
            meta = {
                "source": "local",
                "original_path": str(source.absolute()),
                "installed_at": datetime.now().isoformat(),
            }

            meta_file = skill_target / ".skill-meta.json"
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)

            if progress_callback:
                progress_callback("安装完成！")

            return True, f"Skill '{skill.name}' 安装成功"

        except Exception as e:
            return False, f"安装失败: {str(e)}"


# ==================== Skill 更新器 ====================
class SkillUpdater:
    """Skill 更新器 - 检查和更新 Skills"""

    @staticmethod
    def check_updates(skills: List[DiscoveredSkill]) -> List[Dict[str, Any]]:
        """检查 Skills 更新

        Args:
            skills: Skill 列表

        Returns:
            更新信息列表
        """
        import requests

        updates = []

        for skill in skills:
            meta_file = skill.path.parent / ".skill-meta.json"

            if not meta_file.exists():
                # 本地 Skill，无元数据
                updates.append(
                    {
                        "skill": skill,
                        "has_update": False,
                        "current_commit": None,
                        "latest_commit": None,
                        "meta": None,
                        "status": "本地",
                    }
                )
                continue

            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)

                if meta.get("source") != "github":
                    # 非 GitHub 来源
                    updates.append(
                        {
                            "skill": skill,
                            "has_update": False,
                            "current_commit": None,
                            "latest_commit": None,
                            "meta": meta,
                            "status": "本地",
                        }
                    )
                    continue

                # 获取最新 commit
                owner = meta["owner"]
                repo = meta["repo"]
                branch = meta.get("branch", "main")

                api_url = (
                    f"https://api.github.com/repos/{owner}/{repo}/commits/{branch}"
                )
                response = requests.get(api_url, timeout=10)
                response.raise_for_status()

                latest_commit = response.json()["sha"]
                current_commit = meta.get("commit_hash")

                has_update = current_commit is None or current_commit != latest_commit

                updates.append(
                    {
                        "skill": skill,
                        "has_update": has_update,
                        "current_commit": current_commit[:7]
                        if current_commit
                        else "未知",
                        "latest_commit": latest_commit[:7],
                        "meta": meta,
                        "status": "有更新" if has_update else "最新",
                    }
                )

            except Exception as e:
                print(f"检查更新失败 {skill.name}: {e}")
                updates.append(
                    {
                        "skill": skill,
                        "has_update": False,
                        "current_commit": None,
                        "latest_commit": None,
                        "meta": meta if "meta" in locals() else None,
                        "status": "检查失败",
                    }
                )

        return updates

    @staticmethod
    def update_skill(
        skill: DiscoveredSkill, meta: dict, progress_callback=None
    ) -> Tuple[bool, str]:
        """更新单个 Skill

        Args:
            skill: Skill 对象
            meta: 元数据
            progress_callback: 进度回调

        Returns:
            (是否成功, 消息)
        """
        if meta.get("source") != "github":
            return False, "仅支持更新从 GitHub 安装的 Skills"

        try:
            # 重新安装
            target_dir = skill.path.parent.parent  # skills 根目录

            # 获取子目录路径（如果有）
            subdir = meta.get("subdir", None)

            success, message = SkillInstaller.install_from_github(
                meta["owner"],
                meta["repo"],
                meta.get("branch", "main"),
                target_dir,
                subdir=subdir,
                progress_callback=progress_callback,
            )

            return success, message

        except Exception as e:
            return False, f"更新失败: {str(e)}"


# ==================== Skill 安装对话框 ====================
class SkillInstallDialog(MessageBoxBase):
    """Skill 安装对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel(tr("skill.install_dialog.title"), self)

        # 来源输入
        self.source_label = BodyLabel(
            tr("skill.install_dialog.source_label"), self.widget
        )
        self.source_edit = LineEdit(self.widget)
        self.source_edit.setPlaceholderText("vercel-labs/git-release")

        # 提示信息
        self.hint_label = CaptionLabel(
            tr("skill.install_dialog.format_hint"),
            self.widget,
        )

        # 安装位置
        self.location_label = BodyLabel(
            tr("skill.install_dialog.location_label"), self.widget
        )
        self.location_combo = ComboBox(self.widget)
        self.location_combo.addItems(
            [
                tr("skill.install_dialog.location_opencode_global"),
                tr("skill.install_dialog.location_opencode_project"),
                tr("skill.install_dialog.location_claude_global"),
                tr("skill.install_dialog.location_claude_project"),
            ]
        )

        # 进度标签
        self.progress_label = CaptionLabel("", self.widget)

        # 布局
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.source_label)
        self.viewLayout.addWidget(self.source_edit)
        self.viewLayout.addWidget(self.hint_label)
        self.viewLayout.addWidget(self.location_label)
        self.viewLayout.addWidget(self.location_combo)
        self.viewLayout.addWidget(self.progress_label)

        self.yesButton.setText(tr("skill.install_dialog.install_button"))
        self.cancelButton.setText(tr("common.cancel"))

        self.widget.setMinimumWidth(500)

    def get_source(self) -> str:
        return self.source_edit.text().strip()

    def get_target_dir(self) -> Path:
        loc_text = self.location_combo.currentText()
        if tr("skill.install_dialog.location_opencode_global") in loc_text:
            return Path.home() / ".config" / "opencode" / "skills"
        elif tr("skill.install_dialog.location_opencode_project") in loc_text:
            return Path.cwd() / ".opencode" / "skills"
        elif tr("skill.install_dialog.location_claude_global") in loc_text:
            return Path.home() / ".claude" / "skills"
        else:
            return Path.cwd() / ".claude" / "skills"

    def update_progress(self, message: str):
        self.progress_label.setText(message)
        QApplication.processEvents()


# ==================== Skill 更新对话框 ====================
class SkillUpdateDialog(MessageBoxBase):
    """Skill 更新对话框"""

    def __init__(self, updates: List[Dict[str, Any]], parent=None):
        super().__init__(parent)
        self.updates = updates
        self.titleLabel = SubtitleLabel(tr("skill.update_dialog.title"), self)

        # 统计信息
        total = len(updates)
        has_update_count = sum(1 for u in updates if u["has_update"])
        self.info_label = BodyLabel(
            tr(
                "skill.update_dialog.info_text",
                total=total,
                has_update=has_update_count,
            ),
            self.widget,
        )

        # 表格
        self.table = TableWidget(self.widget)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            [
                tr("skill.update_dialog.table_select"),
                tr("skill.update_dialog.table_name"),
                tr("skill.update_dialog.table_current"),
                tr("skill.update_dialog.table_latest"),
                tr("skill.update_dialog.table_status"),
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.horizontalHeader().resizeSection(0, 60)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeToContents
        )
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setMinimumHeight(300)

        # 填充数据
        self.checkboxes = []
        for update in updates:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # 复选框
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox = CheckBox()
            checkbox.setChecked(update["has_update"])
            checkbox.setEnabled(update["has_update"])
            checkbox_layout.addWidget(checkbox)
            self.checkboxes.append(checkbox)
            self.table.setCellWidget(row, 0, checkbox_widget)

            # Skill 名称
            self.table.setItem(row, 1, QTableWidgetItem(update["skill"].name))

            # 当前版本
            if update["current_commit"]:
                current = update["current_commit"]
            elif update["status"] == tr("skill.update_dialog.status_local"):
                current = tr("skill.update_dialog.status_local")
            else:
                current = tr("skill.update_dialog.status_unknown")
            self.table.setItem(row, 2, QTableWidgetItem(current))

            # 最新版本
            if update["latest_commit"]:
                latest = update["latest_commit"]
            elif update["status"] == tr("skill.update_dialog.status_local"):
                latest = tr("skill.update_dialog.status_local")
            else:
                latest = "-"
            self.table.setItem(row, 3, QTableWidgetItem(latest))

            # 状态
            self.table.setItem(row, 4, QTableWidgetItem(update["status"]))

        # 按钮布局
        btn_layout = QHBoxLayout()
        self.select_all_btn = PushButton(tr("common.select_all"), self.widget)
        self.select_all_btn.clicked.connect(self._on_select_all)
        btn_layout.addWidget(self.select_all_btn)

        self.deselect_all_btn = PushButton(tr("common.deselect_all"), self.widget)
        self.deselect_all_btn.clicked.connect(self._on_deselect_all)
        btn_layout.addWidget(self.deselect_all_btn)
        btn_layout.addStretch()

        # 布局
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.info_label)
        self.viewLayout.addWidget(self.table)
        self.viewLayout.addLayout(btn_layout)

        self.yesButton.setText(tr("skill.update_selected"))
        self.cancelButton.setText(tr("common.cancel"))

        self.widget.setMinimumWidth(700)
        self.widget.setMinimumHeight(500)

    def _on_select_all(self):
        for checkbox in self.checkboxes:
            if checkbox.isEnabled():
                checkbox.setChecked(True)

    def _on_deselect_all(self):
        for checkbox in self.checkboxes:
            checkbox.setChecked(False)

    def get_selected_updates(self) -> List[Dict[str, Any]]:
        """获取选中的更新项"""
        selected = []
        for i, checkbox in enumerate(self.checkboxes):
            if checkbox.isChecked():
                selected.append(self.updates[i])
        return selected


# ==================== Skill 页面 ====================
class SkillPage(BasePage):
    """Skill 管理页面 - 增强版

    功能：
    1. Skill 发现与浏览 - 扫描所有路径显示已有 skill（包括 Claude 兼容路径）
    2. 完整的 frontmatter 编辑 - 支持 license、compatibility、metadata
    3. Skill 预览与编辑 - 查看和编辑现有 skill
    4. 全局权限配置 - 配置 permission.skill 权限
    5. Agent 级别权限配置 - 为特定 agent 配置 skill 权限
    6. 禁用 skill 工具 - 支持 agent.tools.skill: false 配置
    """

    # 来源显示名称映射 - 使用翻译键
    SOURCE_LABELS = {
        "opencode-global": "skill.source_opencode_global",
        "opencode-project": "skill.source_opencode_project",
        "claude-global": "skill.source_claude_global",
        "claude-project": "skill.source_claude_project",
        "unknown": "skill.source_unknown",
    }

    def __init__(self, main_window, parent=None):
        super().__init__(tr("skill.title"), parent)
        self.main_window = main_window
        self._current_skill: Optional[DiscoveredSkill] = None
        self._setup_ui()
        self._load_all_data()

    def _setup_ui(self):
        # 使用 Pivot 实现标签页切换
        self.pivot = Pivot(self)
        self._layout.addWidget(self.pivot)

        # 内容区域
        self.stacked_widget = QStackedWidget(self)
        self._layout.addWidget(self.stacked_widget, 1)

        # 创建各个标签页
        self._create_browse_tab()
        self._create_create_tab()
        self._create_permission_tab()

        # 添加标签页到 Pivot
        self.pivot.addItem(
            routeKey="browse",
            text=tr("skill.browse"),
            onClick=lambda: self.stacked_widget.setCurrentIndex(0),
        )
        self.pivot.addItem(
            routeKey="create",
            text=tr("skill.create"),
            onClick=lambda: self.stacked_widget.setCurrentIndex(1),
        )
        self.pivot.addItem(
            routeKey="permission",
            text=tr("skill.permission"),
            onClick=lambda: self.stacked_widget.setCurrentIndex(2),
        )

        self.pivot.setCurrentItem("browse")

    def _load_all_data(self):
        """加载所有数据"""
        self._refresh_skill_list()
        self._load_permission_data()

    def _refresh_skill_list(self):
        """刷新 Skill 列表"""
        if hasattr(self, "skill_list"):
            self.skill_list.clear()
            skills = SkillDiscovery.discover_all()
            for skill in skills:
                source_key = self.SOURCE_LABELS.get(
                    skill.source, "skill.source_unknown"
                )
                source_label = tr(source_key)
                item = QListWidgetItem(f"{skill.name} ({source_label})")
                item.setData(Qt.UserRole, skill)
                self.skill_list.addItem(item)

    def _load_permission_data(self):
        """加载权限数据"""
        if hasattr(self, "perm_table"):
            self.perm_table.setRowCount(0)
            config = self.main_window.opencode_config or {}
            permissions = config.get("permission", {}).get("skill", {})

            if isinstance(permissions, dict):
                for pattern, perm in permissions.items():
                    row = self.perm_table.rowCount()
                    self.perm_table.insertRow(row)
                    self.perm_table.setItem(row, 0, QTableWidgetItem(pattern))
                    self.perm_table.setItem(row, 1, QTableWidgetItem(perm))

    def _create_browse_tab(self):
        """创建浏览标签页 - 左侧 Skill 列表，右侧详情预览"""
        browse_widget = QWidget()
        browse_layout = QVBoxLayout(browse_widget)
        browse_layout.setContentsMargins(0, 16, 0, 0)

        # 使用 QSplitter 实现左右分栏
        splitter = QSplitter(Qt.Orientation.Horizontal, browse_widget)

        # ===== 左侧：Skill 列表 =====
        left_widget = QWidget()
        left_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 8, 0)

        left_layout.addWidget(SubtitleLabel(tr("skill.discovered_skills"), left_widget))
        left_layout.addWidget(
            CaptionLabel(
                tr("skill.scan_description"),
                left_widget,
            )
        )

        # 工具栏
        toolbar = QHBoxLayout()

        market_btn = PrimaryPushButton(
            FIF.MARKET, tr("skill.skill_market"), left_widget
        )
        market_btn.clicked.connect(self._on_open_market)
        toolbar.addWidget(market_btn)

        install_btn = PushButton(FIF.DOWNLOAD, tr("skill.install_skill"), left_widget)
        install_btn.clicked.connect(self._on_install_skill)
        toolbar.addWidget(install_btn)

        update_btn = PushButton(FIF.UPDATE, tr("skill.check_updates"), left_widget)
        update_btn.clicked.connect(self._on_check_updates)
        toolbar.addWidget(update_btn)

        refresh_btn = PushButton(FIF.SYNC, tr("skill.refresh"), left_widget)
        refresh_btn.clicked.connect(self._refresh_skill_list)
        toolbar.addWidget(refresh_btn)

        toolbar.addStretch()
        left_layout.addLayout(toolbar)

        # Skill 列表
        self.skill_list = ListWidget(left_widget)
        self.skill_list.itemClicked.connect(self._on_skill_selected)
        # 确保显示垂直滚动条
        self.skill_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        left_layout.addWidget(self.skill_list, 1)

        # 路径说明
        path_info = CaptionLabel(
            tr("skill.search_paths"),
            left_widget,
        )
        left_layout.addWidget(path_info)

        # ===== 右侧：Skill 详情预览 =====
        right_widget = QWidget()
        right_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(8, 0, 0, 0)

        right_layout.addWidget(SubtitleLabel(tr("skill.skill_details"), right_widget))

        # 详情卡片
        detail_card = SimpleCardWidget(right_widget)
        detail_layout = QVBoxLayout(detail_card)
        detail_layout.setContentsMargins(16, 12, 16, 12)
        detail_layout.setSpacing(8)

        self.detail_name = StrongBodyLabel(tr("skill.select_to_view"), detail_card)
        detail_layout.addWidget(self.detail_name)

        self.detail_desc = CaptionLabel("", detail_card)
        self.detail_desc.setWordWrap(True)
        detail_layout.addWidget(self.detail_desc)

        # 元信息
        meta_layout = QHBoxLayout()
        self.detail_source = CaptionLabel("", detail_card)
        meta_layout.addWidget(self.detail_source)
        self.detail_license = CaptionLabel("", detail_card)
        meta_layout.addWidget(self.detail_license)
        self.detail_compat = CaptionLabel("", detail_card)
        meta_layout.addWidget(self.detail_compat)
        meta_layout.addStretch()
        detail_layout.addLayout(meta_layout)

        self.detail_path = CaptionLabel("", detail_card)
        self.detail_path.setWordWrap(True)
        detail_layout.addWidget(self.detail_path)

        right_layout.addWidget(detail_card)

        # 内容预览
        right_layout.addWidget(
            BodyLabel(tr("skill.content_preview") + ":", right_widget)
        )
        self.detail_content = TextEdit(right_widget)
        self.detail_content.setReadOnly(True)
        self.detail_content.setPlaceholderText(tr("dialog.placeholder_skill_select"))
        right_layout.addWidget(self.detail_content, 1)

        # 操作按钮
        btn_layout = QHBoxLayout()
        self.edit_skill_btn = PushButton(FIF.EDIT, tr("common.edit"), right_widget)
        self.edit_skill_btn.clicked.connect(self._on_edit_skill)
        self.edit_skill_btn.setEnabled(False)
        btn_layout.addWidget(self.edit_skill_btn)

        self.scan_skill_btn = PushButton(
            FIF.CERTIFICATE, tr("skill.scan_security"), right_widget
        )
        self.scan_skill_btn.clicked.connect(self._on_scan_skill)
        self.scan_skill_btn.setEnabled(False)
        btn_layout.addWidget(self.scan_skill_btn)

        self.delete_skill_btn = PushButton(
            FIF.DELETE, tr("common.delete"), right_widget
        )
        self.delete_skill_btn.clicked.connect(self._on_delete_skill)
        self.delete_skill_btn.setEnabled(False)
        btn_layout.addWidget(self.delete_skill_btn)

        self.open_folder_btn = PushButton(
            FIF.FOLDER, tr("skill.open_directory"), right_widget
        )
        self.open_folder_btn.clicked.connect(self._on_open_skill_folder)
        self.open_folder_btn.setEnabled(False)
        btn_layout.addWidget(self.open_folder_btn)

        btn_layout.addStretch()
        right_layout.addLayout(btn_layout)

        # 添加到 splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([350, 450])

        browse_layout.addWidget(splitter, 1)
        self.stacked_widget.addWidget(browse_widget)

    def _on_skill_selected(self, item):
        """选中 Skill 时显示详情"""
        skill = item.data(Qt.UserRole)
        if not skill:
            return

        self._current_skill = skill
        self.detail_name.setText(skill.name)
        self.detail_desc.setText(skill.description)
        source_key = self.SOURCE_LABELS.get(skill.source, "skill.source_unknown")
        self.detail_source.setText(f"{tr('skill.skill_source')}: {tr(source_key)}")
        self.detail_license.setText(
            f"{tr('skill.skill_license')}: {skill.license_info}"
            if skill.license_info
            else ""
        )
        self.detail_compat.setText(
            f"兼容: {skill.compatibility}" if skill.compatibility else ""
        )
        self.detail_path.setText(f"{tr('skill.skill_path')}: {skill.path}")
        self.detail_content.setText(skill.content)

        # 启用操作按钮
        self.edit_skill_btn.setEnabled(True)
        self.scan_skill_btn.setEnabled(True)
        self.delete_skill_btn.setEnabled(True)
        self.open_folder_btn.setEnabled(True)

    def _on_edit_skill(self):
        """编辑选中的 Skill"""
        if not self._current_skill:
            return

        # 切换到创建标签页并填充数据
        self.pivot.setCurrentItem("create")
        self.stacked_widget.setCurrentIndex(1)

        self.create_name_edit.setText(self._current_skill.name)
        self.create_desc_edit.setText(self._current_skill.description)
        self.create_license_edit.setText(self._current_skill.license_info or "")
        self.create_compat_edit.setText(self._current_skill.compatibility or "")
        self.create_content_edit.setText(self._current_skill.content)

        # 根据路径设置保存位置
        path_str = str(self._current_skill.path)
        if ".claude" in path_str:
            if str(Path.home()) in path_str:
                self.create_loc_combo.setCurrentText("Claude 全局 (~/.claude/skills/)")
            else:
                self.create_loc_combo.setCurrentText("Claude 项目 (.claude/skills/)")
        else:
            if str(Path.home()) in path_str:
                self.create_loc_combo.setCurrentText(
                    "OpenCode 全局 (~/.config/opencode/skills/)"
                )
            else:
                self.create_loc_combo.setCurrentText(
                    "OpenCode 项目 (.opencode/skills/)"
                )

    def _on_delete_skill(self):
        """删除选中的 Skill"""
        if not self._current_skill:
            return

        w = FluentMessageBox(
            tr("common.confirm_delete_title"),
            f"{tr('skill.delete_confirm', name=self._current_skill.name)}\n{tr('skill.skill_path')}: {self._current_skill.path}",
            self,
        )
        if w.exec_():
            try:
                skill_dir = self._current_skill.path.parent
                shutil.rmtree(skill_dir)
                self.show_success(
                    self.tr("common.success"),
                    self.tr(
                        "skill.skill_deleted_detail", name=self._current_skill.name
                    ),
                )
                self._current_skill = None
                self._refresh_skill_list()
                self._clear_detail()
            except Exception as e:
                self.show_error("错误", f"删除失败: {e}")

    def _on_open_skill_folder(self):
        """打开 Skill 所在目录"""
        if not self._current_skill:
            return

        folder = self._current_skill.path.parent
        if folder.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    def _clear_detail(self):
        """清空详情显示"""
        self.detail_name.setText(tr("skill.select_to_view"))
        self.detail_desc.setText("")
        self.detail_source.setText("")
        self.detail_license.setText("")
        self.detail_compat.setText("")
        self.detail_path.setText("")
        self.detail_content.setText("")
        self.edit_skill_btn.setEnabled(False)
        self.scan_skill_btn.setEnabled(False)
        self.delete_skill_btn.setEnabled(False)
        self.open_folder_btn.setEnabled(False)

    def _create_create_tab(self):
        """创建 Skill 创建/编辑标签页"""
        create_widget = QWidget()
        create_layout = QVBoxLayout(create_widget)
        create_layout.setContentsMargins(0, 16, 0, 0)

        create_layout.addWidget(
            SubtitleLabel(tr("skill.create_tab.title"), create_widget)
        )
        create_layout.addWidget(
            CaptionLabel(
                tr("skill.create_tab.subtitle"),
                create_widget,
            )
        )

        # 基本信息卡片
        basic_card = SimpleCardWidget(create_widget)
        basic_layout = QVBoxLayout(basic_card)
        basic_layout.setContentsMargins(16, 12, 16, 12)
        basic_layout.setSpacing(12)

        # Skill 名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(BodyLabel(tr("skill.create_tab.name_label"), basic_card))
        self.create_name_edit = LineEdit(basic_card)
        self.create_name_edit.setPlaceholderText(
            tr("skill.create_tab.name_placeholder")
        )
        self.create_name_edit.setToolTip(get_tooltip("skill_name"))
        name_layout.addWidget(self.create_name_edit)
        basic_layout.addLayout(name_layout)

        # 描述
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(BodyLabel(tr("skill.create_tab.desc_label"), basic_card))
        self.create_desc_edit = LineEdit(basic_card)
        self.create_desc_edit.setPlaceholderText(tr("dialog.placeholder_skill_desc"))
        desc_layout.addWidget(self.create_desc_edit)
        basic_layout.addLayout(desc_layout)

        # License
        license_layout = QHBoxLayout()
        license_layout.addWidget(BodyLabel(tr("skill.license") + ":", basic_card))
        self.create_license_edit = LineEdit(basic_card)
        self.create_license_edit.setPlaceholderText(tr("dialog.placeholder_license"))
        license_layout.addWidget(self.create_license_edit)
        basic_layout.addLayout(license_layout)

        # Compatibility
        compat_layout = QHBoxLayout()
        compat_layout.addWidget(
            BodyLabel(tr("skill.create_tab.compat_label"), basic_card)
        )
        self.create_compat_edit = LineEdit(basic_card)
        self.create_compat_edit.setPlaceholderText(tr("dialog.placeholder_tags"))
        compat_layout.addWidget(self.create_compat_edit)
        basic_layout.addLayout(compat_layout)

        # 保存位置
        loc_layout = QHBoxLayout()
        loc_layout.addWidget(
            BodyLabel(tr("skill.create_tab.location_label"), basic_card)
        )
        self.create_loc_combo = ComboBox(basic_card)
        self.create_loc_combo.addItems(
            [
                tr("skill.create_tab.location_opencode_global"),
                tr("skill.create_tab.location_opencode_project"),
                tr("skill.create_tab.location_claude_global"),
                tr("skill.create_tab.location_claude_project"),
            ]
        )
        loc_layout.addWidget(self.create_loc_combo)
        loc_layout.addStretch()
        basic_layout.addLayout(loc_layout)

        create_layout.addWidget(basic_card)

        # 内容编辑
        create_layout.addWidget(
            BodyLabel(tr("skill.create_tab.content_label"), create_widget)
        )
        self.create_content_edit = TextEdit(create_widget)
        self.create_content_edit.setPlaceholderText(
            tr("skill.create_tab.content_placeholder")
        )
        create_layout.addWidget(self.create_content_edit, 1)

        # 按钮
        btn_layout = QHBoxLayout()
        save_btn = PrimaryPushButton(
            FIF.SAVE, tr("skill.create_tab.save_button"), create_widget
        )
        save_btn.clicked.connect(self._on_save_skill)
        btn_layout.addWidget(save_btn)

        clear_btn = PushButton(
            FIF.DELETE, tr("skill.create_tab.clear_button"), create_widget
        )
        clear_btn.clicked.connect(self._on_clear_create_form)
        btn_layout.addWidget(clear_btn)

        btn_layout.addStretch()
        create_layout.addLayout(btn_layout)

        self.stacked_widget.addWidget(create_widget)

    def _on_save_skill(self):
        """保存 Skill"""
        name = self.create_name_edit.text().strip()
        desc = self.create_desc_edit.text().strip()
        license_info = self.create_license_edit.text().strip()
        compat = self.create_compat_edit.text().strip()
        content = self.create_content_edit.toPlainText().strip()

        # 验证
        valid, msg = SkillDiscovery.validate_skill_name(name)
        if not valid:
            self.show_error("名称错误", msg)
            return

        valid, msg = SkillDiscovery.validate_description(desc)
        if not valid:
            self.show_error("描述错误", msg)
            return

        # 确定保存路径
        loc_text = self.create_loc_combo.currentText()
        if "OpenCode 全局" in loc_text:
            base_path = Path.home() / ".config" / "opencode" / "skills"
        elif "OpenCode 项目" in loc_text:
            base_path = Path.cwd() / ".opencode" / "skills"
        elif "Claude 全局" in loc_text:
            base_path = Path.home() / ".claude" / "skills"
        else:
            base_path = Path.cwd() / ".claude" / "skills"

        skill_dir = base_path / name
        skill_file = skill_dir / "SKILL.md"

        # 构建 frontmatter
        frontmatter_lines = [
            f"name: {name}",
            f"description: {desc}",
        ]
        if license_info:
            frontmatter_lines.append(f"license: {license_info}")
        if compat:
            frontmatter_lines.append(f"compatibility: {compat}")

        frontmatter = "\n".join(frontmatter_lines)

        # 默认内容
        if not content:
            content = "## What I do\n\n- 描述功能\n\n## Instructions\n\n- 具体指令"

        skill_content = f"---\n{frontmatter}\n---\n\n{content}\n"

        try:
            skill_dir.mkdir(parents=True, exist_ok=True)
            with open(skill_file, "w", encoding="utf-8") as f:
                f.write(skill_content)

            self.show_success(
                self.tr("common.success"),
                self.tr("skill.skill_saved_detail", path=str(skill_file)),
            )
            self._refresh_skill_list()
            self._on_clear_create_form()
        except Exception as e:
            self.show_error("错误", f"保存失败: {e}")

    def _on_clear_create_form(self):
        """清空创建表单"""
        self.create_name_edit.clear()
        self.create_desc_edit.clear()
        self.create_license_edit.clear()
        self.create_compat_edit.clear()
        self.create_content_edit.clear()
        self._current_skill = None

    def _create_permission_tab(self):
        """创建权限配置标签页"""
        perm_widget = QWidget()
        perm_layout = QVBoxLayout(perm_widget)
        perm_layout.setContentsMargins(0, 16, 0, 0)

        # 使用 QSplitter 实现左右分栏
        splitter = QSplitter(Qt.Orientation.Horizontal, perm_widget)

        # ===== 左侧：全局权限配置 =====
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 8, 0)

        left_layout.addWidget(
            SubtitleLabel(tr("skill.permission_tab.global_title"), left_widget)
        )
        left_layout.addWidget(
            CaptionLabel(tr("skill.permission_tab.global_subtitle"), left_widget)
        )

        # 工具栏
        toolbar = QHBoxLayout()
        add_perm_btn = PrimaryPushButton(
            FIF.ADD, tr("skill.permission_tab.add_button"), left_widget
        )
        add_perm_btn.clicked.connect(self._on_add_permission)
        toolbar.addWidget(add_perm_btn)

        del_perm_btn = PushButton(
            FIF.DELETE, tr("skill.permission_tab.delete_button"), left_widget
        )
        del_perm_btn.clicked.connect(self._on_delete_permission)
        toolbar.addWidget(del_perm_btn)

        toolbar.addStretch()
        left_layout.addLayout(toolbar)

        # 权限表格
        self.perm_table = TableWidget(left_widget)
        self.perm_table.setColumnCount(2)
        self.perm_table.setHorizontalHeaderLabels(
            [tr("skill.pattern"), tr("skill.permission")]
        )
        self.perm_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.perm_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.perm_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.perm_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.perm_table.itemSelectionChanged.connect(self._on_perm_selected)
        left_layout.addWidget(self.perm_table, 1)

        # 编辑区域
        edit_card = SimpleCardWidget(left_widget)
        edit_layout = QVBoxLayout(edit_card)
        edit_layout.setContentsMargins(12, 8, 12, 8)

        pattern_layout = QHBoxLayout()
        pattern_layout.addWidget(
            BodyLabel(tr("skill.permission_tab.pattern_label"), edit_card)
        )
        self.perm_pattern_edit = LineEdit(edit_card)
        self.perm_pattern_edit.setPlaceholderText(
            tr("dialog.placeholder_allow_pattern")
        )
        self.perm_pattern_edit.setToolTip(get_tooltip("skill_pattern"))
        pattern_layout.addWidget(self.perm_pattern_edit)
        edit_layout.addLayout(pattern_layout)

        perm_sel_layout = QHBoxLayout()
        perm_sel_layout.addWidget(
            BodyLabel(tr("skill.permission_tab.permission_label"), edit_card)
        )
        self.perm_level_combo = ComboBox(edit_card)
        self.perm_level_combo.addItems(["allow", "ask", "deny"])
        self.perm_level_combo.setToolTip(get_tooltip("skill_permission"))
        perm_sel_layout.addWidget(self.perm_level_combo)
        perm_sel_layout.addStretch()
        edit_layout.addLayout(perm_sel_layout)

        save_perm_btn = PrimaryPushButton(
            tr("skill.permission_tab.save_permission"), edit_card
        )
        save_perm_btn.clicked.connect(self._on_save_permission)
        edit_layout.addWidget(save_perm_btn)

        left_layout.addWidget(edit_card)

        # ===== 右侧：Agent 级别配置 =====
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(8, 0, 0, 0)

        right_layout.addWidget(
            SubtitleLabel(tr("skill.permission_tab.agent_level_title"), right_widget)
        )
        right_layout.addWidget(
            CaptionLabel(tr("skill.permission_tab.agent_level_subtitle"), right_widget)
        )

        # Agent 选择
        agent_layout = QHBoxLayout()
        agent_layout.addWidget(
            BodyLabel(tr("skill.permission_tab.select_agent"), right_widget)
        )
        self.agent_combo = ComboBox(right_widget)
        self.agent_combo.addItems(["task", "plan", "code", "summarize"])
        self.agent_combo.currentTextChanged.connect(self._on_agent_changed)
        agent_layout.addWidget(self.agent_combo)
        agent_layout.addStretch()
        right_layout.addLayout(agent_layout)

        # 禁用 Skill 工具
        self.disable_skill_check = CheckBox(
            tr("skill.permission_tab.disable_skill_tool") + " (tools.skill: false)",
            right_widget,
        )
        self.disable_skill_check.stateChanged.connect(self._on_disable_skill_changed)
        right_layout.addWidget(self.disable_skill_check)

        # Agent 权限覆盖
        right_layout.addWidget(
            BodyLabel(
                tr("skill.permission_tab.agent_skill_permission") + ":", right_widget
            )
        )
        self.agent_perm_table = TableWidget(right_widget)
        self.agent_perm_table.setColumnCount(2)
        self.agent_perm_table.setHorizontalHeaderLabels(
            [tr("skill.pattern"), tr("skill.permission")]
        )
        self.agent_perm_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        self.agent_perm_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.agent_perm_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        right_layout.addWidget(self.agent_perm_table, 1)

        # Agent 权限编辑
        agent_edit_card = SimpleCardWidget(right_widget)
        agent_edit_layout = QVBoxLayout(agent_edit_card)
        agent_edit_layout.setContentsMargins(12, 8, 12, 8)

        agent_pattern_layout = QHBoxLayout()
        agent_pattern_layout.addWidget(BodyLabel(tr("rules.pattern"), agent_edit_card))
        self.agent_perm_pattern_edit = LineEdit(agent_edit_card)
        self.agent_perm_pattern_edit.setPlaceholderText(
            tr("dialog.placeholder_deny_pattern")
        )
        agent_pattern_layout.addWidget(self.agent_perm_pattern_edit)
        agent_edit_layout.addLayout(agent_pattern_layout)

        agent_perm_layout = QHBoxLayout()
        agent_perm_layout.addWidget(BodyLabel(tr("rules.permission"), agent_edit_card))
        self.agent_perm_level_combo = ComboBox(agent_edit_card)
        self.agent_perm_level_combo.addItems(["allow", "ask", "deny"])
        agent_perm_layout.addWidget(self.agent_perm_level_combo)
        agent_perm_layout.addStretch()
        agent_edit_layout.addLayout(agent_perm_layout)

        agent_btn_layout = QHBoxLayout()
        add_agent_perm_btn = PushButton(FIF.ADD, tr("common.add"), agent_edit_card)
        add_agent_perm_btn.clicked.connect(self._on_add_agent_permission)
        agent_btn_layout.addWidget(add_agent_perm_btn)

        del_agent_perm_btn = PushButton(
            FIF.DELETE, tr("common.delete"), agent_edit_card
        )
        del_agent_perm_btn.clicked.connect(self._on_delete_agent_permission)
        agent_btn_layout.addWidget(del_agent_perm_btn)
        agent_btn_layout.addStretch()
        agent_edit_layout.addLayout(agent_btn_layout)

        right_layout.addWidget(agent_edit_card)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([400, 400])

        perm_layout.addWidget(splitter, 1)
        self.stacked_widget.addWidget(perm_widget)

    def _on_add_permission(self):
        """添加新权限"""
        self.perm_pattern_edit.clear()
        self.perm_level_combo.setCurrentText("ask")

    def _on_delete_permission(self):
        """删除选中的权限"""
        row = self.perm_table.currentRow()
        if row < 0:
            self.show_warning(
                tr("common.info"),
                tr("common.please_select_first", item=tr("permission.title")),
            )
            return

        pattern = self.perm_table.item(row, 0).text()
        w = FluentMessageBox(
            tr("common.confirm_delete_title"),
            tr("dialog.confirm_delete_permission", pattern=pattern),
            self,
        )
        if w.exec_():
            config = self.main_window.opencode_config or {}
            skill_perms = config.get("permission", {}).get("skill", {})
            if isinstance(skill_perms, dict) and pattern in skill_perms:
                del skill_perms[pattern]
                self.main_window.save_opencode_config()
                self._load_permission_data()
                self.show_success(
                    self.tr("common.success"),
                    self.tr("rules.permission_deleted", pattern=pattern),
                )

    def _on_perm_selected(self):
        """选中权限时填充编辑区"""
        row = self.perm_table.currentRow()
        if row >= 0:
            pattern_item = self.perm_table.item(row, 0)
            perm_item = self.perm_table.item(row, 1)
            if pattern_item:
                self.perm_pattern_edit.setText(pattern_item.text())
            if perm_item:
                self.perm_level_combo.setCurrentText(perm_item.text())

    def _on_save_permission(self):
        """保存权限"""
        pattern = self.perm_pattern_edit.text().strip()
        if not pattern:
            self.show_warning(
                self.tr("common.info"), self.tr("common.please_enter_pattern")
            )
            return

        config = self.main_window.opencode_config
        if config is None:
            config = {}
            self.main_window.opencode_config = config

        if "permission" not in config:
            config["permission"] = {}
        if "skill" not in config["permission"] or not isinstance(
            config["permission"]["skill"], dict
        ):
            config["permission"]["skill"] = {}

        config["permission"]["skill"][pattern] = self.perm_level_combo.currentText()
        self.main_window.save_opencode_config()
        self._load_permission_data()
        self.show_success(
            self.tr("common.success"),
            self.tr("rules.permission_saved", pattern=pattern),
        )

    def _on_agent_changed(self, agent_name: str):
        """切换 Agent 时加载其配置"""
        self._load_agent_skill_config(agent_name)

    def _load_agent_skill_config(self, agent_name: str):
        """加载指定 Agent 的 Skill 配置"""
        config = self.main_window.opencode_config or {}
        agent_config = config.get("agent", {}).get(agent_name, {})

        # 加载 tools.skill 状态
        tools = agent_config.get("tools", {})
        skill_enabled = tools.get("skill", True)
        self.disable_skill_check.setChecked(skill_enabled is False)

        # 加载 Agent 权限覆盖
        self.agent_perm_table.setRowCount(0)
        agent_perms = agent_config.get("permission", {}).get("skill", {})
        if isinstance(agent_perms, dict):
            for pattern, perm in agent_perms.items():
                row = self.agent_perm_table.rowCount()
                self.agent_perm_table.insertRow(row)
                self.agent_perm_table.setItem(row, 0, QTableWidgetItem(pattern))
                self.agent_perm_table.setItem(row, 1, QTableWidgetItem(perm))

    def _on_disable_skill_changed(self, state):
        """禁用 Skill 工具状态变化"""
        agent_name = self.agent_combo.currentText()
        config = self.main_window.opencode_config
        if config is None:
            config = {}
            self.main_window.opencode_config = config

        if "agent" not in config:
            config["agent"] = {}
        if agent_name not in config["agent"]:
            config["agent"][agent_name] = {}
        if "tools" not in config["agent"][agent_name]:
            config["agent"][agent_name]["tools"] = {}

        if state == Qt.Checked:
            config["agent"][agent_name]["tools"]["skill"] = False
        else:
            # 移除配置，使用默认值
            if "skill" in config["agent"][agent_name]["tools"]:
                del config["agent"][agent_name]["tools"]["skill"]

        self.main_window.save_opencode_config()

    def _on_add_agent_permission(self):
        """添加 Agent 权限覆盖"""
        pattern = self.agent_perm_pattern_edit.text().strip()
        if not pattern:
            self.show_warning(
                self.tr("common.info"), self.tr("common.please_enter_pattern")
            )
            return

        agent_name = self.agent_combo.currentText()
        config = self.main_window.opencode_config
        if config is None:
            config = {}
            self.main_window.opencode_config = config

        if "agent" not in config:
            config["agent"] = {}
        if agent_name not in config["agent"]:
            config["agent"][agent_name] = {}
        if "permission" not in config["agent"][agent_name]:
            config["agent"][agent_name]["permission"] = {}
        if "skill" not in config["agent"][agent_name]["permission"]:
            config["agent"][agent_name]["permission"]["skill"] = {}

        config["agent"][agent_name]["permission"]["skill"][pattern] = (
            self.agent_perm_level_combo.currentText()
        )
        self.main_window.save_opencode_config()
        self._load_agent_skill_config(agent_name)
        self.show_success(
            self.tr("common.success"),
            self.tr("rules.agent_permission_added", agent=agent_name, pattern=pattern),
        )

    def _on_delete_agent_permission(self):
        """删除 Agent 权限覆盖"""
        row = self.agent_perm_table.currentRow()
        if row < 0:
            self.show_warning(
                tr("common.info"),
                tr("common.please_select_first", item=tr("permission.title")),
            )
            return

        pattern = self.agent_perm_table.item(row, 0).text()
        agent_name = self.agent_combo.currentText()

        config = self.main_window.opencode_config or {}
        agent_perms = (
            config.get("agent", {})
            .get(agent_name, {})
            .get("permission", {})
            .get("skill", {})
        )

        if isinstance(agent_perms, dict) and pattern in agent_perms:
            del agent_perms[pattern]
            self.main_window.save_opencode_config()
            self._load_agent_skill_config(agent_name)
            self.show_success(
                self.tr("common.success"),
                self.tr("rules.permission_deleted", pattern=pattern),
            )

    def _on_open_market(self):
        """打开 Skill 市场"""
        dialog = SkillMarketDialog(self)
        if dialog.exec_():
            skill = dialog.get_selected_skill()
            if skill:
                # 弹出安装位置选择对话框
                install_dialog = SkillInstallDialog(self)
                install_dialog.source_edit.setText(skill["repo"])
                install_dialog.source_edit.setReadOnly(True)

                if install_dialog.exec_():
                    target_dir = install_dialog.get_target_dir()

                    try:
                        # 确保目标目录存在
                        target_dir.mkdir(parents=True, exist_ok=True)

                        # 从市场安装
                        owner, repo_name = skill["repo"].split("/")
                        # 获取子目录路径（如果有）
                        subdir = skill.get("path", None)

                        # 自动检测分支 (main 或 master)
                        branch = SkillInstaller.detect_default_branch(owner, repo_name)

                        success, message = SkillInstaller.install_from_github(
                            owner,
                            repo_name,
                            branch,
                            target_dir,
                            subdir=subdir,
                            progress_callback=install_dialog.update_progress,
                        )

                        if success:
                            self.show_success("成功", message)
                            self._refresh_skill_list()
                        else:
                            self.show_error("失败", message)

                    except Exception as e:
                        self.show_error("错误", f"安装失败: {str(e)}")

    def _on_scan_skill(self):
        """扫描选中的 Skill"""
        if not self._current_skill:
            return

        try:
            # 扫描 Skill
            scan_result = SkillSecurityScanner.scan_skill(self._current_skill.path)

            # 显示扫描结果
            dialog = SecurityScanDialog(scan_result, self._current_skill.name, self)
            dialog.exec_()

        except Exception as e:
            self.show_error("错误", f"扫描失败: {str(e)}")

    def _on_install_skill(self):
        """安装 Skill"""
        dialog = SkillInstallDialog(self)
        if dialog.exec_():
            source = dialog.get_source()
            target_dir = dialog.get_target_dir()

            if not source:
                self.show_warning(
                    self.tr("common.info"), self.tr("common.please_enter_source")
                )
                return

            try:
                # 确保目标目录存在
                target_dir.mkdir(parents=True, exist_ok=True)

                # 解析来源
                source_type, details = SkillInstaller.parse_source(source)

                # 安装
                if source_type == "github":
                    success, message = SkillInstaller.install_from_github(
                        details["owner"],
                        details["repo"],
                        details["branch"],
                        target_dir,
                        progress_callback=dialog.update_progress,
                    )
                else:
                    success, message = SkillInstaller.install_from_local(
                        details["path"],
                        target_dir,
                        progress_callback=dialog.update_progress,
                    )

                if success:
                    self.show_success("成功", message)
                    self._refresh_skill_list()
                else:
                    self.show_error("失败", message)

            except ValueError as e:
                self.show_error("错误", str(e))
            except Exception as e:
                self.show_error("错误", f"安装失败: {str(e)}")

    def _on_check_updates(self):
        """检查更新"""
        # 获取所有 Skills
        skills = SkillDiscovery.discover_all()

        if not skills:
            self.show_info("提示", "未发现任何 Skills")
            return

        # 显示进度对话框
        progress = ProgressDialog("正在检查更新...", self)
        progress.show()
        QApplication.processEvents()

        try:
            # 检查更新
            updates = SkillUpdater.check_updates(skills)

            progress.close()

            # 显示更新对话框
            update_dialog = SkillUpdateDialog(updates, self)
            if update_dialog.exec_():
                selected = update_dialog.get_selected_updates()

                if not selected:
                    self.show_info("提示", "未选择任何 Skills")
                    return

                # 更新选中的 Skills
                self._update_selected_skills(selected)

        except Exception as e:
            progress.close()
            self.show_error("错误", f"检查更新失败: {str(e)}")

    def _update_selected_skills(self, selected_updates: List[Dict[str, Any]]):
        """更新选中的 Skills"""
        total = len(selected_updates)
        success_count = 0
        failed_skills = []

        # 创建进度对话框
        progress = ProgressDialog(f"正在更新 Skills (0/{total})...", self)
        progress.show()
        QApplication.processEvents()

        for i, update in enumerate(selected_updates):
            skill = update["skill"]
            meta = update["meta"]

            progress.setLabelText(f"正在更新 {skill.name} ({i + 1}/{total})...")
            QApplication.processEvents()

            success, message = SkillUpdater.update_skill(skill, meta)

            if success:
                success_count += 1
            else:
                failed_skills.append(f"{skill.name}: {message}")

        progress.close()

        # 显示结果
        if success_count == total:
            self.show_success("成功", f"成功更新 {success_count} 个 Skills")
        elif success_count > 0:
            failed_msg = "\n".join(failed_skills)
            self.show_warning(
                "部分成功",
                f"成功更新 {success_count} 个，失败 {len(failed_skills)} 个\n\n失败详情:\n{failed_msg}",
            )
        else:
            failed_msg = "\n".join(failed_skills)
            self.show_error("失败", f"所有更新均失败\n\n详情:\n{failed_msg}")

        # 刷新列表
        self._refresh_skill_list()


# ==================== 进度对话框 ====================
class ProgressDialog(MessageBoxBase):
    """简单的进度对话框 - 使用 Fluent 风格"""

    def __init__(self, message: str, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel("请稍候", self)

        self.label = BodyLabel(message, self.widget)
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.label)

        # 隐藏按钮
        self.yesButton.hide()
        self.cancelButton.hide()

        self.widget.setMinimumWidth(350)
        self.widget.setMinimumHeight(100)

    def setLabelText(self, text: str):
        self.label.setText(text)
        QApplication.processEvents()


# ==================== Rules 页面 ====================
class RulesPage(BasePage):
    """Rules/Instructions 管理和 AGENTS.md 编辑页面"""

    def __init__(self, main_window, parent=None):
        super().__init__(tr("rules.title"), parent)
        self.main_window = main_window
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        # Instructions 配置卡片
        inst_card = self.add_card(self.tr("rules.instructions_config"))
        inst_layout = inst_card.layout()
        inst_layout.setSpacing(12)

        inst_layout.addWidget(
            BodyLabel(self.tr("rules.instructions_description"), inst_card)
        )

        # Instructions 列表
        self.inst_list = ListWidget(inst_card)
        self.inst_list.setMaximumHeight(120)
        inst_layout.addWidget(self.inst_list)

        # 添加输入
        add_layout = QHBoxLayout()
        add_layout.setSpacing(8)
        self.inst_path_edit = LineEdit(inst_card)
        self.inst_path_edit.setPlaceholderText(self.tr("rules.file_path_placeholder"))
        self.inst_path_edit.setFixedHeight(36)
        add_layout.addWidget(self.inst_path_edit)

        add_btn = PushButton(FIF.ADD, tr("common.add"), inst_card)
        add_btn.setFixedHeight(36)
        add_btn.clicked.connect(self._on_add_instruction)
        add_layout.addWidget(add_btn)

        del_btn = PushButton(FIF.DELETE, tr("common.delete"), inst_card)
        del_btn.setFixedHeight(36)
        del_btn.clicked.connect(self._on_delete_instruction)
        add_layout.addWidget(del_btn)

        inst_layout.addLayout(add_layout)

        # 快捷路径
        quick_layout = QHBoxLayout()
        quick_layout.setSpacing(8)
        quick_layout.addWidget(BodyLabel(tr("rules.quick"), inst_card))
        for path in ["CONTRIBUTING.md", "docs/*.md", ".cursor/rules/*.md"]:
            btn = PushButton(path, inst_card)
            btn.setFixedHeight(32)
            btn.clicked.connect(lambda checked, p=path: self.inst_path_edit.setText(p))
            quick_layout.addWidget(btn)
        quick_layout.addStretch()
        inst_layout.addLayout(quick_layout)

        # 保存按钮
        save_inst_btn = PrimaryPushButton(tr("rules.save_instructions"), inst_card)
        save_inst_btn.setFixedHeight(36)
        save_inst_btn.clicked.connect(self._on_save_instructions)
        inst_layout.addWidget(save_inst_btn)

        # AGENTS.md 编辑卡片
        agents_card = self.add_card(self.tr("rules.agents_md_edit"))
        agents_layout = agents_card.layout()
        agents_layout.setSpacing(12)

        # 位置选择
        loc_layout = QHBoxLayout()
        loc_layout.setSpacing(12)
        loc_layout.addWidget(BodyLabel(tr("rules.edit_location"), agents_card))
        self.global_radio = RadioButton(tr("rules.global"), agents_card)
        self.global_radio.setChecked(True)
        self.global_radio.clicked.connect(self._load_agents_md)
        loc_layout.addWidget(self.global_radio)
        self.project_radio = RadioButton(tr("rules.project"), agents_card)
        self.project_radio.clicked.connect(self._load_agents_md)
        loc_layout.addWidget(self.project_radio)
        loc_layout.addStretch()
        agents_layout.addLayout(loc_layout)

        # 路径显示
        self.path_label = CaptionLabel("", agents_card)
        agents_layout.addWidget(self.path_label)

        # 编辑器
        self.agents_edit = TextEdit(agents_card)
        self.agents_edit.setMinimumHeight(200)
        agents_layout.addWidget(self.agents_edit)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        save_btn = PrimaryPushButton(tr("rules.save_agents_md"), agents_card)
        save_btn.setFixedHeight(36)
        save_btn.clicked.connect(self._on_save_agents_md)
        btn_layout.addWidget(save_btn)

        reload_btn = PushButton(self.tr("rules.reload"), agents_card)
        reload_btn.setFixedHeight(36)
        reload_btn.clicked.connect(self._load_agents_md)
        btn_layout.addWidget(reload_btn)

        template_btn = PushButton(self.tr("rules.use_template"), agents_card)
        template_btn.setFixedHeight(36)
        template_btn.clicked.connect(self._use_template)
        btn_layout.addWidget(template_btn)

        btn_layout.addStretch()
        agents_layout.addLayout(btn_layout)

        self._layout.addStretch()

        # 初始加载
        self._load_agents_md()

    def _load_data(self):
        """加载 Instructions 列表"""
        self.inst_list.clear()
        config = self.main_window.opencode_config or {}
        instructions = config.get("instructions", [])
        for path in instructions:
            self.inst_list.addItem(path)

    def _on_add_instruction(self):
        path = self.inst_path_edit.text().strip()
        if not path:
            self.show_warning(
                self.tr("common.info"), self.tr("common.please_enter_file_path")
            )
            return

        config = self.main_window.opencode_config
        if config is None:
            config = {}
            self.main_window.opencode_config = config

        instructions = config.setdefault("instructions", [])
        if path not in instructions:
            instructions.append(path)
            self._load_data()
            self.inst_path_edit.setText("")

    def _on_delete_instruction(self):
        current = self.inst_list.currentItem()
        if not current:
            self.show_warning(
                tr("common.info"),
                tr("common.please_select_first", item=tr("skill.path")),
            )
            return

        path = current.text()
        config = self.main_window.opencode_config or {}
        instructions = config.get("instructions", [])
        if path in instructions:
            instructions.remove(path)
            self._load_data()

    def _on_save_instructions(self):
        self.main_window.save_opencode_config()
        self.show_success(
            self.tr("common.success"), self.tr("rules.instructions_saved")
        )

    def _get_agents_path(self) -> Path:
        if self.global_radio.isChecked():
            return Path.home() / ".config" / "opencode" / tr("rules.agents_md")
        else:
            return Path.cwd() / tr("rules.agents_md")

    def _load_agents_md(self):
        path = self._get_agents_path()
        self.path_label.setText(f"{tr('rules.path_label')}: {path}")

        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.agents_edit.setPlainText(content)
            except Exception as e:
                self.agents_edit.setPlainText(f"# {tr('rules.read_failed')}: {e}")
        else:
            self.agents_edit.setPlainText(self.tr("rules.agents_md_not_exist"))

    def _on_save_agents_md(self):
        path = self._get_agents_path()
        content = self.agents_edit.toPlainText()

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            self.show_success(
                self.tr("common.success"),
                self.tr("rules.agents_md_saved", path=str(path)),
            )
        except Exception as e:
            self.show_error("错误", f"保存失败: {e}")

    def _use_template(self):
        template = """# Project Rules

This is a project-specific rules file for OpenCode.

## Project Structure
- `src/` - Source code
- `tests/` - Test files
- `docs/` - Documentation

## Code Standards
- Use TypeScript with strict mode enabled
- Follow existing code patterns
- Write tests for new features

## Conventions
- Use meaningful variable names
- Add comments for complex logic
- Keep functions small and focused
"""
        self.agents_edit.setPlainText(template)


# ==================== Compaction 页面 ====================
class CompactionPage(BasePage):
    """上下文压缩配置页面"""

    def __init__(self, main_window, parent=None):
        super().__init__(tr("compaction.title"), parent)
        self.main_window = main_window
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        # 说明卡片
        desc_card = self.add_card(tr("compaction.card_title"))
        desc_layout = desc_card.layout()

        desc_layout.addWidget(
            BodyLabel(
                tr("compaction.description"),
                desc_card,
            )
        )

        # auto 选项
        self.auto_check = CheckBox(tr("compaction.auto_compress"), desc_card)
        self.auto_check.setChecked(True)
        desc_layout.addWidget(self.auto_check)

        # prune 选项
        self.prune_check = CheckBox(tr("compaction.prune_old_output"), desc_card)
        self.prune_check.setChecked(True)
        desc_layout.addWidget(self.prune_check)

        # 保存按钮
        save_btn = PrimaryPushButton(tr("compaction.save_settings"), desc_card)
        save_btn.clicked.connect(self._on_save)
        desc_layout.addWidget(save_btn)

        # 配置预览卡片
        preview_card = self.add_card(tr("compaction.preview"))
        preview_layout = preview_card.layout()

        self.preview_edit = TextEdit(preview_card)
        self.preview_edit.setReadOnly(True)
        self.preview_edit.setMaximumHeight(150)
        preview_layout.addWidget(self.preview_edit)

        self._layout.addStretch()

        # 连接信号更新预览
        self.auto_check.stateChanged.connect(self._update_preview)
        self.prune_check.stateChanged.connect(self._update_preview)

    def _load_data(self):
        """加载 Compaction 配置"""
        config = self.main_window.opencode_config or {}
        compaction = config.get("compaction", {})

        self.auto_check.setChecked(compaction.get("auto", True))
        self.prune_check.setChecked(compaction.get("prune", True))

        self._update_preview()

    def _update_preview(self):
        """更新配置预览"""
        import json

        config = {
            "compaction": {
                "auto": self.auto_check.isChecked(),
                "prune": self.prune_check.isChecked(),
            }
        }
        self.preview_edit.setPlainText(json.dumps(config, indent=2, ensure_ascii=False))

    def _on_save(self):
        config = self.main_window.opencode_config
        if config is None:
            config = {}
            self.main_window.opencode_config = config

        config["compaction"] = {
            "auto": self.auto_check.isChecked(),
            "prune": self.prune_check.isChecked(),
        }

        self.main_window.save_opencode_config()
        self._update_preview()
        self.show_success(tr("common.success"), tr("compaction.settings_saved"))


# ==================== 监控页面 ====================
class MonitorPage(BasePage):
    """站点/模型可用度与延迟监控页面"""

    result_ready = pyqtSignal(object)

    def __init__(self, main_window, parent=None):
        super().__init__(tr("monitor.title"), parent)
        self.title_label.hide()
        self.main_window = main_window
        # 监控数据存储: target_id -> deque[MonitorResult]
        self._history: Dict[str, Deque[MonitorResult]] = {}
        # 监控目标列表
        self._targets: List[MonitorTarget] = []
        # 轮询定时器
        self._poll_timer: Optional[QTimer] = None
        # 轮询状态
        self._is_polling = False
        # 行索引映射
        self._row_index: Dict[str, int] = {}
        # 线程池
        self._executor = ThreadPoolExecutor(max_workers=6)
        # 轮询超时控制
        self._pending_targets: Dict[str, float] = {}
        self._timeout_timer: Optional[QTimer] = None
        self._request_timeout_sec = 15
        # 是否启用对话延迟测试 - 默认关闭，需要手动启动
        self._chat_test_enabled = False
        self._setup_ui()
        self._load_targets()
        # 自动启动轮询（Ping 检测始终运行，对话延迟测试由按钮控制）
        self._start_polling()
        # 连接配置变更信号
        self.main_window.config_changed.connect(self._on_config_changed)
        self.result_ready.connect(self._on_single_result)

    def _on_config_changed(self):
        """配置变更时重新加载目标"""
        self._load_targets()
        self._refresh_ui()

    def _toggle_chat_test(self):
        """切换对话延迟测试状态 - 启动/停止按钮（只控制对话延迟，不影响其他监控）"""
        self._chat_test_enabled = not self._chat_test_enabled
        if self._chat_test_enabled:
            # 启动对话延迟测试
            self.monitor_toggle_btn.setText(tr("monitor.stop_monitoring"))
            self.monitor_toggle_btn.setIcon(FIF.PAUSE)
            self.monitor_toggle_btn.setToolTip(tr("monitor.stop_tooltip"))
        else:
            # 停止对话延迟测试
            self.monitor_toggle_btn.setText(tr("monitor.start_monitoring"))
            self.monitor_toggle_btn.setIcon(FIF.PLAY)
            self.monitor_toggle_btn.setToolTip(tr("monitor.start_tooltip"))
        # 立即执行一次检测以反映状态变化
        self._do_poll()

    def _stop_polling(self):
        """停止轮询"""
        if self._poll_timer:
            self._poll_timer.stop()
        if self._timeout_timer:
            self._timeout_timer.stop()
        self._is_polling = False
        self.poll_status_label.setText("")

    def _setup_ui(self):
        """构建监控页面 UI"""
        self._build_compact_summary()
        self._build_table()

    def _build_compact_summary(self):
        """构建统计区 - 简洁卡片式设计"""
        wrapper = QWidget(self)
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 8, 0, 8)
        wrapper_layout.setSpacing(8)

        # 第一行：统计卡片
        stats_row = QHBoxLayout()
        stats_row.setSpacing(8)

        # 保存卡片引用以便主题切换时更新
        self._stat_cards: List[QFrame] = []
        self._stat_labels: List[CaptionLabel] = []

        # 统计卡片样式
        def create_stat_card(icon, label_text, value_text, color="#58a6ff"):
            card = QFrame()
            card.setFrameShape(QFrame.StyledPanel)
            card.setFixedSize(95, 50)
            self._stat_cards.append(card)

            layout = QVBoxLayout(card)
            layout.setContentsMargins(8, 4, 8, 4)
            layout.setSpacing(2)

            # 数值行（带图标）
            value_row = QHBoxLayout()
            value_row.setSpacing(4)

            icon_label = QLabel()
            icon_label.setPixmap(icon.icon().pixmap(12, 12))
            value_row.addWidget(icon_label)

            value = StrongBodyLabel(value_text)
            value.setStyleSheet(f"color: {color}; font-size: 14px;")
            value_row.addWidget(value)
            value_row.addStretch()
            layout.addLayout(value_row)

            # 标签
            label = CaptionLabel(label_text)
            label.setStyleSheet("font-size: 10px;")
            self._stat_labels.append(label)
            layout.addWidget(label)

            return card, value

        # 可用率
        card, self.availability_value = create_stat_card(
            FIF.ACCEPT, tr("monitor.availability_rate"), "—", "#3fb950"
        )
        stats_row.addWidget(card)

        # 异常数
        card, self.error_count_value = create_stat_card(
            FIF.CANCEL, tr("monitor.error_count"), "0", "#f85149"
        )
        stats_row.addWidget(card)

        # 对话延迟
        card, self.chat_latency_value = create_stat_card(
            FIF.CHAT, tr("monitor.chat_latency"), "—", "#58a6ff"
        )
        stats_row.addWidget(card)

        # Ping 延迟
        card, self.ping_latency_value = create_stat_card(
            FIF.WIFI, tr("monitor.ping"), "—", "#58a6ff"
        )
        stats_row.addWidget(card)

        # 目标数
        card, self.target_count_value = create_stat_card(
            FIF.TAG, tr("monitor.target_count"), "0", "#e6edf3"
        )
        stats_row.addWidget(card)

        # 最近检测
        card, self.last_checked_value = create_stat_card(
            FIF.HISTORY, tr("monitor.last_checked_short"), "—", "#7d8590"
        )
        card.setFixedSize(110, 50)
        stats_row.addWidget(card)

        # 应用初始主题样式
        self._apply_stat_card_theme()

        stats_row.addStretch()

        # 按钮和状态放在统计行右侧
        self.manual_check_btn = PrimaryPushButton(
            FIF.SYNC, tr("monitor.check"), wrapper
        )
        self.manual_check_btn.setFixedSize(80, 32)
        self.manual_check_btn.clicked.connect(self._do_poll)
        stats_row.addWidget(self.manual_check_btn)

        # 启动/停止按钮 - 默认显示"启动"
        self.monitor_toggle_btn = PushButton(FIF.PLAY, tr("monitor.start"), wrapper)
        self.monitor_toggle_btn.setFixedSize(80, 32)
        self.monitor_toggle_btn.setToolTip(tr("monitor.toggle_tooltip"))
        self.monitor_toggle_btn.clicked.connect(self._toggle_chat_test)
        stats_row.addWidget(self.monitor_toggle_btn)

        self.poll_status_label = CaptionLabel("", wrapper)
        self.poll_status_label.setStyleSheet("color: #f0883e; font-weight: bold;")
        self.poll_status_label.setMinimumWidth(50)
        stats_row.addWidget(self.poll_status_label)

        wrapper_layout.addLayout(stats_row)
        self._layout.addWidget(wrapper)

    def _build_table(self):
        """构建明细表格"""
        # 直接添加到页面，不使用卡片，保持与其他页面一致的样式
        self.detail_table = TableWidget(self)
        self.detail_table.setContentsMargins(0, 0, 0, 0)
        self.detail_table.setViewportMargins(0, 0, 0, 0)
        self.detail_table.setColumnCount(7)
        self.detail_table.setHorizontalHeaderLabels(
            [
                tr("monitor.model_provider"),
                tr("monitor.status"),
                tr("monitor.availability_rate"),
                tr("monitor.chat_latency"),
                tr("monitor.ping_latency"),
                tr("monitor.last_check"),
                tr("monitor.history"),
            ]
        )
        header = self.detail_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.resizeSection(1, 90)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.resizeSection(2, 96)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.resizeSection(3, 120)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.resizeSection(4, 120)
        header.setSectionResizeMode(5, QHeaderView.Fixed)
        header.resizeSection(5, 100)
        header.setSectionResizeMode(6, QHeaderView.Fixed)
        header.resizeSection(6, 200)
        self.detail_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.detail_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.detail_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.detail_table.verticalHeader().setDefaultSectionSize(32)
        self._layout.addWidget(self.detail_table, 1)

    def _load_targets(self):
        """从配置加载监控目标"""
        self._targets.clear()
        config = self.main_window.opencode_config or {}
        providers = config.get("provider", {})

        for provider_key, provider_data in providers.items():
            if not isinstance(provider_data, dict):
                continue
            provider_name = provider_data.get("name", provider_key)
            options = provider_data.get("options", {})
            base_url = _safe_base_url(
                options.get("baseURL", "") or provider_data.get("baseURL", "")
            )
            api_key_raw = options.get("apiKey", "") or provider_data.get("apiKey", "")
            api_key = _resolve_env_value(api_key_raw) if api_key_raw else ""

            models = provider_data.get("models", {})
            for model_id, model_data in models.items():
                if not isinstance(model_data, dict):
                    continue
                model_name = model_data.get("name", model_id)
                target = MonitorTarget(
                    provider_key=provider_key,
                    provider_name=provider_name,
                    base_url=base_url,
                    api_key=api_key,
                    model_id=model_id,
                    model_name=model_name,
                )
                self._targets.append(target)
                # 初始化历史记录
                if target.target_id not in self._history:
                    self._history[target.target_id] = deque(
                        maxlen=MONITOR_HISTORY_LIMIT
                    )

        self._refresh_ui()

    def _start_polling(self):
        """启动轮询定时器"""
        if self._poll_timer is None:
            self._poll_timer = QTimer(self)
            self._poll_timer.timeout.connect(self._do_poll)
        self._poll_timer.start(MONITOR_POLL_INTERVAL_MS)
        # 立即执行一次
        QTimer.singleShot(200, self._do_poll)

    def _do_poll(self):
        """执行一次轮询（并发请求）"""
        if self._is_polling:
            return
        if not self._targets:
            self.poll_status_label.setText(tr("monitor.no_targets"))
            return
        self._is_polling = True
        self.poll_status_label.setText(tr("monitor.checking"))
        self._mark_all_pending()

        self._pending_targets = {t.target_id: time.time() for t in self._targets}
        self._start_timeout_timer()

        remaining = len(self._targets)
        if remaining == 0:
            self._is_polling = False
            self.poll_status_label.setText("")
            return

        def _done_callback(target_id: str, future):
            nonlocal remaining
            try:
                result = future.result()
            except Exception as e:
                result = MonitorResult(
                    target_id=target_id,
                    status="error",
                    latency_ms=None,
                    ping_ms=None,
                    checked_at=datetime.now(),
                    message=str(e)[:50],
                )
            if target_id in self._pending_targets:
                self._pending_targets.pop(target_id, None)
            self.result_ready.emit(result)
            remaining -= 1
            if remaining == 0:
                QTimer.singleShot(0, self._on_poll_done)

        # 防止卡住
        QTimer.singleShot(60000, self._on_poll_done)

        for target in self._targets:
            future = self._executor.submit(self._check_target, target)
            future.add_done_callback(
                lambda f, tid=target.target_id: _done_callback(tid, f)
            )

    def _on_poll_done(self):
        """轮询结束"""
        self._is_polling = False
        self.poll_status_label.setText("")
        self._stop_timeout_timer()
        self._refresh_summary()

    def _start_timeout_timer(self):
        """启动超时检测定时器"""
        if self._timeout_timer is None:
            self._timeout_timer = QTimer(self)
            self._timeout_timer.timeout.connect(self._check_pending_timeouts)
        self._timeout_timer.start(1000)

    def _stop_timeout_timer(self):
        """停止超时检测定时器"""
        if self._timeout_timer is not None:
            self._timeout_timer.stop()

    def _check_pending_timeouts(self):
        """检查超时的请求并标记"""
        if not self._pending_targets:
            return
        now_ts = time.time()
        timed_out = [
            tid
            for tid, start_ts in self._pending_targets.items()
            if now_ts - start_ts > self._request_timeout_sec
        ]
        for tid in timed_out:
            self._pending_targets.pop(tid, None)
            result = MonitorResult(
                target_id=tid,
                status="error",
                latency_ms=None,
                ping_ms=None,
                checked_at=datetime.now(),
                message="请求超时",
            )
            self._on_single_result(result)
        if not self._pending_targets:
            self._on_poll_done()

    def _on_single_result(self, result: MonitorResult):
        """处理单个结果并即时刷新行"""
        history = self._history.get(result.target_id)
        if history is not None:
            history.append(result)
        self._update_table_row(result.target_id)

    def _mark_all_pending(self):
        """将所有行标记为检测中"""
        for target in self._targets:
            self._update_table_row(target.target_id, pending=True)

    def _refresh_summary(self):
        """刷新统计摘要"""
        # 计算统计数据
        total_availability = []
        total_chat_latency = []
        total_ping_latency = []
        error_count = 0
        last_checked: Optional[datetime] = None

        for target in self._targets:
            history = self._history.get(target.target_id, deque())
            if history:
                avail = _calc_availability(history)
                if avail is not None:
                    total_availability.append(avail)
                latest = history[-1]
                if latest.latency_ms is not None:
                    total_chat_latency.append(latest.latency_ms)
                if latest.ping_ms is not None:
                    total_ping_latency.append(latest.ping_ms)
                if latest.status in ("failed", "error"):
                    error_count += 1
                if last_checked is None or latest.checked_at > last_checked:
                    last_checked = latest.checked_at

        # 可用率 - 根据数值变色
        if total_availability:
            avg_avail = sum(total_availability) / len(total_availability)
            self.availability_value.setText(f"{avg_avail:.1f}%")
            if avg_avail >= 90:
                color = "#3fb950"  # 绿色
            elif avg_avail >= 70:
                color = "#f0883e"  # 橙色
            else:
                color = "#f85149"  # 红色
            self.availability_value.setStyleSheet(f"color: {color}; font-size: 14px;")
        else:
            self.availability_value.setText("—")
            self.availability_value.setStyleSheet("color: #7d8590; font-size: 14px;")

        # 对话延迟 - 根据数值变色
        if total_chat_latency:
            avg_chat = sum(total_chat_latency) // len(total_chat_latency)
            self.chat_latency_value.setText(f"{avg_chat}ms")
            if avg_chat <= 1000:
                color = "#3fb950"  # 绿色 <= 1s
            elif avg_chat <= 3000:
                color = "#58a6ff"  # 蓝色 <= 3s
            elif avg_chat <= 6000:
                color = "#f0883e"  # 橙色 <= 6s
            else:
                color = "#f85149"  # 红色 > 6s
            self.chat_latency_value.setStyleSheet(f"color: {color}; font-size: 14px;")
        else:
            self.chat_latency_value.setText("—")
            self.chat_latency_value.setStyleSheet("color: #7d8590; font-size: 14px;")

        # Ping 延迟 - 根据数值变色
        if total_ping_latency:
            avg_ping = sum(total_ping_latency) // len(total_ping_latency)
            self.ping_latency_value.setText(f"{avg_ping}ms")
            if avg_ping <= 100:
                color = "#3fb950"  # 绿色 <= 100ms
            elif avg_ping <= 300:
                color = "#58a6ff"  # 蓝色 <= 300ms
            elif avg_ping <= 500:
                color = "#f0883e"  # 橙色 <= 500ms
            else:
                color = "#f85149"  # 红色 > 500ms
            self.ping_latency_value.setStyleSheet(f"color: {color}; font-size: 14px;")
        else:
            self.ping_latency_value.setText("—")
            self.ping_latency_value.setStyleSheet("color: #7d8590; font-size: 14px;")

        # 异常数 - 根据数值变色
        self.error_count_value.setText(str(error_count))
        if error_count == 0:
            self.error_count_value.setStyleSheet("color: #3fb950; font-size: 14px;")
        elif error_count <= 2:
            self.error_count_value.setStyleSheet("color: #f0883e; font-size: 14px;")
        else:
            self.error_count_value.setStyleSheet("color: #f85149; font-size: 14px;")

        if last_checked:
            self.last_checked_value.setText(last_checked.strftime("%H:%M:%S"))
        else:
            self.last_checked_value.setText("—")

    def _check_target(self, target: MonitorTarget) -> MonitorResult:
        """检查单个目标的可用性和延迟"""
        checked_at = datetime.now()
        origin = _extract_origin(target.base_url)

        # Ping 检测
        ping_ms = _measure_ping(origin) if origin else None

        # Chat 延迟检测
        latency_ms: Optional[int] = None
        status = "no_config"
        message = ""

        if not getattr(self, "_chat_test_enabled", True):
            # 对话测试已暂停，根据 Ping 结果判定状态
            if not target.base_url:
                message = "未配置 baseURL"
            elif ping_ms is not None:
                status = "operational"
                message = "对话测试已暂停 (Ping 正常)"
            elif origin:
                status = "error"
                message = "Ping 失败"
            else:
                status = "no_config"
                message = "未配置有效的主机"
        elif not target.base_url:
            message = "未配置 baseURL"
        elif not target.api_key:
            message = "未配置 apiKey"
        else:
            # 发送最小请求
            try:
                url = _build_chat_url(target.base_url)
                if not url:
                    raise ValueError("baseURL 无效")
                payload = json.dumps(
                    {
                        "model": target.model_id,
                        "messages": [{"role": "user", "content": "hi"}],
                        "max_tokens": 1,
                    }
                ).encode("utf-8")
                req = urllib.request.Request(
                    url,
                    data=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {target.api_key}",
                    },
                    method="POST",
                )
                start = time.time()
                with urllib.request.urlopen(req, timeout=30) as resp:
                    resp.read()
                latency_ms = int((time.time() - start) * 1000)
                if latency_ms <= DEGRADED_THRESHOLD_MS:
                    status = "operational"
                    message = "正常"
                else:
                    status = "degraded"
                    message = f"延迟较高 ({latency_ms}ms)"
            except urllib.error.HTTPError as e:
                status = "failed"
                message = "鉴权失败" if e.code in (401, 403) else f"HTTP {e.code}"
            except urllib.error.URLError as e:
                status = "error"
                message = f"连接失败: {e.reason}"
            except Exception as e:
                status = "error"
                message = str(e)[:50]

        return MonitorResult(
            target_id=target.target_id,
            status=status,
            latency_ms=latency_ms,
            ping_ms=ping_ms,
            checked_at=checked_at,
            message=message,
        )

    def _apply_stat_card_theme(self):
        """应用统计卡片的主题样式"""
        if isDarkTheme():
            card_style = """
                QFrame {
                    background-color: #161b22;
                    border: 1px solid #30363d;
                    border-radius: 6px;
                }
            """
            label_color = "#7d8590"
        else:
            card_style = """
                QFrame {
                    background-color: #ffffff;
                    border: 1px solid #d0d7de;
                    border-radius: 6px;
                }
            """
            label_color = "#57606a"

        for card in self._stat_cards:
            card.setStyleSheet(card_style)

        for label in self._stat_labels:
            label.setStyleSheet(f"color: {label_color}; font-size: 10px;")

    def _refresh_ui(self):
        """刷新所有 UI 组件"""
        # 更新目标数
        self.target_count_value.setText(str(len(self._targets)))
        self._refresh_summary()
        self._update_table()

    def _build_history_bar(self, history: Deque[MonitorResult]) -> QWidget:
        """构建状态历史条带"""
        container = QWidget(self)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        max_points = 24
        points = list(history)[-max_points:]
        if not points:
            points = []

        for _ in range(max_points - len(points)):
            points.insert(
                0, MonitorResult("", "no_config", None, None, datetime.now(), "")
            )

        for item in points:
            color = STATUS_COLORS.get(item.status, "#9AA4B2")
            block = QLabel(container)
            block.setFixedSize(6, 10)
            block.setStyleSheet(f"background: {color}; border-radius: 1px;")
            block.setToolTip(
                f"{tr(STATUS_LABELS.get(item.status, 'monitor.status_error'))}: {item.checked_at.strftime('%H:%M:%S')}"
            )
            layout.addWidget(block)

        return container

    def _update_table(self):
        """更新明细表格"""
        self.detail_table.setRowCount(0)

        self._row_index.clear()
        for target in self._targets:
            history = self._history.get(target.target_id, deque())
            row = self.detail_table.rowCount()
            self.detail_table.insertRow(row)
            self._row_index[target.target_id] = row

            # 目标名称
            target_name = f"{target.provider_name}/{target.model_name}"
            self.detail_table.setItem(row, 0, QTableWidgetItem(target_name))

            self._fill_row_from_history(row, history)

    def _update_table_row(self, target_id: str, pending: bool = False):
        """根据 target_id 更新单行"""
        row = self._row_index.get(target_id)
        if row is None:
            return
        history = self._history.get(target_id, deque())
        self._fill_row_from_history(row, history, pending=pending)

    def _fill_row_from_history(
        self,
        row: int,
        history: Deque[MonitorResult],
        pending: bool = False,
    ) -> None:
        """填充表格行"""
        if pending:
            status_item = QTableWidgetItem(f"● {tr('monitor.checking')}")
            status_item.setForeground(QColor("#9AA4B2"))
            self.detail_table.setItem(row, 1, status_item)
            self.detail_table.setItem(row, 2, QTableWidgetItem("—"))
            self.detail_table.setItem(row, 3, QTableWidgetItem("—"))
            self.detail_table.setItem(row, 4, QTableWidgetItem("—"))
            self.detail_table.setItem(row, 5, QTableWidgetItem("—"))
            self.detail_table.setCellWidget(row, 6, self._build_history_bar(history))
            self.detail_table.update()
            return

        if history:
            latest = history[-1]
            # 状态
            status_label = tr(STATUS_LABELS.get(latest.status, "monitor.status_error"))
            status_item = QTableWidgetItem(f"● {status_label}")
            status_item.setForeground(
                QColor(STATUS_COLORS.get(latest.status, "#9AA4B2"))
            )
            status_item.setToolTip(latest.message)
            self.detail_table.setItem(row, 1, status_item)

            # 可用率 - 根据数值变色
            avail = _calc_availability(history)
            avail_item = QTableWidgetItem(f"{avail:.1f}%" if avail is not None else "—")
            if avail is not None:
                if avail >= 90:
                    avail_item.setForeground(QColor("#3fb950"))
                elif avail >= 70:
                    avail_item.setForeground(QColor("#f0883e"))
                else:
                    avail_item.setForeground(QColor("#f85149"))
            self.detail_table.setItem(row, 2, avail_item)

            # 对话延迟 - 根据数值变色
            chat_item = QTableWidgetItem(_format_latency(latest.latency_ms))
            if latest.latency_ms is not None:
                if latest.latency_ms <= 1000:
                    chat_item.setForeground(QColor("#3fb950"))
                elif latest.latency_ms <= 3000:
                    chat_item.setForeground(QColor("#58a6ff"))
                elif latest.latency_ms <= 6000:
                    chat_item.setForeground(QColor("#f0883e"))
                else:
                    chat_item.setForeground(QColor("#f85149"))
            self.detail_table.setItem(row, 3, chat_item)

            # Ping 延迟 - 根据数值变色
            ping_item = QTableWidgetItem(_format_latency(latest.ping_ms))
            if latest.ping_ms is not None:
                if latest.ping_ms <= 100:
                    ping_item.setForeground(QColor("#3fb950"))
                elif latest.ping_ms <= 300:
                    ping_item.setForeground(QColor("#58a6ff"))
                elif latest.ping_ms <= 500:
                    ping_item.setForeground(QColor("#f0883e"))
                else:
                    ping_item.setForeground(QColor("#f85149"))
            self.detail_table.setItem(row, 4, ping_item)

            # 最后检测
            self.detail_table.setItem(
                row, 5, QTableWidgetItem(latest.checked_at.strftime("%H:%M:%S"))
            )

            # 历史条带
            self.detail_table.setCellWidget(row, 6, self._build_history_bar(history))
        else:
            # 无数据
            self.detail_table.setItem(row, 1, QTableWidgetItem("—"))
            self.detail_table.setItem(row, 2, QTableWidgetItem("—"))
            self.detail_table.setItem(row, 3, QTableWidgetItem("—"))
            self.detail_table.setItem(row, 4, QTableWidgetItem("—"))
            self.detail_table.setItem(row, 5, QTableWidgetItem("—"))
            self.detail_table.setCellWidget(row, 6, self._build_history_bar(deque()))

        self.detail_table.update()


class JsonTomlHighlighter(QSyntaxHighlighter):
    """JSON/TOML 语法高亮"""

    def __init__(self, document, is_dark: bool, prefer_toml: bool = False):
        super().__init__(document)
        self._is_dark = is_dark
        self._prefer_toml = prefer_toml
        self._rules = []
        self._init_rules()

    def _make_format(self, color: QColor, bold: bool = False) -> QTextCharFormat:
        fmt = QTextCharFormat()
        fmt.setForeground(color)
        if bold:
            fmt.setFontWeight(QFont.Bold)
        return fmt

    def _init_rules(self) -> None:
        if self._is_dark:
            key_color = QColor("#7AA2F7")
            string_color = QColor("#9ECE6A")
            number_color = QColor("#E0AF68")
            boolean_color = QColor("#7DCFFF")
            null_color = QColor("#F7768E")
            bracket_level_colors = [
                QColor("#C0CAF5"),
                QColor("#B4F9F8"),
                QColor("#BB9AF7"),
                QColor("#F7768E"),
            ]
            section_color = QColor("#FF9E64")
        else:
            key_color = QColor("#1F4AA1")
            string_color = QColor("#1A7F37")
            number_color = QColor("#B26A00")
            boolean_color = QColor("#006D77")
            null_color = QColor("#B00020")
            bracket_level_colors = [
                QColor("#4B4B4B"),
                QColor("#0077B6"),
                QColor("#6A4C93"),
                QColor("#9B2226"),
            ]
            section_color = QColor("#A65D00")

        self._bracket_colors = bracket_level_colors

        string_fmt = self._make_format(string_color)
        number_fmt = self._make_format(number_color)
        boolean_fmt = self._make_format(boolean_color, bold=True)
        null_fmt = self._make_format(null_color, bold=True)
        key_fmt = self._make_format(key_color, bold=True)
        section_fmt = self._make_format(section_color, bold=True)

        def add_rule(pattern: str, fmt: QTextCharFormat, flags=None) -> None:
            regex = QRegularExpression(pattern)
            if flags:
                regex.setPatternOptions(flags)
            self._rules.append((regex, fmt))

        add_rule(r'"[^"\\]*(?:\\.[^"\\]*)*"', string_fmt)
        add_rule(r"'[^'\\]*(?:\\.[^'\\]*)*'", string_fmt)
        add_rule(r"\b-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?\b", number_fmt)
        add_rule(
            r"\b(true|false)\b", boolean_fmt, QRegularExpression.CaseInsensitiveOption
        )
        add_rule(r"\b(null|none)\b", null_fmt, QRegularExpression.CaseInsensitiveOption)
        add_rule(r'"[^"\\]*(?:\\.[^"\\]*)*"(?=\s*[:=])', key_fmt)
        add_rule(r"'[^'\\]*(?:\\.[^'\\]*)*'(?=\s*=)", key_fmt)
        add_rule(r"\b[A-Za-z0-9_\-\.]+(?=\s*=)", key_fmt)
        add_rule(r"^\s*\[[^\]]+\]", section_fmt)

        # 括号层级着色：通过字符前缀决定层级（上限4层）
        for level, color in enumerate(bracket_level_colors, start=1):
            prefix = r"[^\{\}\[\]\(\)]*" * (level - 1)
            add_rule(rf"{prefix}[\{{\[\(]", self._make_format(color))
            add_rule(rf"{prefix}[\}}\]\)]", self._make_format(color))

    def highlightBlock(self, text: str) -> None:
        for regex, fmt in self._rules:
            it = regex.globalMatch(text)
            while it.hasNext():
                match = it.next()
                start = match.capturedStart()
                length = match.capturedLength()
                if start >= 0 and length > 0:
                    self.setFormat(start, length, fmt)

        # 逐字符处理括号层级着色
        if not text:
            return
        depth = self.previousBlockState()
        if depth < 0:
            depth = 0
        colors = self._bracket_colors or []
        color_count = len(colors)
        if color_count == 0:
            return

        for i, ch in enumerate(text):
            if ch in "{[(":
                depth += 1
                color = colors[(depth - 1) % color_count]
                self.setFormat(i, 1, self._make_format(color))
            elif ch in "}])":
                color = colors[(depth - 1) % color_count] if depth > 0 else colors[0]
                self.setFormat(i, 1, self._make_format(color))
                if depth > 0:
                    depth -= 1

        self.setCurrentBlockState(depth)


def _find_matching_bracket(text: str, index: int) -> Optional[int]:
    if index < 0 or index >= len(text):
        return None
    pairs = {"(": ")", ")": "(", "[": "]", "]": "[", "{": "}", "}": "{"}
    char = text[index]
    if char not in pairs:
        return None
    if char in "([{":
        target = pairs[char]
        depth = 0
        for i in range(index + 1, len(text)):
            current = text[i]
            if current == char:
                depth += 1
            elif current == target:
                if depth == 0:
                    return i
                depth -= 1
        return None
    target = pairs[char]
    depth = 0
    for i in range(index - 1, -1, -1):
        current = text[i]
        if current == char:
            depth += 1
        elif current == target:
            if depth == 0:
                return i
            depth -= 1
    return None


def apply_bracket_match_highlight(text_edit: QTextEdit, is_dark: bool) -> None:
    text = text_edit.toPlainText()
    if not text:
        text_edit.setExtraSelections([])
        return

    cursor = text_edit.textCursor()
    pos = cursor.position()
    candidates = [pos - 1, pos]
    match_index = None
    active_index = None
    for idx in candidates:
        if 0 <= idx < len(text) and text[idx] in "()[]{}":
            active_index = idx
            match_index = _find_matching_bracket(text, idx)
            if match_index is not None:
                break

    if active_index is None or match_index is None:
        text_edit.setExtraSelections([])
        return

    fmt = QTextCharFormat()
    if is_dark:
        fmt.setBackground(QColor(255, 255, 255, 50))
    else:
        fmt.setBackground(QColor(0, 0, 0, 35))
    fmt.setFontWeight(QFont.Bold)

    selections = []
    for idx in (active_index, match_index):
        sel = QTextEdit.ExtraSelection()
        sel.format = fmt
        sel_cursor = text_edit.textCursor()
        sel_cursor.setPosition(idx)
        sel_cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, 1)
        sel.cursor = sel_cursor
        selections.append(sel)

    text_edit.setExtraSelections(selections)


# ==================== 语法高亮器 ====================
class ConfigSyntaxHighlighter(QSyntaxHighlighter):
    """配置文件语法高亮器 - 支持 JSON/TOML/ENV 格式"""

    def __init__(self, parent=None, language: str = "json"):
        super().__init__(parent)
        self.language = language
        self._setup_formats()
        self._setup_rules()

    def _setup_formats(self):
        """设置高亮格式"""
        # 检测暗色主题
        is_dark = isDarkTheme()

        # 字符串格式 (绿色)
        self.string_format = QTextCharFormat()
        self.string_format.setForeground(
            QColor("#98C379") if is_dark else QColor("#50A14F")
        )

        # 数字格式 (橙色)
        self.number_format = QTextCharFormat()
        self.number_format.setForeground(
            QColor("#D19A66") if is_dark else QColor("#986801")
        )

        # 关键字格式 (紫色) - true/false/null
        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(
            QColor("#C678DD") if is_dark else QColor("#A626A4")
        )

        # 键名格式 (蓝色)
        self.key_format = QTextCharFormat()
        self.key_format.setForeground(
            QColor("#61AFEF") if is_dark else QColor("#4078F2")
        )

        # 注释格式 (灰色)
        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(
            QColor("#5C6370") if is_dark else QColor("#A0A1A7")
        )
        self.comment_format.setFontItalic(True)

        # 括号格式 (黄色)
        self.bracket_format = QTextCharFormat()
        self.bracket_format.setForeground(
            QColor("#E5C07B") if is_dark else QColor("#C18401")
        )

        # 等号/冒号格式 (白色/黑色)
        self.operator_format = QTextCharFormat()
        self.operator_format.setForeground(
            QColor("#ABB2BF") if is_dark else QColor("#383A42")
        )

    def _setup_rules(self):
        """设置高亮规则"""
        self.rules = []

        if self.language == "json":
            # JSON 键名 "key":
            self.rules.append((r'"[^"]*"\s*:', self.key_format))
            # JSON 字符串值
            self.rules.append((r':\s*"[^"]*"', self.string_format))
            # 数字
            self.rules.append((r"\b-?\d+\.?\d*\b", self.number_format))
            # 关键字
            self.rules.append((r"\b(true|false|null)\b", self.keyword_format))
            # 括号
            self.rules.append((r"[\[\]{}]", self.bracket_format))

        elif self.language == "toml":
            # TOML 注释
            self.rules.append((r"#.*$", self.comment_format))
            # TOML 节名 [section]
            self.rules.append((r"\[[\w.]+\]", self.key_format))
            # TOML 键名
            self.rules.append((r"^[\w_]+\s*=", self.key_format))
            # TOML 字符串
            self.rules.append((r'"[^"]*"', self.string_format))
            # 数字
            self.rules.append((r"\b-?\d+\.?\d*\b", self.number_format))
            # 关键字
            self.rules.append((r"\b(true|false)\b", self.keyword_format))

        elif self.language == "env":
            # ENV 注释
            self.rules.append((r"#.*$", self.comment_format))
            # ENV 键名
            self.rules.append((r"^[A-Z_][A-Z0-9_]*(?==)", self.key_format))
            # ENV 值
            self.rules.append((r"=.*$", self.string_format))

    def highlightBlock(self, text: str):
        """高亮文本块"""
        for pattern, fmt in self.rules:
            for match in re.finditer(pattern, text, re.MULTILINE):
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, fmt)


# ==================== CLI 导出页面 ====================
class CLIExportPage(BasePage):
    """CLI 工具导出页面 - 将 OpenCode 配置导出到 Claude Code、Codex CLI、Gemini CLI"""

    def __init__(self, main_window, parent=None):
        super().__init__(tr("cli_export.title"), parent)
        self.main_window = main_window
        self.export_manager = CLIExportManager()
        self._selected_provider = None
        self._selected_provider_name = None
        # Claude 有 4 个模型字段
        self._claude_models = {
            "main": "",  # ANTHROPIC_MODEL
            "haiku": "",  # ANTHROPIC_DEFAULT_HAIKU_MODEL
            "sonnet": "",  # ANTHROPIC_DEFAULT_SONNET_MODEL
            "opus": "",  # ANTHROPIC_DEFAULT_OPUS_MODEL
        }
        self._selected_models = {"claude": "", "codex": "", "gemini": ""}
        self._cli_status = {}  # 缓存 CLI 状态
        self._use_common_config = {"codex": False, "gemini": False}
        self._common_config_snippets = {"codex": "", "gemini": ""}
        self._highlighters = {}  # 语法高亮器缓存
        self._setup_ui_v2()
        # 延迟刷新 CLI 状态，避免在初始化时阻塞
        QTimer.singleShot(100, self._refresh_cli_status)
        # 连接配置变更信号
        self.main_window.config_changed.connect(self._on_config_changed)

    def _on_config_changed(self):
        """配置变更时刷新页面"""
        self._refresh_providers()
        self._refresh_cli_status()
        self._update_preview()

    def _setup_ui_v2(self):
        """设置 UI 布局 - 紧凑标签页设计"""
        # ===== 顶部区域：标题 + Provider 选择 + CLI 状态 =====
        top_card = self.add_card("")
        top_layout = top_card.layout()

        # 介绍文字
        intro_label = CaptionLabel(
            tr("cli_export.description"),
            top_card,
        )
        intro_label.setStyleSheet("color: #888; margin-bottom: 4px;")
        top_layout.addWidget(intro_label)

        # Provider 选择行 + CLI 状态
        provider_row = QHBoxLayout()
        provider_row.setSpacing(12)

        provider_label = BodyLabel("Provider:", top_card)
        provider_row.addWidget(provider_label)

        self.provider_combo = ComboBox(top_card)
        self.provider_combo.setFixedWidth(180)
        self.provider_combo.setFixedHeight(32)
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        provider_row.addWidget(self.provider_combo)

        # 配置状态
        self.config_status_label = BodyLabel("", top_card)
        provider_row.addWidget(self.config_status_label)

        self.fix_config_btn = PushButton(FIF.EDIT, tr("cli_export.fix"), top_card)
        self.fix_config_btn.setFixedHeight(28)
        self.fix_config_btn.clicked.connect(self._go_to_provider_edit)
        self.fix_config_btn.setVisible(False)
        provider_row.addWidget(self.fix_config_btn)

        provider_row.addStretch()

        # CLI 状态标签 (紧凑显示)
        cli_label = CaptionLabel("CLI:", top_card)
        provider_row.addWidget(cli_label)

        self.claude_chip = QLabel("Claude ⏳", top_card)
        self.claude_chip.setStyleSheet(
            "padding: 2px 6px; border-radius: 8px; background: rgba(128,128,128,0.2); font-size: 11px;"
        )
        provider_row.addWidget(self.claude_chip)

        self.codex_chip = QLabel("Codex ⏳", top_card)
        self.codex_chip.setStyleSheet(
            "padding: 2px 6px; border-radius: 8px; background: rgba(128,128,128,0.2); font-size: 11px;"
        )
        provider_row.addWidget(self.codex_chip)

        self.gemini_chip = QLabel("Gemini ⏳", top_card)
        self.gemini_chip.setStyleSheet(
            "padding: 2px 6px; border-radius: 8px; background: rgba(128,128,128,0.2); font-size: 11px;"
        )
        provider_row.addWidget(self.gemini_chip)

        refresh_btn = ToolButton(FIF.SYNC, top_card)
        refresh_btn.setToolTip(tr("cli_export.refresh_detection"))
        refresh_btn.clicked.connect(self._refresh_cli_status)
        provider_row.addWidget(refresh_btn)

        top_layout.addLayout(provider_row)

        # ===== 主标签页：按 CLI 工具分组 =====
        main_card = self.add_card("")
        main_layout = main_card.layout()

        # 主标签页切换
        self.main_pivot = Pivot(main_card)
        self.main_pivot.addItem(
            routeKey="claude", text=tr("cli_export.tab_claude_code")
        )
        self.main_pivot.addItem(routeKey="codex", text=tr("cli_export.tab_codex"))
        self.main_pivot.addItem(routeKey="gemini", text=tr("cli_export.tab_gemini"))
        self.main_pivot.setCurrentItem("claude")
        self.main_pivot.currentItemChanged.connect(self._on_main_tab_changed)
        main_layout.addWidget(self.main_pivot)

        # 堆叠窗口
        self.main_stack = QStackedWidget(main_card)

        # Claude 页面
        self.claude_tab = self._create_claude_tab_widget(main_card)
        self.main_stack.addWidget(self.claude_tab)

        # Codex 页面
        self.codex_tab = self._create_codex_tab_widget(main_card)
        self.main_stack.addWidget(self.codex_tab)

        # Gemini 页面
        self.gemini_tab = self._create_gemini_tab_widget(main_card)
        self.main_stack.addWidget(self.gemini_tab)

        main_layout.addWidget(self.main_stack, 1)

        # ===== 底部操作栏 =====
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(12)

        self.batch_export_btn = PrimaryPushButton(
            FIF.SEND, tr("cli_export.batch_export_all"), main_card
        )
        self.batch_export_btn.clicked.connect(self._on_batch_export)
        bottom_row.addWidget(self.batch_export_btn)

        bottom_row.addStretch()

        self.backup_info_label = CaptionLabel(
            tr("cli_export.latest_backup_none"), main_card
        )
        bottom_row.addWidget(self.backup_info_label)

        view_backup_btn = PushButton(
            FIF.FOLDER, tr("cli_export.view_backup"), main_card
        )
        view_backup_btn.clicked.connect(self._view_backups)
        bottom_row.addWidget(view_backup_btn)

        restore_btn = PushButton(
            FIF.HISTORY, tr("cli_export.restore_backup"), main_card
        )
        restore_btn.clicked.connect(self._restore_backup)
        bottom_row.addWidget(restore_btn)

        main_layout.addLayout(bottom_row)

        # 初始化数据
        self._refresh_providers()

    def _create_claude_tab_widget(self, parent) -> QWidget:
        """创建 Claude Code 标签页"""
        widget = QWidget(parent)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(8)

        # 模型配置区域 (紧凑)
        model_frame = QFrame(widget)
        model_frame.setStyleSheet(
            "QFrame { background: rgba(128,128,128,0.05); border: 1px solid rgba(128,128,128,0.1); border-radius: 6px; }"
        )
        model_layout = QVBoxLayout(model_frame)
        model_layout.setContentsMargins(12, 8, 12, 8)
        model_layout.setSpacing(6)

        model_title = StrongBodyLabel(tr("cli_export.export_config_title"), model_frame)
        model_layout.addWidget(model_title)

        # Base URL 行
        url_row = QHBoxLayout()
        url_row.setSpacing(8)
        url_row.addWidget(CaptionLabel(tr("cli_export.base_url") + ":", model_frame))
        self.claude_base_url_edit = LineEdit(model_frame)
        self.claude_base_url_edit.setPlaceholderText(
            tr("cli_export.from_provider_config")
        )
        self.claude_base_url_edit.setFixedHeight(28)
        self.claude_base_url_edit.textChanged.connect(lambda: self._update_preview())
        url_row.addWidget(self.claude_base_url_edit, 1)
        model_layout.addLayout(url_row)

        # 可编辑下拉框样式
        editable_combo_style = """
            QComboBox {
                background-color: rgba(128, 128, 128, 0.1);
                border: 1px solid rgba(128, 128, 128, 0.2);
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
                color: #e6edf3;
            }
            QComboBox:hover {
                border-color: rgba(128, 128, 128, 0.4);
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                border: 1px solid rgba(128, 128, 128, 0.3);
                selection-background-color: rgba(33, 150, 243, 0.3);
                color: #e6edf3;
            }
            QComboBox QAbstractItemView::item {
                color: #e6edf3;
                padding: 4px 8px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: rgba(128, 128, 128, 0.2);
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: rgba(33, 150, 243, 0.3);
            }
        """

        # 2x2 网格 - 模型选择 (使用原生 QComboBox 支持编辑)
        grid = QGridLayout()
        grid.setSpacing(8)

        grid.addWidget(
            CaptionLabel(tr("cli_export.main_model") + ":", model_frame), 0, 0
        )
        self.claude_main_model_combo = QNativeComboBox(model_frame)
        self.claude_main_model_combo.setFixedSize(200, 30)
        self.claude_main_model_combo.setEditable(True)
        self.claude_main_model_combo.setStyleSheet(editable_combo_style)
        self.claude_main_model_combo.currentTextChanged.connect(
            lambda t: self._on_claude_model_changed("main", t)
        )
        grid.addWidget(self.claude_main_model_combo, 0, 1)

        grid.addWidget(CaptionLabel("Haiku:", model_frame), 0, 2)
        self.claude_haiku_combo = QNativeComboBox(model_frame)
        self.claude_haiku_combo.setFixedSize(200, 30)
        self.claude_haiku_combo.setEditable(True)
        self.claude_haiku_combo.setStyleSheet(editable_combo_style)
        self.claude_haiku_combo.currentTextChanged.connect(
            lambda t: self._on_claude_model_changed("haiku", t)
        )
        grid.addWidget(self.claude_haiku_combo, 0, 3)

        grid.addWidget(CaptionLabel("Sonnet:", model_frame), 1, 0)
        self.claude_sonnet_combo = QNativeComboBox(model_frame)
        self.claude_sonnet_combo.setFixedSize(200, 30)
        self.claude_sonnet_combo.setEditable(True)
        self.claude_sonnet_combo.setStyleSheet(editable_combo_style)
        self.claude_sonnet_combo.currentTextChanged.connect(
            lambda t: self._on_claude_model_changed("sonnet", t)
        )
        grid.addWidget(self.claude_sonnet_combo, 1, 1)

        grid.addWidget(CaptionLabel("Opus:", model_frame), 1, 2)
        self.claude_opus_combo = QNativeComboBox(model_frame)
        self.claude_opus_combo.setFixedSize(200, 30)
        self.claude_opus_combo.setEditable(True)
        self.claude_opus_combo.setStyleSheet(editable_combo_style)
        self.claude_opus_combo.currentTextChanged.connect(
            lambda t: self._on_claude_model_changed("opus", t)
        )
        grid.addWidget(self.claude_opus_combo, 1, 3)

        grid.setColumnStretch(4, 1)
        model_layout.addLayout(grid)

        hint = CaptionLabel(tr("cli_export.model_hint_full"), model_frame)
        hint.setStyleSheet("color: #666;")
        model_layout.addWidget(hint)

        layout.addWidget(model_frame)

        # 配置预览
        preview_frame = QFrame(widget)
        preview_frame.setStyleSheet(
            "QFrame { background: rgba(128,128,128,0.05); border: 1px solid rgba(128,128,128,0.1); border-radius: 6px; }"
        )
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setContentsMargins(12, 8, 12, 8)
        preview_layout.setSpacing(4)

        header = QHBoxLayout()
        header.addWidget(
            StrongBodyLabel(tr("cli_export.preview_title_claude"), preview_frame)
        )
        header.addStretch()

        format_btn = ToolButton(FIF.ALIGNMENT, preview_frame)
        format_btn.setToolTip(tr("cli_export.format_json"))
        format_btn.clicked.connect(lambda: self._format_preview_for("claude"))
        header.addWidget(format_btn)

        export_btn = PrimaryPushButton(FIF.SEND, tr("cli_export.export"), preview_frame)
        export_btn.setFixedWidth(80)
        export_btn.clicked.connect(lambda: self._on_single_export("claude"))
        header.addWidget(export_btn)

        preview_layout.addLayout(header)

        self.claude_preview_text = PlainTextEdit(preview_frame)
        self.claude_preview_text.setReadOnly(True)
        self.claude_preview_text.setStyleSheet(
            "PlainTextEdit { font-family: Consolas, Monaco, monospace; font-size: 11px; background: rgba(20,20,20,0.9); color: #ABB2BF; border: none; border-radius: 4px; padding: 6px; }"
        )
        preview_layout.addWidget(self.claude_preview_text, 1)

        self._highlighters["claude"] = ConfigSyntaxHighlighter(
            self.claude_preview_text.document(), "json"
        )

        layout.addWidget(preview_frame, 1)
        return widget

    def _create_codex_tab_widget(self, parent) -> QWidget:
        """创建 Codex CLI 标签页"""
        widget = QWidget(parent)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(8)

        # 模型配置
        model_frame = QFrame(widget)
        model_frame.setStyleSheet(
            "QFrame { background: rgba(128,128,128,0.05); border: 1px solid rgba(128,128,128,0.1); border-radius: 6px; }"
        )
        model_layout = QVBoxLayout(model_frame)
        model_layout.setContentsMargins(12, 8, 12, 8)
        model_layout.setSpacing(6)

        model_title = StrongBodyLabel(tr("cli_export.export_config_title"), model_frame)
        model_layout.addWidget(model_title)

        # Base URL 行
        url_row = QHBoxLayout()
        url_row.setSpacing(8)
        url_row.addWidget(CaptionLabel(tr("cli_export.base_url") + ":", model_frame))
        self.codex_base_url_edit = LineEdit(model_frame)
        self.codex_base_url_edit.setPlaceholderText(
            tr("cli_export.from_provider_config")
        )
        self.codex_base_url_edit.setFixedHeight(28)
        self.codex_base_url_edit.textChanged.connect(lambda: self._update_preview())
        url_row.addWidget(self.codex_base_url_edit, 1)
        model_layout.addLayout(url_row)

        # 可编辑下拉框样式
        editable_combo_style = """
            QComboBox {
                background-color: rgba(128, 128, 128, 0.1);
                border: 1px solid rgba(128, 128, 128, 0.2);
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
                color: #e6edf3;
            }
            QComboBox:hover {
                border-color: rgba(128, 128, 128, 0.4);
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                border: 1px solid rgba(128, 128, 128, 0.3);
                selection-background-color: rgba(33, 150, 243, 0.3);
                color: #e6edf3;
            }
            QComboBox QAbstractItemView::item {
                color: #e6edf3;
                padding: 4px 8px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: rgba(128, 128, 128, 0.2);
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: rgba(33, 150, 243, 0.3);
            }
        """

        # 模型选择行
        model_row = QHBoxLayout()
        model_row.setSpacing(12)

        model_row.addWidget(CaptionLabel(tr("cli_export.model") + ":", model_frame))
        self.codex_model_combo = QNativeComboBox(model_frame)
        self.codex_model_combo.setFixedSize(200, 30)
        self.codex_model_combo.setEditable(True)
        self.codex_model_combo.setStyleSheet(editable_combo_style)
        self.codex_model_combo.currentTextChanged.connect(
            lambda t: self._on_model_changed("codex", t)
        )
        model_row.addWidget(self.codex_model_combo)

        hint = CaptionLabel(tr("cli_export.model_hint_simple"), model_frame)
        hint.setStyleSheet("color: #666;")
        model_row.addWidget(hint)

        model_row.addStretch()

        self.codex_common_check = CheckBox(
            tr("cli_export.write_common_config"), model_frame
        )
        self.codex_common_check.stateChanged.connect(
            lambda s: self._on_common_config_toggle("codex", s == Qt.Checked)
        )
        model_row.addWidget(self.codex_common_check)

        edit_btn = HyperlinkButton("", tr("cli_export.edit"), model_frame)
        edit_btn.clicked.connect(lambda: self._edit_common_config("codex"))
        model_row.addWidget(edit_btn)

        model_layout.addLayout(model_row)
        layout.addWidget(model_frame)

        # 配置预览 (双文件)
        preview_frame = QFrame(widget)
        preview_frame.setStyleSheet(
            "QFrame { background: rgba(128,128,128,0.05); border: 1px solid rgba(128,128,128,0.1); border-radius: 6px; }"
        )
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setContentsMargins(12, 8, 12, 8)
        preview_layout.setSpacing(4)

        header = QHBoxLayout()
        header.addWidget(
            StrongBodyLabel(tr("cli_export.preview_title_codex"), preview_frame)
        )
        header.addStretch()

        format_btn = ToolButton(FIF.ALIGNMENT, preview_frame)
        format_btn.setToolTip(tr("cli_export.format_json"))
        format_btn.clicked.connect(lambda: self._format_preview_for("codex"))
        header.addWidget(format_btn)

        export_btn = PrimaryPushButton(FIF.SEND, tr("cli_export.export"), preview_frame)
        export_btn.setFixedWidth(80)
        export_btn.clicked.connect(lambda: self._on_single_export("codex"))
        header.addWidget(export_btn)

        preview_layout.addLayout(header)

        # 子标签页
        self.codex_sub_pivot = Pivot(preview_frame)
        self.codex_sub_pivot.addItem(routeKey="auth", text="auth.json")
        self.codex_sub_pivot.addItem(routeKey="config", text="config.toml")
        self.codex_sub_pivot.setCurrentItem("auth")
        preview_layout.addWidget(self.codex_sub_pivot)

        self.codex_sub_stack = QStackedWidget(preview_frame)

        self.codex_auth_text = PlainTextEdit(preview_frame)
        self.codex_auth_text.setReadOnly(True)
        self.codex_auth_text.setStyleSheet(
            "PlainTextEdit { font-family: Consolas, Monaco, monospace; font-size: 11px; background: rgba(20,20,20,0.9); color: #ABB2BF; border: none; border-radius: 4px; padding: 6px; }"
        )
        self.codex_sub_stack.addWidget(self.codex_auth_text)

        self.codex_config_text = PlainTextEdit(preview_frame)
        self.codex_config_text.setReadOnly(True)
        self.codex_config_text.setStyleSheet(
            "PlainTextEdit { font-family: Consolas, Monaco, monospace; font-size: 11px; background: rgba(20,20,20,0.9); color: #ABB2BF; border: none; border-radius: 4px; padding: 6px; }"
        )
        self.codex_sub_stack.addWidget(self.codex_config_text)

        self.codex_sub_pivot.currentItemChanged.connect(
            lambda k: self.codex_sub_stack.setCurrentIndex(0 if k == "auth" else 1)
        )
        preview_layout.addWidget(self.codex_sub_stack, 1)

        self._highlighters["codex_auth"] = ConfigSyntaxHighlighter(
            self.codex_auth_text.document(), "json"
        )
        self._highlighters["codex_config"] = ConfigSyntaxHighlighter(
            self.codex_config_text.document(), "toml"
        )

        layout.addWidget(preview_frame, 1)
        return widget

    def _create_gemini_tab_widget(self, parent) -> QWidget:
        """创建 Gemini CLI 标签页"""
        widget = QWidget(parent)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(8)

        # 模型配置
        model_frame = QFrame(widget)
        model_frame.setStyleSheet(
            "QFrame { background: rgba(128,128,128,0.05); border: 1px solid rgba(128,128,128,0.1); border-radius: 6px; }"
        )
        model_layout = QVBoxLayout(model_frame)
        model_layout.setContentsMargins(12, 8, 12, 8)
        model_layout.setSpacing(6)

        model_title = StrongBodyLabel(tr("cli_export.export_config_title"), model_frame)
        model_layout.addWidget(model_title)

        # Base URL 行
        url_row = QHBoxLayout()
        url_row.setSpacing(8)
        url_row.addWidget(CaptionLabel(tr("cli_export.base_url") + ":", model_frame))
        self.gemini_base_url_edit = LineEdit(model_frame)
        self.gemini_base_url_edit.setPlaceholderText(
            tr("cli_export.from_provider_config")
        )
        self.gemini_base_url_edit.setFixedHeight(28)
        self.gemini_base_url_edit.textChanged.connect(lambda: self._update_preview())
        url_row.addWidget(self.gemini_base_url_edit, 1)
        model_layout.addLayout(url_row)

        # 可编辑下拉框样式
        editable_combo_style = """
            QComboBox {
                background-color: rgba(128, 128, 128, 0.1);
                border: 1px solid rgba(128, 128, 128, 0.2);
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
                color: #e6edf3;
            }
            QComboBox:hover {
                border-color: rgba(128, 128, 128, 0.4);
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                border: 1px solid rgba(128, 128, 128, 0.3);
                selection-background-color: rgba(33, 150, 243, 0.3);
                color: #e6edf3;
            }
            QComboBox QAbstractItemView::item {
                color: #e6edf3;
                padding: 4px 8px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: rgba(128, 128, 128, 0.2);
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: rgba(33, 150, 243, 0.3);
            }
        """

        # 模型选择行
        model_row = QHBoxLayout()
        model_row.setSpacing(12)

        model_row.addWidget(CaptionLabel(tr("cli_export.model") + ":", model_frame))
        self.gemini_model_combo = QNativeComboBox(model_frame)
        self.gemini_model_combo.setFixedSize(200, 30)
        self.gemini_model_combo.setEditable(True)
        self.gemini_model_combo.setStyleSheet(editable_combo_style)
        self.gemini_model_combo.currentTextChanged.connect(
            lambda t: self._on_model_changed("gemini", t)
        )
        model_row.addWidget(self.gemini_model_combo)

        hint = CaptionLabel(tr("cli_export.model_hint_simple"), model_frame)
        hint.setStyleSheet("color: #666;")
        model_row.addWidget(hint)

        model_row.addStretch()

        self.gemini_common_check = CheckBox(
            tr("cli_export.write_common_config"), model_frame
        )
        self.gemini_common_check.stateChanged.connect(
            lambda s: self._on_common_config_toggle("gemini", s == Qt.Checked)
        )
        model_row.addWidget(self.gemini_common_check)

        edit_btn = HyperlinkButton("", tr("cli_export.edit"), model_frame)
        edit_btn.clicked.connect(lambda: self._edit_common_config("gemini"))
        model_row.addWidget(edit_btn)

        model_layout.addLayout(model_row)
        layout.addWidget(model_frame)

        # 配置预览 (双文件)
        preview_frame = QFrame(widget)
        preview_frame.setStyleSheet(
            "QFrame { background: rgba(128,128,128,0.05); border: 1px solid rgba(128,128,128,0.1); border-radius: 6px; }"
        )
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setContentsMargins(12, 8, 12, 8)
        preview_layout.setSpacing(4)

        header = QHBoxLayout()
        header.addWidget(
            StrongBodyLabel(tr("cli_export.preview_title_codex"), preview_frame)
        )
        header.addStretch()

        format_btn = ToolButton(FIF.ALIGNMENT, preview_frame)
        format_btn.setToolTip(tr("cli_export.format_json"))
        format_btn.clicked.connect(lambda: self._format_preview_for("gemini"))
        header.addWidget(format_btn)

        export_btn = PrimaryPushButton(FIF.SEND, tr("cli_export.export"), preview_frame)
        export_btn.setFixedWidth(80)
        export_btn.clicked.connect(lambda: self._on_single_export("gemini"))
        header.addWidget(export_btn)

        preview_layout.addLayout(header)

        # 子标签页
        self.gemini_sub_pivot = Pivot(preview_frame)
        self.gemini_sub_pivot.addItem(routeKey="env", text=".env")
        self.gemini_sub_pivot.addItem(routeKey="settings", text="settings.json")
        self.gemini_sub_pivot.setCurrentItem("env")
        preview_layout.addWidget(self.gemini_sub_pivot)

        self.gemini_sub_stack = QStackedWidget(preview_frame)

        self.gemini_env_text = PlainTextEdit(preview_frame)
        self.gemini_env_text.setReadOnly(True)
        self.gemini_env_text.setStyleSheet(
            "PlainTextEdit { font-family: Consolas, Monaco, monospace; font-size: 11px; background: rgba(20,20,20,0.9); color: #ABB2BF; border: none; border-radius: 4px; padding: 6px; }"
        )
        self.gemini_sub_stack.addWidget(self.gemini_env_text)

        self.gemini_settings_text = PlainTextEdit(preview_frame)
        self.gemini_settings_text.setReadOnly(True)
        self.gemini_settings_text.setStyleSheet(
            "PlainTextEdit { font-family: Consolas, Monaco, monospace; font-size: 11px; background: rgba(20,20,20,0.9); color: #ABB2BF; border: none; border-radius: 4px; padding: 6px; }"
        )
        self.gemini_sub_stack.addWidget(self.gemini_settings_text)

        self.gemini_sub_pivot.currentItemChanged.connect(
            lambda k: self.gemini_sub_stack.setCurrentIndex(0 if k == "env" else 1)
        )
        preview_layout.addWidget(self.gemini_sub_stack, 1)

        self._highlighters["gemini_env"] = ConfigSyntaxHighlighter(
            self.gemini_env_text.document(), "env"
        )
        self._highlighters["gemini_settings"] = ConfigSyntaxHighlighter(
            self.gemini_settings_text.document(), "json"
        )

        layout.addWidget(preview_frame, 1)
        return widget

    def _on_main_tab_changed(self, route_key: str):
        """主标签页切换"""
        tab_index = {"claude": 0, "codex": 1, "gemini": 2}.get(route_key, 0)
        self.main_stack.setCurrentIndex(tab_index)
        self._update_preview()

    def _format_preview_for(self, cli_type: str):
        """格式化指定 CLI 的预览"""
        if cli_type == "claude":
            text = self.claude_preview_text.toPlainText()
            try:
                data = json.loads(text)
                self.claude_preview_text.setPlainText(
                    json.dumps(data, indent=2, ensure_ascii=False)
                )
            except:
                pass
        elif cli_type == "codex":
            text = self.codex_auth_text.toPlainText()
            try:
                data = json.loads(text)
                self.codex_auth_text.setPlainText(
                    json.dumps(data, indent=2, ensure_ascii=False)
                )
            except:
                pass
        elif cli_type == "gemini":
            text = self.gemini_settings_text.toPlainText()
            try:
                data = json.loads(text)
                self.gemini_settings_text.setPlainText(
                    json.dumps(data, indent=2, ensure_ascii=False)
                )
            except:
                pass

    def _refresh_providers(self):
        """刷新 Provider 列表"""
        self.provider_combo.clear()
        providers = self.main_window.opencode_config.get("provider", {})

        if not providers:
            self.provider_combo.addItem(tr("cli_export.no_provider"))
            return

        for name in providers.keys():
            self.provider_combo.addItem(name)

        # 选择第一个
        if self.provider_combo.count() > 0:
            self.provider_combo.setCurrentIndex(0)

    def _on_provider_changed(self, provider_name: str):
        """Provider 选择变更"""
        if not provider_name or provider_name == tr("cli_export.no_provider"):
            self._selected_provider = None
            self._selected_provider_name = None
            self._update_config_status(None)
            self._update_models([])
            # 清空 base_url 输入框
            self.claude_base_url_edit.setText("")
            self.codex_base_url_edit.setText("")
            self.gemini_base_url_edit.setText("")
            return

        # 显示检测中状态
        self.config_status_label.setText(tr("cli_export.detecting_config"))
        self.config_status_label.setStyleSheet("color: #FFA726; font-weight: bold;")
        self.fix_config_btn.setVisible(False)
        # 移除 processEvents 调用，避免阻塞
        # QApplication.processEvents()

        providers = self.main_window.opencode_config.get("provider", {})
        provider = providers.get(provider_name, {})
        self._selected_provider = provider
        self._selected_provider_name = provider_name

        # 更新 base_url 输入框 - 从 Provider 配置获取
        base_url = provider.get("baseURL", "") or provider.get("options", {}).get(
            "baseURL", ""
        )
        self.claude_base_url_edit.setText(base_url)
        self.codex_base_url_edit.setText(base_url)
        self.gemini_base_url_edit.setText(base_url)

        # 延迟更新配置状态（模拟检测过程）
        QTimer.singleShot(300, lambda: self._update_config_status(provider))

        # 更新 Model 列表 - 从 provider.models 中获取
        models = provider.get("models", {})
        model_list = []
        for model_id, model_config in models.items():
            model_name = model_config.get("name", model_id)
            model_list.append((model_id, model_name))

        self._update_models(model_list)
        self._update_preview()

    def _update_config_status(self, provider: Optional[Dict]):
        """更新配置完整性状态"""
        if provider is None:
            self.config_status_label.setText("")
            self.config_status_label.setStyleSheet("")
            self.fix_config_btn.setVisible(False)
            return

        # 验证 Provider 配置
        result = self.export_manager.validate_provider(provider)

        if result.valid:
            self.config_status_label.setText(tr("cli_export.config_complete"))
            self.config_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            self.fix_config_btn.setVisible(False)
        else:
            error_text = "✗ " + ", ".join(result.errors[:2])
            self.config_status_label.setText(error_text)
            self.config_status_label.setStyleSheet("color: #F44336; font-weight: bold;")
            self.fix_config_btn.setVisible(True)

    def _update_models(self, model_list: List[Tuple[str, str]]):
        """更新所有 Model 下拉框"""
        # 更新 Claude 的 4 个模型下拉框
        for combo in [
            self.claude_main_model_combo,
            self.claude_haiku_combo,
            self.claude_sonnet_combo,
            self.claude_opus_combo,
        ]:
            combo.clear()
            combo.addItem(tr("cli_export.leave_empty"), "")
            for model_id, model_name in model_list:
                display_text = model_name if model_name != model_id else model_id
                combo.addItem(display_text, model_id)

        # 更新 Codex 和 Gemini 的模型下拉框
        for combo in [self.codex_model_combo, self.gemini_model_combo]:
            combo.clear()
            if not model_list:
                combo.addItem(tr("cli_export.no_model"), "")
            else:
                for model_id, model_name in model_list:
                    display_text = model_name if model_name != model_id else model_id
                    combo.addItem(display_text, model_id)

        # 设置默认选择
        if self.codex_model_combo.count() > 0:
            self.codex_model_combo.setCurrentIndex(0)
        if self.gemini_model_combo.count() > 0:
            self.gemini_model_combo.setCurrentIndex(0)

    def _on_claude_model_changed(self, field: str, text: str):
        """Claude 模型选择变更 - 支持自定义输入"""
        # 直接更新预览，使用 ComboBox 的当前文本
        self._update_preview()

    def _on_model_changed(self, cli_type: str, text: str):
        """Codex/Gemini Model 选择变更 - 支持自定义输入"""
        # 直接更新预览，使用 ComboBox 的当前文本
        self._update_preview()

    def _refresh_cli_status(self):
        """刷新 CLI 工具检测状态"""
        # 先显示检测中状态
        for cli_type, chip in [
            ("claude", self.claude_chip),
            ("codex", self.codex_chip),
            ("gemini", self.gemini_chip),
        ]:
            chip.setText(f"{cli_type.capitalize()} ⏳")
            chip.setStyleSheet(
                "padding: 2px 6px; border-radius: 8px; background: rgba(255,167,38,0.3); font-size: 11px; color: #FFA726;"
            )

        # 执行检测
        self._cli_status = self.export_manager.detect_cli_tools()

        # 更新状态显示
        chip_map = {
            "claude": self.claude_chip,
            "codex": self.codex_chip,
            "gemini": self.gemini_chip,
        }
        for cli_type, status in self._cli_status.items():
            chip = chip_map.get(cli_type)
            if chip:
                if status.installed:
                    chip.setText(f"{cli_type.capitalize()} ✓")
                    chip.setStyleSheet(
                        "padding: 2px 6px; border-radius: 8px; background: rgba(76,175,80,0.3); font-size: 11px; color: #4CAF50;"
                    )
                else:
                    chip.setText(f"{cli_type.capitalize()} ✗")
                    chip.setStyleSheet(
                        "padding: 2px 6px; border-radius: 8px; background: rgba(158,158,158,0.3); font-size: 11px; color: #9E9E9E;"
                    )

        # 更新备份信息
        self._update_backup_info()

    def _update_backup_info(self):
        """更新备份信息显示"""
        all_backups = []
        for cli_type in ["claude", "codex", "gemini"]:
            backups = self.export_manager.backup_manager.list_backups(cli_type)
            all_backups.extend(backups)

        if all_backups:
            # 按时间排序，取最新的
            all_backups.sort(key=lambda x: x.created_at, reverse=True)
            latest = all_backups[0]
            time_str = latest.created_at.strftime("%Y-%m-%d %H:%M:%S")
            self.backup_info_label.setText(
                tr(
                    "cli_export.latest_backup",
                    time_str=time_str,
                    cli_type=latest.cli_type,
                )
            )
        else:
            self.backup_info_label.setText(tr("cli_export.latest_backup_none"))

    def _update_preview(self):
        """更新配置预览"""
        if self._selected_provider is None:
            # 清空所有预览
            self.claude_preview_text.setPlainText(
                tr("cli_export.select_provider_first")
            )
            self.codex_auth_text.setPlainText(tr("cli_export.select_provider_first"))
            self.codex_config_text.setPlainText(tr("cli_export.select_provider_first"))
            self.gemini_env_text.setPlainText(tr("cli_export.select_provider_first"))
            self.gemini_settings_text.setPlainText(
                tr("cli_export.select_provider_first")
            )
            return

        try:
            generator = self.export_manager.config_generator

            # 创建临时 provider 副本，使用用户输入的 base_url
            claude_provider = dict(self._selected_provider)
            claude_base_url = self.claude_base_url_edit.text().strip()
            if claude_base_url:
                claude_provider["baseURL"] = claude_base_url

            codex_provider = dict(self._selected_provider)
            codex_base_url = self.codex_base_url_edit.text().strip()
            if codex_base_url:
                codex_provider["baseURL"] = codex_base_url

            gemini_provider = dict(self._selected_provider)
            gemini_base_url = self.gemini_base_url_edit.text().strip()
            if gemini_base_url:
                gemini_provider["baseURL"] = gemini_base_url

            # 获取用户输入的模型（支持自定义输入）
            # 如果是tr("cli_export.leave_empty")则视为空字符串
            DEFAULT_PLACEHOLDER = tr("cli_export.leave_empty")
            claude_main_model = self.claude_main_model_combo.currentText().strip()
            if claude_main_model == DEFAULT_PLACEHOLDER:
                claude_main_model = ""
            claude_haiku_model = self.claude_haiku_combo.currentText().strip()
            if claude_haiku_model == DEFAULT_PLACEHOLDER:
                claude_haiku_model = ""
            claude_sonnet_model = self.claude_sonnet_combo.currentText().strip()
            if claude_sonnet_model == DEFAULT_PLACEHOLDER:
                claude_sonnet_model = ""
            claude_opus_model = self.claude_opus_combo.currentText().strip()
            if claude_opus_model == DEFAULT_PLACEHOLDER:
                claude_opus_model = ""

            # 更新 Claude 预览
            claude_config = generator.generate_claude_config(
                claude_provider, claude_main_model if claude_main_model else None
            )
            # 添加额外的模型映射（仅当有值时才添加）
            if claude_haiku_model:
                claude_config["env"]["ANTHROPIC_DEFAULT_HAIKU_MODEL"] = (
                    claude_haiku_model
                )
            if claude_sonnet_model:
                claude_config["env"]["ANTHROPIC_DEFAULT_SONNET_MODEL"] = (
                    claude_sonnet_model
                )
            if claude_opus_model:
                claude_config["env"]["ANTHROPIC_DEFAULT_OPUS_MODEL"] = claude_opus_model

            claude_preview = json.dumps(claude_config, indent=2, ensure_ascii=False)
            self.claude_preview_text.setPlainText(claude_preview)

            # 获取 Codex 模型（支持自定义输入）
            codex_model = self.codex_model_combo.currentText().strip()

            # 更新 Codex 预览
            auth = generator.generate_codex_auth(codex_provider)
            config_toml = generator.generate_codex_config(codex_provider, codex_model)
            self.codex_auth_text.setPlainText(
                json.dumps(auth, indent=2, ensure_ascii=False)
            )
            self.codex_config_text.setPlainText(config_toml)

            # 获取 Gemini 模型（支持自定义输入）
            gemini_model = self.gemini_model_combo.currentText().strip()

            # 更新 Gemini 预览
            env_map = generator.generate_gemini_env(gemini_provider, gemini_model)
            settings = generator.generate_gemini_settings()
            env_content = "\n".join(f"{k}={v}" for k, v in env_map.items())
            self.gemini_env_text.setPlainText(env_content)
            self.gemini_settings_text.setPlainText(
                json.dumps(settings, indent=2, ensure_ascii=False)
            )

        except Exception as e:
            error_msg = tr("cli_export.preview_generation_failed", e=str(e))
            self.claude_preview_text.setPlainText(error_msg)
            self.codex_auth_text.setPlainText(error_msg)
            self.codex_config_text.setPlainText(error_msg)
            self.gemini_env_text.setPlainText(error_msg)
            self.gemini_settings_text.setPlainText(error_msg)

    def _on_common_config_toggle(self, cli_type: str, checked: bool):
        """通用配置开关切换"""
        self._use_common_config[cli_type] = checked

    def _edit_common_config(self, cli_type: str):
        """编辑通用配置"""
        dialog = CommonConfigEditDialog(
            cli_type, self._common_config_snippets.get(cli_type, ""), self
        )
        if dialog.exec_() == QDialog.Accepted:
            self._common_config_snippets[cli_type] = dialog.get_config()
            InfoBar.success(
                title=tr("cli_export.save_success"),
                content=tr("cli_export.common_config_updated"),
                parent=self,
                duration=2000,
            )

    def _on_single_export(self, cli_type: str):
        """单个 CLI 工具导出"""
        if self._selected_provider is None:
            self.show_error(
                tr("cli_export.export_failed"), tr("cli_export.select_provider_first")
            )
            return

        # 验证配置
        result = self.export_manager.validate_provider(self._selected_provider)
        if not result.valid:
            self.show_error(
                tr("cli_export.config_incomplete"), "\n".join(result.errors)
            )
            return

        # 创建临时 provider 副本，使用用户输入的 base_url
        export_provider = dict(self._selected_provider)

        if cli_type == "claude":
            base_url = self.claude_base_url_edit.text().strip()
            model = self.claude_main_model_combo.currentText().strip()
        elif cli_type == "codex":
            base_url = self.codex_base_url_edit.text().strip()
            model = self.codex_model_combo.currentText().strip()
        elif cli_type == "gemini":
            base_url = self.gemini_base_url_edit.text().strip()
            model = self.gemini_model_combo.currentText().strip()
        else:
            self.show_error(
                tr("cli_export.export_failed"),
                tr("cli_export.unknown_cli_type", cli_type=cli_type),
            )
            return

        if base_url:
            export_provider["baseURL"] = base_url

        try:
            if cli_type == "claude":
                export_result = self.export_manager.export_to_claude(
                    export_provider, model
                )
            elif cli_type == "codex":
                export_result = self.export_manager.export_to_codex(
                    export_provider, model
                )
            elif cli_type == "gemini":
                export_result = self.export_manager.export_to_gemini(
                    export_provider, model
                )

            if export_result.success:
                files_str = ", ".join(str(f.name) for f in export_result.files_written)
                self.show_success(
                    tr("cli_export.export_success"),
                    tr(
                        "cli_export.exported_to",
                        cli_type=cli_type.upper(),
                        files_str=files_str,
                    ),
                )
                self._update_backup_info()
            else:
                self.show_error(
                    tr("cli_export.export_failed"),
                    export_result.error_message or tr("cli_export.unknown_error"),
                )
                # 尝试恢复备份
                if export_result.backup_path:
                    self.export_manager.backup_manager.restore_backup(
                        export_result.backup_path, cli_type
                    )
                    self.show_warning(
                        tr("cli_export.restored"), tr("cli_export.auto_restored")
                    )
        except Exception as e:
            self.show_error("导出失败", str(e))

    def _on_batch_export(self):
        """批量导出"""
        if self._selected_provider is None:
            self.show_error(
                tr("cli_export.export_failed"), tr("cli_export.select_provider_first")
            )
            return

        # 验证配置
        result = self.export_manager.validate_provider(self._selected_provider)
        if not result.valid:
            self.show_error(
                tr("cli_export.config_incomplete"), "\n".join(result.errors)
            )
            return

        # 获取已安装的 CLI 工具
        cli_status = self.export_manager.detect_cli_tools()
        targets = [
            cli_type for cli_type, status in cli_status.items() if status.installed
        ]

        if not targets:
            self.show_warning(
                tr("cli_export.no_available_targets"), tr("cli_export.no_cli_detected")
            )
            return

        # 为每个 CLI 工具创建带有用户输入 base_url 的 provider 副本
        # 并获取用户输入的模型
        models = {
            "claude": self.claude_main_model_combo.currentText().strip(),
            "codex": self.codex_model_combo.currentText().strip(),
            "gemini": self.gemini_model_combo.currentText().strip(),
        }

        # 执行批量导出 - 逐个导出以使用各自的 base_url
        results = []
        for cli_type in targets:
            export_provider = dict(self._selected_provider)
            if cli_type == "claude":
                base_url = self.claude_base_url_edit.text().strip()
            elif cli_type == "codex":
                base_url = self.codex_base_url_edit.text().strip()
            elif cli_type == "gemini":
                base_url = self.gemini_base_url_edit.text().strip()
            else:
                base_url = ""

            if base_url:
                export_provider["baseURL"] = base_url

            try:
                if cli_type == "claude":
                    export_result = self.export_manager.export_to_claude(
                        export_provider, models.get("claude", "")
                    )
                elif cli_type == "codex":
                    export_result = self.export_manager.export_to_codex(
                        export_provider, models.get("codex", "")
                    )
                elif cli_type == "gemini":
                    export_result = self.export_manager.export_to_gemini(
                        export_provider, models.get("gemini", "")
                    )
                else:
                    continue
                results.append(export_result)
            except Exception as e:
                results.append(ExportResult.fail(cli_type, str(e)))

        # 统计结果
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful

        # 显示结果
        if failed == 0:
            self.show_success(
                tr("cli_export.batch_export_success"),
                tr("cli_export.exported_to_count", successful=successful),
            )
        else:
            failed_msgs = [r.error_message for r in results if not r.success]
            self.show_warning(
                tr("cli_export.partial_export_failed"),
                tr(
                    "cli_export.success_failed_count",
                    successful=successful,
                    failed=failed,
                )
                + "\n"
                + "\n".join(failed_msgs[:3]),
            )

        self._update_backup_info()

    def _go_to_provider_edit(self):
        """跳转到 Provider 编辑页面"""
        # 切换到 Provider 页面
        self.main_window.switchTo(self.main_window.provider_page)

    def _view_backups(self):
        """查看备份"""
        backup_dir = self.export_manager.backup_manager.backup_dir
        if backup_dir.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(backup_dir)))
        else:
            self.show_warning(
                tr("cli_export.no_backup"), tr("cli_export.backup_dir_not_exist")
            )

    def _restore_backup(self):
        """恢复备份"""
        # 显示备份选择对话框
        dialog = CLIBackupRestoreDialog(self.export_manager.backup_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            self.show_success(
                tr("cli_export.restore_success"), tr("cli_export.backup_restored")
            )
            self._refresh_cli_status()


class CLIBackupRestoreDialog(QDialog):
    """CLI 备份恢复对话框"""

    def __init__(self, backup_manager: CLIBackupManager, parent=None):
        super().__init__(parent)
        self.backup_manager = backup_manager
        self.setWindowTitle("恢复备份")
        self.setMinimumSize(500, 400)
        self._setup_ui()
        self._load_backups()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # 说明
        layout.addWidget(BodyLabel(tr("backup.select_backup")))

        # 备份列表
        self.backup_table = TableWidget(self)
        self.backup_table.setColumnCount(3)
        self.backup_table.setHorizontalHeaderLabels(
            [tr("backup.cli_type"), tr("backup.backup_time"), tr("backup.file")]
        )
        header = self.backup_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        self.backup_table.setColumnWidth(0, 100)
        self.backup_table.setColumnWidth(1, 160)
        self.backup_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.backup_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.backup_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.backup_table)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = PushButton(tr("common.cancel"), self)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        restore_btn = PrimaryPushButton(tr("backup.restore"), self)
        restore_btn.clicked.connect(self._on_restore)
        btn_layout.addWidget(restore_btn)

        layout.addLayout(btn_layout)

    def _load_backups(self):
        """加载备份列表"""
        all_backups = []
        for cli_type in ["claude", "codex", "gemini"]:
            backups = self.backup_manager.list_backups(cli_type)
            all_backups.extend(backups)

        # 按时间排序
        all_backups.sort(key=lambda x: x.created_at, reverse=True)

        self.backup_table.setRowCount(len(all_backups))
        self._backups = all_backups

        for row, backup in enumerate(all_backups):
            self.backup_table.setItem(row, 0, QTableWidgetItem(backup.cli_type))
            self.backup_table.setItem(
                row,
                1,
                QTableWidgetItem(backup.created_at.strftime("%Y-%m-%d %H:%M:%S")),
            )
            self.backup_table.setItem(row, 2, QTableWidgetItem(", ".join(backup.files)))

    def _on_restore(self):
        """执行恢复"""
        selected = self.backup_table.selectedItems()
        if not selected:
            return

        row = selected[0].row()
        backup = self._backups[row]

        try:
            success = self.backup_manager.restore_backup(backup.path, backup.cli_type)
            if success:
                self.accept()
            else:
                InfoBar.error(title="恢复失败", content="无法恢复备份", parent=self)
        except Exception as e:
            InfoBar.error(title="恢复失败", content=str(e), parent=self)


class CommonConfigEditDialog(QDialog):
    """通用配置编辑对话框"""

    def __init__(self, cli_type: str, initial_config: str = "", parent=None):
        super().__init__(parent)
        self.cli_type = cli_type
        self.initial_config = initial_config
        self.setWindowTitle(f"编辑 {cli_type.upper()} 通用配置")
        self.setMinimumSize(600, 450)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # 说明
        if self.cli_type == "codex":
            hint_text = (
                "编辑 Codex 通用配置 (TOML 格式)，这些配置会合并到 config.toml 中"
            )
            placeholder = """# 示例通用配置
model_reasoning_effort = "high"
disable_response_storage = true

[history]
persistence = true
max_entries = 1000"""
            language = "toml"
        else:  # gemini
            hint_text = "编辑 Gemini 通用配置 (ENV 格式)，这些配置会合并到 .env 文件中"
            placeholder = """# 示例通用配置
GEMINI_TIMEOUT=30000
GEMINI_MAX_RETRIES=3"""
            language = "env"

        layout.addWidget(BodyLabel(hint_text))

        # 配置编辑器
        self.config_edit = PlainTextEdit(self)
        self.config_edit.setPlainText(self.initial_config or placeholder)
        self.config_edit.setMinimumHeight(300)
        self.config_edit.setStyleSheet("""
            PlainTextEdit {
                font-family: "Consolas", "Monaco", "Courier New", monospace;
                font-size: 12px;
                background-color: rgba(30, 30, 30, 0.9);
                color: #ABB2BF;
                border: 1px solid rgba(128, 128, 128, 0.3);
                border-radius: 6px;
                padding: 8px;
            }
        """)
        layout.addWidget(self.config_edit)

        # 添加语法高亮
        self._highlighter = ConfigSyntaxHighlighter(
            self.config_edit.document(), language
        )

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = PushButton(tr("common.cancel"), self)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = PrimaryPushButton(tr("common.save"), self)
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def get_config(self) -> str:
        """获取编辑后的配置"""
        return self.config_edit.toPlainText()


# ==================== Import 页面 ====================
class ImportPage(BasePage):
    """外部配置导入页面"""

    def __init__(self, main_window, parent=None):
        super().__init__(tr("import.title"), parent)
        self.main_window = main_window
        self.import_service = ImportService()
        self._last_converted: Optional[Dict[str, Any]] = None
        self._setup_ui()

    def _setup_ui(self):
        # 检测到的配置卡片
        detect_card = self.add_card(tr("cli_export.detected_configs"))
        detect_card.setStyleSheet(
            "SimpleCardWidget { background-color: transparent; border: none; }"
        )
        detect_layout = detect_card.layout()

        # 刷新按钮
        refresh_btn = PrimaryPushButton(
            FIF.SYNC, tr("cli_export.refresh_detection"), detect_card
        )
        refresh_btn.clicked.connect(self._refresh_scan)
        detect_layout.addWidget(refresh_btn)

        # 手动选择文件
        manual_layout = QHBoxLayout()
        manual_layout.addWidget(BodyLabel(tr("import.manual_select"), detect_card))
        self.manual_source_combo = ComboBox(detect_card)
        self.manual_source_combo.addItems(
            [
                "Claude Code Settings",
                "Claude Providers",
                "Codex Config",
                "Gemini Config",
                "CC-Switch Config",
            ]
        )
        manual_layout.addWidget(self.manual_source_combo)

        manual_btn = PushButton(FIF.FOLDER, tr("common.select_file"), detect_card)
        manual_btn.clicked.connect(self._select_manual_file)
        manual_layout.addWidget(manual_btn)
        manual_layout.addStretch()
        detect_layout.addLayout(manual_layout)

        # 配置列表
        self.config_table = TableWidget(detect_card)
        self.config_table.setColumnCount(3)
        self.config_table.setHorizontalHeaderLabels(
            [tr("import.source"), tr("import.config_path"), tr("import.status")]
        )
        # 设置列宽：第一列25字符，第三列15字符，第二列自动填充
        header = self.config_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        self.config_table.setColumnWidth(0, 180)  # 约25字符
        self.config_table.setColumnWidth(2, 100)  # 约15字符
        self.config_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.config_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.config_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.config_table.itemSelectionChanged.connect(self._on_select)
        self.config_table.setMinimumHeight(320)
        self.config_table.setMaximumHeight(520)
        detect_layout.addWidget(self.config_table)

        # 预览卡片
        preview_card = self.add_card(tr("import.preview_card_title"))
        preview_card.setStyleSheet(
            "SimpleCardWidget { background-color: transparent; border: none; }"
        )
        preview_layout = preview_card.layout()
        preview_layout.addWidget(
            BodyLabel(tr("import.preview_card_description"), preview_card)
        )
        preview_layout = preview_card.layout()
        preview_layout.addWidget(
            BodyLabel("点击“预览转换”在弹窗中查看左右对照。", preview_card)
        )

        # 按钮
        btn_layout = QHBoxLayout()

        preview_btn = PushButton(tr("import.preview_convert"), preview_card)
        preview_btn.clicked.connect(self._preview_convert)
        btn_layout.addWidget(preview_btn)

        import_btn = PrimaryPushButton(tr("import.import_to_opencode"), preview_card)
        import_btn.clicked.connect(self._import_selected)
        btn_layout.addWidget(import_btn)

        confirm_btn = PushButton(tr("import.confirm_mapping"), preview_card)
        confirm_btn.clicked.connect(self._confirm_mapping)
        btn_layout.addWidget(confirm_btn)

        btn_layout.addStretch()
        preview_layout.addLayout(btn_layout)

        self._layout.addStretch()

        # 初始扫描
        self._refresh_scan()

    def _refresh_scan(self):
        """刷新扫描外部配置"""
        self.config_table.setRowCount(0)
        results = self.import_service.scan_external_configs()

        for key, info in results.items():
            row = self.config_table.rowCount()
            self.config_table.insertRow(row)
            self.config_table.setItem(row, 0, QTableWidgetItem(key))
            path_item = QTableWidgetItem(info["path"])
            path_item.setToolTip(info["path"])
            self.config_table.setItem(row, 1, path_item)
            status = tr("import.detected") if info["exists"] else "未找到"
            self.config_table.setItem(row, 2, QTableWidgetItem(status))

    def _select_manual_file(self):
        """手动选择配置文件"""
        source = self.manual_source_combo.currentText()
        if not source:
            return

        file_filter = tr("import.config_files")
        path, _ = QFileDialog.getOpenFileName(
            self, tr("import.select_config_file"), "", file_filter
        )
        if not path:
            return

        source_map = {
            "Claude Code Settings": "claude",
            "Claude Providers": "claude_providers",
            "Codex Config": "codex",
            "Gemini Config": "gemini",
            "CC-Switch Config": "ccswitch",
        }
        source_key = source_map.get(source)
        if not source_key:
            return

        ConfigPaths.set_import_path(source_key, Path(path))
        self._refresh_scan()

    def _on_select(self):
        """选中配置时记录当前选择"""
        row = self.config_table.currentRow()
        if row < 0:
            return

        self._last_converted = None

    def _preview_convert(self):
        """预览转换结果"""
        row = self.config_table.currentRow()
        if row < 0:
            self.show_warning(tr("common.info"), tr("import.select_config_to_convert"))
            return

        source = self.config_table.item(row, 0).text()
        results = self.import_service.scan_external_configs()

        if source in results and results[source]["data"]:
            source_type = results[source].get("type", "")
            converted = self.import_service.convert_to_opencode(
                source_type, results[source]["data"]
            )
            if not converted:
                self.show_warning(
                    self.tr("common.info"), self.tr("common.cannot_convert_format")
                )
                return

            import json

            self._last_converted = converted

            dialog = BaseDialog(self)
            dialog.setWindowTitle("配置转换预览")
            dialog.setMinimumSize(900, 520)

            layout = QVBoxLayout(dialog)
            layout.setSpacing(12)

            columns_layout = QHBoxLayout()
            columns_layout.setSpacing(12)

            left_layout = QVBoxLayout()
            left_layout.addWidget(SubtitleLabel("原始配置", dialog))
            source_edit = TextEdit(dialog)
            source_edit.setReadOnly(True)
            source_edit.setPlainText(
                json.dumps(results[source]["data"], indent=2, ensure_ascii=False)
            )
            left_layout.addWidget(source_edit)

            right_layout = QVBoxLayout()
            right_layout.addWidget(SubtitleLabel(tr("import.converted_config"), dialog))
            convert_edit = TextEdit(dialog)
            convert_edit.setReadOnly(True)
            convert_edit.setPlainText(
                json.dumps(converted, indent=2, ensure_ascii=False)
            )
            right_layout.addWidget(convert_edit)

            is_dark = isDarkTheme()
            dialog._preview_highlighters = [
                JsonTomlHighlighter(
                    source_edit.document(), is_dark, prefer_toml=source_type == "codex"
                ),
                JsonTomlHighlighter(convert_edit.document(), is_dark),
            ]

            def update_source_match():
                apply_bracket_match_highlight(source_edit, is_dark)

            def update_convert_match():
                apply_bracket_match_highlight(convert_edit, is_dark)

            source_edit.cursorPositionChanged.connect(update_source_match)
            convert_edit.cursorPositionChanged.connect(update_convert_match)
            update_source_match()
            update_convert_match()

            columns_layout.addLayout(left_layout, 1)
            columns_layout.addLayout(right_layout, 1)
            layout.addLayout(columns_layout, 1)

            close_btn = PrimaryPushButton("关闭", dialog)
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn, alignment=Qt.AlignRight)

            dialog.exec_()
        else:
            self.show_warning(
                self.tr("common.info"), self.tr("common.config_not_exist_or_empty")
            )

    def _import_selected(self):
        """导入选中的配置"""
        row = self.config_table.currentRow()
        if row < 0:
            self.show_warning(tr("common.info"), "请先选择要导入的配置")
            return

        source = self.config_table.item(row, 0).text()
        results = self.import_service.scan_external_configs()

        if source not in results or not results[source]["data"]:
            self.show_warning(
                self.tr("common.info"), self.tr("common.config_not_exist_or_empty")
            )
            return

        source_type = results[source].get("type", "")
        converted = self.import_service.convert_to_opencode(
            source_type, results[source]["data"]
        )

        if not converted:
            self.show_warning(
                self.tr("common.info"), self.tr("common.cannot_convert_format")
            )
            return

        # 打开确认映射对话框
        dialog = ImportMappingDialog(self.main_window, converted, parent=self)
        if not dialog.exec_():
            return
        confirmed = dialog.get_confirmed_config()
        if not confirmed:
            self.show_warning(
                self.tr("common.info"), self.tr("common.no_valid_import_config")
            )
            return

        self._apply_import(source, confirmed)

    def _apply_import(self, source: str, converted: Dict[str, Any]):
        """应用导入配置"""
        # 确认导入
        provider_count = len(converted.get("provider", {}))
        perm_count = len(converted.get("permission", {}))

        w = FluentMessageBox(
            "确认导入",
            f"将导入以下配置:\n• Provider: {provider_count} 个\n• 权限: {perm_count} 个\n\n是否继续?",
            self,
        )
        if not w.exec_():
            return

        # 合并配置
        config = self.main_window.opencode_config
        if config is None:
            config = {}
            self.main_window.opencode_config = config

        for provider_name, provider_data in converted.get("provider", {}).items():
            if provider_name in config.get("provider", {}):
                w2 = FluentMessageBox(
                    "冲突", f'Provider "{provider_name}" 已存在，是否覆盖?', self
                )
                if not w2.exec_():
                    continue
            config.setdefault("provider", {})[provider_name] = provider_data

        for tool, perm in converted.get("permission", {}).items():
            config.setdefault("permission", {})[tool] = perm

        # 保存
        if self.main_window.save_opencode_config():
            self.show_success(
                self.tr("common.success"),
                self.tr("import.config_imported", source=source),
            )

    def _confirm_mapping(self):
        """手动确认映射"""
        if not self._last_converted:
            self.show_warning(tr("common.info"), "请先预览转换结果")
            return
        dialog = ImportMappingDialog(
            self.main_window, self._last_converted, parent=self
        )
        if not dialog.exec_():
            return
        confirmed = dialog.get_confirmed_config()
        if not confirmed:
            self.show_warning(
                self.tr("common.info"), self.tr("common.no_valid_import_config")
            )
            return
        self._apply_import("手动确认", confirmed)


# ==================== Backup 对话框 ====================
class ImportMappingDialog(BaseDialog):
    """导入映射确认对话框（仅必需字段）"""

    def __init__(self, main_window, converted: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.converted = converted or {}
        self._confirmed: Dict[str, Any] = {}

        self.setWindowTitle("确认导入映射")
        self.setMinimumWidth(560)
        self.setFixedHeight(520)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        layout.addWidget(SubtitleLabel("请确认必要字段", self))

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll_container = QWidget(scroll)
        scroll_layout = QVBoxLayout(scroll_container)
        scroll_layout.setSpacing(12)
        scroll_layout.setContentsMargins(0, 0, 0, 0)

        providers = self.converted.get("provider", {})
        if not providers:
            scroll_layout.addWidget(
                BodyLabel(tr("import.no_provider_detected"), scroll_container)
            )
        else:
            self.provider_edits = {}
            for provider_key, provider_data in providers.items():
                card = SimpleCardWidget(scroll_container)
                card_layout = QVBoxLayout(card)
                card_layout.setSpacing(8)

                card_layout.addWidget(
                    StrongBodyLabel(f"Provider: {provider_key}", card)
                )

                name_layout = QHBoxLayout()
                name_layout.addWidget(BodyLabel(tr("model.model_name") + ":", card))
                name_edit = LineEdit(card)
                name_edit.setText(provider_data.get("name", ""))
                name_layout.addWidget(name_edit)
                card_layout.addLayout(name_layout)

                key_layout = QHBoxLayout()
                key_layout.addWidget(BodyLabel(tr("cli_export.api_key") + ":", card))
                key_edit = LineEdit(card)
                key_edit.setText(provider_data.get("options", {}).get("apiKey", ""))
                key_layout.addWidget(key_edit)
                card_layout.addLayout(key_layout)

                url_layout = QHBoxLayout()
                url_layout.addWidget(BodyLabel("BaseURL:", card))
                url_edit = LineEdit(card)
                url_edit.setText(provider_data.get("options", {}).get("baseURL", ""))
                url_layout.addWidget(url_edit)
                card_layout.addLayout(url_layout)

                self.provider_edits[provider_key] = {
                    "name": name_edit,
                    "apiKey": key_edit,
                    "baseURL": url_edit,
                }

                scroll_layout.addWidget(card)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_container)
        layout.addWidget(scroll, 1)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = PushButton(tr("common.cancel"), self)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        ok_btn = PrimaryPushButton("确认导入", self)
        ok_btn.clicked.connect(self._on_confirm)
        btn_layout.addWidget(ok_btn)

        layout.addLayout(btn_layout)

    def _on_confirm(self):
        providers = {}
        for provider_key, edits in getattr(self, "provider_edits", {}).items():
            name = edits["name"].text().strip()
            api_key = edits["apiKey"].text().strip()
            base_url = edits["baseURL"].text().strip()
            if not name and not api_key and not base_url:
                continue
            original = self.converted.get("provider", {}).get(provider_key, {})
            providers[provider_key] = {
                "npm": original.get("npm", ""),
                "name": name,
                "options": {
                    "apiKey": api_key,
                    "baseURL": base_url,
                },
                "models": original.get("models", {}),
            }

        self._confirmed = {
            "provider": providers,
            "permission": self.converted.get("permission", {}),
        }
        self.accept()

    def get_confirmed_config(self) -> Dict[str, Any]:
        return self._confirmed


class BackupDialog(BaseDialog):
    """备份恢复对话框"""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.backup_manager = main_window.backup_manager

        self.setWindowTitle(tr("backup.title"))
        self.setMinimumSize(600, 400)
        self._setup_ui()
        self._load_backups()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # 工具栏
        toolbar = QHBoxLayout()

        backup_opencode_btn = PrimaryPushButton(
            FIF.SAVE, tr("backup.backup_opencode"), self
        )
        backup_opencode_btn.clicked.connect(self._backup_opencode)
        toolbar.addWidget(backup_opencode_btn)

        backup_ohmy_btn = PushButton(FIF.SAVE, tr("backup.backup_ohmyopencode"), self)
        backup_ohmy_btn.clicked.connect(self._backup_ohmyopencode)
        toolbar.addWidget(backup_ohmy_btn)

        toolbar.addStretch()

        refresh_btn = PushButton(FIF.SYNC, tr("backup.refresh"), self)
        refresh_btn.clicked.connect(self._load_backups)
        toolbar.addWidget(refresh_btn)

        open_dir_btn = PushButton(FIF.FOLDER, tr("backup.open_backup_dir"), self)
        open_dir_btn.clicked.connect(self._open_backup_dir)
        toolbar.addWidget(open_dir_btn)

        preview_btn = PushButton(FIF.VIEW, tr("backup.preview_content"), self)
        preview_btn.clicked.connect(self._preview_backup)
        toolbar.addWidget(preview_btn)

        layout.addLayout(toolbar)

        # 备份列表
        layout.addWidget(SubtitleLabel(tr("backup.backup_list"), self))

        self.backup_table = TableWidget(self)
        self.backup_table.setColumnCount(4)
        self.backup_table.setHorizontalHeaderLabels(
            [
                tr("backup.config_file"),
                tr("backup.time"),
                tr("backup.tag"),
                tr("backup.path"),
            ]
        )
        # 设置列宽：配置文件固定，时间固定，标签增大，路径自适应
        header = self.backup_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.resizeSection(0, 150)  # 配置文件列 120 → 150
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.resizeSection(1, 160)  # 时间列 150 → 160
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.resizeSection(2, 120)  # 标签列 80 → 120（增大以完整显示）
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # 路径列自适应

        self.backup_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.backup_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.backup_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.backup_table)

        # 操作按钮
        btn_layout = QHBoxLayout()

        restore_btn = PrimaryPushButton(tr("backup.restore_selected"), self)
        restore_btn.clicked.connect(self._restore_backup)
        btn_layout.addWidget(restore_btn)

        delete_btn = PushButton(FIF.DELETE, tr("backup.delete_backup"), self)
        delete_btn.clicked.connect(self._delete_backup)
        btn_layout.addWidget(delete_btn)

        btn_layout.addStretch()

        close_btn = PushButton(tr("backup.close"), self)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _load_backups(self):
        """加载备份列表"""
        self.backup_table.setRowCount(0)
        backups = self.backup_manager.list_backups()

        for backup in backups:
            row = self.backup_table.rowCount()
            self.backup_table.insertRow(row)
            self.backup_table.setItem(row, 0, QTableWidgetItem(backup["name"]))
            self.backup_table.setItem(row, 1, QTableWidgetItem(backup["timestamp"]))
            self.backup_table.setItem(row, 2, QTableWidgetItem(backup["tag"]))

            # 路径列：显示完整路径，设置 tooltip
            path_str = str(backup["path"])
            path_item = QTableWidgetItem(path_str)
            path_item.setToolTip(path_str)  # 鼠标悬停显示完整路径
            self.backup_table.setItem(row, 3, path_item)

    def _backup_opencode(self):
        """备份 OpenCode 配置"""
        path = self.backup_manager.backup(
            ConfigPaths.get_opencode_config(), tag="manual"
        )
        if path:
            InfoBar.success(
                tr("common.success"), tr("backup.backed_up_to", path=path), parent=self
            )
            self._load_backups()
        else:
            InfoBar.error(tr("common.error"), tr("dialog.backup_failed"), parent=self)

    def _backup_ohmyopencode(self):
        """备份 Oh My OpenCode 配置"""
        path = self.backup_manager.backup(
            ConfigPaths.get_ohmyopencode_config(), tag="manual"
        )
        if path:
            InfoBar.success(
                tr("common.success"), tr("backup.backed_up_to", path=path), parent=self
            )
            self._load_backups()
        else:
            InfoBar.error(tr("common.error"), tr("dialog.backup_failed"), parent=self)

    def _open_backup_dir(self):
        """打开备份目录"""
        backup_dir = str(self.backup_manager.backup_dir)
        if backup_dir:
            QDesktopServices.openUrl(QUrl.fromLocalFile(backup_dir))

    def _preview_backup(self):
        """预览选中备份内容"""
        row = self.backup_table.currentRow()
        if row < 0:
            InfoBar.warning(
                tr("common.hint"), tr("dialog.select_backup_first"), parent=self
            )
            return
        backup_path = Path(self.backup_table.item(row, 3).text())
        if not backup_path.exists():
            InfoBar.error(
                tr("common.error"), tr("dialog.backup_file_not_exist"), parent=self
            )
            return
        try:
            with open(backup_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            InfoBar.error("错误", f"无法读取备份内容: {e}", parent=self)
            return

        dialog = BaseDialog(self)
        dialog.setWindowTitle("备份内容预览")
        dialog.setMinimumSize(700, 500)
        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)
        text_edit = TextEdit(dialog)
        text_edit.setReadOnly(True)
        text_edit.setPlainText(content)
        layout.addWidget(text_edit)
        close_btn = PrimaryPushButton("关闭", dialog)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        dialog.exec_()

    def _restore_backup(self):
        """恢复备份"""
        row = self.backup_table.currentRow()
        if row < 0:
            InfoBar.warning(
                tr("common.hint"), tr("dialog.select_backup_first"), parent=self
            )
            return

        backup_path = Path(self.backup_table.item(row, 3).text())
        config_name = self.backup_table.item(row, 0).text()

        # 确定目标路径
        if "opencode" in config_name and "oh-my" not in config_name:
            target_path = ConfigPaths.get_opencode_config()
        else:
            target_path = ConfigPaths.get_ohmyopencode_config()

        w = FluentMessageBox(
            "确认恢复",
            f"确定要恢复此备份吗？\n当前配置将被覆盖（会先自动备份）。",
            self,
        )
        if w.exec_():
            if self.backup_manager.restore(backup_path, target_path):
                InfoBar.success(
                    tr("common.success"), tr("dialog.backup_restored"), parent=self
                )
                # 重新加载配置
                if target_path == ConfigPaths.get_opencode_config():
                    self.main_window.opencode_config = ConfigManager.load_json(
                        target_path
                    )
                else:
                    self.main_window.ohmyopencode_config = ConfigManager.load_json(
                        target_path
                    )
            else:
                InfoBar.error(
                    tr("common.error"), tr("dialog.restore_failed"), parent=self
                )

    def _delete_backup(self):
        """删除备份"""
        row = self.backup_table.currentRow()
        if row < 0:
            InfoBar.warning(
                tr("common.hint"), tr("dialog.select_backup_first"), parent=self
            )
            return

        backup_path = Path(self.backup_table.item(row, 3).text())

        w = FluentMessageBox(
            tr("common.confirm_delete_title"), tr("dialog.confirm_delete_backup"), self
        )
        if w.exec_():
            if self.backup_manager.delete_backup(backup_path):
                InfoBar.success(
                    tr("common.success"), tr("dialog.backup_deleted"), parent=self
                )
                self._load_backups()
            else:
                InfoBar.error(
                    tr("common.error"), tr("dialog.delete_failed"), parent=self
                )


# ==================== 程序入口 ====================
def main():
    # 抑制 Qt 字体枚举警告
    import os

    os.environ["QT_LOGGING_RULES"] = "qt.qpa.fonts.warning=false"

    # 启用高DPI支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    app.setApplicationName("OpenCode Config Manager")
    app.setApplicationVersion(APP_VERSION)

    # 在创建窗口前设置深色主题，避免启动闪烁
    setTheme(Theme.DARK)
    setThemeColor("#2979FF")

    # 设置全局字体 - 使用优化后的字体栈
    font = QFont()
    font.setFamilies(
        [
            "-apple-system",
            "BlinkMacSystemFont",
            "Segoe UI",
            "Roboto",
            "Microsoft YaHei UI",
            "微软雅黑",
            "PingFang SC",
        ]
    )
    font.setPointSize(10)
    app.setFont(font)

    # 应用全局样式
    app.setStyleSheet(UIConfig.get_stylesheet())

    window = MainWindow()

    # 确保窗口显示在屏幕上
    window.show()
    window.raise_()
    window.activateWindow()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
