from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional


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
        id="github-copilot",
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
        id="google-vertex",
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
        id="zhipuai",
        name="Zhipu AI (智谱GLM)",
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
                "https://open.bigmodel.cn/api/paas/v4",
            ),
        ],
        env_vars=["ZHIPU_API_KEY"],
        test_endpoint="/models",
    ),
    NativeProviderConfig(
        id="zhipuai-coding-plan",
        name="Zhipu AI Coding Plan (智谱GLM编码套餐)",
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
                "https://open.bigmodel.cn/api/coding/paas/v4",
            ),
        ],
        env_vars=["ZHIPU_API_KEY"],
        test_endpoint="/models",
    ),
    NativeProviderConfig(
        id="zai",
        name="Z.AI",
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
                "https://api.z.ai/api/paas/v4",
            ),
        ],
        env_vars=["ZHIPU_API_KEY"],
        test_endpoint="/models",
    ),
    NativeProviderConfig(
        id="zai-coding-plan",
        name="Z.AI Coding Plan",
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
                "https://api.z.ai/api/coding/paas/v4",
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
        id="moonshot",
        name="Moonshot AI (Kimi)",
        sdk="@ai-sdk/openai-compatible",
        auth_fields=[
            AuthField("apiKey", "API Key", "password", True, ""),
        ],
        option_fields=[
            OptionField(
                "baseURL", "Base URL", "text", [], "https://api.moonshot.cn/v1"
            ),
        ],
        env_vars=["MOONSHOT_API_KEY"],
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
                "baseURL",
                "Base URL",
                "select",
                [
                    "https://api.minimax.io/v1",
                    "https://api.minimaxi.com/v1",
                ],
                "https://api.minimax.io/v1",
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
        "google-vertex": [
            "GOOGLE_APPLICATION_CREDENTIALS",
            "GOOGLE_CLOUD_PROJECT",
            "VERTEX_LOCATION",
        ],
        "deepseek": ["DEEPSEEK_API_KEY"],
        "zhipuai": ["ZHIPU_API_KEY"],
        "zhipuai-coding-plan": ["ZHIPU_API_KEY"],
        "zai": ["ZHIPU_API_KEY"],
        "zai-coding-plan": ["ZHIPU_API_KEY"],
        "qwen": ["DASHSCOPE_API_KEY", "QWEN_API_KEY"],
        "moonshot": ["MOONSHOT_API_KEY"],
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
