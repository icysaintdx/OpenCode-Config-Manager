# -*- coding: utf-8 -*-
"""
OpenCode 配置管理器 v0.9.0 - PyQt5 + QFluentWidgets 版本
完整合并版本

功能特性：
- 服务商配置管理（支持18种预设SDK）
- 模型配置管理（Token限制、上下文窗口、特性支持）
- MCP服务器配置（本地/远程类型）
- Agent管理（自定义Agent、预设模板）
- 权限配置（allow/ask/deny列表、Bash命令权限）
- 分类配置（Temperature滑块、预设分类模板）
- 技能配置（SKILL.md编辑器）
- 规则配置（AGENTS.md编辑器、全局指令）
- 上下文压缩配置
- 导入导出功能
- 备份恢复功能
- 主题切换（明/暗）

依赖：
- PyQt5
- qfluentwidgets

作者: OpenCode Team
版本: 0.9.0
"""

import os
import sys
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

from PyQt5.QtCore import Qt, QSize, pyqtSignal, QUrl, QTimer
from PyQt5.QtGui import QIcon, QFont, QDesktopServices
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QStackedWidget, QLabel, QFrame, QSizePolicy, QSpacerItem,
    QSplitter, QDialog, QDialogButtonBox, QFileDialog
)

from qfluentwidgets import (
    FluentWindow, NavigationInterface, NavigationItemPosition,
    FluentIcon, Theme, setTheme, isDarkTheme,
    InfoBar, InfoBarPosition, MessageBox,
    PushButton, PrimaryPushButton, TransparentPushButton,
    SubtitleLabel, BodyLabel, CaptionLabel, TitleLabel,
    CardWidget, SimpleCardWidget, ElevatedCardWidget,
    ScrollArea, SmoothScrollArea,
    ComboBox, LineEdit, TextEdit, SpinBox, DoubleSpinBox,
    SwitchButton, CheckBox, RadioButton,
    Slider, ProgressBar,
    TableWidget, ListWidget, TreeWidget,
    ToolTipFilter, ToolTipPosition,
    Action, RoundMenu,
    StateToolTip,
    setThemeColor, NavigationAvatarWidget,
    SplashScreen, HyperlinkButton, Dialog
)
from qfluentwidgets import FluentIcon as FIF



# ======================================================================
# Part 1: 常量定义和预设数据
# ======================================================================

# ==================== 版本信息 ====================
VERSION = "0.9.0"
APP_NAME = "OpenCode 配置管理器"
APP_TITLE = f"{APP_NAME} v{VERSION}"

# ==================== 路径常量 ====================
HOME_DIR = Path.home()
OPENCODE_DIR = HOME_DIR / ".opencode"
OPENCODE_JSON = OPENCODE_DIR / "opencode.json"
AGENTS_MD = OPENCODE_DIR / "AGENTS.md"
SKILL_MD = OPENCODE_DIR / "SKILL.md"
BACKUP_DIR = OPENCODE_DIR / "backups"

# ==================== 预设SDK配置 ====================
PRESET_SDKS = {
    "OpenAI": {
        "name": "openai",
        "env_key": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo", "o1", "o1-mini", "o1-preview", "o3-mini"]
    },
    "Anthropic": {
        "name": "anthropic",
        "env_key": "ANTHROPIC_API_KEY",
        "base_url": "https://api.anthropic.com",
        "models": ["claude-sonnet-4-20250514", "claude-3-7-sonnet-20250219", "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"]
    },
    "Google": {
        "name": "google",
        "env_key": "GOOGLE_API_KEY",
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "models": ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-pro", "gemini-1.5-flash"]
    },
    "Azure OpenAI": {
        "name": "azure",
        "env_key": "AZURE_OPENAI_API_KEY",
        "base_url": "",
        "models": ["gpt-4o", "gpt-4-turbo", "gpt-35-turbo"]
    },
    "Groq": {
        "name": "groq",
        "env_key": "GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1",
        "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"]
    },
    "OpenRouter": {
        "name": "openrouter",
        "env_key": "OPENROUTER_API_KEY",
        "base_url": "https://openrouter.ai/api/v1",
        "models": ["anthropic/claude-sonnet-4", "openai/gpt-4o", "google/gemini-2.0-flash-exp:free"]
    },
    "DeepSeek": {
        "name": "deepseek",
        "env_key": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com/v1",
        "models": ["deepseek-chat", "deepseek-reasoner"]
    },
    "Mistral": {
        "name": "mistral",
        "env_key": "MISTRAL_API_KEY",
        "base_url": "https://api.mistral.ai/v1",
        "models": ["mistral-large-latest", "mistral-medium-latest", "mistral-small-latest"]
    },
    "xAI": {
        "name": "xai",
        "env_key": "XAI_API_KEY",
        "base_url": "https://api.x.ai/v1",
        "models": ["grok-beta", "grok-2", "grok-2-mini"]
    },
    "Ollama": {
        "name": "ollama",
        "env_key": "",
        "base_url": "http://localhost:11434/v1",
        "models": ["llama3.3", "qwen2.5-coder", "deepseek-r1", "codellama"]
    },
    "硅基流动": {
        "name": "siliconflow",
        "env_key": "SILICONFLOW_API_KEY",
        "base_url": "https://api.siliconflow.cn/v1",
        "models": ["Qwen/Qwen2.5-72B-Instruct", "deepseek-ai/DeepSeek-V3", "Pro/deepseek-ai/DeepSeek-R1"]
    },
    "阿里云百炼": {
        "name": "dashscope",
        "env_key": "DASHSCOPE_API_KEY",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "models": ["qwen-max", "qwen-plus", "qwen-turbo", "qwen-coder-plus"]
    },
    "火山引擎": {
        "name": "volcengine",
        "env_key": "ARK_API_KEY",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "models": ["doubao-pro-32k", "doubao-lite-32k"]
    },
    "智谱AI": {
        "name": "zhipu",
        "env_key": "ZHIPU_API_KEY",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "models": ["glm-4-plus", "glm-4", "glm-4-flash"]
    },
    "百度千帆": {
        "name": "qianfan",
        "env_key": "QIANFAN_API_KEY",
        "base_url": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop",
        "models": ["ernie-4.0-8k", "ernie-3.5-8k", "ernie-speed-8k"]
    },
    "腾讯混元": {
        "name": "hunyuan",
        "env_key": "HUNYUAN_API_KEY",
        "base_url": "https://api.hunyuan.cloud.tencent.com/v1",
        "models": ["hunyuan-pro", "hunyuan-standard", "hunyuan-lite"]
    },
    "Moonshot": {
        "name": "moonshot",
        "env_key": "MOONSHOT_API_KEY",
        "base_url": "https://api.moonshot.cn/v1",
        "models": ["moonshot-v1-128k", "moonshot-v1-32k", "moonshot-v1-8k"]
    },
    "零一万物": {
        "name": "lingyiwanwu",
        "env_key": "LINGYIWANWU_API_KEY",
        "base_url": "https://api.lingyiwanwu.com/v1",
        "models": ["yi-large", "yi-medium", "yi-spark"]
    },
    "自定义": {
        "name": "custom",
        "env_key": "",
        "base_url": "",
        "models": []
    }
}

# ==================== 预设模型配置 ====================
PRESET_MODEL_CONFIGS = {
    # OpenAI 系列
    "gpt-4o": {"maxTokens": 16384, "contextWindow": 128000, "supportsImages": True, "supportsComputerUse": False},
    "gpt-4o-mini": {"maxTokens": 16384, "contextWindow": 128000, "supportsImages": True, "supportsComputerUse": False},
    "gpt-4-turbo": {"maxTokens": 4096, "contextWindow": 128000, "supportsImages": True, "supportsComputerUse": False},
    "gpt-4": {"maxTokens": 8192, "contextWindow": 8192, "supportsImages": False, "supportsComputerUse": False},
    "gpt-3.5-turbo": {"maxTokens": 4096, "contextWindow": 16385, "supportsImages": False, "supportsComputerUse": False},
    "o1": {"maxTokens": 100000, "contextWindow": 200000, "supportsImages": True, "supportsComputerUse": False, "reasoning": True},
    "o1-mini": {"maxTokens": 65536, "contextWindow": 128000, "supportsImages": False, "supportsComputerUse": False, "reasoning": True},
    "o1-preview": {"maxTokens": 32768, "contextWindow": 128000, "supportsImages": False, "supportsComputerUse": False, "reasoning": True},
    "o3-mini": {"maxTokens": 100000, "contextWindow": 200000, "supportsImages": True, "supportsComputerUse": False, "reasoning": True},

    # Anthropic 系列
    "claude-sonnet-4-20250514": {"maxTokens": 16000, "contextWindow": 200000, "supportsImages": True, "supportsComputerUse": True},
    "claude-3-7-sonnet-20250219": {"maxTokens": 16000, "contextWindow": 200000, "supportsImages": True, "supportsComputerUse": True},
    "claude-3-5-sonnet-20241022": {"maxTokens": 8192, "contextWindow": 200000, "supportsImages": True, "supportsComputerUse": True},
    "claude-3-5-haiku-20241022": {"maxTokens": 8192, "contextWindow": 200000, "supportsImages": True, "supportsComputerUse": False},
    "claude-3-opus-20240229": {"maxTokens": 4096, "contextWindow": 200000, "supportsImages": True, "supportsComputerUse": False},

    # Google 系列
    "gemini-2.0-flash": {"maxTokens": 8192, "contextWindow": 1000000, "supportsImages": True, "supportsComputerUse": False},
    "gemini-2.0-flash-lite": {"maxTokens": 8192, "contextWindow": 1000000, "supportsImages": True, "supportsComputerUse": False},
    "gemini-1.5-pro": {"maxTokens": 8192, "contextWindow": 2000000, "supportsImages": True, "supportsComputerUse": False},
    "gemini-1.5-flash": {"maxTokens": 8192, "contextWindow": 1000000, "supportsImages": True, "supportsComputerUse": False},

    # DeepSeek 系列
    "deepseek-chat": {"maxTokens": 8192, "contextWindow": 64000, "supportsImages": False, "supportsComputerUse": False},
    "deepseek-reasoner": {"maxTokens": 8192, "contextWindow": 64000, "supportsImages": False, "supportsComputerUse": False, "reasoning": True},

    # 国产模型
    "qwen-max": {"maxTokens": 8192, "contextWindow": 32000, "supportsImages": False, "supportsComputerUse": False},
    "qwen-plus": {"maxTokens": 8192, "contextWindow": 131072, "supportsImages": False, "supportsComputerUse": False},
    "qwen-turbo": {"maxTokens": 8192, "contextWindow": 131072, "supportsImages": False, "supportsComputerUse": False},
    "glm-4-plus": {"maxTokens": 4096, "contextWindow": 128000, "supportsImages": True, "supportsComputerUse": False},
    "glm-4": {"maxTokens": 4096, "contextWindow": 128000, "supportsImages": True, "supportsComputerUse": False},
    "glm-4-flash": {"maxTokens": 4096, "contextWindow": 128000, "supportsImages": True, "supportsComputerUse": False},
}

# ==================== 预设Agent配置 ====================
PRESET_AGENTS = {
    "代码助手": {
        "name": "code-assistant",
        "model": "",
        "description": "专注于代码编写、调试和优化的AI助手",
        "instructions": "你是一个专业的代码助手，擅长编写高质量代码、调试问题和优化性能。"
    },
    "文档专家": {
        "name": "doc-expert",
        "model": "",
        "description": "专注于文档编写和技术写作的AI助手",
        "instructions": "你是一个文档专家，擅长编写清晰、准确的技术文档和用户指南。"
    },
    "架构师": {
        "name": "architect",
        "model": "",
        "description": "专注于系统设计和架构规划的AI助手",
        "instructions": "你是一个系统架构师，擅长设计可扩展、高性能的系统架构。"
    },
    "测试工程师": {
        "name": "tester",
        "model": "",
        "description": "专注于测试策略和质量保证的AI助手",
        "instructions": "你是一个测试工程师，擅长编写测试用例、发现bug和确保代码质量。"
    },
    "DevOps专家": {
        "name": "devops",
        "model": "",
        "description": "专注于CI/CD和运维自动化的AI助手",
        "instructions": "你是一个DevOps专家，擅长配置CI/CD流水线、容器化部署和运维自动化。"
    }
}

# ==================== 分类预设 ====================
CATEGORY_PRESETS = {
    "代码生成": {"temperature": 0.3, "description": "适合生成结构化代码，保持一致性"},
    "代码审查": {"temperature": 0.2, "description": "适合严格的代码审查，减少随机性"},
    "创意写作": {"temperature": 0.8, "description": "适合创意内容，增加多样性"},
    "技术文档": {"temperature": 0.4, "description": "适合技术文档，平衡准确性和可读性"},
    "问答对话": {"temperature": 0.5, "description": "适合一般对话，平衡准确性和自然度"},
    "数据分析": {"temperature": 0.1, "description": "适合数据分析，最大化准确性"},
    "头脑风暴": {"temperature": 0.9, "description": "适合创意发散，最大化多样性"},
}

# ==================== 权限预设 ====================
PERMISSION_MODES = {
    "allow": "允许 - 自动执行，无需确认",
    "ask": "询问 - 每次执行前询问用户",
    "deny": "拒绝 - 禁止执行此操作"
}

BASH_COMMAND_MODES = {
    "allow": "允许所有命令",
    "ask": "每次询问",
    "deny": "拒绝所有命令",
    "allowlist": "仅允许白名单命令"
}

# ==================== Tooltip提示 ====================
TOOLTIPS = {
    # Provider相关
    "provider_name": "服务商名称，用于在配置中标识此服务商",
    "provider_api_key": "API密钥，用于身份验证。支持直接填写密钥或使用环境变量格式 ${ENV_VAR}",
    "provider_base_url": "API基础URL，不同服务商有不同的端点地址",
    "provider_disabled": "禁用此服务商，禁用后将不会使用此服务商的模型",

    # Model相关
    "model_id": "模型ID，用于API调用时指定使用的模型",
    "model_max_tokens": "最大输出Token数，限制模型单次回复的最大长度",
    "model_context_window": "上下文窗口大小，模型能处理的最大输入Token数",
    "model_supports_images": "是否支持图像输入，启用后可以处理图片",
    "model_supports_computer_use": "是否支持计算机使用功能（Anthropic特有）",
    "model_reasoning": "是否为推理模型，推理模型会显示思考过程",
    "model_options": "模型选项，如temperature、top_p等参数",
    "model_variants": "模型变体，用于A/B测试或特定场景的模型配置",

    # Thinking相关
    "thinking_enabled": "启用思考模式，模型会显示推理过程",
    "thinking_budget": "思考预算Token数，限制思考过程的长度",
    "thinking_type": "思考类型：enabled(启用)、disabled(禁用)",

    # MCP相关
    "mcp_name": "MCP服务器名称，用于标识此服务器",
    "mcp_type": "服务器类型：local(本地进程)、remote(远程SSE)",
    "mcp_command": "启动命令，用于启动本地MCP服务器",
    "mcp_args": "命令参数，传递给启动命令的参数列表",
    "mcp_url": "远程服务器URL，用于连接远程MCP服务器",
    "mcp_env": "环境变量，传递给MCP服务器的环境变量",
    "mcp_timeout": "超时时间（秒），等待服务器响应的最大时间",

    # Agent相关
    "agent_mode": "Agent模式：auto(自动)、manual(手动)、hybrid(混合)",
    "agent_temperature": "温度参数，控制输出的随机性，0-1之间",
    "agent_max_steps": "最大步骤数，限制Agent执行的最大步骤",
    "agent_tools": "可用工具列表，Agent可以调用的工具",
    "agent_permission": "权限设置，控制Agent的操作权限",

    # Permission相关
    "permission_allow": "允许：自动执行，无需用户确认",
    "permission_ask": "询问：每次执行前询问用户确认",
    "permission_deny": "拒绝：禁止执行此操作",
    "permission_bash": "Bash命令权限，控制命令行操作的权限",

    # Compaction相关
    "compaction_enabled": "启用自动压缩，当上下文过长时自动压缩历史消息",
    "compaction_threshold": "压缩阈值，超过此Token数时触发压缩",
    "compaction_trim_old": "修剪旧输出，移除较早的输出以节省空间",

    # 其他
    "category_temperature": "分类温度，不同任务类型使用不同的温度设置",
    "skill_permission": "技能权限，控制技能的执行权限",
    "rules_instructions": "规则指令，自定义AI的行为规则",
}

# ==================== 默认配置模板 ====================
DEFAULT_CONFIG = {
    "providers": {},
    "models": {},
    "mcpServers": {},
    "agents": {},
    "permissions": {
        "allow": [],
        "ask": [],
        "deny": []
    },
    "compaction": {
        "enabled": False,
        "threshold": 100000,
        "trimOldOutput": False
    }
}


# ======================================================================
# Part 2: 服务类
# ======================================================================

class ConfigPaths:
    """配置文件路径管理"""

    def __init__(self):
        self.home = Path.home()
        self.opencode_dir = self.home / ".opencode"
        self.config_file = self.opencode_dir / "opencode.json"
        self.agents_md = self.opencode_dir / "AGENTS.md"
        self.skill_md = self.opencode_dir / "SKILL.md"
        self.backup_dir = self.opencode_dir / "backups"

    def ensure_dirs(self):
        """确保必要的目录存在"""
        self.opencode_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def config_exists(self) -> bool:
        """检查配置文件是否存在"""
        return self.config_file.exists()

    def get_external_configs(self) -> List[Dict[str, Any]]:
        """获取外部配置文件列表"""
        external_configs = []

        # 检查常见的配置文件位置
        locations = [
            (self.home / ".claude" / "claude.json", "Claude CLI"),
            (self.home / ".config" / "opencode" / "config.json", "OpenCode XDG"),
            (Path(os.environ.get("APPDATA", "")) / "opencode" / "config.json", "OpenCode AppData"),
        ]

        for path, name in locations:
            if path.exists():
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    external_configs.append({
                        "path": str(path),
                        "name": name,
                        "data": data,
                        "size": path.stat().st_size,
                        "modified": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                    })
                except Exception:
                    pass

        return external_configs


class ConfigManager:
    """配置文件管理器"""

    def __init__(self, paths: ConfigPaths):
        self.paths = paths
        self._config: Dict[str, Any] = {}
        self._dirty = False

    def load(self) -> Dict[str, Any]:
        """加载配置文件"""
        if self.paths.config_file.exists():
            try:
                with open(self.paths.config_file, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
            except Exception as e:
                print(f"加载配置失败: {e}")
                self._config = self._get_default_config()
        else:
            self._config = self._get_default_config()

        self._dirty = False
        return self._config

    def save(self) -> bool:
        """保存配置文件"""
        try:
            self.paths.ensure_dirs()
            with open(self.paths.config_file, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            self._dirty = False
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value

    def set(self, key: str, value: Any):
        """设置配置项"""
        keys = key.split(".")
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self._dirty = True

    def delete(self, key: str) -> bool:
        """删除配置项"""
        keys = key.split(".")
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                return False
            config = config[k]
        if keys[-1] in config:
            del config[keys[-1]]
            self._dirty = True
            return True
        return False

    def is_dirty(self) -> bool:
        """检查是否有未保存的更改"""
        return self._dirty

    def get_config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self._config

    def set_config(self, config: Dict[str, Any]):
        """设置完整配置"""
        self._config = config
        self._dirty = True

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "providers": {},
            "models": {},
            "mcpServers": {},
            "agents": {},
            "permissions": {
                "allow": [],
                "ask": [],
                "deny": []
            },
            "compaction": {
                "enabled": False,
                "threshold": 100000,
                "trimOldOutput": False
            }
        }

    # Provider 操作
    def get_providers(self) -> Dict[str, Any]:
        """获取所有服务商"""
        return self._config.get("providers", {})

    def get_provider(self, name: str) -> Optional[Dict[str, Any]]:
        """获取指定服务商"""
        return self._config.get("providers", {}).get(name)

    def add_provider(self, name: str, config: Dict[str, Any]):
        """添加服务商"""
        if "providers" not in self._config:
            self._config["providers"] = {}
        self._config["providers"][name] = config
        self._dirty = True

    def update_provider(self, name: str, config: Dict[str, Any]):
        """更新服务商"""
        if "providers" in self._config and name in self._config["providers"]:
            self._config["providers"][name] = config
            self._dirty = True

    def delete_provider(self, name: str) -> bool:
        """删除服务商"""
        if "providers" in self._config and name in self._config["providers"]:
            del self._config["providers"][name]
            self._dirty = True
            return True
        return False

    # Model 操作
    def get_models(self) -> Dict[str, Any]:
        """获取所有模型"""
        return self._config.get("models", {})

    def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        """获取指定模型"""
        return self._config.get("models", {}).get(model_id)

    def add_model(self, model_id: str, config: Dict[str, Any]):
        """添加模型"""
        if "models" not in self._config:
            self._config["models"] = {}
        self._config["models"][model_id] = config
        self._dirty = True

    def update_model(self, model_id: str, config: Dict[str, Any]):
        """更新模型"""
        if "models" in self._config and model_id in self._config["models"]:
            self._config["models"][model_id] = config
            self._dirty = True

    def delete_model(self, model_id: str) -> bool:
        """删除模型"""
        if "models" in self._config and model_id in self._config["models"]:
            del self._config["models"][model_id]
            self._dirty = True
            return True
        return False

    # MCP Server 操作
    def get_mcp_servers(self) -> Dict[str, Any]:
        """获取所有MCP服务器"""
        return self._config.get("mcpServers", {})

    def get_mcp_server(self, name: str) -> Optional[Dict[str, Any]]:
        """获取指定MCP服务器"""
        return self._config.get("mcpServers", {}).get(name)

    def add_mcp_server(self, name: str, config: Dict[str, Any]):
        """添加MCP服务器"""
        if "mcpServers" not in self._config:
            self._config["mcpServers"] = {}
        self._config["mcpServers"][name] = config
        self._dirty = True

    def update_mcp_server(self, name: str, config: Dict[str, Any]):
        """更新MCP服务器"""
        if "mcpServers" in self._config and name in self._config["mcpServers"]:
            self._config["mcpServers"][name] = config
            self._dirty = True

    def delete_mcp_server(self, name: str) -> bool:
        """删除MCP服务器"""
        if "mcpServers" in self._config and name in self._config["mcpServers"]:
            del self._config["mcpServers"][name]
            self._dirty = True
            return True
        return False

    # Agent 操作
    def get_agents(self) -> Dict[str, Any]:
        """获取所有Agent"""
        return self._config.get("agents", {})

    def get_agent(self, name: str) -> Optional[Dict[str, Any]]:
        """获取指定Agent"""
        return self._config.get("agents", {}).get(name)

    def add_agent(self, name: str, config: Dict[str, Any]):
        """添加Agent"""
        if "agents" not in self._config:
            self._config["agents"] = {}
        self._config["agents"][name] = config
        self._dirty = True

    def update_agent(self, name: str, config: Dict[str, Any]):
        """更新Agent"""
        if "agents" in self._config and name in self._config["agents"]:
            self._config["agents"][name] = config
            self._dirty = True

    def delete_agent(self, name: str) -> bool:
        """删除Agent"""
        if "agents" in self._config and name in self._config["agents"]:
            del self._config["agents"][name]
            self._dirty = True
            return True
        return False

    # Permission 操作
    def get_permissions(self) -> Dict[str, List[str]]:
        """获取权限配置"""
        return self._config.get("permissions", {"allow": [], "ask": [], "deny": []})

    def set_permissions(self, permissions: Dict[str, List[str]]):
        """设置权限配置"""
        self._config["permissions"] = permissions
        self._dirty = True

    # Compaction 操作
    def get_compaction(self) -> Dict[str, Any]:
        """获取压缩配置"""
        return self._config.get("compaction", {"enabled": False, "threshold": 100000, "trimOldOutput": False})

    def set_compaction(self, compaction: Dict[str, Any]):
        """设置压缩配置"""
        self._config["compaction"] = compaction
        self._dirty = True


class BackupManager:
    """备份管理器"""

    def __init__(self, paths: ConfigPaths):
        self.paths = paths
        self.max_backups = 10

    def create_backup(self, description: str = "") -> Optional[str]:
        """创建备份"""
        if not self.paths.config_file.exists():
            return None

        try:
            self.paths.ensure_dirs()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}.json"
            backup_path = self.paths.backup_dir / backup_name

            # 复制配置文件
            shutil.copy2(self.paths.config_file, backup_path)

            # 创建备份元数据
            meta_path = self.paths.backup_dir / f"backup_{timestamp}.meta"
            meta = {
                "timestamp": timestamp,
                "description": description,
                "original_size": self.paths.config_file.stat().st_size
            }
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False)

            # 清理旧备份
            self._cleanup_old_backups()

            return backup_name
        except Exception as e:
            print(f"创建备份失败: {e}")
            return None

    def restore_backup(self, backup_name: str) -> bool:
        """恢复备份"""
        backup_path = self.paths.backup_dir / backup_name
        if not backup_path.exists():
            return False

        try:
            # 先备份当前配置
            self.create_backup("自动备份（恢复前）")

            # 恢复备份
            shutil.copy2(backup_path, self.paths.config_file)
            return True
        except Exception as e:
            print(f"恢复备份失败: {e}")
            return False

    def delete_backup(self, backup_name: str) -> bool:
        """删除备份"""
        backup_path = self.paths.backup_dir / backup_name
        meta_path = self.paths.backup_dir / backup_name.replace(".json", ".meta")

        try:
            if backup_path.exists():
                backup_path.unlink()
            if meta_path.exists():
                meta_path.unlink()
            return True
        except Exception as e:
            print(f"删除备份失败: {e}")
            return False

    def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有备份"""
        backups = []
        if not self.paths.backup_dir.exists():
            return backups

        for backup_file in sorted(self.paths.backup_dir.glob("backup_*.json"), reverse=True):
            meta_file = backup_file.with_suffix(".meta")
            meta = {}
            if meta_file.exists():
                try:
                    with open(meta_file, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                except Exception:
                    pass

            backups.append({
                "name": backup_file.name,
                "path": str(backup_file),
                "size": backup_file.stat().st_size,
                "modified": datetime.fromtimestamp(backup_file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "description": meta.get("description", ""),
                "timestamp": meta.get("timestamp", "")
            })

        return backups

    def _cleanup_old_backups(self):
        """清理旧备份，保留最新的N个"""
        backups = sorted(self.paths.backup_dir.glob("backup_*.json"), reverse=True)
        for backup in backups[self.max_backups:]:
            try:
                backup.unlink()
                meta = backup.with_suffix(".meta")
                if meta.exists():
                    meta.unlink()
            except Exception:
                pass


class ModelRegistry:
    """模型注册表"""

    def __init__(self):
        self._presets = {}
        self._load_presets()

    def _load_presets(self):
        """加载预设模型配置"""
        from part1_constants import PRESET_MODEL_CONFIGS
        self._presets = PRESET_MODEL_CONFIGS.copy()

    def get_preset(self, model_id: str) -> Optional[Dict[str, Any]]:
        """获取预设模型配置"""
        return self._presets.get(model_id)

    def get_all_presets(self) -> Dict[str, Dict[str, Any]]:
        """获取所有预设模型配置"""
        return self._presets.copy()

    def get_models_for_provider(self, provider_name: str) -> List[str]:
        """获取指定服务商的模型列表"""
        from part1_constants import PRESET_SDKS
        for sdk_name, sdk_config in PRESET_SDKS.items():
            if sdk_config["name"] == provider_name:
                return sdk_config.get("models", [])
        return []


class ImportService:
    """导入服务"""

    def __init__(self, config_manager: ConfigManager, paths: ConfigPaths):
        self.config_manager = config_manager
        self.paths = paths

    def detect_external_configs(self) -> List[Dict[str, Any]]:
        """检测外部配置文件"""
        return self.paths.get_external_configs()

    def preview_import(self, external_config: Dict[str, Any]) -> Dict[str, Any]:
        """预览导入内容"""
        data = external_config.get("data", {})
        preview = {
            "providers": list(data.get("providers", {}).keys()),
            "models": list(data.get("models", {}).keys()),
            "mcpServers": list(data.get("mcpServers", {}).keys()),
            "agents": list(data.get("agents", {}).keys()),
            "has_permissions": "permissions" in data,
            "has_compaction": "compaction" in data
        }
        return preview

    def import_config(self, external_config: Dict[str, Any], merge: bool = True) -> bool:
        """导入配置"""
        try:
            data = external_config.get("data", {})

            if merge:
                # 合并模式：保留现有配置，添加新配置
                current = self.config_manager.get_config()

                for key in ["providers", "models", "mcpServers", "agents"]:
                    if key in data:
                        if key not in current:
                            current[key] = {}
                        current[key].update(data[key])

                if "permissions" in data:
                    current["permissions"] = data["permissions"]
                if "compaction" in data:
                    current["compaction"] = data["compaction"]

                self.config_manager.set_config(current)
            else:
                # 覆盖模式：完全替换
                self.config_manager.set_config(data)

            return self.config_manager.save()
        except Exception as e:
            print(f"导入配置失败: {e}")
            return False

    def export_config(self, export_path: str) -> bool:
        """导出配置"""
        try:
            config = self.config_manager.get_config()
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"导出配置失败: {e}")
            return False


class MarkdownFileManager:
    """Markdown文件管理器"""

    def __init__(self, paths: ConfigPaths):
        self.paths = paths

    def read_agents_md(self) -> str:
        """读取AGENTS.md"""
        if self.paths.agents_md.exists():
            try:
                with open(self.paths.agents_md, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                pass
        return ""

    def write_agents_md(self, content: str) -> bool:
        """写入AGENTS.md"""
        try:
            self.paths.ensure_dirs()
            with open(self.paths.agents_md, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"写入AGENTS.md失败: {e}")
            return False

    def read_skill_md(self) -> str:
        """读取SKILL.md"""
        if self.paths.skill_md.exists():
            try:
                with open(self.paths.skill_md, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                pass
        return ""

    def write_skill_md(self, content: str) -> bool:
        """写入SKILL.md"""
        try:
            self.paths.ensure_dirs()
            with open(self.paths.skill_md, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"写入SKILL.md失败: {e}")
            return False


# ======================================================================
# Part 3: 主窗口架构和UI组件
# ======================================================================

class BasePage(ScrollArea):
    """页面基类"""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self._init_ui()

    def _init_ui(self):
        self.setObjectName(self.title.replace(" ", "_"))
        self.setWidgetResizable(True)

        # 创建内容容器
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(36, 20, 36, 20)
        self.content_layout.setSpacing(16)
        self.content_layout.setAlignment(Qt.AlignTop)

        self.setWidget(self.content_widget)

        # 设置样式
        self.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.content_widget.setStyleSheet("background: transparent;")

    def add_title(self, text: str):
        """添加标题"""
        label = SubtitleLabel(text)
        label.setFont(QFont("Microsoft YaHei UI", 18, QFont.Bold))
        self.content_layout.addWidget(label)

    def add_subtitle(self, text: str):
        """添加副标题"""
        label = BodyLabel(text)
        label.setFont(QFont("Microsoft YaHei UI", 12))
        label.setStyleSheet("color: gray;")
        self.content_layout.addWidget(label)

    def add_card(self, widget: QWidget) -> CardWidget:
        """添加卡片"""
        card = CardWidget()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.addWidget(widget)
        self.content_layout.addWidget(card)
        return card

    def add_spacing(self, height: int = 16):
        """添加间距"""
        self.content_layout.addSpacing(height)

    def add_stretch(self):
        """添加弹性空间"""
        self.content_layout.addStretch()

    def show_success(self, title: str, content: str):
        """显示成功提示"""
        InfoBar.success(
            title=title,
            content=content,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )

    def show_error(self, title: str, content: str):
        """显示错误提示"""
        InfoBar.error(
            title=title,
            content=content,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )

    def show_warning(self, title: str, content: str):
        """显示警告提示"""
        InfoBar.warning(
            title=title,
            content=content,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=4000,
            parent=self
        )

    def show_info(self, title: str, content: str):
        """显示信息提示"""
        InfoBar.info(
            title=title,
            content=content,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )


class SettingCard(CardWidget):
    """设置卡片"""

    def __init__(self, icon: FluentIcon, title: str, content: str = "", parent=None):
        super().__init__(parent)
        self.setFixedHeight(70)

        self.h_layout = QHBoxLayout(self)
        self.h_layout.setContentsMargins(16, 12, 16, 12)
        self.h_layout.setSpacing(16)

        # 图标
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(24, 24)
        if icon:
            self.icon_label.setPixmap(icon.icon().pixmap(24, 24))
        self.h_layout.addWidget(self.icon_label)

        # 文本区域
        self.text_layout = QVBoxLayout()
        self.text_layout.setSpacing(2)

        self.title_label = BodyLabel(title)
        self.title_label.setFont(QFont("Microsoft YaHei UI", 11))
        self.text_layout.addWidget(self.title_label)

        if content:
            self.content_label = CaptionLabel(content)
            self.content_label.setStyleSheet("color: gray;")
            self.text_layout.addWidget(self.content_label)

        self.h_layout.addLayout(self.text_layout)
        self.h_layout.addStretch()

    def add_widget(self, widget: QWidget):
        """添加控件到右侧"""
        self.h_layout.addWidget(widget)


class SwitchSettingCard(SettingCard):
    """开关设置卡片"""

    switched = pyqtSignal(bool)

    def __init__(self, icon: FluentIcon, title: str, content: str = "", checked: bool = False, parent=None):
        super().__init__(icon, title, content, parent)
        self.switch = SwitchButton()
        self.switch.setChecked(checked)
        self.switch.checkedChanged.connect(self.switched.emit)
        self.add_widget(self.switch)

    def is_checked(self) -> bool:
        return self.switch.isChecked()

    def set_checked(self, checked: bool):
        self.switch.setChecked(checked)


class ComboBoxSettingCard(SettingCard):
    """下拉框设置卡片"""

    currentIndexChanged = pyqtSignal(int)
    currentTextChanged = pyqtSignal(str)

    def __init__(self, icon: FluentIcon, title: str, content: str = "", items: list = None, parent=None):
        super().__init__(icon, title, content, parent)
        self.combo = ComboBox()
        self.combo.setMinimumWidth(150)
        if items:
            self.combo.addItems(items)
        self.combo.currentIndexChanged.connect(self.currentIndexChanged.emit)
        self.combo.currentTextChanged.connect(self.currentTextChanged.emit)
        self.add_widget(self.combo)

    def current_text(self) -> str:
        return self.combo.currentText()

    def current_index(self) -> int:
        return self.combo.currentIndex()

    def set_current_index(self, index: int):
        self.combo.setCurrentIndex(index)

    def set_current_text(self, text: str):
        self.combo.setCurrentText(text)

    def add_items(self, items: list):
        self.combo.addItems(items)

    def clear(self):
        self.combo.clear()


class SpinBoxSettingCard(SettingCard):
    """数字输入设置卡片"""

    valueChanged = pyqtSignal(int)

    def __init__(self, icon: FluentIcon, title: str, content: str = "",
                 min_val: int = 0, max_val: int = 100, value: int = 0, parent=None):
        super().__init__(icon, title, content, parent)
        self.spin = SpinBox()
        self.spin.setRange(min_val, max_val)
        self.spin.setValue(value)
        self.spin.setMinimumWidth(120)
        self.spin.valueChanged.connect(self.valueChanged.emit)
        self.add_widget(self.spin)

    def value(self) -> int:
        return self.spin.value()

    def set_value(self, value: int):
        self.spin.setValue(value)


class SliderSettingCard(SettingCard):
    """滑块设置卡片"""

    valueChanged = pyqtSignal(int)

    def __init__(self, icon: FluentIcon, title: str, content: str = "",
                 min_val: int = 0, max_val: int = 100, value: int = 0, parent=None):
        super().__init__(icon, title, content, parent)

        self.value_label = BodyLabel(str(value))
        self.value_label.setMinimumWidth(40)
        self.value_label.setAlignment(Qt.AlignCenter)

        self.slider = Slider(Qt.Horizontal)
        self.slider.setRange(min_val, max_val)
        self.slider.setValue(value)
        self.slider.setMinimumWidth(200)
        self.slider.valueChanged.connect(self._on_value_changed)

        self.add_widget(self.slider)
        self.add_widget(self.value_label)

    def _on_value_changed(self, value: int):
        self.value_label.setText(str(value))
        self.valueChanged.emit(value)

    def value(self) -> int:
        return self.slider.value()

    def set_value(self, value: int):
        self.slider.setValue(value)
        self.value_label.setText(str(value))


class LineEditSettingCard(SettingCard):
    """文本输入设置卡片"""

    textChanged = pyqtSignal(str)

    def __init__(self, icon: FluentIcon, title: str, content: str = "",
                 placeholder: str = "", text: str = "", parent=None):
        super().__init__(icon, title, content, parent)
        self.line_edit = LineEdit()
        self.line_edit.setPlaceholderText(placeholder)
        self.line_edit.setText(text)
        self.line_edit.setMinimumWidth(200)
        self.line_edit.textChanged.connect(self.textChanged.emit)
        self.add_widget(self.line_edit)

    def text(self) -> str:
        return self.line_edit.text()

    def set_text(self, text: str):
        self.line_edit.setText(text)


class ButtonSettingCard(SettingCard):
    """按钮设置卡片"""

    clicked = pyqtSignal()

    def __init__(self, icon: FluentIcon, title: str, content: str = "",
                 button_text: str = "操作", parent=None):
        super().__init__(icon, title, content, parent)
        self.button = PushButton(button_text)
        self.button.clicked.connect(self.clicked.emit)
        self.add_widget(self.button)


class PrimaryButtonSettingCard(SettingCard):
    """主要按钮设置卡片"""

    clicked = pyqtSignal()

    def __init__(self, icon: FluentIcon, title: str, content: str = "",
                 button_text: str = "操作", parent=None):
        super().__init__(icon, title, content, parent)
        self.button = PrimaryPushButton(button_text)
        self.button.clicked.connect(self.clicked.emit)
        self.add_widget(self.button)


class FormCard(CardWidget):
    """表单卡片"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.form_layout = QVBoxLayout(self)
        self.form_layout.setContentsMargins(20, 20, 20, 20)
        self.form_layout.setSpacing(16)

    def add_row(self, label_text: str, widget: QWidget, tooltip: str = ""):
        """添加表单行"""
        row_layout = QHBoxLayout()
        row_layout.setSpacing(12)

        label = BodyLabel(label_text)
        label.setMinimumWidth(120)
        if tooltip:
            label.setToolTip(tooltip)
            label.installEventFilter(ToolTipFilter(label, showDelay=300, position=ToolTipPosition.TOP))

        row_layout.addWidget(label)
        row_layout.addWidget(widget, 1)

        self.form_layout.addLayout(row_layout)

    def add_widget(self, widget: QWidget):
        """添加控件"""
        self.form_layout.addWidget(widget)

    def add_spacing(self, height: int = 8):
        """添加间距"""
        self.form_layout.addSpacing(height)

    def add_buttons(self, *buttons):
        """添加按钮组"""
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()
        for btn in buttons:
            btn_layout.addWidget(btn)
        self.form_layout.addLayout(btn_layout)


class ListCard(CardWidget):
    """列表卡片"""

    itemSelected = pyqtSignal(str)
    itemDoubleClicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.v_layout = QVBoxLayout(self)
        self.v_layout.setContentsMargins(0, 0, 0, 0)
        self.v_layout.setSpacing(0)

        # 工具栏
        self.toolbar = QWidget()
        self.toolbar_layout = QHBoxLayout(self.toolbar)
        self.toolbar_layout.setContentsMargins(16, 12, 16, 12)
        self.toolbar_layout.setSpacing(8)
        self.v_layout.addWidget(self.toolbar)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #e0e0e0;")
        line.setFixedHeight(1)
        self.v_layout.addWidget(line)

        # 列表
        self.list_widget = ListWidget()
        self.list_widget.itemClicked.connect(lambda item: self.itemSelected.emit(item.text()))
        self.list_widget.itemDoubleClicked.connect(lambda item: self.itemDoubleClicked.emit(item.text()))
        self.v_layout.addWidget(self.list_widget)

    def add_toolbar_button(self, text: str, icon: FluentIcon = None) -> PushButton:
        """添加工具栏按钮"""
        btn = PushButton(text)
        if icon:
            btn.setIcon(icon)
        self.toolbar_layout.addWidget(btn)
        return btn

    def add_toolbar_stretch(self):
        """添加工具栏弹性空间"""
        self.toolbar_layout.addStretch()

    def add_item(self, text: str):
        """添加列表项"""
        self.list_widget.addItem(text)

    def add_items(self, items: list):
        """添加多个列表项"""
        self.list_widget.addItems(items)

    def clear(self):
        """清空列表"""
        self.list_widget.clear()

    def current_item(self) -> str:
        """获取当前选中项"""
        item = self.list_widget.currentItem()
        return item.text() if item else ""

    def remove_current_item(self):
        """移除当前选中项"""
        row = self.list_widget.currentRow()
        if row >= 0:
            self.list_widget.takeItem(row)

    def count(self) -> int:
        """获取列表项数量"""
        return self.list_widget.count()

    def get_all_items(self) -> list:
        """获取所有列表项"""
        return [self.list_widget.item(i).text() for i in range(self.list_widget.count())]


# ======================================================================
# Part 4: Provider页面和Model页面
# ======================================================================

class ProviderDialog(Dialog):
    """服务商编辑对话框"""

    def __init__(self, parent=None, provider_name: str = "", provider_config: dict = None, presets: dict = None):
        super().__init__("编辑服务商" if provider_name else "添加服务商", "", parent)
        self.provider_name = provider_name
        self.provider_config = provider_config or {}
        self.presets = presets or {}
        self._init_ui()

    def _init_ui(self):
        # 移除默认内容
        self.textLayout.deleteLater()

        # 创建表单
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(16)

        # SDK预设选择
        preset_layout = QHBoxLayout()
        preset_label = BodyLabel("SDK预设:")
        preset_label.setMinimumWidth(100)
        self.preset_combo = ComboBox()
        self.preset_combo.addItem("自定义")
        self.preset_combo.addItems(list(self.presets.keys()))
        self.preset_combo.currentTextChanged.connect(self._on_preset_changed)
        preset_layout.addWidget(preset_label)
        preset_layout.addWidget(self.preset_combo, 1)
        form_layout.addLayout(preset_layout)

        # 名称
        name_layout = QHBoxLayout()
        name_label = BodyLabel("名称:")
        name_label.setMinimumWidth(100)
        self.name_edit = LineEdit()
        self.name_edit.setPlaceholderText("服务商名称")
        self.name_edit.setText(self.provider_name)
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit, 1)
        form_layout.addLayout(name_layout)

        # API Key
        key_layout = QHBoxLayout()
        key_label = BodyLabel("API Key:")
        key_label.setMinimumWidth(100)
        self.key_edit = LineEdit()
        self.key_edit.setPlaceholderText("API密钥或环境变量 ${ENV_VAR}")
        self.key_edit.setText(self.provider_config.get("apiKey", ""))
        key_layout.addWidget(key_label)
        key_layout.addWidget(self.key_edit, 1)
        form_layout.addLayout(key_layout)

        # Base URL
        url_layout = QHBoxLayout()
        url_label = BodyLabel("Base URL:")
        url_label.setMinimumWidth(100)
        self.url_edit = LineEdit()
        self.url_edit.setPlaceholderText("API基础URL")
        self.url_edit.setText(self.provider_config.get("baseUrl", ""))
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_edit, 1)
        form_layout.addLayout(url_layout)

        # 禁用开关
        disabled_layout = QHBoxLayout()
        disabled_label = BodyLabel("禁用:")
        disabled_label.setMinimumWidth(100)
        self.disabled_switch = SwitchButton()
        self.disabled_switch.setChecked(self.provider_config.get("disabled", False))
        disabled_layout.addWidget(disabled_label)
        disabled_layout.addWidget(self.disabled_switch)
        disabled_layout.addStretch()
        form_layout.addLayout(disabled_layout)

        self.vBoxLayout.insertWidget(0, form_widget)
        self.widget.setMinimumWidth(500)

    def _on_preset_changed(self, preset_name: str):
        """预设选择变化"""
        if preset_name in self.presets:
            preset = self.presets[preset_name]
            self.name_edit.setText(preset.get("name", ""))
            self.url_edit.setText(preset.get("base_url", ""))
            env_key = preset.get("env_key", "")
            if env_key:
                self.key_edit.setText(f"${{{env_key}}}")

    def get_data(self) -> tuple:
        """获取表单数据"""
        name = self.name_edit.text().strip()
        config = {
            "apiKey": self.key_edit.text().strip(),
            "baseUrl": self.url_edit.text().strip(),
        }
        if self.disabled_switch.isChecked():
            config["disabled"] = True
        return name, config


class ProviderPage(BasePage):
    """服务商配置页面"""

    def __init__(self, config_manager, presets: dict, parent=None):
        super().__init__("服务商配置", parent)
        self.config_manager = config_manager
        self.presets = presets
        self._init_content()
        self._load_data()

    def _init_content(self):
        self.add_title("服务商配置")
        self.add_subtitle("管理API服务商，配置API密钥和端点地址")
        self.add_spacing(8)

        # 创建分栏布局
        splitter = QSplitter(Qt.Horizontal)

        # 左侧列表
        self.list_card = ListCard()
        self.add_btn = self.list_card.add_toolbar_button("添加", FIF.ADD)
        self.edit_btn = self.list_card.add_toolbar_button("编辑", FIF.EDIT)
        self.delete_btn = self.list_card.add_toolbar_button("删除", FIF.DELETE)
        self.list_card.add_toolbar_stretch()

        self.add_btn.clicked.connect(self._on_add)
        self.edit_btn.clicked.connect(self._on_edit)
        self.delete_btn.clicked.connect(self._on_delete)
        self.list_card.itemDoubleClicked.connect(lambda: self._on_edit())
        self.list_card.itemSelected.connect(self._on_select)

        splitter.addWidget(self.list_card)

        # 右侧详情
        self.detail_card = CardWidget()
        detail_layout = QVBoxLayout(self.detail_card)
        detail_layout.setContentsMargins(20, 20, 20, 20)
        detail_layout.setSpacing(12)

        self.detail_title = SubtitleLabel("选择服务商查看详情")
        detail_layout.addWidget(self.detail_title)

        self.detail_info = QWidget()
        info_layout = QGridLayout(self.detail_info)
        info_layout.setSpacing(8)

        info_layout.addWidget(BodyLabel("名称:"), 0, 0)
        self.info_name = BodyLabel("-")
        info_layout.addWidget(self.info_name, 0, 1)

        info_layout.addWidget(BodyLabel("API Key:"), 1, 0)
        self.info_key = BodyLabel("-")
        info_layout.addWidget(self.info_key, 1, 1)

        info_layout.addWidget(BodyLabel("Base URL:"), 2, 0)
        self.info_url = BodyLabel("-")
        self.info_url.setWordWrap(True)
        info_layout.addWidget(self.info_url, 2, 1)

        info_layout.addWidget(BodyLabel("状态:"), 3, 0)
        self.info_status = BodyLabel("-")
        info_layout.addWidget(self.info_status, 3, 1)

        info_layout.setColumnStretch(1, 1)
        detail_layout.addWidget(self.detail_info)
        detail_layout.addStretch()

        splitter.addWidget(self.detail_card)
        splitter.setSizes([300, 400])

        self.content_layout.addWidget(splitter, 1)

    def _load_data(self):
        """加载数据"""
        self.list_card.clear()
        providers = self.config_manager.get_providers()
        for name in providers.keys():
            self.list_card.add_item(name)

    def _on_select(self, name: str):
        """选择服务商"""
        provider = self.config_manager.get_provider(name)
        if provider:
            self.detail_title.setText(name)
            self.info_name.setText(name)

            api_key = provider.get("apiKey", "")
            if api_key.startswith("${"):
                self.info_key.setText(api_key)
            else:
                self.info_key.setText("*" * 8 if api_key else "-")

            self.info_url.setText(provider.get("baseUrl", "-") or "-")
            self.info_status.setText("已禁用" if provider.get("disabled") else "已启用")

    def _on_add(self):
        """添加服务商"""
        dialog = ProviderDialog(self, presets=self.presets)
        if dialog.exec():
            name, config = dialog.get_data()
            if name:
                self.config_manager.add_provider(name, config)
                self._load_data()
                self.show_success("成功", f"已添加服务商: {name}")
            else:
                self.show_error("错误", "服务商名称不能为空")

    def _on_edit(self):
        """编辑服务商"""
        name = self.list_card.current_item()
        if not name:
            self.show_warning("提示", "请先选择要编辑的服务商")
            return

        provider = self.config_manager.get_provider(name)
        dialog = ProviderDialog(self, name, provider, self.presets)
        if dialog.exec():
            new_name, config = dialog.get_data()
            if new_name:
                if new_name != name:
                    self.config_manager.delete_provider(name)
                self.config_manager.add_provider(new_name, config)
                self._load_data()
                self.show_success("成功", f"已更新服务商: {new_name}")

    def _on_delete(self):
        """删除服务商"""
        name = self.list_card.current_item()
        if not name:
            self.show_warning("提示", "请先选择要删除的服务商")
            return

        box = MessageBox("确认删除", f"确定要删除服务商 '{name}' 吗？", self)
        if box.exec():
            self.config_manager.delete_provider(name)
            self._load_data()
            self.detail_title.setText("选择服务商查看详情")
            self.show_success("成功", f"已删除服务商: {name}")


class ModelDialog(Dialog):
    """模型编辑对话框"""

    def __init__(self, parent=None, model_id: str = "", model_config: dict = None, presets: dict = None):
        super().__init__("编辑模型" if model_id else "添加模型", "", parent)
        self.model_id = model_id
        self.model_config = model_config or {}
        self.presets = presets or {}
        self._init_ui()

    def _init_ui(self):
        self.textLayout.deleteLater()

        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(12)

        # 预设选择
        preset_layout = QHBoxLayout()
        preset_label = BodyLabel("预设模型:")
        preset_label.setMinimumWidth(120)
        self.preset_combo = ComboBox()
        self.preset_combo.addItem("自定义")
        self.preset_combo.addItems(list(self.presets.keys()))
        self.preset_combo.currentTextChanged.connect(self._on_preset_changed)
        preset_layout.addWidget(preset_label)
        preset_layout.addWidget(self.preset_combo, 1)
        form_layout.addLayout(preset_layout)

        # 模型ID
        id_layout = QHBoxLayout()
        id_label = BodyLabel("模型ID:")
        id_label.setMinimumWidth(120)
        self.id_edit = LineEdit()
        self.id_edit.setPlaceholderText("模型标识符")
        self.id_edit.setText(self.model_id)
        id_layout.addWidget(id_label)
        id_layout.addWidget(self.id_edit, 1)
        form_layout.addLayout(id_layout)

        # 最大Token数
        tokens_layout = QHBoxLayout()
        tokens_label = BodyLabel("最大Token数:")
        tokens_label.setMinimumWidth(120)
        self.tokens_spin = SpinBox()
        self.tokens_spin.setRange(1, 1000000)
        self.tokens_spin.setValue(self.model_config.get("maxTokens", 8192))
        tokens_layout.addWidget(tokens_label)
        tokens_layout.addWidget(self.tokens_spin, 1)
        form_layout.addLayout(tokens_layout)

        # 上下文窗口
        context_layout = QHBoxLayout()
        context_label = BodyLabel("上下文窗口:")
        context_label.setMinimumWidth(120)
        self.context_spin = SpinBox()
        self.context_spin.setRange(1, 10000000)
        self.context_spin.setValue(self.model_config.get("contextWindow", 128000))
        context_layout.addWidget(context_label)
        context_layout.addWidget(self.context_spin, 1)
        form_layout.addLayout(context_layout)

        # 支持图像
        images_layout = QHBoxLayout()
        images_label = BodyLabel("支持图像:")
        images_label.setMinimumWidth(120)
        self.images_switch = SwitchButton()
        self.images_switch.setChecked(self.model_config.get("supportsImages", False))
        images_layout.addWidget(images_label)
        images_layout.addWidget(self.images_switch)
        images_layout.addStretch()
        form_layout.addLayout(images_layout)

        # 支持计算机使用
        computer_layout = QHBoxLayout()
        computer_label = BodyLabel("计算机使用:")
        computer_label.setMinimumWidth(120)
        self.computer_switch = SwitchButton()
        self.computer_switch.setChecked(self.model_config.get("supportsComputerUse", False))
        computer_layout.addWidget(computer_label)
        computer_layout.addWidget(self.computer_switch)
        computer_layout.addStretch()
        form_layout.addLayout(computer_layout)

        # 推理模型
        reasoning_layout = QHBoxLayout()
        reasoning_label = BodyLabel("推理模型:")
        reasoning_label.setMinimumWidth(120)
        self.reasoning_switch = SwitchButton()
        self.reasoning_switch.setChecked(self.model_config.get("reasoning", False))
        reasoning_layout.addWidget(reasoning_label)
        reasoning_layout.addWidget(self.reasoning_switch)
        reasoning_layout.addStretch()
        form_layout.addLayout(reasoning_layout)

        self.vBoxLayout.insertWidget(0, form_widget)
        self.widget.setMinimumWidth(500)

    def _on_preset_changed(self, preset_name: str):
        """预设选择变化"""
        if preset_name in self.presets:
            preset = self.presets[preset_name]
            self.id_edit.setText(preset_name)
            self.tokens_spin.setValue(preset.get("maxTokens", 8192))
            self.context_spin.setValue(preset.get("contextWindow", 128000))
            self.images_switch.setChecked(preset.get("supportsImages", False))
            self.computer_switch.setChecked(preset.get("supportsComputerUse", False))
            self.reasoning_switch.setChecked(preset.get("reasoning", False))

    def get_data(self) -> tuple:
        """获取表单数据"""
        model_id = self.id_edit.text().strip()
        config = {
            "maxTokens": self.tokens_spin.value(),
            "contextWindow": self.context_spin.value(),
            "supportsImages": self.images_switch.isChecked(),
            "supportsComputerUse": self.computer_switch.isChecked(),
        }
        if self.reasoning_switch.isChecked():
            config["reasoning"] = True
        return model_id, config


class ModelPage(BasePage):
    """模型配置页面"""

    def __init__(self, config_manager, presets: dict, parent=None):
        super().__init__("模型配置", parent)
        self.config_manager = config_manager
        self.presets = presets
        self._init_content()
        self._load_data()

    def _init_content(self):
        self.add_title("模型配置")
        self.add_subtitle("配置模型参数，包括Token限制、上下文窗口和特性支持")
        self.add_spacing(8)

        # 创建分栏布局
        splitter = QSplitter(Qt.Horizontal)

        # 左侧列表
        self.list_card = ListCard()
        self.add_btn = self.list_card.add_toolbar_button("添加", FIF.ADD)
        self.edit_btn = self.list_card.add_toolbar_button("编辑", FIF.EDIT)
        self.delete_btn = self.list_card.add_toolbar_button("删除", FIF.DELETE)
        self.list_card.add_toolbar_stretch()

        self.add_btn.clicked.connect(self._on_add)
        self.edit_btn.clicked.connect(self._on_edit)
        self.delete_btn.clicked.connect(self._on_delete)
        self.list_card.itemDoubleClicked.connect(lambda: self._on_edit())
        self.list_card.itemSelected.connect(self._on_select)

        splitter.addWidget(self.list_card)

        # 右侧详情
        self.detail_card = CardWidget()
        detail_layout = QVBoxLayout(self.detail_card)
        detail_layout.setContentsMargins(20, 20, 20, 20)
        detail_layout.setSpacing(12)

        self.detail_title = SubtitleLabel("选择模型查看详情")
        detail_layout.addWidget(self.detail_title)

        self.detail_info = QWidget()
        info_layout = QGridLayout(self.detail_info)
        info_layout.setSpacing(8)

        info_layout.addWidget(BodyLabel("模型ID:"), 0, 0)
        self.info_id = BodyLabel("-")
        info_layout.addWidget(self.info_id, 0, 1)

        info_layout.addWidget(BodyLabel("最大Token:"), 1, 0)
        self.info_tokens = BodyLabel("-")
        info_layout.addWidget(self.info_tokens, 1, 1)

        info_layout.addWidget(BodyLabel("上下文窗口:"), 2, 0)
        self.info_context = BodyLabel("-")
        info_layout.addWidget(self.info_context, 2, 1)

        info_layout.addWidget(BodyLabel("支持图像:"), 3, 0)
        self.info_images = BodyLabel("-")
        info_layout.addWidget(self.info_images, 3, 1)

        info_layout.addWidget(BodyLabel("计算机使用:"), 4, 0)
        self.info_computer = BodyLabel("-")
        info_layout.addWidget(self.info_computer, 4, 1)

        info_layout.addWidget(BodyLabel("推理模型:"), 5, 0)
        self.info_reasoning = BodyLabel("-")
        info_layout.addWidget(self.info_reasoning, 5, 1)

        info_layout.setColumnStretch(1, 1)
        detail_layout.addWidget(self.detail_info)

        # Options配置区域
        options_label = SubtitleLabel("Options配置")
        detail_layout.addWidget(options_label)

        self.options_edit = TextEdit()
        self.options_edit.setPlaceholderText('{"temperature": 0.7, "top_p": 0.9}')
        self.options_edit.setMaximumHeight(100)
        detail_layout.addWidget(self.options_edit)

        # Variants配置区域
        variants_label = SubtitleLabel("Variants配置")
        detail_layout.addWidget(variants_label)

        self.variants_edit = TextEdit()
        self.variants_edit.setPlaceholderText('{"fast": {"maxTokens": 4096}}')
        self.variants_edit.setMaximumHeight(100)
        detail_layout.addWidget(self.variants_edit)

        # 保存按钮
        save_btn = PrimaryPushButton("保存Options/Variants")
        save_btn.clicked.connect(self._save_options_variants)
        detail_layout.addWidget(save_btn)

        detail_layout.addStretch()

        splitter.addWidget(self.detail_card)
        splitter.setSizes([300, 500])

        self.content_layout.addWidget(splitter, 1)

    def _load_data(self):
        """加载数据"""
        self.list_card.clear()
        models = self.config_manager.get_models()
        for model_id in models.keys():
            self.list_card.add_item(model_id)

    def _on_select(self, model_id: str):
        """选择模型"""
        model = self.config_manager.get_model(model_id)
        if model:
            self.detail_title.setText(model_id)
            self.info_id.setText(model_id)
            self.info_tokens.setText(str(model.get("maxTokens", "-")))
            self.info_context.setText(str(model.get("contextWindow", "-")))
            self.info_images.setText("是" if model.get("supportsImages") else "否")
            self.info_computer.setText("是" if model.get("supportsComputerUse") else "否")
            self.info_reasoning.setText("是" if model.get("reasoning") else "否")

            # 加载options和variants
            import json
            options = model.get("options", {})
            variants = model.get("variants", {})
            self.options_edit.setText(json.dumps(options, indent=2, ensure_ascii=False) if options else "")
            self.variants_edit.setText(json.dumps(variants, indent=2, ensure_ascii=False) if variants else "")

    def _on_add(self):
        """添加模型"""
        dialog = ModelDialog(self, presets=self.presets)
        if dialog.exec():
            model_id, config = dialog.get_data()
            if model_id:
                self.config_manager.add_model(model_id, config)
                self._load_data()
                self.show_success("成功", f"已添加模型: {model_id}")
            else:
                self.show_error("错误", "模型ID不能为空")

    def _on_edit(self):
        """编辑模型"""
        model_id = self.list_card.current_item()
        if not model_id:
            self.show_warning("提示", "请先选择要编辑的模型")
            return

        model = self.config_manager.get_model(model_id)
        dialog = ModelDialog(self, model_id, model, self.presets)
        if dialog.exec():
            new_id, config = dialog.get_data()
            if new_id:
                if new_id != model_id:
                    self.config_manager.delete_model(model_id)
                self.config_manager.add_model(new_id, config)
                self._load_data()
                self.show_success("成功", f"已更新模型: {new_id}")

    def _on_delete(self):
        """删除模型"""
        model_id = self.list_card.current_item()
        if not model_id:
            self.show_warning("提示", "请先选择要删除的模型")
            return

        box = MessageBox("确认删除", f"确定要删除模型 '{model_id}' 吗？", self)
        if box.exec():
            self.config_manager.delete_model(model_id)
            self._load_data()
            self.detail_title.setText("选择模型查看详情")
            self.show_success("成功", f"已删除模型: {model_id}")

    def _save_options_variants(self):
        """保存Options和Variants配置"""
        model_id = self.list_card.current_item()
        if not model_id:
            self.show_warning("提示", "请先选择模型")
            return

        import json
        model = self.config_manager.get_model(model_id)
        if not model:
            return

        try:
            options_text = self.options_edit.toPlainText().strip()
            variants_text = self.variants_edit.toPlainText().strip()

            if options_text:
                model["options"] = json.loads(options_text)
            elif "options" in model:
                del model["options"]

            if variants_text:
                model["variants"] = json.loads(variants_text)
            elif "variants" in model:
                del model["variants"]

            self.config_manager.update_model(model_id, model)
            self.show_success("成功", "Options/Variants配置已保存")
        except json.JSONDecodeError as e:
            self.show_error("JSON格式错误", str(e))


# ======================================================================
# Part 5: MCP页面和Agent页面
# ======================================================================

class MCPDialog(Dialog):
    """MCP服务器编辑对话框"""

    def __init__(self, parent=None, server_name: str = "", server_config: dict = None):
        super().__init__("编辑MCP服务器" if server_name else "添加MCP服务器", "", parent)
        self.server_name = server_name
        self.server_config = server_config or {}
        self._init_ui()

    def _init_ui(self):
        self.textLayout.deleteLater()

        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(12)

        # 名称
        name_layout = QHBoxLayout()
        name_label = BodyLabel("名称:")
        name_label.setMinimumWidth(100)
        self.name_edit = LineEdit()
        self.name_edit.setPlaceholderText("MCP服务器名称")
        self.name_edit.setText(self.server_name)
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit, 1)
        form_layout.addLayout(name_layout)

        # 类型
        type_layout = QHBoxLayout()
        type_label = BodyLabel("类型:")
        type_label.setMinimumWidth(100)
        self.type_combo = ComboBox()
        self.type_combo.addItems(["local", "remote"])
        current_type = self.server_config.get("type", "local")
        self.type_combo.setCurrentText(current_type)
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo, 1)
        form_layout.addLayout(type_layout)

        # Local配置区域
        self.local_widget = QWidget()
        local_layout = QVBoxLayout(self.local_widget)
        local_layout.setContentsMargins(0, 0, 0, 0)
        local_layout.setSpacing(12)

        # 命令
        cmd_layout = QHBoxLayout()
        cmd_label = BodyLabel("命令:")
        cmd_label.setMinimumWidth(100)
        self.cmd_edit = LineEdit()
        self.cmd_edit.setPlaceholderText("启动命令，如 npx, python")
        self.cmd_edit.setText(self.server_config.get("command", ""))
        cmd_layout.addWidget(cmd_label)
        cmd_layout.addWidget(self.cmd_edit, 1)
        local_layout.addLayout(cmd_layout)

        # 参数
        args_layout = QHBoxLayout()
        args_label = BodyLabel("参数:")
        args_label.setMinimumWidth(100)
        self.args_edit = LineEdit()
        self.args_edit.setPlaceholderText("命令参数，用逗号分隔")
        args = self.server_config.get("args", [])
        self.args_edit.setText(", ".join(args) if args else "")
        args_layout.addWidget(args_label)
        args_layout.addWidget(self.args_edit, 1)
        local_layout.addLayout(args_layout)

        form_layout.addWidget(self.local_widget)

        # Remote配置区域
        self.remote_widget = QWidget()
        remote_layout = QVBoxLayout(self.remote_widget)
        remote_layout.setContentsMargins(0, 0, 0, 0)
        remote_layout.setSpacing(12)

        # URL
        url_layout = QHBoxLayout()
        url_label = BodyLabel("URL:")
        url_label.setMinimumWidth(100)
        self.url_edit = LineEdit()
        self.url_edit.setPlaceholderText("远程服务器URL")
        self.url_edit.setText(self.server_config.get("url", ""))
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_edit, 1)
        remote_layout.addLayout(url_layout)

        form_layout.addWidget(self.remote_widget)

        # 环境变量
        env_layout = QHBoxLayout()
        env_label = BodyLabel("环境变量:")
        env_label.setMinimumWidth(100)
        self.env_edit = TextEdit()
        self.env_edit.setPlaceholderText('{"KEY": "value"}')
        self.env_edit.setMaximumHeight(80)
        import json
        env = self.server_config.get("env", {})
        self.env_edit.setText(json.dumps(env, indent=2, ensure_ascii=False) if env else "")
        env_layout.addWidget(env_label)
        env_layout.addWidget(self.env_edit, 1)
        form_layout.addLayout(env_layout)

        # 超时
        timeout_layout = QHBoxLayout()
        timeout_label = BodyLabel("超时(秒):")
        timeout_label.setMinimumWidth(100)
        self.timeout_spin = SpinBox()
        self.timeout_spin.setRange(1, 3600)
        self.timeout_spin.setValue(self.server_config.get("timeout", 60))
        timeout_layout.addWidget(timeout_label)
        timeout_layout.addWidget(self.timeout_spin, 1)
        form_layout.addLayout(timeout_layout)

        self.vBoxLayout.insertWidget(0, form_widget)
        self.widget.setMinimumWidth(500)

        # 初始化显示
        self._on_type_changed(current_type)

    def _on_type_changed(self, type_name: str):
        """类型变化"""
        self.local_widget.setVisible(type_name == "local")
        self.remote_widget.setVisible(type_name == "remote")

    def get_data(self) -> tuple:
        """获取表单数据"""
        import json
        name = self.name_edit.text().strip()
        server_type = self.type_combo.currentText()

        config = {"type": server_type}

        if server_type == "local":
            config["command"] = self.cmd_edit.text().strip()
            args_text = self.args_edit.text().strip()
            if args_text:
                config["args"] = [a.strip() for a in args_text.split(",") if a.strip()]
        else:
            config["url"] = self.url_edit.text().strip()

        env_text = self.env_edit.toPlainText().strip()
        if env_text:
            try:
                config["env"] = json.loads(env_text)
            except json.JSONDecodeError:
                pass

        timeout = self.timeout_spin.value()
        if timeout != 60:
            config["timeout"] = timeout

        return name, config


class MCPPage(BasePage):
    """MCP服务器配置页面"""

    def __init__(self, config_manager, parent=None):
        super().__init__("MCP配置", parent)
        self.config_manager = config_manager
        self._init_content()
        self._load_data()

    def _init_content(self):
        self.add_title("MCP服务器配置")
        self.add_subtitle("管理Model Context Protocol服务器，支持本地和远程类型")
        self.add_spacing(8)

        # 创建分栏布局
        splitter = QSplitter(Qt.Horizontal)

        # 左侧列表
        self.list_card = ListCard()
        self.add_btn = self.list_card.add_toolbar_button("添加", FIF.ADD)
        self.edit_btn = self.list_card.add_toolbar_button("编辑", FIF.EDIT)
        self.delete_btn = self.list_card.add_toolbar_button("删除", FIF.DELETE)
        self.list_card.add_toolbar_stretch()

        self.add_btn.clicked.connect(self._on_add)
        self.edit_btn.clicked.connect(self._on_edit)
        self.delete_btn.clicked.connect(self._on_delete)
        self.list_card.itemDoubleClicked.connect(lambda: self._on_edit())
        self.list_card.itemSelected.connect(self._on_select)

        splitter.addWidget(self.list_card)

        # 右侧详情
        self.detail_card = CardWidget()
        detail_layout = QVBoxLayout(self.detail_card)
        detail_layout.setContentsMargins(20, 20, 20, 20)
        detail_layout.setSpacing(12)

        self.detail_title = SubtitleLabel("选择MCP服务器查看详情")
        detail_layout.addWidget(self.detail_title)

        self.detail_info = QWidget()
        info_layout = QGridLayout(self.detail_info)
        info_layout.setSpacing(8)

        info_layout.addWidget(BodyLabel("名称:"), 0, 0)
        self.info_name = BodyLabel("-")
        info_layout.addWidget(self.info_name, 0, 1)

        info_layout.addWidget(BodyLabel("类型:"), 1, 0)
        self.info_type = BodyLabel("-")
        info_layout.addWidget(self.info_type, 1, 1)

        info_layout.addWidget(BodyLabel("命令/URL:"), 2, 0)
        self.info_cmd = BodyLabel("-")
        self.info_cmd.setWordWrap(True)
        info_layout.addWidget(self.info_cmd, 2, 1)

        info_layout.addWidget(BodyLabel("参数:"), 3, 0)
        self.info_args = BodyLabel("-")
        self.info_args.setWordWrap(True)
        info_layout.addWidget(self.info_args, 3, 1)

        info_layout.addWidget(BodyLabel("超时:"), 4, 0)
        self.info_timeout = BodyLabel("-")
        info_layout.addWidget(self.info_timeout, 4, 1)

        info_layout.setColumnStretch(1, 1)
        detail_layout.addWidget(self.detail_info)

        # 环境变量显示
        env_label = SubtitleLabel("环境变量")
        detail_layout.addWidget(env_label)

        self.env_display = TextEdit()
        self.env_display.setReadOnly(True)
        self.env_display.setMaximumHeight(120)
        detail_layout.addWidget(self.env_display)

        detail_layout.addStretch()

        splitter.addWidget(self.detail_card)
        splitter.setSizes([300, 400])

        self.content_layout.addWidget(splitter, 1)

    def _load_data(self):
        """加载数据"""
        self.list_card.clear()
        servers = self.config_manager.get_mcp_servers()
        for name in servers.keys():
            self.list_card.add_item(name)

    def _on_select(self, name: str):
        """选择MCP服务器"""
        server = self.config_manager.get_mcp_server(name)
        if server:
            self.detail_title.setText(name)
            self.info_name.setText(name)
            self.info_type.setText(server.get("type", "local"))

            if server.get("type") == "remote":
                self.info_cmd.setText(server.get("url", "-"))
                self.info_args.setText("-")
            else:
                self.info_cmd.setText(server.get("command", "-"))
                args = server.get("args", [])
                self.info_args.setText(", ".join(args) if args else "-")

            self.info_timeout.setText(f"{server.get('timeout', 60)}秒")

            import json
            env = server.get("env", {})
            self.env_display.setText(json.dumps(env, indent=2, ensure_ascii=False) if env else "无")

    def _on_add(self):
        """添加MCP服务器"""
        dialog = MCPDialog(self)
        if dialog.exec():
            name, config = dialog.get_data()
            if name:
                self.config_manager.add_mcp_server(name, config)
                self._load_data()
                self.show_success("成功", f"已添加MCP服务器: {name}")
            else:
                self.show_error("错误", "服务器名称不能为空")

    def _on_edit(self):
        """编辑MCP服务器"""
        name = self.list_card.current_item()
        if not name:
            self.show_warning("提示", "请先选择要编辑的MCP服务器")
            return

        server = self.config_manager.get_mcp_server(name)
        dialog = MCPDialog(self, name, server)
        if dialog.exec():
            new_name, config = dialog.get_data()
            if new_name:
                if new_name != name:
                    self.config_manager.delete_mcp_server(name)
                self.config_manager.add_mcp_server(new_name, config)
                self._load_data()
                self.show_success("成功", f"已更新MCP服务器: {new_name}")

    def _on_delete(self):
        """删除MCP服务器"""
        name = self.list_card.current_item()
        if not name:
            self.show_warning("提示", "请先选择要删除的MCP服务器")
            return

        box = MessageBox("确认删除", f"确定要删除MCP服务器 '{name}' 吗？", self)
        if box.exec():
            self.config_manager.delete_mcp_server(name)
            self._load_data()
            self.detail_title.setText("选择MCP服务器查看详情")
            self.show_success("成功", f"已删除MCP服务器: {name}")


class OpenCodeAgentPage(BasePage):
    """OpenCode Agent配置页面"""

    def __init__(self, config_manager, parent=None):
        super().__init__("OpenCode Agent", parent)
        self.config_manager = config_manager
        self._init_content()
        self._load_data()

    def _init_content(self):
        self.add_title("OpenCode Agent配置")
        self.add_subtitle("配置Agent的运行模式、温度参数和工具权限")
        self.add_spacing(8)

        # Agent模式
        mode_card = CardWidget()
        mode_layout = QVBoxLayout(mode_card)
        mode_layout.setContentsMargins(20, 16, 20, 16)
        mode_layout.setSpacing(12)

        mode_title = SubtitleLabel("运行模式")
        mode_layout.addWidget(mode_title)

        mode_row = QHBoxLayout()
        mode_row.addWidget(BodyLabel("Agent模式:"))
        self.mode_combo = ComboBox()
        self.mode_combo.addItems(["auto", "manual", "hybrid"])
        self.mode_combo.setMinimumWidth(150)
        mode_row.addWidget(self.mode_combo)
        mode_row.addStretch()
        mode_layout.addLayout(mode_row)

        self.content_layout.addWidget(mode_card)

        # 参数配置
        param_card = CardWidget()
        param_layout = QVBoxLayout(param_card)
        param_layout.setContentsMargins(20, 16, 20, 16)
        param_layout.setSpacing(12)

        param_title = SubtitleLabel("参数配置")
        param_layout.addWidget(param_title)

        # Temperature
        temp_row = QHBoxLayout()
        temp_row.addWidget(BodyLabel("Temperature:"))
        self.temp_slider = DoubleSpinBox()
        self.temp_slider.setRange(0, 2)
        self.temp_slider.setSingleStep(0.1)
        self.temp_slider.setValue(0.7)
        self.temp_slider.setMinimumWidth(120)
        temp_row.addWidget(self.temp_slider)
        temp_row.addStretch()
        param_layout.addLayout(temp_row)

        # Max Steps
        steps_row = QHBoxLayout()
        steps_row.addWidget(BodyLabel("最大步骤数:"))
        self.steps_spin = SpinBox()
        self.steps_spin.setRange(1, 1000)
        self.steps_spin.setValue(50)
        self.steps_spin.setMinimumWidth(120)
        steps_row.addWidget(self.steps_spin)
        steps_row.addStretch()
        param_layout.addLayout(steps_row)

        self.content_layout.addWidget(param_card)

        # 工具配置
        tools_card = CardWidget()
        tools_layout = QVBoxLayout(tools_card)
        tools_layout.setContentsMargins(20, 16, 20, 16)
        tools_layout.setSpacing(12)

        tools_title = SubtitleLabel("可用工具")
        tools_layout.addWidget(tools_title)

        tools_grid = QGridLayout()
        tools_grid.setSpacing(8)

        self.tool_checks = {}
        tools = ["read", "write", "edit", "bash", "glob", "grep", "ls", "web_search", "web_fetch"]
        for i, tool in enumerate(tools):
            check = CheckBox(tool)
            check.setChecked(True)
            self.tool_checks[tool] = check
            tools_grid.addWidget(check, i // 3, i % 3)

        tools_layout.addLayout(tools_grid)
        self.content_layout.addWidget(tools_card)

        # 权限配置
        perm_card = CardWidget()
        perm_layout = QVBoxLayout(perm_card)
        perm_layout.setContentsMargins(20, 16, 20, 16)
        perm_layout.setSpacing(12)

        perm_title = SubtitleLabel("权限配置")
        perm_layout.addWidget(perm_title)

        # 文件写入权限
        write_row = QHBoxLayout()
        write_row.addWidget(BodyLabel("文件写入:"))
        self.write_perm = ComboBox()
        self.write_perm.addItems(["allow", "ask", "deny"])
        self.write_perm.setMinimumWidth(120)
        write_row.addWidget(self.write_perm)
        write_row.addStretch()
        perm_layout.addLayout(write_row)

        # Bash执行权限
        bash_row = QHBoxLayout()
        bash_row.addWidget(BodyLabel("Bash执行:"))
        self.bash_perm = ComboBox()
        self.bash_perm.addItems(["allow", "ask", "deny", "allowlist"])
        self.bash_perm.setMinimumWidth(120)
        bash_row.addWidget(self.bash_perm)
        bash_row.addStretch()
        perm_layout.addLayout(bash_row)

        self.content_layout.addWidget(perm_card)

        # 保存按钮
        save_btn = PrimaryPushButton("保存配置")
        save_btn.clicked.connect(self._save_config)
        self.content_layout.addWidget(save_btn)

        self.add_stretch()

    def _load_data(self):
        """加载数据"""
        config = self.config_manager.get_config()
        agent_config = config.get("agent", {})

        self.mode_combo.setCurrentText(agent_config.get("mode", "auto"))
        self.temp_slider.setValue(agent_config.get("temperature", 0.7))
        self.steps_spin.setValue(agent_config.get("maxSteps", 50))

        tools = agent_config.get("tools", list(self.tool_checks.keys()))
        for tool, check in self.tool_checks.items():
            check.setChecked(tool in tools)

        permissions = agent_config.get("permissions", {})
        self.write_perm.setCurrentText(permissions.get("write", "ask"))
        self.bash_perm.setCurrentText(permissions.get("bash", "ask"))

    def _save_config(self):
        """保存配置"""
        agent_config = {
            "mode": self.mode_combo.currentText(),
            "temperature": self.temp_slider.value(),
            "maxSteps": self.steps_spin.value(),
            "tools": [tool for tool, check in self.tool_checks.items() if check.isChecked()],
            "permissions": {
                "write": self.write_perm.currentText(),
                "bash": self.bash_perm.currentText()
            }
        }

        self.config_manager.set("agent", agent_config)
        self.show_success("成功", "Agent配置已保存")


class AgentPage(BasePage):
    """Agent配置页面 - OhMy OpenCode"""

    def __init__(self, config_manager, presets: dict, parent=None):
        super().__init__("Agent管理", parent)
        self.config_manager = config_manager
        self.presets = presets
        self._init_content()
        self._load_data()

    def _init_content(self):
        self.add_title("Agent管理")
        self.add_subtitle("管理自定义Agent，配置模型绑定和行为指令")
        self.add_spacing(8)

        # 创建分栏布局
        splitter = QSplitter(Qt.Horizontal)

        # 左侧列表
        self.list_card = ListCard()
        self.add_btn = self.list_card.add_toolbar_button("添加", FIF.ADD)
        self.preset_btn = self.list_card.add_toolbar_button("预设", FIF.LIBRARY)
        self.delete_btn = self.list_card.add_toolbar_button("删除", FIF.DELETE)
        self.list_card.add_toolbar_stretch()

        self.add_btn.clicked.connect(self._on_add)
        self.preset_btn.clicked.connect(self._on_add_preset)
        self.delete_btn.clicked.connect(self._on_delete)
        self.list_card.itemSelected.connect(self._on_select)

        splitter.addWidget(self.list_card)

        # 右侧编辑区
        self.edit_card = CardWidget()
        edit_layout = QVBoxLayout(self.edit_card)
        edit_layout.setContentsMargins(20, 20, 20, 20)
        edit_layout.setSpacing(12)

        self.edit_title = SubtitleLabel("选择Agent进行编辑")
        edit_layout.addWidget(self.edit_title)

        # 名称
        name_row = QHBoxLayout()
        name_row.addWidget(BodyLabel("名称:"))
        self.name_edit = LineEdit()
        self.name_edit.setPlaceholderText("Agent名称")
        name_row.addWidget(self.name_edit, 1)
        edit_layout.addLayout(name_row)

        # 绑定模型
        model_row = QHBoxLayout()
        model_row.addWidget(BodyLabel("绑定模型:"))
        self.model_combo = ComboBox()
        self.model_combo.setMinimumWidth(200)
        model_row.addWidget(self.model_combo, 1)
        edit_layout.addLayout(model_row)

        # 描述
        desc_row = QHBoxLayout()
        desc_row.addWidget(BodyLabel("描述:"))
        self.desc_edit = LineEdit()
        self.desc_edit.setPlaceholderText("Agent描述")
        desc_row.addWidget(self.desc_edit, 1)
        edit_layout.addLayout(desc_row)

        # 指令
        inst_label = BodyLabel("指令:")
        edit_layout.addWidget(inst_label)

        self.inst_edit = TextEdit()
        self.inst_edit.setPlaceholderText("Agent行为指令")
        self.inst_edit.setMinimumHeight(150)
        edit_layout.addWidget(self.inst_edit)

        # 保存按钮
        save_btn = PrimaryPushButton("保存Agent")
        save_btn.clicked.connect(self._save_agent)
        edit_layout.addWidget(save_btn)

        edit_layout.addStretch()

        splitter.addWidget(self.edit_card)
        splitter.setSizes([300, 500])

        self.content_layout.addWidget(splitter, 1)

    def _load_data(self):
        """加载数据"""
        self.list_card.clear()
        agents = self.config_manager.get_agents()
        for name in agents.keys():
            self.list_card.add_item(name)

        # 更新模型下拉框
        self.model_combo.clear()
        self.model_combo.addItem("")
        models = self.config_manager.get_models()
        self.model_combo.addItems(list(models.keys()))

    def _on_select(self, name: str):
        """选择Agent"""
        agent = self.config_manager.get_agent(name)
        if agent:
            self.edit_title.setText(f"编辑: {name}")
            self.name_edit.setText(agent.get("name", name))
            self.model_combo.setCurrentText(agent.get("model", ""))
            self.desc_edit.setText(agent.get("description", ""))
            self.inst_edit.setText(agent.get("instructions", ""))

    def _on_add(self):
        """添加Agent"""
        self.edit_title.setText("新建Agent")
        self.name_edit.clear()
        self.model_combo.setCurrentIndex(0)
        self.desc_edit.clear()
        self.inst_edit.clear()

    def _on_add_preset(self):
        """添加预设Agent"""
        from qfluentwidgets import RoundMenu, Action
        menu = RoundMenu(parent=self)
        for preset_name in self.presets.keys():
            action = Action(preset_name)
            action.triggered.connect(lambda checked, n=preset_name: self._apply_preset(n))
            menu.addAction(action)
        menu.exec_(self.preset_btn.mapToGlobal(self.preset_btn.rect().bottomLeft()))

    def _apply_preset(self, preset_name: str):
        """应用预设"""
        preset = self.presets.get(preset_name, {})
        self.edit_title.setText(f"新建Agent (预设: {preset_name})")
        self.name_edit.setText(preset.get("name", ""))
        self.model_combo.setCurrentText(preset.get("model", ""))
        self.desc_edit.setText(preset.get("description", ""))
        self.inst_edit.setText(preset.get("instructions", ""))

    def _on_delete(self):
        """删除Agent"""
        name = self.list_card.current_item()
        if not name:
            self.show_warning("提示", "请先选择要删除的Agent")
            return

        box = MessageBox("确认删除", f"确定要删除Agent '{name}' 吗？", self)
        if box.exec():
            self.config_manager.delete_agent(name)
            self._load_data()
            self.edit_title.setText("选择Agent进行编辑")
            self.show_success("成功", f"已删除Agent: {name}")

    def _save_agent(self):
        """保存Agent"""
        name = self.name_edit.text().strip()
        if not name:
            self.show_error("错误", "Agent名称不能为空")
            return

        config = {
            "name": name,
            "model": self.model_combo.currentText(),
            "description": self.desc_edit.text().strip(),
            "instructions": self.inst_edit.toPlainText().strip()
        }

        # 检查是否是编辑现有Agent
        current = self.list_card.current_item()
        if current and current != name:
            self.config_manager.delete_agent(current)

        self.config_manager.add_agent(name, config)
        self._load_data()
        self.show_success("成功", f"已保存Agent: {name}")


# ======================================================================
# Part 6: Category页面和Permission页面
# ======================================================================

class CategoryPage(BasePage):
    """分类配置页面 - Temperature滑块和预设分类模板"""

    def __init__(self, config_manager, presets: dict, parent=None):
        super().__init__("分类配置", parent)
        self.config_manager = config_manager
        self.presets = presets
        self._init_content()
        self._load_data()

    def _init_content(self):
        self.add_title("分类配置")
        self.add_subtitle("为不同任务类型配置Temperature参数，优化AI输出效果")
        self.add_spacing(8)

        # 预设分类卡片
        preset_card = CardWidget()
        preset_layout = QVBoxLayout(preset_card)
        preset_layout.setContentsMargins(20, 16, 20, 16)
        preset_layout.setSpacing(16)

        preset_title = SubtitleLabel("预设分类模板")
        preset_layout.addWidget(preset_title)

        preset_desc = CaptionLabel("点击预设分类快速应用推荐的Temperature值")
        preset_desc.setStyleSheet("color: gray;")
        preset_layout.addWidget(preset_desc)

        # 预设按钮网格
        preset_grid = QGridLayout()
        preset_grid.setSpacing(12)

        self.preset_buttons = {}
        for i, (name, config) in enumerate(self.presets.items()):
            btn = PushButton(f"{name}\n({config['temperature']})")
            btn.setMinimumHeight(60)
            btn.setToolTip(config['description'])
            btn.clicked.connect(lambda checked, n=name: self._apply_preset(n))
            self.preset_buttons[name] = btn
            preset_grid.addWidget(btn, i // 4, i % 4)

        preset_layout.addLayout(preset_grid)
        self.content_layout.addWidget(preset_card)

        # 当前配置卡片
        config_card = CardWidget()
        config_layout = QVBoxLayout(config_card)
        config_layout.setContentsMargins(20, 16, 20, 16)
        config_layout.setSpacing(16)

        config_title = SubtitleLabel("当前Temperature配置")
        config_layout.addWidget(config_title)

        # Temperature滑块
        temp_row = QHBoxLayout()
        temp_row.addWidget(BodyLabel("Temperature:"))

        self.temp_slider = Slider(Qt.Horizontal)
        self.temp_slider.setRange(0, 200)  # 0.0 - 2.0
        self.temp_slider.setValue(70)  # 0.7
        self.temp_slider.setMinimumWidth(300)
        self.temp_slider.valueChanged.connect(self._on_temp_changed)
        temp_row.addWidget(self.temp_slider)

        self.temp_label = BodyLabel("0.70")
        self.temp_label.setMinimumWidth(50)
        self.temp_label.setAlignment(Qt.AlignCenter)
        temp_row.addWidget(self.temp_label)

        temp_row.addStretch()
        config_layout.addLayout(temp_row)

        # 说明文字
        temp_desc = CaptionLabel("Temperature控制输出的随机性：0=确定性输出，1=平衡，2=高创造性")
        temp_desc.setStyleSheet("color: gray;")
        config_layout.addWidget(temp_desc)

        self.content_layout.addWidget(config_card)

        # 自定义分类配置
        custom_card = CardWidget()
        custom_layout = QVBoxLayout(custom_card)
        custom_layout.setContentsMargins(20, 16, 20, 16)
        custom_layout.setSpacing(12)

        custom_title = SubtitleLabel("自定义分类")
        custom_layout.addWidget(custom_title)

        # 分类列表
        self.category_list = ListWidget()
        self.category_list.setMaximumHeight(150)
        custom_layout.addWidget(self.category_list)

        # 添加分类
        add_row = QHBoxLayout()
        self.category_name = LineEdit()
        self.category_name.setPlaceholderText("分类名称")
        add_row.addWidget(self.category_name)

        self.category_temp = DoubleSpinBox()
        self.category_temp.setRange(0, 2)
        self.category_temp.setSingleStep(0.1)
        self.category_temp.setValue(0.7)
        add_row.addWidget(self.category_temp)

        add_btn = PushButton("添加")
        add_btn.clicked.connect(self._add_category)
        add_row.addWidget(add_btn)

        del_btn = PushButton("删除")
        del_btn.clicked.connect(self._delete_category)
        add_row.addWidget(del_btn)

        custom_layout.addLayout(add_row)
        self.content_layout.addWidget(custom_card)

        # 保存按钮
        save_btn = PrimaryPushButton("保存配置")
        save_btn.clicked.connect(self._save_config)
        self.content_layout.addWidget(save_btn)

        self.add_stretch()

    def _load_data(self):
        """加载数据"""
        config = self.config_manager.get_config()
        categories = config.get("categories", {})

        # 加载默认temperature
        default_temp = config.get("defaultTemperature", 0.7)
        self.temp_slider.setValue(int(default_temp * 100))
        self.temp_label.setText(f"{default_temp:.2f}")

        # 加载自定义分类
        self.category_list.clear()
        for name, temp in categories.items():
            self.category_list.addItem(f"{name}: {temp}")

    def _on_temp_changed(self, value: int):
        """Temperature滑块变化"""
        temp = value / 100.0
        self.temp_label.setText(f"{temp:.2f}")

    def _apply_preset(self, preset_name: str):
        """应用预设"""
        preset = self.presets.get(preset_name, {})
        temp = preset.get("temperature", 0.7)
        self.temp_slider.setValue(int(temp * 100))
        self.show_info("已应用", f"已应用预设: {preset_name} (Temperature: {temp})")

    def _add_category(self):
        """添加分类"""
        name = self.category_name.text().strip()
        if not name:
            self.show_warning("提示", "请输入分类名称")
            return

        temp = self.category_temp.value()
        self.category_list.addItem(f"{name}: {temp}")
        self.category_name.clear()
        self.show_success("成功", f"已添加分类: {name}")

    def _delete_category(self):
        """删除分类"""
        row = self.category_list.currentRow()
        if row >= 0:
            self.category_list.takeItem(row)
            self.show_success("成功", "已删除分类")
        else:
            self.show_warning("提示", "请先选择要删除的分类")

    def _save_config(self):
        """保存配置"""
        # 保存默认temperature
        default_temp = self.temp_slider.value() / 100.0
        self.config_manager.set("defaultTemperature", default_temp)

        # 保存自定义分类
        categories = {}
        for i in range(self.category_list.count()):
            item_text = self.category_list.item(i).text()
            if ": " in item_text:
                name, temp = item_text.rsplit(": ", 1)
                try:
                    categories[name] = float(temp)
                except ValueError:
                    pass

        self.config_manager.set("categories", categories)
        self.show_success("成功", "分类配置已保存")


class PermissionPage(BasePage):
    """权限配置页面"""

    def __init__(self, config_manager, parent=None):
        super().__init__("权限配置", parent)
        self.config_manager = config_manager
        self._init_content()
        self._load_data()

    def _init_content(self):
        self.add_title("权限配置")
        self.add_subtitle("配置文件操作、命令执行等权限，控制AI的操作范围")
        self.add_spacing(8)

        # 权限模式说明
        mode_card = CardWidget()
        mode_layout = QVBoxLayout(mode_card)
        mode_layout.setContentsMargins(20, 16, 20, 16)
        mode_layout.setSpacing(8)

        mode_title = SubtitleLabel("权限模式说明")
        mode_layout.addWidget(mode_title)

        modes = [
            ("allow", "允许", "自动执行，无需用户确认"),
            ("ask", "询问", "每次执行前询问用户确认"),
            ("deny", "拒绝", "禁止执行此操作")
        ]

        for mode, name, desc in modes:
            row = QHBoxLayout()
            label = BodyLabel(f"• {name} ({mode}):")
            label.setMinimumWidth(120)
            row.addWidget(label)
            row.addWidget(BodyLabel(desc))
            row.addStretch()
            mode_layout.addLayout(row)

        self.content_layout.addWidget(mode_card)

        # Allow列表
        allow_card = CardWidget()
        allow_layout = QVBoxLayout(allow_card)
        allow_layout.setContentsMargins(20, 16, 20, 16)
        allow_layout.setSpacing(12)

        allow_title = SubtitleLabel("允许列表 (Allow)")
        allow_layout.addWidget(allow_title)

        self.allow_list = ListWidget()
        self.allow_list.setMaximumHeight(120)
        allow_layout.addWidget(self.allow_list)

        allow_row = QHBoxLayout()
        self.allow_input = LineEdit()
        self.allow_input.setPlaceholderText("输入操作名称或路径模式")
        allow_row.addWidget(self.allow_input, 1)

        allow_add = PushButton("添加")
        allow_add.clicked.connect(lambda: self._add_item("allow"))
        allow_row.addWidget(allow_add)

        allow_del = PushButton("删除")
        allow_del.clicked.connect(lambda: self._delete_item("allow"))
        allow_row.addWidget(allow_del)

        allow_layout.addLayout(allow_row)
        self.content_layout.addWidget(allow_card)

        # Ask列表
        ask_card = CardWidget()
        ask_layout = QVBoxLayout(ask_card)
        ask_layout.setContentsMargins(20, 16, 20, 16)
        ask_layout.setSpacing(12)

        ask_title = SubtitleLabel("询问列表 (Ask)")
        ask_layout.addWidget(ask_title)

        self.ask_list = ListWidget()
        self.ask_list.setMaximumHeight(120)
        ask_layout.addWidget(self.ask_list)

        ask_row = QHBoxLayout()
        self.ask_input = LineEdit()
        self.ask_input.setPlaceholderText("输入操作名称或路径模式")
        ask_row.addWidget(self.ask_input, 1)

        ask_add = PushButton("添加")
        ask_add.clicked.connect(lambda: self._add_item("ask"))
        ask_row.addWidget(ask_add)

        ask_del = PushButton("删除")
        ask_del.clicked.connect(lambda: self._delete_item("ask"))
        ask_row.addWidget(ask_del)

        ask_layout.addLayout(ask_row)
        self.content_layout.addWidget(ask_card)

        # Deny列表
        deny_card = CardWidget()
        deny_layout = QVBoxLayout(deny_card)
        deny_layout.setContentsMargins(20, 16, 20, 16)
        deny_layout.setSpacing(12)

        deny_title = SubtitleLabel("拒绝列表 (Deny)")
        deny_layout.addWidget(deny_title)

        self.deny_list = ListWidget()
        self.deny_list.setMaximumHeight(120)
        deny_layout.addWidget(self.deny_list)

        deny_row = QHBoxLayout()
        self.deny_input = LineEdit()
        self.deny_input.setPlaceholderText("输入操作名称或路径模式")
        deny_row.addWidget(self.deny_input, 1)

        deny_add = PushButton("添加")
        deny_add.clicked.connect(lambda: self._add_item("deny"))
        deny_row.addWidget(deny_add)

        deny_del = PushButton("删除")
        deny_del.clicked.connect(lambda: self._delete_item("deny"))
        deny_row.addWidget(deny_del)

        deny_layout.addLayout(deny_row)
        self.content_layout.addWidget(deny_card)

        # Bash命令模式
        bash_card = CardWidget()
        bash_layout = QVBoxLayout(bash_card)
        bash_layout.setContentsMargins(20, 16, 20, 16)
        bash_layout.setSpacing(12)

        bash_title = SubtitleLabel("Bash命令权限")
        bash_layout.addWidget(bash_title)

        bash_row = QHBoxLayout()
        bash_row.addWidget(BodyLabel("命令模式:"))
        self.bash_mode = ComboBox()
        self.bash_mode.addItems(["allow", "ask", "deny", "allowlist"])
        self.bash_mode.setMinimumWidth(150)
        self.bash_mode.currentTextChanged.connect(self._on_bash_mode_changed)
        bash_row.addWidget(self.bash_mode)
        bash_row.addStretch()
        bash_layout.addLayout(bash_row)

        # 白名单
        self.allowlist_widget = QWidget()
        allowlist_layout = QVBoxLayout(self.allowlist_widget)
        allowlist_layout.setContentsMargins(0, 8, 0, 0)
        allowlist_layout.setSpacing(8)

        allowlist_label = BodyLabel("命令白名单:")
        allowlist_layout.addWidget(allowlist_label)

        self.allowlist_edit = TextEdit()
        self.allowlist_edit.setPlaceholderText("每行一个命令，如:\ngit\nnpm\npython")
        self.allowlist_edit.setMaximumHeight(100)
        allowlist_layout.addWidget(self.allowlist_edit)

        bash_layout.addWidget(self.allowlist_widget)
        self.content_layout.addWidget(bash_card)

        # 保存按钮
        save_btn = PrimaryPushButton("保存权限配置")
        save_btn.clicked.connect(self._save_config)
        self.content_layout.addWidget(save_btn)

        self.add_stretch()

    def _load_data(self):
        """加载数据"""
        permissions = self.config_manager.get_permissions()

        # 加载列表
        self.allow_list.clear()
        self.allow_list.addItems(permissions.get("allow", []))

        self.ask_list.clear()
        self.ask_list.addItems(permissions.get("ask", []))

        self.deny_list.clear()
        self.deny_list.addItems(permissions.get("deny", []))

        # 加载Bash模式
        bash_config = permissions.get("bash", {})
        if isinstance(bash_config, str):
            self.bash_mode.setCurrentText(bash_config)
        elif isinstance(bash_config, dict):
            mode = bash_config.get("mode", "ask")
            self.bash_mode.setCurrentText(mode)
            allowlist = bash_config.get("allowlist", [])
            self.allowlist_edit.setText("\n".join(allowlist))

        self._on_bash_mode_changed(self.bash_mode.currentText())

    def _on_bash_mode_changed(self, mode: str):
        """Bash模式变化"""
        self.allowlist_widget.setVisible(mode == "allowlist")

    def _add_item(self, list_type: str):
        """添加项目"""
        input_map = {
            "allow": (self.allow_input, self.allow_list),
            "ask": (self.ask_input, self.ask_list),
            "deny": (self.deny_input, self.deny_list)
        }

        input_edit, list_widget = input_map[list_type]
        text = input_edit.text().strip()
        if text:
            list_widget.addItem(text)
            input_edit.clear()
        else:
            self.show_warning("提示", "请输入内容")

    def _delete_item(self, list_type: str):
        """删除项目"""
        list_map = {
            "allow": self.allow_list,
            "ask": self.ask_list,
            "deny": self.deny_list
        }

        list_widget = list_map[list_type]
        row = list_widget.currentRow()
        if row >= 0:
            list_widget.takeItem(row)
        else:
            self.show_warning("提示", "请先选择要删除的项目")

    def _save_config(self):
        """保存配置"""
        permissions = {
            "allow": [self.allow_list.item(i).text() for i in range(self.allow_list.count())],
            "ask": [self.ask_list.item(i).text() for i in range(self.ask_list.count())],
            "deny": [self.deny_list.item(i).text() for i in range(self.deny_list.count())]
        }

        # Bash配置
        bash_mode = self.bash_mode.currentText()
        if bash_mode == "allowlist":
            allowlist = [cmd.strip() for cmd in self.allowlist_edit.toPlainText().split("\n") if cmd.strip()]
            permissions["bash"] = {
                "mode": "allowlist",
                "allowlist": allowlist
            }
        else:
            permissions["bash"] = bash_mode

        self.config_manager.set_permissions(permissions)
        self.show_success("成功", "权限配置已保存")


# ======================================================================
# Part 7: Skill页面和Rules页面
# ======================================================================

class SkillPage(BasePage):
    """技能配置页面"""

    def __init__(self, config_manager, md_manager, parent=None):
        super().__init__("技能配置", parent)
        self.config_manager = config_manager
        self.md_manager = md_manager
        self._init_content()
        self._load_data()

    def _init_content(self):
        self.add_title("技能配置")
        self.add_subtitle("管理SKILL.md文件，配置技能权限和行为")
        self.add_spacing(8)

        # 技能权限配置
        perm_card = CardWidget()
        perm_layout = QVBoxLayout(perm_card)
        perm_layout.setContentsMargins(20, 16, 20, 16)
        perm_layout.setSpacing(12)

        perm_title = SubtitleLabel("技能权限")
        perm_layout.addWidget(perm_title)

        # 权限列表
        perm_grid = QGridLayout()
        perm_grid.setSpacing(8)

        self.skill_perms = {}
        skills = [
            ("read", "读取文件"),
            ("write", "写入文件"),
            ("edit", "编辑文件"),
            ("bash", "执行命令"),
            ("web_search", "网络搜索"),
            ("web_fetch", "获取网页"),
        ]

        for i, (skill_id, skill_name) in enumerate(skills):
            row_layout = QHBoxLayout()
            label = BodyLabel(f"{skill_name}:")
            label.setMinimumWidth(80)
            row_layout.addWidget(label)

            combo = ComboBox()
            combo.addItems(["allow", "ask", "deny"])
            combo.setMinimumWidth(100)
            self.skill_perms[skill_id] = combo
            row_layout.addWidget(combo)
            row_layout.addStretch()

            perm_grid.addLayout(row_layout, i // 2, i % 2)

        perm_layout.addLayout(perm_grid)
        self.content_layout.addWidget(perm_card)

        # SKILL.md编辑器
        editor_card = CardWidget()
        editor_layout = QVBoxLayout(editor_card)
        editor_layout.setContentsMargins(20, 16, 20, 16)
        editor_layout.setSpacing(12)

        editor_header = QHBoxLayout()
        editor_title = SubtitleLabel("SKILL.md 编辑器")
        editor_header.addWidget(editor_title)
        editor_header.addStretch()

        reload_btn = PushButton("重新加载")
        reload_btn.setIcon(FIF.SYNC)
        reload_btn.clicked.connect(self._reload_skill_md)
        editor_header.addWidget(reload_btn)

        editor_layout.addLayout(editor_header)

        # 文件路径显示
        path_row = QHBoxLayout()
        path_row.addWidget(CaptionLabel("文件路径:"))
        self.path_label = CaptionLabel("")
        self.path_label.setStyleSheet("color: gray;")
        path_row.addWidget(self.path_label, 1)
        editor_layout.addLayout(path_row)

        # 编辑器
        self.skill_editor = TextEdit()
        self.skill_editor.setPlaceholderText("# SKILL.md\n\n在此编辑技能配置...")
        self.skill_editor.setMinimumHeight(300)
        self.skill_editor.setStyleSheet("font-family: Consolas, 'Microsoft YaHei UI'; font-size: 12px;")
        editor_layout.addWidget(self.skill_editor)

        # 按钮组
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        save_btn = PrimaryPushButton("保存SKILL.md")
        save_btn.clicked.connect(self._save_skill_md)
        btn_row.addWidget(save_btn)

        editor_layout.addLayout(btn_row)
        self.content_layout.addWidget(editor_card)

        self.add_stretch()

    def _load_data(self):
        """加载数据"""
        # 加载技能权限
        config = self.config_manager.get_config()
        skill_perms = config.get("skillPermissions", {})
        for skill_id, combo in self.skill_perms.items():
            perm = skill_perms.get(skill_id, "ask")
            combo.setCurrentText(perm)

        # 加载SKILL.md
        self._reload_skill_md()

    def _reload_skill_md(self):
        """重新加载SKILL.md"""
        content = self.md_manager.read_skill_md()
        self.skill_editor.setText(content)
        self.path_label.setText(str(self.md_manager.paths.skill_md))

    def _save_skill_md(self):
        """保存SKILL.md"""
        content = self.skill_editor.toPlainText()
        if self.md_manager.write_skill_md(content):
            # 保存技能权限
            skill_perms = {skill_id: combo.currentText() for skill_id, combo in self.skill_perms.items()}
            self.config_manager.set("skillPermissions", skill_perms)
            self.show_success("成功", "SKILL.md已保存")
        else:
            self.show_error("错误", "保存SKILL.md失败")


class RulesPage(BasePage):
    """规则配置页面"""

    def __init__(self, config_manager, md_manager, parent=None):
        super().__init__("规则配置", parent)
        self.config_manager = config_manager
        self.md_manager = md_manager
        self._init_content()
        self._load_data()

    def _init_content(self):
        self.add_title("规则配置")
        self.add_subtitle("管理AGENTS.md文件，配置AI行为规则和指令")
        self.add_spacing(8)

        # Instructions配置
        inst_card = CardWidget()
        inst_layout = QVBoxLayout(inst_card)
        inst_layout.setContentsMargins(20, 16, 20, 16)
        inst_layout.setSpacing(12)

        inst_title = SubtitleLabel("全局指令 (Instructions)")
        inst_layout.addWidget(inst_title)

        inst_desc = CaptionLabel("配置全局AI行为指令，这些指令会应用到所有对话中")
        inst_desc.setStyleSheet("color: gray;")
        inst_layout.addWidget(inst_desc)

        self.instructions_edit = TextEdit()
        self.instructions_edit.setPlaceholderText("输入全局指令...")
        self.instructions_edit.setMaximumHeight(150)
        inst_layout.addWidget(self.instructions_edit)

        save_inst_btn = PushButton("保存指令")
        save_inst_btn.clicked.connect(self._save_instructions)
        inst_layout.addWidget(save_inst_btn, alignment=Qt.AlignRight)

        self.content_layout.addWidget(inst_card)

        # AGENTS.md编辑器
        editor_card = CardWidget()
        editor_layout = QVBoxLayout(editor_card)
        editor_layout.setContentsMargins(20, 16, 20, 16)
        editor_layout.setSpacing(12)

        editor_header = QHBoxLayout()
        editor_title = SubtitleLabel("AGENTS.md 编辑器")
        editor_header.addWidget(editor_title)
        editor_header.addStretch()

        reload_btn = PushButton("重新加载")
        reload_btn.setIcon(FIF.SYNC)
        reload_btn.clicked.connect(self._reload_agents_md)
        editor_header.addWidget(reload_btn)

        editor_layout.addLayout(editor_header)

        # 文件路径显示
        path_row = QHBoxLayout()
        path_row.addWidget(CaptionLabel("文件路径:"))
        self.path_label = CaptionLabel("")
        self.path_label.setStyleSheet("color: gray;")
        path_row.addWidget(self.path_label, 1)
        editor_layout.addLayout(path_row)

        # 编辑器
        self.agents_editor = TextEdit()
        self.agents_editor.setPlaceholderText("# AGENTS.md\n\n在此编辑Agent规则...")
        self.agents_editor.setMinimumHeight(300)
        self.agents_editor.setStyleSheet("font-family: Consolas, 'Microsoft YaHei UI'; font-size: 12px;")
        editor_layout.addWidget(self.agents_editor)

        # 按钮组
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        template_btn = PushButton("插入模板")
        template_btn.clicked.connect(self._insert_template)
        btn_row.addWidget(template_btn)

        save_btn = PrimaryPushButton("保存AGENTS.md")
        save_btn.clicked.connect(self._save_agents_md)
        btn_row.addWidget(save_btn)

        editor_layout.addLayout(btn_row)
        self.content_layout.addWidget(editor_card)

        self.add_stretch()

    def _load_data(self):
        """加载数据"""
        # 加载全局指令
        config = self.config_manager.get_config()
        instructions = config.get("instructions", "")
        self.instructions_edit.setText(instructions)

        # 加载AGENTS.md
        self._reload_agents_md()

    def _reload_agents_md(self):
        """重新加载AGENTS.md"""
        content = self.md_manager.read_agents_md()
        self.agents_editor.setText(content)
        self.path_label.setText(str(self.md_manager.paths.agents_md))

    def _save_instructions(self):
        """保存全局指令"""
        instructions = self.instructions_edit.toPlainText().strip()
        self.config_manager.set("instructions", instructions)
        self.show_success("成功", "全局指令已保存")

    def _save_agents_md(self):
        """保存AGENTS.md"""
        content = self.agents_editor.toPlainText()
        if self.md_manager.write_agents_md(content):
            self.show_success("成功", "AGENTS.md已保存")
        else:
            self.show_error("错误", "保存AGENTS.md失败")

    def _insert_template(self):
        """插入模板"""
        template = """# AGENTS.md

## 代码规范

- 使用简体中文编写注释
- 遵循项目既有的代码风格
- 保持代码简洁，避免过度设计

## 文档规范

- 所有文档使用Markdown格式
- 文档存放在 /docs/ 目录下
- 文件名使用中文命名

## 提交规范

- 使用语义化版本号
- Commit信息使用中文
- 每次提交前确保代码可运行

## 安全规范

- 不在代码中硬编码敏感信息
- API密钥使用环境变量
- 定期备份重要配置
"""
        current = self.agents_editor.toPlainText()
        if current.strip():
            box = MessageBox("确认", "当前内容不为空，是否追加模板？", self)
            if box.exec():
                self.agents_editor.setText(current + "\n\n" + template)
        else:
            self.agents_editor.setText(template)


# ======================================================================
# Part 8: Compaction页面和Import页面
# ======================================================================

class CompactionPage(BasePage):
    """上下文压缩配置页面"""

    def __init__(self, config_manager, parent=None):
        super().__init__("压缩配置", parent)
        self.config_manager = config_manager
        self._init_content()
        self._load_data()

    def _init_content(self):
        self.add_title("上下文压缩配置")
        self.add_subtitle("配置自动压缩功能，优化长对话的上下文管理")
        self.add_spacing(8)

        # 启用压缩
        enable_card = CardWidget()
        enable_layout = QHBoxLayout(enable_card)
        enable_layout.setContentsMargins(20, 16, 20, 16)

        enable_text = QVBoxLayout()
        enable_title = BodyLabel("启用自动压缩")
        enable_title.setFont(QFont("Microsoft YaHei UI", 11))
        enable_text.addWidget(enable_title)

        enable_desc = CaptionLabel("当上下文超过阈值时自动压缩历史消息")
        enable_desc.setStyleSheet("color: gray;")
        enable_text.addWidget(enable_desc)

        enable_layout.addLayout(enable_text)
        enable_layout.addStretch()

        self.enable_switch = SwitchButton()
        self.enable_switch.checkedChanged.connect(self._on_enable_changed)
        enable_layout.addWidget(self.enable_switch)

        self.content_layout.addWidget(enable_card)

        # 压缩参数
        self.param_card = CardWidget()
        param_layout = QVBoxLayout(self.param_card)
        param_layout.setContentsMargins(20, 16, 20, 16)
        param_layout.setSpacing(16)

        param_title = SubtitleLabel("压缩参数")
        param_layout.addWidget(param_title)

        # 压缩阈值
        threshold_row = QHBoxLayout()
        threshold_row.addWidget(BodyLabel("压缩阈值 (Token数):"))
        self.threshold_spin = SpinBox()
        self.threshold_spin.setRange(10000, 1000000)
        self.threshold_spin.setSingleStep(10000)
        self.threshold_spin.setValue(100000)
        self.threshold_spin.setMinimumWidth(150)
        threshold_row.addWidget(self.threshold_spin)
        threshold_row.addStretch()
        param_layout.addLayout(threshold_row)

        threshold_desc = CaptionLabel("当上下文Token数超过此值时触发压缩")
        threshold_desc.setStyleSheet("color: gray;")
        param_layout.addWidget(threshold_desc)

        # 修剪旧输出
        trim_row = QHBoxLayout()
        trim_text = QVBoxLayout()
        trim_title = BodyLabel("修剪旧输出")
        trim_text.addWidget(trim_title)
        trim_desc = CaptionLabel("移除较早的输出内容以节省空间")
        trim_desc.setStyleSheet("color: gray;")
        trim_text.addWidget(trim_desc)
        trim_row.addLayout(trim_text)
        trim_row.addStretch()

        self.trim_switch = SwitchButton()
        trim_row.addWidget(self.trim_switch)
        param_layout.addLayout(trim_row)

        self.content_layout.addWidget(self.param_card)

        # 压缩策略
        strategy_card = CardWidget()
        strategy_layout = QVBoxLayout(strategy_card)
        strategy_layout.setContentsMargins(20, 16, 20, 16)
        strategy_layout.setSpacing(12)

        strategy_title = SubtitleLabel("压缩策略")
        strategy_layout.addWidget(strategy_title)

        strategy_row = QHBoxLayout()
        strategy_row.addWidget(BodyLabel("策略:"))
        self.strategy_combo = ComboBox()
        self.strategy_combo.addItems(["summarize", "truncate", "sliding_window"])
        self.strategy_combo.setMinimumWidth(150)
        strategy_row.addWidget(self.strategy_combo)
        strategy_row.addStretch()
        strategy_layout.addLayout(strategy_row)

        strategies_desc = {
            "summarize": "总结 - 将历史消息总结为摘要",
            "truncate": "截断 - 直接移除最早的消息",
            "sliding_window": "滑动窗口 - 保留最近N条消息"
        }

        for strategy, desc in strategies_desc.items():
            desc_label = CaptionLabel(f"• {desc}")
            desc_label.setStyleSheet("color: gray;")
            strategy_layout.addWidget(desc_label)

        self.content_layout.addWidget(strategy_card)

        # 保存按钮
        save_btn = PrimaryPushButton("保存压缩配置")
        save_btn.clicked.connect(self._save_config)
        self.content_layout.addWidget(save_btn)

        self.add_stretch()

    def _load_data(self):
        """加载数据"""
        compaction = self.config_manager.get_compaction()
        self.enable_switch.setChecked(compaction.get("enabled", False))
        self.threshold_spin.setValue(compaction.get("threshold", 100000))
        self.trim_switch.setChecked(compaction.get("trimOldOutput", False))

        strategy = compaction.get("strategy", "summarize")
        self.strategy_combo.setCurrentText(strategy)

        self._on_enable_changed(self.enable_switch.isChecked())

    def _on_enable_changed(self, enabled: bool):
        """启用状态变化"""
        self.param_card.setEnabled(enabled)

    def _save_config(self):
        """保存配置"""
        compaction = {
            "enabled": self.enable_switch.isChecked(),
            "threshold": self.threshold_spin.value(),
            "trimOldOutput": self.trim_switch.isChecked(),
            "strategy": self.strategy_combo.currentText()
        }
        self.config_manager.set_compaction(compaction)
        self.show_success("成功", "压缩配置已保存")


class ImportPage(BasePage):
    """导入配置页面"""

    def __init__(self, config_manager, import_service, backup_manager, parent=None):
        super().__init__("导入配置", parent)
        self.config_manager = config_manager
        self.import_service = import_service
        self.backup_manager = backup_manager
        self._init_content()
        self._detect_configs()

    def _init_content(self):
        self.add_title("导入配置")
        self.add_subtitle("检测并导入外部配置文件，支持合并或覆盖模式")
        self.add_spacing(8)

        # 检测到的配置
        detect_card = CardWidget()
        detect_layout = QVBoxLayout(detect_card)
        detect_layout.setContentsMargins(20, 16, 20, 16)
        detect_layout.setSpacing(12)

        detect_header = QHBoxLayout()
        detect_title = SubtitleLabel("检测到的配置文件")
        detect_header.addWidget(detect_title)
        detect_header.addStretch()

        refresh_btn = PushButton("刷新")
        refresh_btn.setIcon(FIF.SYNC)
        refresh_btn.clicked.connect(self._detect_configs)
        detect_header.addWidget(refresh_btn)

        detect_layout.addLayout(detect_header)

        self.config_list = ListWidget()
        self.config_list.setMaximumHeight(150)
        self.config_list.itemClicked.connect(self._on_config_selected)
        detect_layout.addWidget(self.config_list)

        self.content_layout.addWidget(detect_card)

        # 预览区域
        preview_card = CardWidget()
        preview_layout = QVBoxLayout(preview_card)
        preview_layout.setContentsMargins(20, 16, 20, 16)
        preview_layout.setSpacing(12)

        preview_title = SubtitleLabel("配置预览")
        preview_layout.addWidget(preview_title)

        # 预览信息
        self.preview_info = QWidget()
        preview_info_layout = QGridLayout(self.preview_info)
        preview_info_layout.setSpacing(8)

        preview_info_layout.addWidget(BodyLabel("路径:"), 0, 0)
        self.preview_path = BodyLabel("-")
        self.preview_path.setWordWrap(True)
        preview_info_layout.addWidget(self.preview_path, 0, 1)

        preview_info_layout.addWidget(BodyLabel("大小:"), 1, 0)
        self.preview_size = BodyLabel("-")
        preview_info_layout.addWidget(self.preview_size, 1, 1)

        preview_info_layout.addWidget(BodyLabel("修改时间:"), 2, 0)
        self.preview_modified = BodyLabel("-")
        preview_info_layout.addWidget(self.preview_modified, 2, 1)

        preview_info_layout.addWidget(BodyLabel("服务商:"), 3, 0)
        self.preview_providers = BodyLabel("-")
        preview_info_layout.addWidget(self.preview_providers, 3, 1)

        preview_info_layout.addWidget(BodyLabel("模型:"), 4, 0)
        self.preview_models = BodyLabel("-")
        preview_info_layout.addWidget(self.preview_models, 4, 1)

        preview_info_layout.addWidget(BodyLabel("MCP服务器:"), 5, 0)
        self.preview_mcp = BodyLabel("-")
        preview_info_layout.addWidget(self.preview_mcp, 5, 1)

        preview_info_layout.setColumnStretch(1, 1)
        preview_layout.addWidget(self.preview_info)

        self.content_layout.addWidget(preview_card)

        # 导入选项
        import_card = CardWidget()
        import_layout = QVBoxLayout(import_card)
        import_layout.setContentsMargins(20, 16, 20, 16)
        import_layout.setSpacing(12)

        import_title = SubtitleLabel("导入选项")
        import_layout.addWidget(import_title)

        # 导入模式
        mode_row = QHBoxLayout()
        mode_row.addWidget(BodyLabel("导入模式:"))
        self.merge_radio = RadioButton("合并 (保留现有配置)")
        self.merge_radio.setChecked(True)
        mode_row.addWidget(self.merge_radio)
        self.replace_radio = RadioButton("覆盖 (替换现有配置)")
        mode_row.addWidget(self.replace_radio)
        mode_row.addStretch()
        import_layout.addLayout(mode_row)

        # 备份选项
        backup_row = QHBoxLayout()
        self.backup_check = CheckBox("导入前自动备份当前配置")
        self.backup_check.setChecked(True)
        backup_row.addWidget(self.backup_check)
        backup_row.addStretch()
        import_layout.addLayout(backup_row)

        # 按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        browse_btn = PushButton("浏览文件...")
        browse_btn.clicked.connect(self._browse_file)
        btn_row.addWidget(browse_btn)

        self.import_btn = PrimaryPushButton("导入配置")
        self.import_btn.clicked.connect(self._import_config)
        self.import_btn.setEnabled(False)
        btn_row.addWidget(self.import_btn)

        import_layout.addLayout(btn_row)
        self.content_layout.addWidget(import_card)

        # 导出配置
        export_card = CardWidget()
        export_layout = QVBoxLayout(export_card)
        export_layout.setContentsMargins(20, 16, 20, 16)
        export_layout.setSpacing(12)

        export_title = SubtitleLabel("导出配置")
        export_layout.addWidget(export_title)

        export_desc = CaptionLabel("将当前配置导出为JSON文件，方便备份或迁移")
        export_desc.setStyleSheet("color: gray;")
        export_layout.addWidget(export_desc)

        export_btn = PushButton("导出配置...")
        export_btn.clicked.connect(self._export_config)
        export_layout.addWidget(export_btn, alignment=Qt.AlignLeft)

        self.content_layout.addWidget(export_card)

        self.add_stretch()

        # 存储检测到的配置
        self._detected_configs = []
        self._selected_config = None

    def _detect_configs(self):
        """检测外部配置"""
        self.config_list.clear()
        self._detected_configs = self.import_service.detect_external_configs()

        for config in self._detected_configs:
            self.config_list.addItem(f"{config['name']} - {config['path']}")

        if not self._detected_configs:
            self.config_list.addItem("未检测到外部配置文件")

    def _on_config_selected(self, item):
        """选择配置"""
        index = self.config_list.currentRow()
        if index >= 0 and index < len(self._detected_configs):
            self._selected_config = self._detected_configs[index]
            self._update_preview()
            self.import_btn.setEnabled(True)
        else:
            self._selected_config = None
            self.import_btn.setEnabled(False)

    def _update_preview(self):
        """更新预览"""
        if not self._selected_config:
            return

        self.preview_path.setText(self._selected_config.get("path", "-"))
        self.preview_size.setText(f"{self._selected_config.get('size', 0)} 字节")
        self.preview_modified.setText(self._selected_config.get("modified", "-"))

        preview = self.import_service.preview_import(self._selected_config)
        self.preview_providers.setText(", ".join(preview.get("providers", [])) or "无")
        self.preview_models.setText(", ".join(preview.get("models", [])) or "无")
        self.preview_mcp.setText(", ".join(preview.get("mcpServers", [])) or "无")

    def _browse_file(self):
        """浏览文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择配置文件", "", "JSON文件 (*.json);;所有文件 (*)"
        )
        if file_path:
            try:
                import json
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                import os
                from datetime import datetime
                stat = os.stat(file_path)

                self._selected_config = {
                    "path": file_path,
                    "name": "手动选择",
                    "data": data,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                }
                self._update_preview()
                self.import_btn.setEnabled(True)
            except Exception as e:
                self.show_error("错误", f"无法读取文件: {e}")

    def _import_config(self):
        """导入配置"""
        if not self._selected_config:
            self.show_warning("提示", "请先选择要导入的配置")
            return

        # 备份
        if self.backup_check.isChecked():
            self.backup_manager.create_backup("导入前自动备份")

        # 导入
        merge = self.merge_radio.isChecked()
        if self.import_service.import_config(self._selected_config, merge):
            self.config_manager.load()  # 重新加载配置
            self.show_success("成功", "配置已导入")
        else:
            self.show_error("错误", "导入配置失败")

    def _export_config(self):
        """导出配置"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出配置", "opencode_config.json", "JSON文件 (*.json)"
        )
        if file_path:
            if self.import_service.export_config(file_path):
                self.show_success("成功", f"配置已导出到: {file_path}")
            else:
                self.show_error("错误", "导出配置失败")


# ======================================================================
# Part 9: Help页面和备份恢复功能
# ======================================================================

class HelpPage(BasePage):
    """帮助页面"""

    def __init__(self, version: str, parent=None):
        super().__init__("帮助", parent)
        self.version = version
        self._init_content()

    def _init_content(self):
        self.add_title("帮助与关于")
        self.add_subtitle("配置优先级说明、使用指南和版本信息")
        self.add_spacing(8)

        # 配置优先级
        priority_card = CardWidget()
        priority_layout = QVBoxLayout(priority_card)
        priority_layout.setContentsMargins(20, 16, 20, 16)
        priority_layout.setSpacing(12)

        priority_title = SubtitleLabel("配置优先级")
        priority_layout.addWidget(priority_title)

        priority_desc = CaptionLabel("OpenCode配置文件的加载优先级（从高到低）")
        priority_desc.setStyleSheet("color: gray;")
        priority_layout.addWidget(priority_desc)

        priorities = [
            ("1. 项目级配置", ".opencode/opencode.json", "当前项目目录下的配置"),
            ("2. 用户级配置", "~/.opencode/opencode.json", "用户主目录下的配置"),
            ("3. 环境变量", "OPENCODE_*", "以OPENCODE_开头的环境变量"),
            ("4. 默认配置", "内置默认值", "程序内置的默认配置"),
        ]

        for level, path, desc in priorities:
            row = QHBoxLayout()
            level_label = BodyLabel(level)
            level_label.setMinimumWidth(120)
            row.addWidget(level_label)

            path_label = CaptionLabel(path)
            path_label.setMinimumWidth(200)
            path_label.setStyleSheet("color: #0078d4;")
            row.addWidget(path_label)

            desc_label = CaptionLabel(desc)
            desc_label.setStyleSheet("color: gray;")
            row.addWidget(desc_label)

            row.addStretch()
            priority_layout.addLayout(row)

        self.content_layout.addWidget(priority_card)

        # 使用说明
        guide_card = CardWidget()
        guide_layout = QVBoxLayout(guide_card)
        guide_layout.setContentsMargins(20, 16, 20, 16)
        guide_layout.setSpacing(12)

        guide_title = SubtitleLabel("使用说明")
        guide_layout.addWidget(guide_title)

        guides = [
            ("服务商配置", "添加API服务商，配置API密钥和端点地址。支持OpenAI、Anthropic等主流服务商。"),
            ("模型配置", "配置模型参数，包括Token限制、上下文窗口大小和特性支持。"),
            ("MCP服务器", "管理Model Context Protocol服务器，支持本地进程和远程SSE两种类型。"),
            ("Agent管理", "创建和管理自定义Agent，配置模型绑定和行为指令。"),
            ("权限配置", "控制文件操作、命令执行等权限，保护系统安全。"),
            ("备份恢复", "定期备份配置文件，支持多版本管理和一键恢复。"),
        ]

        for title, desc in guides:
            item_layout = QVBoxLayout()
            item_title = BodyLabel(f"• {title}")
            item_title.setFont(QFont("Microsoft YaHei UI", 10, QFont.Bold))
            item_layout.addWidget(item_title)

            item_desc = CaptionLabel(f"  {desc}")
            item_desc.setStyleSheet("color: gray;")
            item_desc.setWordWrap(True)
            item_layout.addWidget(item_desc)

            guide_layout.addLayout(item_layout)

        self.content_layout.addWidget(guide_card)

        # 快捷键
        shortcut_card = CardWidget()
        shortcut_layout = QVBoxLayout(shortcut_card)
        shortcut_layout.setContentsMargins(20, 16, 20, 16)
        shortcut_layout.setSpacing(12)

        shortcut_title = SubtitleLabel("快捷键")
        shortcut_layout.addWidget(shortcut_title)

        shortcuts = [
            ("Ctrl+S", "保存当前配置"),
            ("Ctrl+Z", "撤销操作"),
            ("Ctrl+Shift+S", "另存为"),
            ("F5", "刷新配置"),
            ("F1", "打开帮助"),
        ]

        shortcut_grid = QGridLayout()
        shortcut_grid.setSpacing(8)

        for i, (key, desc) in enumerate(shortcuts):
            key_label = BodyLabel(key)
            key_label.setStyleSheet("background: #f0f0f0; padding: 4px 8px; border-radius: 4px;")
            shortcut_grid.addWidget(key_label, i, 0)

            desc_label = BodyLabel(desc)
            shortcut_grid.addWidget(desc_label, i, 1)

        shortcut_grid.setColumnStretch(1, 1)
        shortcut_layout.addLayout(shortcut_grid)

        self.content_layout.addWidget(shortcut_card)

        # 关于
        about_card = CardWidget()
        about_layout = QVBoxLayout(about_card)
        about_layout.setContentsMargins(20, 16, 20, 16)
        about_layout.setSpacing(12)

        about_title = SubtitleLabel("关于")
        about_layout.addWidget(about_title)

        version_row = QHBoxLayout()
        version_row.addWidget(BodyLabel("版本:"))
        version_label = BodyLabel(f"v{self.version}")
        version_label.setStyleSheet("color: #0078d4;")
        version_row.addWidget(version_label)
        version_row.addStretch()
        about_layout.addLayout(version_row)

        framework_row = QHBoxLayout()
        framework_row.addWidget(BodyLabel("框架:"))
        framework_label = BodyLabel("PyQt5 + QFluentWidgets")
        framework_row.addWidget(framework_label)
        framework_row.addStretch()
        about_layout.addLayout(framework_row)

        author_row = QHBoxLayout()
        author_row.addWidget(BodyLabel("作者:"))
        author_label = BodyLabel("OpenCode Team")
        author_row.addWidget(author_label)
        author_row.addStretch()
        about_layout.addLayout(author_row)

        # 链接
        links_row = QHBoxLayout()
        github_btn = HyperlinkButton("https://github.com/opencode", "GitHub")
        links_row.addWidget(github_btn)

        docs_btn = HyperlinkButton("https://opencode.dev/docs", "文档")
        links_row.addWidget(docs_btn)

        links_row.addStretch()
        about_layout.addLayout(links_row)

        self.content_layout.addWidget(about_card)

        self.add_stretch()


class BackupDialog(Dialog):
    """备份管理对话框"""

    def __init__(self, backup_manager, parent=None):
        super().__init__("备份管理", "", parent)
        self.backup_manager = backup_manager
        self._init_ui()
        self._load_backups()

    def _init_ui(self):
        self.textLayout.deleteLater()

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(16)

        # 创建备份
        create_card = CardWidget()
        create_layout = QVBoxLayout(create_card)
        create_layout.setContentsMargins(16, 12, 16, 12)
        create_layout.setSpacing(8)

        create_title = BodyLabel("创建新备份")
        create_title.setFont(QFont("Microsoft YaHei UI", 11, QFont.Bold))
        create_layout.addWidget(create_title)

        create_row = QHBoxLayout()
        self.desc_edit = LineEdit()
        self.desc_edit.setPlaceholderText("备份描述（可选）")
        create_row.addWidget(self.desc_edit, 1)

        create_btn = PrimaryPushButton("创建备份")
        create_btn.clicked.connect(self._create_backup)
        create_row.addWidget(create_btn)

        create_layout.addLayout(create_row)
        layout.addWidget(create_card)

        # 备份列表
        list_title = BodyLabel("备份列表")
        list_title.setFont(QFont("Microsoft YaHei UI", 11, QFont.Bold))
        layout.addWidget(list_title)

        self.backup_list = ListWidget()
        self.backup_list.setMinimumHeight(200)
        layout.addWidget(self.backup_list)

        # 操作按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        restore_btn = PushButton("恢复选中")
        restore_btn.clicked.connect(self._restore_backup)
        btn_row.addWidget(restore_btn)

        delete_btn = PushButton("删除选中")
        delete_btn.clicked.connect(self._delete_backup)
        btn_row.addWidget(delete_btn)

        refresh_btn = PushButton("刷新")
        refresh_btn.clicked.connect(self._load_backups)
        btn_row.addWidget(refresh_btn)

        layout.addLayout(btn_row)

        self.vBoxLayout.insertWidget(0, content)
        self.widget.setMinimumWidth(600)
        self.widget.setMinimumHeight(450)

    def _load_backups(self):
        """加载备份列表"""
        self.backup_list.clear()
        self._backups = self.backup_manager.list_backups()

        for backup in self._backups:
            desc = backup.get("description", "")
            desc_text = f" - {desc}" if desc else ""
            item_text = f"{backup['modified']} ({backup['size']} 字节){desc_text}"
            self.backup_list.addItem(item_text)

    def _create_backup(self):
        """创建备份"""
        desc = self.desc_edit.text().strip()
        result = self.backup_manager.create_backup(desc)
        if result:
            self.desc_edit.clear()
            self._load_backups()
            InfoBar.success(
                title="成功",
                content="备份已创建",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
        else:
            InfoBar.error(
                title="错误",
                content="创建备份失败",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )

    def _restore_backup(self):
        """恢复备份"""
        index = self.backup_list.currentRow()
        if index < 0 or index >= len(self._backups):
            InfoBar.warning(
                title="提示",
                content="请先选择要恢复的备份",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return

        backup = self._backups[index]
        box = MessageBox("确认恢复", f"确定要恢复备份 '{backup['modified']}' 吗？\n当前配置将被覆盖。", self)
        if box.exec():
            if self.backup_manager.restore_backup(backup["name"]):
                InfoBar.success(
                    title="成功",
                    content="备份已恢复",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
            else:
                InfoBar.error(
                    title="错误",
                    content="恢复备份失败",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )

    def _delete_backup(self):
        """删除备份"""
        index = self.backup_list.currentRow()
        if index < 0 or index >= len(self._backups):
            InfoBar.warning(
                title="提示",
                content="请先选择要删除的备份",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return

        backup = self._backups[index]
        box = MessageBox("确认删除", f"确定要删除备份 '{backup['modified']}' 吗？", self)
        if box.exec():
            if self.backup_manager.delete_backup(backup["name"]):
                self._load_backups()
                InfoBar.success(
                    title="成功",
                    content="备份已删除",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
            else:
                InfoBar.error(
                    title="错误",
                    content="删除备份失败",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )


class VersionChecker:
    """版本检查器"""

    def __init__(self, current_version: str):
        self.current_version = current_version
        self.latest_version = None
        self.update_url = "https://github.com/opencode/releases"

    def check_update(self) -> tuple:
        """检查更新，返回 (has_update, latest_version, update_url)"""
        # 这里可以实现实际的版本检查逻辑
        # 目前返回模拟数据
        return False, self.current_version, self.update_url

    def compare_versions(self, v1: str, v2: str) -> int:
        """比较版本号，返回 -1, 0, 1"""
        def parse_version(v):
            return [int(x) for x in v.replace("v", "").split(".")]

        try:
            p1 = parse_version(v1)
            p2 = parse_version(v2)

            for a, b in zip(p1, p2):
                if a < b:
                    return -1
                elif a > b:
                    return 1
            return 0
        except Exception:
            return 0


# ======================================================================
# Part 10: 主窗口和应用入口
# ======================================================================

class MainWindow(FluentWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self._init_services()
        self._init_window()
        self._init_navigation()
        self._init_pages()
        self._load_config()

    def _init_services(self):
        """初始化服务"""
        self.paths = ConfigPaths()
        self.paths.ensure_dirs()

        self.config_manager = ConfigManager(self.paths)
        self.backup_manager = BackupManager(self.paths)
        self.model_registry = ModelRegistry()
        self.import_service = ImportService(self.config_manager, self.paths)
        self.md_manager = MarkdownFileManager(self.paths)
        self.version_checker = VersionChecker(VERSION)

    def _init_window(self):
        """初始化窗口"""
        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        # 设置主题色
        setThemeColor("#0078d4")

        # 居中显示
        desktop = QApplication.desktop()
        screen_rect = desktop.availableGeometry(self)
        self.move(
            (screen_rect.width() - self.width()) // 2,
            (screen_rect.height() - self.height()) // 2
        )

    def _init_navigation(self):
        """初始化导航"""
        # 设置导航栏
        self.navigationInterface.setExpandWidth(240)
        self.navigationInterface.setMinimumExpandWidth(200)

        # 添加头像/Logo
        self.navigationInterface.addWidget(
            routeKey="avatar",
            widget=NavigationAvatarWidget("OC", "OpenCode"),
            onClick=lambda: None,
            position=NavigationItemPosition.TOP
        )

    def _init_pages(self):
        """初始化页面"""
        # 服务商配置
        self.provider_page = ProviderPage(self.config_manager, PRESET_SDKS)
        self.addSubInterface(self.provider_page, FIF.CLOUD, "服务商")

        # 模型配置
        self.model_page = ModelPage(self.config_manager, PRESET_MODEL_CONFIGS)
        self.addSubInterface(self.model_page, FIF.ROBOT, "模型")

        # MCP配置
        self.mcp_page = MCPPage(self.config_manager)
        self.addSubInterface(self.mcp_page, FIF.CONNECT, "MCP服务器")

        # OpenCode Agent配置
        self.opencode_agent_page = OpenCodeAgentPage(self.config_manager)
        self.addSubInterface(self.opencode_agent_page, FIF.COMMAND_PROMPT, "OpenCode Agent")

        # Agent管理
        self.agent_page = AgentPage(self.config_manager, PRESET_AGENTS)
        self.addSubInterface(self.agent_page, FIF.PEOPLE, "Agent管理")

        # 分类配置
        self.category_page = CategoryPage(self.config_manager, CATEGORY_PRESETS)
        self.addSubInterface(self.category_page, FIF.TAG, "分类配置")

        # 权限配置
        self.permission_page = PermissionPage(self.config_manager)
        self.addSubInterface(self.permission_page, FIF.CERTIFICATE, "权限配置")

        # 技能配置
        self.skill_page = SkillPage(self.config_manager, self.md_manager)
        self.addSubInterface(self.skill_page, FIF.DEVELOPER_TOOLS, "技能配置")

        # 规则配置
        self.rules_page = RulesPage(self.config_manager, self.md_manager)
        self.addSubInterface(self.rules_page, FIF.BOOK_SHELF, "规则配置")

        # 压缩配置
        self.compaction_page = CompactionPage(self.config_manager)
        self.addSubInterface(self.compaction_page, FIF.ZIP_FOLDER, "压缩配置")

        # 导入配置
        self.import_page = ImportPage(self.config_manager, self.import_service, self.backup_manager)
        self.addSubInterface(self.import_page, FIF.DOWNLOAD, "导入导出")

        # 分隔线
        self.navigationInterface.addSeparator(NavigationItemPosition.BOTTOM)

        # 备份管理（底部）
        self.navigationInterface.addItem(
            routeKey="backup",
            icon=FIF.HISTORY,
            text="备份管理",
            onClick=self._show_backup_dialog,
            position=NavigationItemPosition.BOTTOM
        )

        # 主题切换（底部）
        self.navigationInterface.addItem(
            routeKey="theme",
            icon=FIF.CONSTRACT,
            text="切换主题",
            onClick=self._toggle_theme,
            position=NavigationItemPosition.BOTTOM
        )

        # 保存配置（底部）
        self.navigationInterface.addItem(
            routeKey="save",
            icon=FIF.SAVE,
            text="保存配置",
            onClick=self._save_config,
            position=NavigationItemPosition.BOTTOM
        )

        # 帮助页面（底部）
        self.help_page = HelpPage(VERSION)
        self.addSubInterface(
            self.help_page, FIF.HELP, "帮助",
            position=NavigationItemPosition.BOTTOM
        )

    def _load_config(self):
        """加载配置"""
        self.config_manager.load()

        # 检查更新
        QTimer.singleShot(2000, self._check_update)

    def _save_config(self):
        """保存配置"""
        if self.config_manager.save():
            InfoBar.success(
                title="保存成功",
                content="配置已保存到 " + str(self.paths.config_file),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
        else:
            InfoBar.error(
                title="保存失败",
                content="无法保存配置文件",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )

    def _toggle_theme(self):
        """切换主题"""
        if isDarkTheme():
            setTheme(Theme.LIGHT)
        else:
            setTheme(Theme.DARK)

    def _show_backup_dialog(self):
        """显示备份管理对话框"""
        dialog = BackupDialog(self.backup_manager, self)
        dialog.exec()
        # 如果恢复了备份，重新加载配置
        self.config_manager.load()

    def _check_update(self):
        """检查更新"""
        has_update, latest_version, update_url = self.version_checker.check_update()
        if has_update:
            InfoBar.info(
                title="发现新版本",
                content=f"新版本 v{latest_version} 可用",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=10000,
                parent=self
            )

    def closeEvent(self, event):
        """关闭事件"""
        if self.config_manager.is_dirty():
            box = MessageBox(
                "未保存的更改",
                "配置已修改但未保存，是否保存后退出？",
                self
            )
            box.yesButton.setText("保存并退出")
            box.cancelButton.setText("不保存")

            if box.exec():
                self.config_manager.save()

        event.accept()


def main():
    """主函数"""
    # 启用高DPI支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(VERSION)

    # 设置字体
    font = QFont("Microsoft YaHei UI", 9)
    app.setFont(font)

    # 创建主窗口
    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
