#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenCode & Oh My OpenCode 配置管理器 v1.0.0 (QFluentWidgets 版本)
一个可视化的GUI工具，用于管理OpenCode和Oh My OpenCode的配置文件

基于 PyQt5 + QFluentWidgets 重写，提供现代化 Fluent Design 界面
"""

import sys
import json
import re
import shutil
import webbrowser
import threading
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

from PyQt5.QtCore import Qt, QUrl, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QDesktopServices, QFont
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
)

from qfluentwidgets import (
    FluentWindow,
    NavigationItemPosition,
    MessageBox as FluentMessageBox,
    InfoBar,
    InfoBarPosition,
    PushButton,
    PrimaryPushButton,
    TransparentPushButton,
    ToolButton,
    LineEdit,
    TextEdit,
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
)


APP_VERSION = "1.0.0"
GITHUB_REPO = "icysaintdx/OpenCode-Config-Manager"
GITHUB_URL = f"https://github.com/{GITHUB_REPO}"
GITHUB_RELEASES_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
AUTHOR_NAME = "IcySaint"
AUTHOR_GITHUB = "https://github.com/icysaintdx"


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
                "variants": {
                    "high": {"thinking": {"type": "enabled", "budgetTokens": 32000}},
                    "max": {"thinking": {"type": "enabled", "budgetTokens": 64000}},
                },
                "description": "最强大的Claude模型，支持extended thinking模式\noptions.thinking.budgetTokens 控制思考预算",
            },
            "claude-sonnet-4-5-20250929": {
                "name": "Claude Sonnet 4.5",
                "attachment": True,
                "limit": {"context": 200000, "output": 16000},
                "modalities": {"input": ["text", "image"], "output": ["text"]},
                "options": {"thinking": {"type": "enabled", "budgetTokens": 8000}},
                "variants": {
                    "high": {"thinking": {"type": "enabled", "budgetTokens": 16000}},
                    "max": {"thinking": {"type": "enabled", "budgetTokens": 32000}},
                },
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
    """配置文件路径管理"""

    @staticmethod
    def get_user_home() -> Path:
        return Path.home()

    @classmethod
    def get_opencode_config(cls) -> Path:
        return cls.get_user_home() / ".config" / "opencode" / "opencode.json"

    @classmethod
    def get_ohmyopencode_config(cls) -> Path:
        return cls.get_user_home() / ".config" / "opencode" / "oh-my-opencode.json"

    @classmethod
    def get_claude_settings(cls) -> Path:
        return cls.get_user_home() / ".claude" / "settings.json"

    @classmethod
    def get_claude_providers(cls) -> Path:
        return cls.get_user_home() / ".claude" / "providers.json"

    @classmethod
    def get_backup_dir(cls) -> Path:
        return cls.get_user_home() / ".config" / "opencode" / "backups"


class ConfigManager:
    """配置文件读写管理"""

    @staticmethod
    def load_json(path: Path) -> Optional[Dict]:
        try:
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Load failed {path}: {e}")
        return None

    @staticmethod
    def save_json(path: Path, data: Dict) -> bool:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Save failed {path}: {e}")
            return False


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


class ModelRegistry:
    """模型注册表 - 管理所有已配置的模型"""

    def __init__(self, opencode_config: Optional[Dict]):
        self.config = opencode_config or {}
        self.models: Dict[str, bool] = {}
        self.refresh()

    def refresh(self):
        self.models = {}
        providers = self.config.get("provider", {})
        for provider_name, provider_data in providers.items():
            models = provider_data.get("models", {})
            for model_id in models.keys():
                full_ref = f"{provider_name}/{model_id}"
                self.models[full_ref] = True

    def get_all_models(self) -> List[str]:
        return list(self.models.keys())


class ImportService:
    """外部配置导入服务 - 支持Claude Code、Codex、Gemini、cc-switch等配置格式"""

    def scan_external_configs(self) -> Dict:
        """扫描所有支持的外部配置文件"""
        results = {}

        # Claude Code配置
        claude_settings = ConfigPaths.get_claude_settings()
        results["Claude Code Settings"] = {
            "path": str(claude_settings),
            "exists": claude_settings.exists(),
            "data": ConfigManager.load_json(claude_settings)
            if claude_settings.exists()
            else None,
            "type": "claude",
        }

        claude_providers = ConfigPaths.get_claude_providers()
        results["Claude Providers"] = {
            "path": str(claude_providers),
            "exists": claude_providers.exists(),
            "data": ConfigManager.load_json(claude_providers)
            if claude_providers.exists()
            else None,
            "type": "claude_providers",
        }

        # Codex配置 (TOML格式)
        codex_config = Path.home() / ".codex" / "config.toml"
        results["Codex Config"] = {
            "path": str(codex_config),
            "exists": codex_config.exists(),
            "data": self._parse_toml(codex_config) if codex_config.exists() else None,
            "type": "codex",
        }

        # Gemini配置
        gemini_config = Path.home() / ".config" / "gemini" / "config.json"
        results["Gemini Config"] = {
            "path": str(gemini_config),
            "exists": gemini_config.exists(),
            "data": ConfigManager.load_json(gemini_config)
            if gemini_config.exists()
            else None,
            "type": "gemini",
        }

        # cc-switch配置
        ccswitch_config = Path.home() / ".cc-switch" / "config.json"
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
            result = {}
            current_section = result
            for line in content.split("\n"):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("[") and line.endswith("]"):
                    section = line[1:-1]
                    result[section] = {}
                    current_section = result[section]
                elif "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    current_section[key] = value
            return result
        except Exception as e:
            print(f"TOML parse failed: {e}")
            return None

    def convert_to_opencode(
        self, source_type: str, source_data: Dict
    ) -> Optional[Dict]:
        """将外部配置转换为OpenCode格式"""
        if not source_data:
            return None

        result = {"provider": {}, "permission": {}}

        if source_type == "claude":
            if "apiKey" in source_data:
                result["provider"]["anthropic"] = {
                    "npm": "@ai-sdk/anthropic",
                    "name": "Anthropic (Claude)",
                    "options": {"apiKey": source_data["apiKey"]},
                    "models": {},
                }
            if "permissions" in source_data:
                for tool, perm in source_data.get("permissions", {}).items():
                    result["permission"][tool] = perm

        elif source_type == "claude_providers":
            for provider_name, provider_data in source_data.items():
                if isinstance(provider_data, dict):
                    result["provider"][provider_name] = {
                        "npm": "@ai-sdk/anthropic",
                        "name": provider_data.get("name", provider_name),
                        "options": {
                            "baseURL": provider_data.get("baseUrl", ""),
                            "apiKey": provider_data.get("apiKey", ""),
                        },
                        "models": {},
                    }

        elif source_type == "codex":
            if "api" in source_data:
                api_config = source_data["api"]
                result["provider"]["openai"] = {
                    "npm": "@ai-sdk/openai",
                    "name": "OpenAI (Codex)",
                    "options": {
                        "baseURL": api_config.get("base_url", ""),
                        "apiKey": api_config.get("api_key", ""),
                    },
                    "models": {},
                }

        elif source_type == "gemini":
            if "apiKey" in source_data:
                result["provider"]["google"] = {
                    "npm": "@ai-sdk/google",
                    "name": "Google (Gemini)",
                    "options": {"apiKey": source_data["apiKey"]},
                    "models": {},
                }

        elif source_type == "ccswitch":
            for provider_name, provider_data in source_data.get(
                "providers", {}
            ).items():
                if isinstance(provider_data, dict):
                    sdk = "@ai-sdk/openai"
                    if (
                        "anthropic" in provider_name.lower()
                        or "claude" in provider_name.lower()
                    ):
                        sdk = "@ai-sdk/anthropic"
                    elif (
                        "google" in provider_name.lower()
                        or "gemini" in provider_name.lower()
                    ):
                        sdk = "@ai-sdk/google"
                    result["provider"][provider_name] = {
                        "npm": sdk,
                        "name": provider_data.get("name", provider_name),
                        "options": {
                            "baseURL": provider_data.get(
                                "baseUrl", provider_data.get("base_url", "")
                            ),
                            "apiKey": provider_data.get(
                                "apiKey", provider_data.get("api_key", "")
                            ),
                        },
                        "models": {},
                    }

        return result


class VersionChecker:
    """GitHub 版本检查服务"""

    def __init__(self, callback=None):
        self.callback = callback
        self.latest_version: Optional[str] = None
        self.release_url: Optional[str] = None
        self.checking = False

    def check_update_async(self):
        """异步检查更新"""
        if self.checking:
            return
        self.checking = True
        thread = threading.Thread(target=self._check_update, daemon=True)
        thread.start()

    def _check_update(self):
        """检查 GitHub 最新版本"""
        try:
            req = urllib.request.Request(
                GITHUB_RELEASES_API, headers={"User-Agent": "OpenCode-Config-Manager"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                tag_name = data.get("tag_name", "")
                version_match = re.search(r"v?(\d+\.\d+\.\d+)", tag_name)
                if version_match:
                    self.latest_version = version_match.group(1)
                    self.release_url = data.get("html_url", GITHUB_URL + "/releases")
                    if self.callback:
                        self.callback(self.latest_version, self.release_url)
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
class BasePage(QWidget):
    """页面基类 - 所有页面继承此类"""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName(title.replace(" ", "_").lower())
        self._init_ui(title)

    def _init_ui(self, title: str):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(36, 20, 36, 20)
        self.layout.setSpacing(16)

        # 页面标题
        self.title_label = TitleLabel(title, self)
        self.layout.addWidget(self.title_label)

    def add_card(self, title: str = None) -> SimpleCardWidget:
        """添加一个卡片容器"""
        card = SimpleCardWidget(self)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(12)

        if title:
            card_title = SubtitleLabel(title, card)
            card_layout.addWidget(card_title)

        self.layout.addWidget(card)
        return card

    def show_success(self, title: str, content: str):
        """显示成功提示"""
        InfoBar.success(
            title=title,
            content=content,
            orient=Qt.Horizontal,
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
            orient=Qt.Horizontal,
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
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=4000,
            parent=self,
        )


# ==================== Provider 页面 ====================
class ProviderPage(BasePage):
    """Provider 管理页面"""

    def __init__(self, main_window, parent=None):
        super().__init__("Provider 管理", parent)
        self.main_window = main_window
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        # 工具栏
        toolbar = QHBoxLayout()

        self.add_btn = PrimaryPushButton(FIF.ADD, "添加 Provider", self)
        self.add_btn.clicked.connect(self._on_add)
        toolbar.addWidget(self.add_btn)

        self.edit_btn = PushButton(FIF.EDIT, "编辑", self)
        self.edit_btn.clicked.connect(self._on_edit)
        toolbar.addWidget(self.edit_btn)

        self.delete_btn = PushButton(FIF.DELETE, "删除", self)
        self.delete_btn.clicked.connect(self._on_delete)
        toolbar.addWidget(self.delete_btn)

        toolbar.addStretch()
        self.layout.addLayout(toolbar)

        # Provider 列表
        self.table = TableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["名称", "显示名称", "SDK", "API地址", "模型数"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.layout.addWidget(self.table)

    def _load_data(self):
        """加载 Provider 数据"""
        self.table.setRowCount(0)
        config = self.main_window.opencode_config or {}
        providers = config.get("provider", {})

        for name, data in providers.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(data.get("name", "")))
            self.table.setItem(row, 2, QTableWidgetItem(data.get("npm", "")))
            self.table.setItem(
                row, 3, QTableWidgetItem(data.get("options", {}).get("baseURL", ""))
            )
            self.table.setItem(
                row, 4, QTableWidgetItem(str(len(data.get("models", {}))))
            )

    def _on_add(self):
        """添加 Provider"""
        dialog = ProviderDialog(self.main_window, parent=self)
        if dialog.exec_():
            self._load_data()
            self.show_success("成功", "Provider 已添加")

    def _on_edit(self):
        """编辑 Provider"""
        row = self.table.currentRow()
        if row < 0:
            self.show_warning("提示", "请先选择一个 Provider")
            return

        name = self.table.item(row, 0).text()
        dialog = ProviderDialog(self.main_window, provider_name=name, parent=self)
        if dialog.exec_():
            self._load_data()
            self.show_success("成功", "Provider 已更新")

    def _on_delete(self):
        """删除 Provider"""
        row = self.table.currentRow()
        if row < 0:
            self.show_warning("提示", "请先选择一个 Provider")
            return

        name = self.table.item(row, 0).text()
        w = FluentMessageBox(
            "确认删除", f'确定要删除 Provider "{name}" 吗？\n此操作不可恢复。', self
        )
        if w.exec_():
            config = self.main_window.opencode_config or {}
            if "provider" in config and name in config["provider"]:
                del config["provider"][name]
                self.main_window.save_opencode_config()
                self._load_data()
                self.show_success("成功", f'Provider "{name}" 已删除')


class ProviderDialog(QDialog):
    """Provider 编辑对话框"""

    def __init__(self, main_window, provider_name: str = None, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.provider_name = provider_name
        self.is_edit = provider_name is not None

        self.setWindowTitle("编辑 Provider" if self.is_edit else "添加 Provider")
        self.setMinimumWidth(500)
        self._setup_ui()

        if self.is_edit:
            self._load_provider_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Provider 名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(BodyLabel("Provider 名称:", self))
        self.name_edit = LineEdit(self)
        self.name_edit.setPlaceholderText("如: anthropic, openai, my-proxy")
        if self.is_edit:
            self.name_edit.setEnabled(False)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        # 显示名称
        display_layout = QHBoxLayout()
        display_layout.addWidget(BodyLabel("显示名称:", self))
        self.display_edit = LineEdit(self)
        self.display_edit.setPlaceholderText("如: Anthropic (Claude)")
        display_layout.addWidget(self.display_edit)
        layout.addLayout(display_layout)

        # SDK 选择
        sdk_layout = QHBoxLayout()
        sdk_layout.addWidget(BodyLabel("SDK:", self))
        self.sdk_combo = ComboBox(self)
        self.sdk_combo.addItems(PRESET_SDKS)
        sdk_layout.addWidget(self.sdk_combo)
        layout.addLayout(sdk_layout)

        # API 地址
        url_layout = QHBoxLayout()
        url_layout.addWidget(BodyLabel("API 地址:", self))
        self.url_edit = LineEdit(self)
        self.url_edit.setPlaceholderText("留空使用默认地址")
        url_layout.addWidget(self.url_edit)
        layout.addLayout(url_layout)

        # API 密钥
        key_layout = QHBoxLayout()
        key_layout.addWidget(BodyLabel("API 密钥:", self))
        self.key_edit = LineEdit(self)
        self.key_edit.setPlaceholderText("支持环境变量: {env:API_KEY}")
        self.key_edit.setEchoMode(LineEdit.Password)
        key_layout.addWidget(self.key_edit)

        self.show_key_btn = ToolButton(FIF.VIEW, self)
        self.show_key_btn.clicked.connect(self._toggle_key_visibility)
        key_layout.addWidget(self.show_key_btn)
        layout.addLayout(key_layout)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = PushButton("取消", self)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.save_btn = PrimaryPushButton("保存", self)
        self.save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)

    def _toggle_key_visibility(self):
        if self.key_edit.echoMode() == LineEdit.Password:
            self.key_edit.setEchoMode(LineEdit.Normal)
            self.show_key_btn.setIcon(FIF.HIDE)
        else:
            self.key_edit.setEchoMode(LineEdit.Password)
            self.show_key_btn.setIcon(FIF.VIEW)

    def _load_provider_data(self):
        config = self.main_window.opencode_config or {}
        provider = config.get("provider", {}).get(self.provider_name, {})

        self.name_edit.setText(self.provider_name)
        self.display_edit.setText(provider.get("name", ""))

        sdk = provider.get("npm", "")
        if sdk in PRESET_SDKS:
            self.sdk_combo.setCurrentText(sdk)

        options = provider.get("options", {})
        self.url_edit.setText(options.get("baseURL", ""))
        self.key_edit.setText(options.get("apiKey", ""))

    def _on_save(self):
        name = self.name_edit.text().strip()
        if not name:
            InfoBar.error("错误", "请输入 Provider 名称", parent=self)
            return

        config = self.main_window.opencode_config
        if config is None:
            config = {}
            self.main_window.opencode_config = config

        if "provider" not in config:
            config["provider"] = {}

        # 检查名称冲突
        if not self.is_edit and name in config["provider"]:
            InfoBar.error("错误", f'Provider "{name}" 已存在', parent=self)
            return

        # 保存数据
        provider_data = config["provider"].get(name, {"models": {}})
        provider_data["npm"] = self.sdk_combo.currentText()
        provider_data["name"] = self.display_edit.text().strip()
        provider_data["options"] = {
            "baseURL": self.url_edit.text().strip(),
            "apiKey": self.key_edit.text().strip(),
        }

        config["provider"][name] = provider_data
        self.main_window.save_opencode_config()
        self.accept()


# ==================== Model 页面 ====================
class ModelPage(BasePage):
    """Model 管理页面"""

    def __init__(self, main_window, parent=None):
        super().__init__("Model 管理", parent)
        self.main_window = main_window
        self._setup_ui()
        self._load_providers()

    def _setup_ui(self):
        # Provider 选择
        provider_layout = QHBoxLayout()
        provider_layout.addWidget(BodyLabel("选择 Provider:", self))
        self.provider_combo = ComboBox(self)
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        provider_layout.addWidget(self.provider_combo)
        provider_layout.addStretch()
        self.layout.addLayout(provider_layout)

        # 工具栏
        toolbar = QHBoxLayout()

        self.add_btn = PrimaryPushButton(FIF.ADD, "添加模型", self)
        self.add_btn.clicked.connect(self._on_add)
        toolbar.addWidget(self.add_btn)

        self.preset_btn = PushButton(FIF.LIBRARY, "从预设添加", self)
        self.preset_btn.clicked.connect(self._on_add_preset)
        toolbar.addWidget(self.preset_btn)

        self.edit_btn = PushButton(FIF.EDIT, "编辑", self)
        self.edit_btn.clicked.connect(self._on_edit)
        toolbar.addWidget(self.edit_btn)

        self.delete_btn = PushButton(FIF.DELETE, "删除", self)
        self.delete_btn.clicked.connect(self._on_delete)
        toolbar.addWidget(self.delete_btn)

        toolbar.addStretch()
        self.layout.addLayout(toolbar)

        # Model 列表
        self.table = TableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["模型ID", "显示名称", "上下文", "输出", "附件"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.layout.addWidget(self.table)

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
            self.show_warning("提示", "请先选择一个 Provider")
            return
        dialog = ModelDialog(self.main_window, provider, parent=self)
        if dialog.exec_():
            self._load_models(provider)
            self.show_success("成功", "模型已添加")

    def _on_add_preset(self):
        """从预设添加模型"""
        provider = self.provider_combo.currentText()
        if not provider:
            self.show_warning("提示", "请先选择一个 Provider")
            return
        dialog = PresetModelDialog(self.main_window, provider, parent=self)
        if dialog.exec_():
            self._load_models(provider)
            self.show_success("成功", "预设模型已添加")

    def _on_edit(self):
        """编辑模型"""
        provider = self.provider_combo.currentText()
        row = self.table.currentRow()
        if row < 0:
            self.show_warning("提示", "请先选择一个模型")
            return
        model_id = self.table.item(row, 0).text()
        dialog = ModelDialog(self.main_window, provider, model_id=model_id, parent=self)
        if dialog.exec_():
            self._load_models(provider)
            self.show_success("成功", "模型已更新")

    def _on_delete(self):
        """删除模型"""
        provider = self.provider_combo.currentText()
        row = self.table.currentRow()
        if row < 0:
            self.show_warning("提示", "请先选择一个模型")
            return

        model_id = self.table.item(row, 0).text()
        w = FluentMessageBox("确认删除", f'确定要删除模型 "{model_id}" 吗？', self)
        if w.exec_():
            config = self.main_window.opencode_config or {}
            if "provider" in config and provider in config["provider"]:
                models = config["provider"][provider].get("models", {})
                if model_id in models:
                    del models[model_id]
                    self.main_window.save_opencode_config()
                    self._load_models(provider)
                    self.show_success("成功", f'模型 "{model_id}" 已删除')


class ModelDialog(QDialog):
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

        self.setWindowTitle("编辑模型" if self.is_edit else "添加模型")
        self.setMinimumSize(700, 700)
        self._setup_ui()

        if self.is_edit:
            self._load_model_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # ===== 基本信息区域 =====
        basic_card = CardWidget(self)
        basic_layout = QVBoxLayout(basic_card)
        basic_layout.setSpacing(8)

        # 模型ID
        id_layout = QHBoxLayout()
        id_layout.addWidget(BodyLabel("模型 ID:", self))
        self.id_edit = LineEdit(self)
        self.id_edit.setPlaceholderText("如: claude-sonnet-4-5-20250929")
        if self.is_edit:
            self.id_edit.setEnabled(False)
        id_layout.addWidget(self.id_edit)
        basic_layout.addLayout(id_layout)

        # 显示名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(BodyLabel("显示名称:", self))
        self.name_edit = LineEdit(self)
        name_layout.addWidget(self.name_edit)
        basic_layout.addLayout(name_layout)

        # 支持附件
        self.attachment_check = CheckBox("支持附件 (图片/文档)", self)
        basic_layout.addWidget(self.attachment_check)

        # 上下文窗口和最大输出
        limit_layout = QHBoxLayout()
        limit_layout.addWidget(BodyLabel("上下文窗口:", self))
        self.context_spin = SpinBox(self)
        self.context_spin.setRange(0, 10000000)
        self.context_spin.setValue(200000)
        limit_layout.addWidget(self.context_spin)
        limit_layout.addSpacing(20)
        limit_layout.addWidget(BodyLabel("最大输出:", self))
        self.output_spin = SpinBox(self)
        self.output_spin.setRange(0, 1000000)
        self.output_spin.setValue(16000)
        limit_layout.addWidget(self.output_spin)
        basic_layout.addLayout(limit_layout)

        layout.addWidget(basic_card)

        # ===== Tab 切换区域 =====
        self.pivot = Pivot(self)
        self.stacked_widget = QStackedWidget(self)

        # Options Tab
        self.options_widget = QWidget()
        self._setup_options_tab(self.options_widget)
        self.stacked_widget.addWidget(self.options_widget)
        self.pivot.addItem(routeKey="options", text="Options 配置")

        # Variants Tab
        self.variants_widget = QWidget()
        self._setup_variants_tab(self.variants_widget)
        self.stacked_widget.addWidget(self.variants_widget)
        self.pivot.addItem(routeKey="variants", text="Variants 变体")

        self.pivot.currentItemChanged.connect(
            lambda k: self.stacked_widget.setCurrentIndex(0 if k == "options" else 1)
        )
        self.pivot.setCurrentItem("options")

        layout.addWidget(self.pivot)
        layout.addWidget(self.stacked_widget, 1)

        # ===== 按钮区域 =====
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = PushButton("取消", self)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.save_btn = PrimaryPushButton("保存", self)
        self.save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)

    def _setup_options_tab(self, parent):
        """设置 Options Tab"""
        layout = QVBoxLayout(parent)
        layout.setSpacing(8)

        # Claude Thinking 快捷按钮
        claude_card = CardWidget(parent)
        claude_layout = QVBoxLayout(claude_card)
        claude_layout.addWidget(CaptionLabel("Claude Thinking 配置", parent))
        claude_btn_layout = QHBoxLayout()

        btn_thinking_type = PushButton("thinking.type=enabled", parent)
        btn_thinking_type.clicked.connect(
            lambda: self._add_thinking_config("type", "enabled")
        )
        claude_btn_layout.addWidget(btn_thinking_type)

        btn_budget = PushButton("budgetTokens=16000", parent)
        btn_budget.clicked.connect(
            lambda: self._add_thinking_config("budgetTokens", 16000)
        )
        claude_btn_layout.addWidget(btn_budget)

        btn_full = PrimaryPushButton("一键添加 Thinking", parent)
        btn_full.clicked.connect(self._add_full_thinking_config)
        claude_btn_layout.addWidget(btn_full)

        claude_layout.addLayout(claude_btn_layout)
        layout.addWidget(claude_card)

        # OpenAI 推理快捷按钮
        openai_card = CardWidget(parent)
        openai_layout = QVBoxLayout(openai_card)
        openai_layout.addWidget(CaptionLabel("OpenAI 推理配置", parent))
        openai_btn_layout = QHBoxLayout()

        openai_presets = [
            ("reasoningEffort", "high"),
            ("textVerbosity", "low"),
            ("reasoningSummary", "auto"),
        ]
        for key, val in openai_presets:
            btn = PushButton(f"{key}={val}", parent)
            btn.clicked.connect(
                lambda checked, k=key, v=val: self._add_option_preset(k, v)
            )
            openai_btn_layout.addWidget(btn)

        openai_layout.addLayout(openai_btn_layout)
        layout.addWidget(openai_card)

        # Gemini Thinking 快捷按钮
        gemini_card = CardWidget(parent)
        gemini_layout = QVBoxLayout(gemini_card)
        gemini_layout.addWidget(CaptionLabel("Gemini Thinking 配置", parent))
        gemini_btn_layout = QHBoxLayout()

        btn_gemini_8k = PushButton("thinkingBudget=8000", parent)
        btn_gemini_8k.clicked.connect(lambda: self._add_gemini_thinking_config(8000))
        gemini_btn_layout.addWidget(btn_gemini_8k)

        btn_gemini_16k = PushButton("thinkingBudget=16000", parent)
        btn_gemini_16k.clicked.connect(lambda: self._add_gemini_thinking_config(16000))
        gemini_btn_layout.addWidget(btn_gemini_16k)

        gemini_layout.addLayout(gemini_btn_layout)
        layout.addWidget(gemini_card)

        # Options 列表
        layout.addWidget(BodyLabel("Options 键值对列表:", parent))
        self.options_table = TableWidget(parent)
        self.options_table.setColumnCount(2)
        self.options_table.setHorizontalHeaderLabels(["键", "值"])
        self.options_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.options_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.options_table.setMinimumHeight(120)
        layout.addWidget(self.options_table)

        # 键值输入
        input_layout = QHBoxLayout()
        input_layout.addWidget(BodyLabel("键:", parent))
        self.option_key_edit = LineEdit(parent)
        self.option_key_edit.setPlaceholderText("如: temperature")
        input_layout.addWidget(self.option_key_edit)
        input_layout.addWidget(BodyLabel("值:", parent))
        self.option_value_edit = LineEdit(parent)
        self.option_value_edit.setPlaceholderText("如: 0.7")
        input_layout.addWidget(self.option_value_edit)
        layout.addLayout(input_layout)

        # 添加/删除按钮
        opt_btn_layout = QHBoxLayout()
        add_opt_btn = PrimaryPushButton("添加", parent)
        add_opt_btn.clicked.connect(self._add_option)
        opt_btn_layout.addWidget(add_opt_btn)
        del_opt_btn = PushButton("删除选中", parent)
        del_opt_btn.clicked.connect(self._delete_option)
        opt_btn_layout.addWidget(del_opt_btn)
        opt_btn_layout.addStretch()
        layout.addLayout(opt_btn_layout)

    def _setup_variants_tab(self, parent):
        """设置 Variants Tab"""
        layout = QVBoxLayout(parent)
        layout.setSpacing(8)

        layout.addWidget(BodyLabel("模型变体配置 (Variants):", parent))

        # Variants 列表
        self.variants_table = TableWidget(parent)
        self.variants_table.setColumnCount(2)
        self.variants_table.setHorizontalHeaderLabels(["变体名称", "配置"])
        self.variants_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.variants_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.variants_table.setMinimumHeight(120)
        self.variants_table.itemSelectionChanged.connect(self._on_variant_select)
        layout.addWidget(self.variants_table)

        # 变体名称输入
        name_layout = QHBoxLayout()
        name_layout.addWidget(BodyLabel("变体名:", parent))
        self.variant_name_edit = LineEdit(parent)
        self.variant_name_edit.setPlaceholderText("如: high, low, thinking")
        name_layout.addWidget(self.variant_name_edit)
        layout.addLayout(name_layout)

        # 预设名称按钮
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(CaptionLabel("预设名称:", parent))
        for name in ["high", "low", "thinking", "fast", "default"]:
            btn = PushButton(name, parent)
            btn.clicked.connect(
                lambda checked, n=name: self.variant_name_edit.setText(n)
            )
            preset_layout.addWidget(btn)
        preset_layout.addStretch()
        layout.addLayout(preset_layout)

        # JSON 配置编辑器
        layout.addWidget(BodyLabel("配置 (JSON):", parent))
        self.variant_config_edit = TextEdit(parent)
        self.variant_config_edit.setPlaceholderText('{"reasoningEffort": "high"}')
        self.variant_config_edit.setMaximumHeight(100)
        layout.addWidget(self.variant_config_edit)

        # 添加/删除按钮
        var_btn_layout = QHBoxLayout()
        add_var_btn = PrimaryPushButton("添加变体", parent)
        add_var_btn.clicked.connect(self._add_variant)
        var_btn_layout.addWidget(add_var_btn)
        del_var_btn = PushButton("删除变体", parent)
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
            InfoBar.warning("提示", "请输入变体名称", parent=self)
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
        model = provider.get("models", {}).get(self.model_id, {})

        self.id_edit.setText(self.model_id)
        self.name_edit.setText(model.get("name", ""))
        self.attachment_check.setChecked(model.get("attachment", False))

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
        if self.provider_name not in config["provider"]:
            config["provider"][self.provider_name] = {"models": {}}
        if "models" not in config["provider"][self.provider_name]:
            config["provider"][self.provider_name]["models"] = {}

        models = config["provider"][self.provider_name]["models"]

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
        options = self.current_model_data.get("options", {})
        if options:
            model_data["options"] = options
        variants = self.current_model_data.get("variants", {})
        if variants:
            model_data["variants"] = variants

        models[model_id] = model_data
        self.main_window.save_opencode_config()
        self.accept()


class PresetModelDialog(QDialog):
    """预设模型选择对话框"""

    def __init__(self, main_window, provider_name: str, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.provider_name = provider_name

        self.setWindowTitle("从预设添加模型")
        self.setMinimumSize(500, 400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 模型系列选择
        series_layout = QHBoxLayout()
        series_layout.addWidget(BodyLabel("模型系列:", self))
        self.series_combo = ComboBox(self)
        self.series_combo.addItems(list(PRESET_MODEL_CONFIGS.keys()))
        self.series_combo.currentTextChanged.connect(self._on_series_changed)
        series_layout.addWidget(self.series_combo)
        layout.addLayout(series_layout)

        # 模型列表
        layout.addWidget(BodyLabel("选择模型:", self))
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

        self.cancel_btn = PushButton("取消", self)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.add_btn = PrimaryPushButton("添加选中模型", self)
        self.add_btn.clicked.connect(self._on_add)
        btn_layout.addWidget(self.add_btn)

        layout.addLayout(btn_layout)

        # 初始化
        self._on_series_changed(self.series_combo.currentText())

    def _on_series_changed(self, series: str):
        self.model_list.clear()
        if series in PRESET_MODEL_CONFIGS:
            models = PRESET_MODEL_CONFIGS[series]["models"]
            for model_id, data in models.items():
                self.model_list.addItem(f"{model_id} - {data.get('name', '')}")

    def _on_add(self):
        selected = self.model_list.selectedItems()
        if not selected:
            InfoBar.warning("提示", "请选择至少一个模型", parent=self)
            return

        series = self.series_combo.currentText()
        series_data = PRESET_MODEL_CONFIGS.get(series, {})
        models_data = series_data.get("models", {})

        config = self.main_window.opencode_config
        if config is None:
            config = {}
            self.main_window.opencode_config = config

        if "provider" not in config:
            config["provider"] = {}
        if self.provider_name not in config["provider"]:
            config["provider"][self.provider_name] = {"models": {}}
        if "models" not in config["provider"][self.provider_name]:
            config["provider"][self.provider_name]["models"] = {}

        models = config["provider"][self.provider_name]["models"]
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
        InfoBar.success("成功", f"已添加 {added} 个模型", parent=self)
        self.accept()


# ==================== MCP 页面 ====================
class MCPPage(BasePage):
    """MCP 服务器管理页面"""

    def __init__(self, main_window, parent=None):
        super().__init__("MCP 服务器", parent)
        self.main_window = main_window
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        # 工具栏
        toolbar = QHBoxLayout()

        self.add_local_btn = PrimaryPushButton(FIF.ADD, "添加 Local MCP", self)
        self.add_local_btn.clicked.connect(lambda: self._on_add("local"))
        toolbar.addWidget(self.add_local_btn)

        self.add_remote_btn = PushButton(FIF.CLOUD, "添加 Remote MCP", self)
        self.add_remote_btn.clicked.connect(lambda: self._on_add("remote"))
        toolbar.addWidget(self.add_remote_btn)

        self.edit_btn = PushButton(FIF.EDIT, "编辑", self)
        self.edit_btn.clicked.connect(self._on_edit)
        toolbar.addWidget(self.edit_btn)

        self.delete_btn = PushButton(FIF.DELETE, "删除", self)
        self.delete_btn.clicked.connect(self._on_delete)
        toolbar.addWidget(self.delete_btn)

        toolbar.addStretch()
        self.layout.addLayout(toolbar)

        # MCP 列表
        self.table = TableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["名称", "类型", "命令/URL", "启用", "超时"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.layout.addWidget(self.table)

    def _load_data(self):
        self.table.setRowCount(0)
        config = self.main_window.opencode_config or {}
        mcps = config.get("mcp", {})

        for name, data in mcps.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(name))

            mcp_type = "remote" if "url" in data else "local"
            self.table.setItem(row, 1, QTableWidgetItem(mcp_type))

            if mcp_type == "local":
                cmd = data.get("command", [])
                self.table.setItem(
                    row,
                    2,
                    QTableWidgetItem(
                        " ".join(cmd) if isinstance(cmd, list) else str(cmd)
                    ),
                )
            else:
                self.table.setItem(row, 2, QTableWidgetItem(data.get("url", "")))

            enabled = data.get("enabled", True)
            self.table.setItem(row, 3, QTableWidgetItem("✓" if enabled else "✗"))
            self.table.setItem(row, 4, QTableWidgetItem(str(data.get("timeout", 5000))))

    def _on_add(self, mcp_type: str):
        dialog = MCPDialog(self.main_window, mcp_type=mcp_type, parent=self)
        if dialog.exec_():
            self._load_data()
            self.show_success("成功", "MCP 服务器已添加")

    def _on_edit(self):
        row = self.table.currentRow()
        if row < 0:
            self.show_warning("提示", "请先选择一个 MCP 服务器")
            return

        name = self.table.item(row, 0).text()
        mcp_type = self.table.item(row, 1).text()
        dialog = MCPDialog(
            self.main_window, mcp_name=name, mcp_type=mcp_type, parent=self
        )
        if dialog.exec_():
            self._load_data()
            self.show_success("成功", "MCP 服务器已更新")

    def _on_delete(self):
        row = self.table.currentRow()
        if row < 0:
            self.show_warning("提示", "请先选择一个 MCP 服务器")
            return

        name = self.table.item(row, 0).text()
        w = FluentMessageBox("确认删除", f'确定要删除 MCP "{name}" 吗？', self)
        if w.exec_():
            config = self.main_window.opencode_config or {}
            if "mcp" in config and name in config["mcp"]:
                del config["mcp"][name]
                self.main_window.save_opencode_config()
                self._load_data()
                self.show_success("成功", f'MCP "{name}" 已删除')


class MCPDialog(QDialog):
    """MCP 编辑对话框"""

    def __init__(
        self, main_window, mcp_name: str = None, mcp_type: str = "local", parent=None
    ):
        super().__init__(parent)
        self.main_window = main_window
        self.mcp_name = mcp_name
        self.mcp_type = mcp_type
        self.is_edit = mcp_name is not None

        self.setWindowTitle(
            "编辑 MCP" if self.is_edit else f"添加 {mcp_type.title()} MCP"
        )
        self.setMinimumWidth(550)
        self._setup_ui()

        if self.is_edit:
            self._load_mcp_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # MCP 名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(BodyLabel("MCP 名称:", self))
        self.name_edit = LineEdit(self)
        self.name_edit.setPlaceholderText("如: context7, filesystem")
        if self.is_edit:
            self.name_edit.setEnabled(False)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        # 启用状态
        self.enabled_check = CheckBox("启用此 MCP 服务器", self)
        self.enabled_check.setChecked(True)
        layout.addWidget(self.enabled_check)

        if self.mcp_type == "local":
            # 启动命令
            layout.addWidget(BodyLabel("启动命令 (JSON数组):", self))
            self.command_edit = TextEdit(self)
            self.command_edit.setPlaceholderText('["npx", "-y", "@mcp/server"]')
            self.command_edit.setMaximumHeight(80)
            layout.addWidget(self.command_edit)

            # 环境变量
            layout.addWidget(BodyLabel("环境变量 (JSON对象):", self))
            self.env_edit = TextEdit(self)
            self.env_edit.setPlaceholderText('{"API_KEY": "xxx"}')
            self.env_edit.setMaximumHeight(80)
            layout.addWidget(self.env_edit)
        else:
            # URL
            url_layout = QHBoxLayout()
            url_layout.addWidget(BodyLabel("服务器 URL:", self))
            self.url_edit = LineEdit(self)
            self.url_edit.setPlaceholderText("https://mcp.example.com/mcp")
            url_layout.addWidget(self.url_edit)
            layout.addLayout(url_layout)

            # Headers
            layout.addWidget(BodyLabel("请求头 (JSON对象):", self))
            self.headers_edit = TextEdit(self)
            self.headers_edit.setPlaceholderText('{"Authorization": "Bearer xxx"}')
            self.headers_edit.setMaximumHeight(80)
            layout.addWidget(self.headers_edit)

        # 超时
        timeout_layout = QHBoxLayout()
        timeout_layout.addWidget(BodyLabel("超时 (ms):", self))
        self.timeout_spin = SpinBox(self)
        self.timeout_spin.setRange(1000, 300000)
        self.timeout_spin.setValue(5000)
        timeout_layout.addWidget(self.timeout_spin)
        layout.addLayout(timeout_layout)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = PushButton("取消", self)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.save_btn = PrimaryPushButton("保存", self)
        self.save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)

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

    def _on_save(self):
        name = self.name_edit.text().strip()
        if not name:
            InfoBar.error("错误", "请输入 MCP 名称", parent=self)
            return

        config = self.main_window.opencode_config
        if config is None:
            config = {}
            self.main_window.opencode_config = config

        if "mcp" not in config:
            config["mcp"] = {}

        if not self.is_edit and name in config["mcp"]:
            InfoBar.error("错误", f'MCP "{name}" 已存在', parent=self)
            return

        mcp_data = {
            "enabled": self.enabled_check.isChecked(),
            "timeout": self.timeout_spin.value(),
        }

        if self.mcp_type == "local":
            cmd_text = self.command_edit.toPlainText().strip()
            if cmd_text:
                try:
                    mcp_data["command"] = json.loads(cmd_text)
                except json.JSONDecodeError as e:
                    InfoBar.error("错误", f"命令 JSON 格式错误: {e}", parent=self)
                    return

            env_text = self.env_edit.toPlainText().strip()
            if env_text:
                try:
                    mcp_data["environment"] = json.loads(env_text)
                except json.JSONDecodeError as e:
                    InfoBar.error("错误", f"环境变量 JSON 格式错误: {e}", parent=self)
                    return
        else:
            url = self.url_edit.text().strip()
            if not url:
                InfoBar.error("错误", "请输入服务器 URL", parent=self)
                return
            mcp_data["url"] = url

            headers_text = self.headers_edit.toPlainText().strip()
            if headers_text:
                try:
                    mcp_data["headers"] = json.loads(headers_text)
                except json.JSONDecodeError as e:
                    InfoBar.error("错误", f"请求头 JSON 格式错误: {e}", parent=self)
                    return

        config["mcp"][name] = mcp_data
        self.main_window.save_opencode_config()
        self.accept()


# ==================== OpenCode Agent 页面 ====================
class OpenCodeAgentPage(BasePage):
    """OpenCode 原生 Agent 配置页面"""

    def __init__(self, main_window, parent=None):
        super().__init__("OpenCode Agent", parent)
        self.main_window = main_window
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        # 工具栏
        toolbar = QHBoxLayout()

        self.add_btn = PrimaryPushButton(FIF.ADD, "添加 Agent", self)
        self.add_btn.clicked.connect(self._on_add)
        toolbar.addWidget(self.add_btn)

        self.preset_btn = PushButton(FIF.LIBRARY, "从预设添加", self)
        self.preset_btn.clicked.connect(self._on_add_preset)
        toolbar.addWidget(self.preset_btn)

        self.edit_btn = PushButton(FIF.EDIT, "编辑", self)
        self.edit_btn.clicked.connect(self._on_edit)
        toolbar.addWidget(self.edit_btn)

        self.delete_btn = PushButton(FIF.DELETE, "删除", self)
        self.delete_btn.clicked.connect(self._on_delete)
        toolbar.addWidget(self.delete_btn)

        toolbar.addStretch()
        self.layout.addLayout(toolbar)

        # Agent 列表
        self.table = TableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["名称", "模式", "Temperature", "描述"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.layout.addWidget(self.table)

    def _load_data(self):
        self.table.setRowCount(0)
        config = self.main_window.opencode_config or {}
        agents = config.get("agent", {})

        for name, data in agents.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(data.get("mode", "subagent")))
            self.table.setItem(
                row, 2, QTableWidgetItem(str(data.get("temperature", "")))
            )
            self.table.setItem(
                row, 3, QTableWidgetItem(data.get("description", "")[:50])
            )

    def _on_add(self):
        dialog = OpenCodeAgentDialog(self.main_window, parent=self)
        if dialog.exec_():
            self._load_data()
            self.show_success("成功", "Agent 已添加")

    def _on_add_preset(self):
        dialog = PresetOpenCodeAgentDialog(self.main_window, parent=self)
        if dialog.exec_():
            self._load_data()
            self.show_success("成功", "预设 Agent 已添加")

    def _on_edit(self):
        row = self.table.currentRow()
        if row < 0:
            self.show_warning("提示", "请先选择一个 Agent")
            return

        name = self.table.item(row, 0).text()
        dialog = OpenCodeAgentDialog(self.main_window, agent_name=name, parent=self)
        if dialog.exec_():
            self._load_data()
            self.show_success("成功", "Agent 已更新")

    def _on_delete(self):
        row = self.table.currentRow()
        if row < 0:
            self.show_warning("提示", "请先选择一个 Agent")
            return

        name = self.table.item(row, 0).text()
        w = FluentMessageBox("确认删除", f'确定要删除 Agent "{name}" 吗？', self)
        if w.exec_():
            config = self.main_window.opencode_config or {}
            if "agent" in config and name in config["agent"]:
                del config["agent"][name]
                self.main_window.save_opencode_config()
                self._load_data()
                self.show_success("成功", f'Agent "{name}" 已删除')


class OpenCodeAgentDialog(QDialog):
    """OpenCode Agent 编辑对话框 - 完整版本"""

    def __init__(self, main_window, agent_name: str = None, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.agent_name = agent_name
        self.is_edit = agent_name is not None

        self.setWindowTitle("编辑 Agent" if self.is_edit else "添加 Agent")
        self.setMinimumSize(600, 700)
        self._setup_ui()

        if self.is_edit:
            self._load_agent_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 使用滚动区域
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(10)

        # ===== 基本信息 =====
        basic_card = CardWidget(content)
        basic_layout = QVBoxLayout(basic_card)
        basic_layout.addWidget(SubtitleLabel("基本信息", basic_card))

        # Agent 名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(BodyLabel("Agent 名称:", basic_card))
        self.name_edit = LineEdit(basic_card)
        self.name_edit.setPlaceholderText("如: build, plan, explore")
        if self.is_edit:
            self.name_edit.setEnabled(False)
        name_layout.addWidget(self.name_edit)
        basic_layout.addLayout(name_layout)

        # 描述
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(BodyLabel("描述:", basic_card))
        self.desc_edit = LineEdit(basic_card)
        self.desc_edit.setPlaceholderText("Agent 功能描述")
        desc_layout.addWidget(self.desc_edit)
        basic_layout.addLayout(desc_layout)

        # 模式
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(BodyLabel("模式:", basic_card))
        self.mode_combo = ComboBox(basic_card)
        self.mode_combo.addItems(["primary", "subagent", "all"])
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        basic_layout.addLayout(mode_layout)

        # 模型 (可选)
        model_layout = QHBoxLayout()
        model_layout.addWidget(BodyLabel("模型 (可选):", basic_card))
        self.model_edit = LineEdit(basic_card)
        self.model_edit.setPlaceholderText(
            "绑定特定模型，如: claude-sonnet-4-5-20250929"
        )
        model_layout.addWidget(self.model_edit)
        basic_layout.addLayout(model_layout)

        content_layout.addWidget(basic_card)

        # ===== 参数配置 =====
        param_card = CardWidget(content)
        param_layout = QVBoxLayout(param_card)
        param_layout.addWidget(SubtitleLabel("参数配置", param_card))

        # Temperature
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(BodyLabel("Temperature:", param_card))
        self.temp_slider = Slider(Qt.Orientation.Horizontal, param_card)
        self.temp_slider.setRange(0, 200)
        self.temp_slider.setValue(30)
        self.temp_label = BodyLabel("0.3", param_card)
        self.temp_slider.valueChanged.connect(
            lambda v: self.temp_label.setText(f"{v / 100:.1f}")
        )
        temp_layout.addWidget(self.temp_slider)
        temp_layout.addWidget(self.temp_label)
        param_layout.addLayout(temp_layout)

        # 最大步数
        steps_layout = QHBoxLayout()
        steps_layout.addWidget(BodyLabel("最大步数 (可选):", param_card))
        self.maxsteps_spin = SpinBox(param_card)
        self.maxsteps_spin.setRange(0, 1000)
        self.maxsteps_spin.setValue(0)
        self.maxsteps_spin.setSpecialValueText("不限制")
        steps_layout.addWidget(self.maxsteps_spin)
        steps_layout.addStretch()
        param_layout.addLayout(steps_layout)

        # 复选框
        check_layout = QHBoxLayout()
        self.hidden_check = CheckBox("隐藏 (仅 subagent)", param_card)
        check_layout.addWidget(self.hidden_check)
        self.disable_check = CheckBox("禁用此 Agent", param_card)
        check_layout.addWidget(self.disable_check)
        check_layout.addStretch()
        param_layout.addLayout(check_layout)

        content_layout.addWidget(param_card)

        # ===== 工具和权限配置 =====
        tools_card = CardWidget(content)
        tools_layout = QVBoxLayout(tools_card)
        tools_layout.addWidget(SubtitleLabel("工具和权限配置", tools_card))

        # 工具配置 (JSON)
        tools_layout.addWidget(BodyLabel("工具配置 (JSON):", tools_card))
        self.tools_edit = TextEdit(tools_card)
        self.tools_edit.setPlaceholderText(
            '{"write": true, "edit": true, "bash": true}'
        )
        self.tools_edit.setMaximumHeight(80)
        tools_layout.addWidget(self.tools_edit)

        # 权限配置 (JSON)
        tools_layout.addWidget(BodyLabel("权限配置 (JSON):", tools_card))
        self.permission_edit = TextEdit(tools_card)
        self.permission_edit.setPlaceholderText('{"edit": "allow", "bash": "ask"}')
        self.permission_edit.setMaximumHeight(80)
        tools_layout.addWidget(self.permission_edit)

        content_layout.addWidget(tools_card)

        # ===== 系统提示词 =====
        prompt_card = CardWidget(content)
        prompt_layout = QVBoxLayout(prompt_card)
        prompt_layout.addWidget(SubtitleLabel("系统提示词", prompt_card))
        self.prompt_edit = TextEdit(prompt_card)
        self.prompt_edit.setPlaceholderText("自定义系统提示词...")
        self.prompt_edit.setMinimumHeight(100)
        prompt_layout.addWidget(self.prompt_edit)

        content_layout.addWidget(prompt_card)
        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        # ===== 按钮 =====
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = PushButton("取消", self)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.save_btn = PrimaryPushButton("保存", self)
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
            InfoBar.error("错误", "请输入 Agent 名称", parent=self)
            return

        desc = self.desc_edit.text().strip()
        if not desc:
            InfoBar.error("错误", "请输入 Agent 描述", parent=self)
            return

        config = self.main_window.opencode_config
        if config is None:
            config = {}
            self.main_window.opencode_config = config

        if "agent" not in config:
            config["agent"] = {}

        if not self.is_edit and name in config["agent"]:
            InfoBar.error("错误", f'Agent "{name}" 已存在', parent=self)
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
                InfoBar.error("错误", f"工具配置 JSON 格式错误: {e}", parent=self)
                return

        # 权限配置
        perm_text = self.permission_edit.toPlainText().strip()
        if perm_text:
            try:
                permission = json.loads(perm_text)
                if permission:
                    agent_data["permission"] = permission
            except json.JSONDecodeError as e:
                InfoBar.error("错误", f"权限配置 JSON 格式错误: {e}", parent=self)
                return

        # 系统提示词
        prompt = self.prompt_edit.toPlainText().strip()
        if prompt:
            agent_data["prompt"] = prompt

        config["agent"][name] = agent_data
        self.main_window.save_opencode_config()
        self.accept()


class PresetOpenCodeAgentDialog(QDialog):
    """预设 OpenCode Agent 选择对话框"""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window

        self.setWindowTitle("从预设添加 Agent")
        self.setMinimumSize(450, 350)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        layout.addWidget(BodyLabel("选择预设 Agent:", self))

        self.agent_list = ListWidget(self)
        self.agent_list.setSelectionMode(QAbstractItemView.MultiSelection)
        for name, data in PRESET_OPENCODE_AGENTS.items():
            self.agent_list.addItem(f"{name} - {data.get('description', '')[:40]}")
        layout.addWidget(self.agent_list)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = PushButton("取消", self)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.add_btn = PrimaryPushButton("添加选中", self)
        self.add_btn.clicked.connect(self._on_add)
        btn_layout.addWidget(self.add_btn)

        layout.addLayout(btn_layout)

    def _on_add(self):
        selected = self.agent_list.selectedItems()
        if not selected:
            InfoBar.warning("提示", "请选择至少一个 Agent", parent=self)
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
        InfoBar.success("成功", f"已添加 {added} 个 Agent", parent=self)
        self.accept()


# ==================== Permission 页面 ====================
class PermissionPage(BasePage):
    """权限管理页面"""

    def __init__(self, main_window, parent=None):
        super().__init__("权限管理", parent)
        self.main_window = main_window
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        # 工具栏
        toolbar = QHBoxLayout()

        self.add_btn = PrimaryPushButton(FIF.ADD, "添加权限", self)
        self.add_btn.clicked.connect(self._on_add)
        toolbar.addWidget(self.add_btn)

        self.delete_btn = PushButton(FIF.DELETE, "删除", self)
        self.delete_btn.clicked.connect(self._on_delete)
        toolbar.addWidget(self.delete_btn)

        toolbar.addStretch()

        # 快捷按钮
        for tool in ["Bash", "Read", "Write", "Edit", "WebFetch"]:
            btn = PushButton(tool, self)
            btn.clicked.connect(lambda checked, t=tool: self._quick_add(t))
            toolbar.addWidget(btn)

        self.layout.addLayout(toolbar)

        # 权限列表
        self.table = TableWidget(self)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["工具名称", "权限级别"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.layout.addWidget(self.table)

    def _load_data(self):
        self.table.setRowCount(0)
        config = self.main_window.opencode_config or {}
        permissions = config.get("permission", {})

        for tool, level in permissions.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(tool))
            self.table.setItem(row, 1, QTableWidgetItem(str(level)))

    def _on_add(self):
        dialog = PermissionDialog(self.main_window, parent=self)
        if dialog.exec_():
            self._load_data()
            self.show_success("成功", "权限已添加")

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
        self.show_success("成功", f"已添加 {tool} = allow")

    def _on_delete(self):
        row = self.table.currentRow()
        if row < 0:
            self.show_warning("提示", "请先选择一个权限")
            return

        tool = self.table.item(row, 0).text()
        config = self.main_window.opencode_config or {}
        if "permission" in config and tool in config["permission"]:
            del config["permission"][tool]
            self.main_window.save_opencode_config()
            self._load_data()
            self.show_success("成功", f'权限 "{tool}" 已删除')


class PermissionDialog(QDialog):
    """权限编辑对话框"""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window

        self.setWindowTitle("添加权限")
        self.setMinimumWidth(400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 工具名称
        tool_layout = QHBoxLayout()
        tool_layout.addWidget(BodyLabel("工具名称:", self))
        self.tool_edit = LineEdit(self)
        self.tool_edit.setPlaceholderText("如: Bash, Read, mcp_*")
        tool_layout.addWidget(self.tool_edit)
        layout.addLayout(tool_layout)

        # 权限级别
        level_layout = QHBoxLayout()
        level_layout.addWidget(BodyLabel("权限级别:", self))
        self.level_combo = ComboBox(self)
        self.level_combo.addItems(["allow", "ask", "deny"])
        level_layout.addWidget(self.level_combo)
        layout.addLayout(level_layout)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = PushButton("取消", self)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.save_btn = PrimaryPushButton("保存", self)
        self.save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)

    def _on_save(self):
        tool = self.tool_edit.text().strip()
        if not tool:
            InfoBar.error("错误", "请输入工具名称", parent=self)
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
        super().__init__("帮助", parent)
        self.main_window = main_window
        self._setup_ui()

    def _setup_ui(self):
        # 关于卡片
        about_card = self.add_card("关于")
        about_layout = about_card.layout()

        about_layout.addWidget(
            TitleLabel(f"OpenCode Config Manager v{APP_VERSION}", about_card)
        )
        about_layout.addWidget(
            BodyLabel(
                "一个可视化的GUI工具，用于管理OpenCode和Oh My OpenCode的配置文件",
                about_card,
            )
        )
        about_layout.addWidget(BodyLabel(f"作者: {AUTHOR_NAME}", about_card))

        link_layout = QHBoxLayout()
        github_btn = PushButton(FIF.GITHUB, "GitHub", about_card)
        github_btn.clicked.connect(lambda: webbrowser.open(GITHUB_URL))
        link_layout.addWidget(github_btn)
        link_layout.addStretch()
        about_layout.addLayout(link_layout)

        # 配置优先级卡片
        priority_card = self.add_card("配置优先级（从高到低）")
        priority_layout = priority_card.layout()

        priorities = [
            "1. 远程配置 (Remote) - 通过 .well-known/opencode 获取",
            "2. 全局配置 (Global) - ~/.config/opencode/opencode.json",
            "3. 自定义配置 (Custom) - OPENCODE_CONFIG 环境变量指定",
            "4. 项目配置 (Project) - <项目>/opencode.json",
            "5. .opencode 目录 - <项目>/.opencode/config.json",
            "6. 内联配置 (Inline) - OPENCODE_CONFIG_CONTENT 环境变量",
        ]

        for p in priorities:
            priority_layout.addWidget(BodyLabel(p, priority_card))

        # 配置文件路径卡片
        paths_card = self.add_card("配置文件路径")
        paths_layout = paths_card.layout()

        paths_layout.addWidget(
            BodyLabel(f"OpenCode: {ConfigPaths.get_opencode_config()}", paths_card)
        )
        paths_layout.addWidget(
            BodyLabel(
                f"Oh My OpenCode: {ConfigPaths.get_ohmyopencode_config()}", paths_card
            )
        )
        paths_layout.addWidget(
            BodyLabel(f"备份目录: {ConfigPaths.get_backup_dir()}", paths_card)
        )

        self.layout.addStretch()


# ==================== 主窗口 ====================
class MainWindow(FluentWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()

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

        # 备份管理器
        self.backup_manager = BackupManager()

        # 版本检查器
        self.version_checker = VersionChecker(callback=self._on_version_check)

        self._init_window()
        self._init_navigation()

        # 异步检查更新
        QTimer.singleShot(1000, self.version_checker.check_update_async)

    def _init_window(self):
        self.setWindowTitle(f"OpenCode Config Manager v{APP_VERSION}")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)

        # 设置主题
        setTheme(Theme.AUTO)

    def _init_navigation(self):
        # ===== OpenCode 配置 =====
        # Provider 页面
        self.provider_page = ProviderPage(self)
        self.addSubInterface(self.provider_page, FIF.PEOPLE, "Provider")

        # Model 页面
        self.model_page = ModelPage(self)
        self.addSubInterface(self.model_page, FIF.ROBOT, "Model")

        # MCP 页面
        self.mcp_page = MCPPage(self)
        self.addSubInterface(self.mcp_page, FIF.CLOUD, "MCP")

        # OpenCode Agent 页面
        self.opencode_agent_page = OpenCodeAgentPage(self)
        self.addSubInterface(self.opencode_agent_page, FIF.COMMAND_PROMPT, "Agent")

        # Permission 页面
        self.permission_page = PermissionPage(self)
        self.addSubInterface(self.permission_page, FIF.CERTIFICATE, "Permission")

        # Skill 页面
        self.skill_page = SkillPage(self)
        self.addSubInterface(self.skill_page, FIF.BOOK_SHELF, "Skill")

        # Rules 页面
        self.rules_page = RulesPage(self)
        self.addSubInterface(self.rules_page, FIF.DOCUMENT, "Rules")

        # Compaction 页面
        self.compaction_page = CompactionPage(self)
        self.addSubInterface(self.compaction_page, FIF.ZIP_FOLDER, "Compaction")

        # ===== Oh My OpenCode 配置 =====
        # Oh My Agent 页面
        self.ohmy_agent_page = OhMyAgentPage(self)
        self.addSubInterface(self.ohmy_agent_page, FIF.EMOJI_TAB_SYMBOLS, "Oh My Agent")

        # Category 页面
        self.category_page = CategoryPage(self)
        self.addSubInterface(self.category_page, FIF.TAG, "Category")

        # ===== 工具 =====
        # Import 页面
        self.import_page = ImportPage(self)
        self.addSubInterface(self.import_page, FIF.DOWNLOAD, "Import")

        # ===== 底部导航 =====
        # Backup 按钮
        self.navigationInterface.addItem(
            routeKey="backup",
            icon=FIF.HISTORY,
            text="Backup",
            onClick=self._show_backup_dialog,
            position=NavigationItemPosition.BOTTOM,
        )

        # Help 页面 (底部)
        self.help_page = HelpPage(self)
        self.addSubInterface(
            self.help_page, FIF.HELP, "Help", NavigationItemPosition.BOTTOM
        )

    def _show_backup_dialog(self):
        """显示备份管理对话框"""
        dialog = BackupDialog(self, parent=self)
        dialog.exec_()

    def save_opencode_config(self):
        """保存 OpenCode 配置"""
        if ConfigManager.save_json(
            ConfigPaths.get_opencode_config(), self.opencode_config
        ):
            return True
        return False

    def save_ohmyopencode_config(self):
        """保存 Oh My OpenCode 配置"""
        if ConfigManager.save_json(
            ConfigPaths.get_ohmyopencode_config(), self.ohmyopencode_config
        ):
            return True
        return False

    def _on_version_check(self, latest_version: str, release_url: str):
        """版本检查回调"""
        if VersionChecker.compare_versions(APP_VERSION, latest_version):
            InfoBar.info(
                title="发现新版本",
                content=f"v{latest_version} 可用，点击查看",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=10000,
                parent=self,
            )


# ==================== Oh My Agent 页面 ====================
class OhMyAgentPage(BasePage):
    """Oh My OpenCode Agent 管理页面"""

    def __init__(self, main_window, parent=None):
        super().__init__("Oh My Agent", parent)
        self.main_window = main_window
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        # 工具栏
        toolbar = QHBoxLayout()

        self.add_btn = PrimaryPushButton(FIF.ADD, "添加 Agent", self)
        self.add_btn.clicked.connect(self._on_add)
        toolbar.addWidget(self.add_btn)

        self.preset_btn = PushButton(FIF.LIBRARY, "从预设添加", self)
        self.preset_btn.clicked.connect(self._on_add_preset)
        toolbar.addWidget(self.preset_btn)

        self.edit_btn = PushButton(FIF.EDIT, "编辑", self)
        self.edit_btn.clicked.connect(self._on_edit)
        toolbar.addWidget(self.edit_btn)

        self.delete_btn = PushButton(FIF.DELETE, "删除", self)
        self.delete_btn.clicked.connect(self._on_delete)
        toolbar.addWidget(self.delete_btn)

        toolbar.addStretch()
        self.layout.addLayout(toolbar)

        # Agent 列表
        self.table = TableWidget(self)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["名称", "绑定模型", "描述"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.layout.addWidget(self.table)

    def _load_data(self):
        """加载 Agent 数据"""
        self.table.setRowCount(0)
        config = self.main_window.ohmyopencode_config or {}
        agents = config.get("agents", {})

        for name, data in agents.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(data.get("model", "")))
            self.table.setItem(
                row, 2, QTableWidgetItem(data.get("description", "")[:50])
            )

    def _on_add(self):
        """添加 Agent"""
        dialog = OhMyAgentDialog(self.main_window, parent=self)
        if dialog.exec_():
            self._load_data()
            self.show_success("成功", "Agent 已添加")

    def _on_add_preset(self):
        """从预设添加 Agent"""
        dialog = PresetOhMyAgentDialog(self.main_window, parent=self)
        if dialog.exec_():
            self._load_data()
            self.show_success("成功", "预设 Agent 已添加")

    def _on_edit(self):
        """编辑 Agent"""
        row = self.table.currentRow()
        if row < 0:
            self.show_warning("提示", "请先选择一个 Agent")
            return

        name = self.table.item(row, 0).text()
        dialog = OhMyAgentDialog(self.main_window, agent_name=name, parent=self)
        if dialog.exec_():
            self._load_data()
            self.show_success("成功", "Agent 已更新")

    def _on_delete(self):
        """删除 Agent"""
        row = self.table.currentRow()
        if row < 0:
            self.show_warning("提示", "请先选择一个 Agent")
            return

        name = self.table.item(row, 0).text()
        w = FluentMessageBox("确认删除", f'确定要删除 Agent "{name}" 吗？', self)
        if w.exec_():
            config = self.main_window.ohmyopencode_config or {}
            if "agents" in config and name in config["agents"]:
                del config["agents"][name]
                self.main_window.save_ohmyopencode_config()
                self._load_data()
                self.show_success("成功", f'Agent "{name}" 已删除')


class OhMyAgentDialog(QDialog):
    """Oh My Agent 编辑对话框"""

    def __init__(self, main_window, agent_name: str = None, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.agent_name = agent_name
        self.is_edit = agent_name is not None

        self.setWindowTitle("编辑 Agent" if self.is_edit else "添加 Agent")
        self.setMinimumWidth(450)
        self._setup_ui()

        if self.is_edit:
            self._load_agent_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Agent 名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(BodyLabel("Agent 名称:", self))
        self.name_edit = LineEdit(self)
        self.name_edit.setPlaceholderText("如: oracle, librarian, explore")
        if self.is_edit:
            self.name_edit.setEnabled(False)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        # 绑定模型
        model_layout = QHBoxLayout()
        model_layout.addWidget(BodyLabel("绑定模型:", self))
        self.model_combo = ComboBox(self)
        self._load_models()
        model_layout.addWidget(self.model_combo)
        layout.addLayout(model_layout)

        # 描述
        layout.addWidget(BodyLabel("描述:", self))
        self.desc_edit = TextEdit(self)
        self.desc_edit.setPlaceholderText("描述 Agent 的功能和适用场景")
        self.desc_edit.setMaximumHeight(100)
        layout.addWidget(self.desc_edit)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = PushButton("取消", self)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.save_btn = PrimaryPushButton("保存", self)
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
            InfoBar.error("错误", "请输入 Agent 名称", parent=self)
            return

        config = self.main_window.ohmyopencode_config
        if config is None:
            config = {}
            self.main_window.ohmyopencode_config = config

        if "agents" not in config:
            config["agents"] = {}

        # 检查名称冲突
        if not self.is_edit and name in config["agents"]:
            InfoBar.error("错误", f'Agent "{name}" 已存在', parent=self)
            return

        # 保存数据
        config["agents"][name] = {
            "model": self.model_combo.currentText(),
            "description": self.desc_edit.toPlainText().strip(),
        }

        self.main_window.save_ohmyopencode_config()
        self.accept()


class PresetOhMyAgentDialog(QDialog):
    """预设 Oh My Agent 选择对话框"""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window

        self.setWindowTitle("从预设添加 Agent")
        self.setMinimumWidth(500)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        layout.addWidget(SubtitleLabel("选择预设 Agent", self))

        # 预设列表
        self.list_widget = ListWidget(self)
        for name, desc in PRESET_AGENTS.items():
            self.list_widget.addItem(f"{name} - {desc}")
        layout.addWidget(self.list_widget)

        # 绑定模型
        model_layout = QHBoxLayout()
        model_layout.addWidget(BodyLabel("绑定模型:", self))
        self.model_combo = ComboBox(self)
        self._load_models()
        model_layout.addWidget(self.model_combo)
        layout.addLayout(model_layout)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = PushButton("取消", self)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.add_btn = PrimaryPushButton("添加", self)
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
            InfoBar.warning("提示", "请选择一个预设 Agent", parent=self)
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
            InfoBar.warning("提示", f'Agent "{name}" 已存在', parent=self)
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
        super().__init__("Category 管理", parent)
        self.main_window = main_window
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        # 工具栏
        toolbar = QHBoxLayout()

        self.add_btn = PrimaryPushButton(FIF.ADD, "添加 Category", self)
        self.add_btn.clicked.connect(self._on_add)
        toolbar.addWidget(self.add_btn)

        self.preset_btn = PushButton(FIF.LIBRARY, "从预设添加", self)
        self.preset_btn.clicked.connect(self._on_add_preset)
        toolbar.addWidget(self.preset_btn)

        self.edit_btn = PushButton(FIF.EDIT, "编辑", self)
        self.edit_btn.clicked.connect(self._on_edit)
        toolbar.addWidget(self.edit_btn)

        self.delete_btn = PushButton(FIF.DELETE, "删除", self)
        self.delete_btn.clicked.connect(self._on_delete)
        toolbar.addWidget(self.delete_btn)

        toolbar.addStretch()
        self.layout.addLayout(toolbar)

        # Category 列表
        self.table = TableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["名称", "绑定模型", "Temperature", "描述"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.layout.addWidget(self.table)

    def _load_data(self):
        """加载 Category 数据"""
        self.table.setRowCount(0)
        config = self.main_window.ohmyopencode_config or {}
        categories = config.get("categories", {})

        for name, data in categories.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(data.get("model", "")))
            self.table.setItem(
                row, 2, QTableWidgetItem(str(data.get("temperature", 0.7)))
            )
            self.table.setItem(
                row, 3, QTableWidgetItem(data.get("description", "")[:30])
            )

    def _on_add(self):
        dialog = CategoryDialog(self.main_window, parent=self)
        if dialog.exec_():
            self._load_data()
            self.show_success("成功", "Category 已添加")

    def _on_add_preset(self):
        dialog = PresetCategoryDialog(self.main_window, parent=self)
        if dialog.exec_():
            self._load_data()
            self.show_success("成功", "预设 Category 已添加")

    def _on_edit(self):
        row = self.table.currentRow()
        if row < 0:
            self.show_warning("提示", "请先选择一个 Category")
            return

        name = self.table.item(row, 0).text()
        dialog = CategoryDialog(self.main_window, category_name=name, parent=self)
        if dialog.exec_():
            self._load_data()
            self.show_success("成功", "Category 已更新")

    def _on_delete(self):
        row = self.table.currentRow()
        if row < 0:
            self.show_warning("提示", "请先选择一个 Category")
            return

        name = self.table.item(row, 0).text()
        w = FluentMessageBox("确认删除", f'确定要删除 Category "{name}" 吗？', self)
        if w.exec_():
            config = self.main_window.ohmyopencode_config or {}
            if "categories" in config and name in config["categories"]:
                del config["categories"][name]
                self.main_window.save_ohmyopencode_config()
                self._load_data()
                self.show_success("成功", f'Category "{name}" 已删除')


class CategoryDialog(QDialog):
    """Category 编辑对话框"""

    def __init__(self, main_window, category_name: str = None, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.category_name = category_name
        self.is_edit = category_name is not None

        self.setWindowTitle("编辑 Category" if self.is_edit else "添加 Category")
        self.setMinimumWidth(450)
        self._setup_ui()

        if self.is_edit:
            self._load_category_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Category 名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(BodyLabel("Category 名称:", self))
        self.name_edit = LineEdit(self)
        self.name_edit.setPlaceholderText("如: visual, business-logic")
        if self.is_edit:
            self.name_edit.setEnabled(False)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        # 绑定模型
        model_layout = QHBoxLayout()
        model_layout.addWidget(BodyLabel("绑定模型:", self))
        self.model_combo = ComboBox(self)
        self._load_models()
        model_layout.addWidget(self.model_combo)
        layout.addLayout(model_layout)

        # Temperature 滑块
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(BodyLabel("Temperature:", self))
        self.temp_slider = Slider(Qt.Horizontal, self)
        self.temp_slider.setRange(0, 200)  # 0.0 - 2.0
        self.temp_slider.setValue(70)  # 默认 0.7
        self.temp_slider.valueChanged.connect(self._on_temp_changed)
        temp_layout.addWidget(self.temp_slider)
        self.temp_label = BodyLabel("0.7", self)
        self.temp_label.setMinimumWidth(40)
        temp_layout.addWidget(self.temp_label)
        layout.addLayout(temp_layout)

        # 描述
        layout.addWidget(BodyLabel("描述:", self))
        self.desc_edit = TextEdit(self)
        self.desc_edit.setPlaceholderText("描述该分类的用途和适用场景")
        self.desc_edit.setMaximumHeight(80)
        layout.addWidget(self.desc_edit)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = PushButton("取消", self)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.save_btn = PrimaryPushButton("保存", self)
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
            InfoBar.error("错误", "请输入 Category 名称", parent=self)
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


class PresetCategoryDialog(QDialog):
    """预设 Category 选择对话框"""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window

        self.setWindowTitle("从预设添加 Category")
        self.setMinimumWidth(500)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        layout.addWidget(SubtitleLabel("选择预设 Category", self))

        # 预设列表
        self.list_widget = ListWidget(self)
        for name, data in PRESET_CATEGORIES.items():
            temp = data.get("temperature", 0.7)
            desc = data.get("description", "")
            self.list_widget.addItem(f"{name} (temp={temp}) - {desc}")
        layout.addWidget(self.list_widget)

        # 绑定模型
        model_layout = QHBoxLayout()
        model_layout.addWidget(BodyLabel("绑定模型:", self))
        self.model_combo = ComboBox(self)
        self._load_models()
        model_layout.addWidget(self.model_combo)
        layout.addLayout(model_layout)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = PushButton("取消", self)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.add_btn = PrimaryPushButton("添加", self)
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
            InfoBar.warning("提示", "请选择一个预设 Category", parent=self)
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
            InfoBar.warning("提示", f'Category "{name}" 已存在', parent=self)
            return

        config["categories"][name] = {
            "model": self.model_combo.currentText(),
            "temperature": preset.get("temperature", 0.7),
            "description": preset.get("description", ""),
        }

        self.main_window.save_ohmyopencode_config()
        self.accept()


# ==================== Skill 页面 ====================
class SkillPage(BasePage):
    """Skill 权限配置和 SKILL.md 创建页面"""

    def __init__(self, main_window, parent=None):
        super().__init__("Skill 管理", parent)
        self.main_window = main_window
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        # 说明卡片
        desc_card = self.add_card("Skill 权限配置")
        desc_layout = desc_card.layout()
        desc_layout.addWidget(
            BodyLabel(
                "配置 Skill 的加载权限。Skill 是可复用的指令文件，Agent 可按需加载。",
                desc_card,
            )
        )

        # 权限列表工具栏
        toolbar = QHBoxLayout()

        self.add_btn = PrimaryPushButton(FIF.ADD, "添加权限", self)
        self.add_btn.clicked.connect(self._on_add)
        toolbar.addWidget(self.add_btn)

        self.delete_btn = PushButton(FIF.DELETE, "删除", self)
        self.delete_btn.clicked.connect(self._on_delete)
        toolbar.addWidget(self.delete_btn)

        toolbar.addStretch()
        self.layout.addLayout(toolbar)

        # 权限列表
        self.table = TableWidget(self)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["模式", "权限"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self._on_select)
        self.layout.addWidget(self.table)

        # 编辑区域
        edit_card = self.add_card("编辑权限")
        edit_layout = edit_card.layout()

        # 模式输入
        pattern_layout = QHBoxLayout()
        pattern_layout.addWidget(BodyLabel("模式:", edit_card))
        self.pattern_edit = LineEdit(edit_card)
        self.pattern_edit.setPlaceholderText("如: *, internal-*, my-skill")
        pattern_layout.addWidget(self.pattern_edit)
        edit_layout.addLayout(pattern_layout)

        # 权限选择
        perm_layout = QHBoxLayout()
        perm_layout.addWidget(BodyLabel("权限:", edit_card))
        self.perm_combo = ComboBox(edit_card)
        self.perm_combo.addItems(["allow", "ask", "deny"])
        perm_layout.addWidget(self.perm_combo)
        perm_layout.addStretch()
        edit_layout.addLayout(perm_layout)

        # 保存按钮
        save_btn = PrimaryPushButton("保存权限", edit_card)
        save_btn.clicked.connect(self._on_save)
        edit_layout.addWidget(save_btn)

        # 创建 SKILL.md 卡片
        create_card = self.add_card("创建 SKILL.md")
        create_layout = create_card.layout()

        # Skill 名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(BodyLabel("Skill 名称:", create_card))
        self.skill_name_edit = LineEdit(create_card)
        self.skill_name_edit.setPlaceholderText(
            "小写字母、数字、连字符，如: git-release"
        )
        name_layout.addWidget(self.skill_name_edit)
        create_layout.addLayout(name_layout)

        # Skill 描述
        desc_layout2 = QHBoxLayout()
        desc_layout2.addWidget(BodyLabel("描述:", create_card))
        self.skill_desc_edit = LineEdit(create_card)
        self.skill_desc_edit.setPlaceholderText("描述 Skill 的功能")
        desc_layout2.addWidget(self.skill_desc_edit)
        create_layout.addLayout(desc_layout2)

        # Skill 内容
        create_layout.addWidget(BodyLabel("Skill 内容 (Markdown):", create_card))
        self.skill_content_edit = TextEdit(create_card)
        self.skill_content_edit.setPlaceholderText(
            "## What I do\n- 描述功能\n\n## Instructions\n- 具体指令"
        )
        self.skill_content_edit.setMaximumHeight(150)
        create_layout.addWidget(self.skill_content_edit)

        # 保存位置
        loc_layout = QHBoxLayout()
        loc_layout.addWidget(BodyLabel("保存位置:", create_card))
        self.global_radio = RadioButton("全局 (~/.config/opencode/skill/)", create_card)
        self.global_radio.setChecked(True)
        loc_layout.addWidget(self.global_radio)
        self.project_radio = RadioButton("项目 (.opencode/skill/)", create_card)
        loc_layout.addWidget(self.project_radio)
        loc_layout.addStretch()
        create_layout.addLayout(loc_layout)

        # 创建按钮
        create_btn = PrimaryPushButton("创建 SKILL.md", create_card)
        create_btn.clicked.connect(self._on_create_skill)
        create_layout.addWidget(create_btn)

        self.layout.addStretch()

    def _load_data(self):
        """加载 Skill 权限数据"""
        self.table.setRowCount(0)
        config = self.main_window.opencode_config or {}
        permissions = config.get("permission", {}).get("skill", {})

        if isinstance(permissions, dict):
            for pattern, perm in permissions.items():
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(pattern))
                self.table.setItem(row, 1, QTableWidgetItem(perm))
        elif isinstance(permissions, str):
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem("*"))
            self.table.setItem(row, 1, QTableWidgetItem(permissions))

    def _on_select(self):
        row = self.table.currentRow()
        if row >= 0:
            pattern_item = self.table.item(row, 0)
            perm_item = self.table.item(row, 1)
            if pattern_item:
                self.pattern_edit.setText(pattern_item.text())
            if perm_item:
                self.perm_combo.setCurrentText(perm_item.text())

    def _on_add(self):
        self.pattern_edit.setText("")
        self.perm_combo.setCurrentText("ask")

    def _on_delete(self):
        row = self.table.currentRow()
        if row < 0:
            self.show_warning("提示", "请先选择一个权限")
            return

        pattern = self.table.item(row, 0).text()
        w = FluentMessageBox(
            "确认删除", f'确定要删除 Skill 权限 "{pattern}" 吗？', self
        )
        if w.exec_():
            config = self.main_window.opencode_config or {}
            skill_perms = config.get("permission", {}).get("skill", {})
            if isinstance(skill_perms, dict) and pattern in skill_perms:
                del skill_perms[pattern]
                self.main_window.save_opencode_config()
                self._load_data()
                self.show_success("成功", f'权限 "{pattern}" 已删除')

    def _on_save(self):
        pattern = self.pattern_edit.text().strip()
        if not pattern:
            self.show_warning("提示", "请输入模式")
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

        config["permission"]["skill"][pattern] = self.perm_combo.currentText()
        self.main_window.save_opencode_config()
        self._load_data()
        self.show_success("成功", f'Skill 权限 "{pattern}" 已保存')

    def _on_create_skill(self):
        name = self.skill_name_edit.text().strip()
        desc = self.skill_desc_edit.text().strip()
        content = self.skill_content_edit.toPlainText().strip()

        if not name:
            self.show_warning("提示", "请输入 Skill 名称")
            return
        if not desc:
            self.show_warning("提示", "请输入 Skill 描述")
            return

        # 验证名称格式
        import re

        if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", name):
            self.show_error("错误", "Skill 名称格式错误！要求：小写字母、数字、连字符")
            return

        # 确定保存路径
        if self.global_radio.isChecked():
            base_path = Path.home() / ".config" / "opencode" / "skill"
        else:
            base_path = Path.cwd() / ".opencode" / "skill"

        skill_dir = base_path / name
        skill_file = skill_dir / "SKILL.md"

        try:
            skill_dir.mkdir(parents=True, exist_ok=True)
            default_content = "## What I do\n- 描述功能\n\n## Instructions\n- 具体指令"
            skill_content = f"""---
name: {name}
description: {desc}
---

{content if content else default_content}
"""
            with open(skill_file, "w", encoding="utf-8") as f:
                f.write(skill_content)

            self.show_success("成功", f"Skill 已创建: {skill_file}")
        except Exception as e:
            self.show_error("错误", f"创建失败: {e}")


# ==================== Rules 页面 ====================
class RulesPage(BasePage):
    """Rules/Instructions 管理和 AGENTS.md 编辑页面"""

    def __init__(self, main_window, parent=None):
        super().__init__("Rules 管理", parent)
        self.main_window = main_window
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        # Instructions 配置卡片
        inst_card = self.add_card("Instructions 配置")
        inst_layout = inst_card.layout()

        inst_layout.addWidget(
            BodyLabel(
                "配置额外的指令文件，这些文件会与 AGENTS.md 合并加载。", inst_card
            )
        )

        # Instructions 列表
        self.inst_list = ListWidget(inst_card)
        self.inst_list.setMaximumHeight(120)
        inst_layout.addWidget(self.inst_list)

        # 添加输入
        add_layout = QHBoxLayout()
        self.inst_path_edit = LineEdit(inst_card)
        self.inst_path_edit.setPlaceholderText(
            "文件路径，如: CONTRIBUTING.md, docs/*.md"
        )
        add_layout.addWidget(self.inst_path_edit)

        add_btn = PushButton(FIF.ADD, "添加", inst_card)
        add_btn.clicked.connect(self._on_add_instruction)
        add_layout.addWidget(add_btn)

        del_btn = PushButton(FIF.DELETE, "删除", inst_card)
        del_btn.clicked.connect(self._on_delete_instruction)
        add_layout.addWidget(del_btn)

        inst_layout.addLayout(add_layout)

        # 快捷路径
        quick_layout = QHBoxLayout()
        quick_layout.addWidget(BodyLabel("快捷:", inst_card))
        for path in ["CONTRIBUTING.md", "docs/*.md", ".cursor/rules/*.md"]:
            btn = PushButton(path, inst_card)
            btn.clicked.connect(lambda checked, p=path: self.inst_path_edit.setText(p))
            quick_layout.addWidget(btn)
        quick_layout.addStretch()
        inst_layout.addLayout(quick_layout)

        # 保存按钮
        save_inst_btn = PrimaryPushButton("保存 Instructions", inst_card)
        save_inst_btn.clicked.connect(self._on_save_instructions)
        inst_layout.addWidget(save_inst_btn)

        # AGENTS.md 编辑卡片
        agents_card = self.add_card("AGENTS.md 编辑")
        agents_layout = agents_card.layout()

        # 位置选择
        loc_layout = QHBoxLayout()
        loc_layout.addWidget(BodyLabel("编辑位置:", agents_card))
        self.global_radio = RadioButton("全局", agents_card)
        self.global_radio.setChecked(True)
        self.global_radio.clicked.connect(self._load_agents_md)
        loc_layout.addWidget(self.global_radio)
        self.project_radio = RadioButton("项目", agents_card)
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
        save_btn = PrimaryPushButton("保存 AGENTS.md", agents_card)
        save_btn.clicked.connect(self._on_save_agents_md)
        btn_layout.addWidget(save_btn)

        reload_btn = PushButton("重新加载", agents_card)
        reload_btn.clicked.connect(self._load_agents_md)
        btn_layout.addWidget(reload_btn)

        template_btn = PushButton("使用模板", agents_card)
        template_btn.clicked.connect(self._use_template)
        btn_layout.addWidget(template_btn)

        btn_layout.addStretch()
        agents_layout.addLayout(btn_layout)

        self.layout.addStretch()

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
            self.show_warning("提示", "请输入文件路径")
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
            self.show_warning("提示", "请先选择一个路径")
            return

        path = current.text()
        config = self.main_window.opencode_config or {}
        instructions = config.get("instructions", [])
        if path in instructions:
            instructions.remove(path)
            self._load_data()

    def _on_save_instructions(self):
        self.main_window.save_opencode_config()
        self.show_success("成功", "Instructions 配置已保存")

    def _get_agents_path(self) -> Path:
        if self.global_radio.isChecked():
            return Path.home() / ".config" / "opencode" / "AGENTS.md"
        else:
            return Path.cwd() / "AGENTS.md"

    def _load_agents_md(self):
        path = self._get_agents_path()
        self.path_label.setText(f"路径: {path}")

        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.agents_edit.setPlainText(content)
            except Exception as e:
                self.agents_edit.setPlainText(f"# 读取失败: {e}")
        else:
            self.agents_edit.setPlainText(
                '# AGENTS.md 文件不存在\n# 点击"使用模板"创建新文件'
            )

    def _on_save_agents_md(self):
        path = self._get_agents_path()
        content = self.agents_edit.toPlainText()

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            self.show_success("成功", f"AGENTS.md 已保存: {path}")
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
        super().__init__("Compaction 配置", parent)
        self.main_window = main_window
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        # 说明卡片
        desc_card = self.add_card("上下文压缩 (Compaction)")
        desc_layout = desc_card.layout()

        desc_layout.addWidget(
            BodyLabel(
                "上下文压缩用于在会话上下文接近满时自动压缩，以节省 tokens 并保持会话连续性。",
                desc_card,
            )
        )

        # auto 选项
        self.auto_check = CheckBox(
            "自动压缩 (auto) - 当上下文已满时自动压缩会话", desc_card
        )
        self.auto_check.setChecked(True)
        desc_layout.addWidget(self.auto_check)

        # prune 选项
        self.prune_check = CheckBox(
            "修剪旧输出 (prune) - 删除旧的工具输出以节省 tokens", desc_card
        )
        self.prune_check.setChecked(True)
        desc_layout.addWidget(self.prune_check)

        # 保存按钮
        save_btn = PrimaryPushButton("保存设置", desc_card)
        save_btn.clicked.connect(self._on_save)
        desc_layout.addWidget(save_btn)

        # 配置预览卡片
        preview_card = self.add_card("配置预览")
        preview_layout = preview_card.layout()

        self.preview_edit = TextEdit(preview_card)
        self.preview_edit.setReadOnly(True)
        self.preview_edit.setMaximumHeight(150)
        preview_layout.addWidget(self.preview_edit)

        self.layout.addStretch()

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
        self.show_success("成功", "上下文压缩配置已保存")


# ==================== Import 页面 ====================
class ImportPage(BasePage):
    """外部配置导入页面"""

    def __init__(self, main_window, parent=None):
        super().__init__("外部导入", parent)
        self.main_window = main_window
        self.import_service = ImportService()
        self._setup_ui()

    def _setup_ui(self):
        # 检测到的配置卡片
        detect_card = self.add_card("检测到的外部配置")
        detect_layout = detect_card.layout()

        # 刷新按钮
        refresh_btn = PrimaryPushButton(FIF.SYNC, "刷新检测", detect_card)
        refresh_btn.clicked.connect(self._refresh_scan)
        detect_layout.addWidget(refresh_btn)

        # 配置列表
        self.config_table = TableWidget(detect_card)
        self.config_table.setColumnCount(3)
        self.config_table.setHorizontalHeaderLabels(["来源", "配置路径", "状态"])
        self.config_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.config_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.config_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.config_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.config_table.itemSelectionChanged.connect(self._on_select)
        self.config_table.setMaximumHeight(180)
        detect_layout.addWidget(self.config_table)

        # 预览卡片
        preview_card = self.add_card("配置预览与转换结果")
        preview_layout = preview_card.layout()

        # 原始配置预览
        preview_layout.addWidget(BodyLabel("原始配置:", preview_card))
        self.preview_edit = TextEdit(preview_card)
        self.preview_edit.setReadOnly(True)
        self.preview_edit.setMaximumHeight(120)
        preview_layout.addWidget(self.preview_edit)

        # 转换结果预览
        preview_layout.addWidget(BodyLabel("转换为 OpenCode 格式:", preview_card))
        self.convert_edit = TextEdit(preview_card)
        self.convert_edit.setReadOnly(True)
        self.convert_edit.setMaximumHeight(120)
        preview_layout.addWidget(self.convert_edit)

        # 按钮
        btn_layout = QHBoxLayout()

        preview_btn = PushButton("预览转换", preview_card)
        preview_btn.clicked.connect(self._preview_convert)
        btn_layout.addWidget(preview_btn)

        import_btn = PrimaryPushButton("导入到 OpenCode", preview_card)
        import_btn.clicked.connect(self._import_selected)
        btn_layout.addWidget(import_btn)

        btn_layout.addStretch()
        preview_layout.addLayout(btn_layout)

        self.layout.addStretch()

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
            self.config_table.setItem(row, 1, QTableWidgetItem(info["path"]))
            status = "已检测" if info["exists"] else "未找到"
            self.config_table.setItem(row, 2, QTableWidgetItem(status))

    def _on_select(self):
        """选中配置时显示预览"""
        row = self.config_table.currentRow()
        if row < 0:
            return

        source = self.config_table.item(row, 0).text()
        results = self.import_service.scan_external_configs()

        if source in results and results[source]["data"]:
            import json

            self.preview_edit.setPlainText(
                json.dumps(results[source]["data"], indent=2, ensure_ascii=False)
            )
            self.convert_edit.setPlainText("")
        else:
            self.preview_edit.setPlainText("无数据")
            self.convert_edit.setPlainText("")

    def _preview_convert(self):
        """预览转换结果"""
        row = self.config_table.currentRow()
        if row < 0:
            self.show_warning("提示", "请先选择要转换的配置")
            return

        source = self.config_table.item(row, 0).text()
        results = self.import_service.scan_external_configs()

        if source in results and results[source]["data"]:
            source_type = results[source].get("type", "")
            converted = self.import_service.convert_to_opencode(
                source_type, results[source]["data"]
            )
            if converted:
                import json

                self.convert_edit.setPlainText(
                    json.dumps(converted, indent=2, ensure_ascii=False)
                )
            else:
                self.show_warning("提示", "无法转换此配置格式")

    def _import_selected(self):
        """导入选中的配置"""
        row = self.config_table.currentRow()
        if row < 0:
            self.show_warning("提示", "请先选择要导入的配置")
            return

        source = self.config_table.item(row, 0).text()
        results = self.import_service.scan_external_configs()

        if source not in results or not results[source]["data"]:
            self.show_warning("提示", "所选配置不存在或为空")
            return

        source_type = results[source].get("type", "")
        converted = self.import_service.convert_to_opencode(
            source_type, results[source]["data"]
        )

        if not converted:
            self.show_warning("提示", "无法转换此配置格式")
            return

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
            self.show_success("成功", f"已导入 {source} 的配置")


# ==================== Backup 对话框 ====================
class BackupDialog(QDialog):
    """备份恢复对话框"""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.backup_manager = main_window.backup_manager

        self.setWindowTitle("备份管理")
        self.setMinimumSize(600, 400)
        self._setup_ui()
        self._load_backups()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # 工具栏
        toolbar = QHBoxLayout()

        backup_opencode_btn = PrimaryPushButton(FIF.SAVE, "备份 OpenCode", self)
        backup_opencode_btn.clicked.connect(self._backup_opencode)
        toolbar.addWidget(backup_opencode_btn)

        backup_ohmy_btn = PushButton(FIF.SAVE, "备份 Oh My OpenCode", self)
        backup_ohmy_btn.clicked.connect(self._backup_ohmyopencode)
        toolbar.addWidget(backup_ohmy_btn)

        toolbar.addStretch()

        refresh_btn = PushButton(FIF.SYNC, "刷新", self)
        refresh_btn.clicked.connect(self._load_backups)
        toolbar.addWidget(refresh_btn)

        layout.addLayout(toolbar)

        # 备份列表
        layout.addWidget(SubtitleLabel("备份列表", self))

        self.backup_table = TableWidget(self)
        self.backup_table.setColumnCount(4)
        self.backup_table.setHorizontalHeaderLabels(
            ["配置文件", "时间", "标签", "路径"]
        )
        self.backup_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.backup_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.backup_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.backup_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.backup_table)

        # 操作按钮
        btn_layout = QHBoxLayout()

        restore_btn = PrimaryPushButton("恢复选中备份", self)
        restore_btn.clicked.connect(self._restore_backup)
        btn_layout.addWidget(restore_btn)

        delete_btn = PushButton(FIF.DELETE, "删除备份", self)
        delete_btn.clicked.connect(self._delete_backup)
        btn_layout.addWidget(delete_btn)

        btn_layout.addStretch()

        close_btn = PushButton("关闭", self)
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
            self.backup_table.setItem(row, 3, QTableWidgetItem(str(backup["path"])))

    def _backup_opencode(self):
        """备份 OpenCode 配置"""
        path = self.backup_manager.backup(
            ConfigPaths.get_opencode_config(), tag="manual"
        )
        if path:
            InfoBar.success("成功", f"已备份到: {path}", parent=self)
            self._load_backups()
        else:
            InfoBar.error("错误", "备份失败", parent=self)

    def _backup_ohmyopencode(self):
        """备份 Oh My OpenCode 配置"""
        path = self.backup_manager.backup(
            ConfigPaths.get_ohmyopencode_config(), tag="manual"
        )
        if path:
            InfoBar.success("成功", f"已备份到: {path}", parent=self)
            self._load_backups()
        else:
            InfoBar.error("错误", "备份失败", parent=self)

    def _restore_backup(self):
        """恢复备份"""
        row = self.backup_table.currentRow()
        if row < 0:
            InfoBar.warning("提示", "请先选择一个备份", parent=self)
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
                InfoBar.success("成功", "备份已恢复", parent=self)
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
                InfoBar.error("错误", "恢复失败", parent=self)

    def _delete_backup(self):
        """删除备份"""
        row = self.backup_table.currentRow()
        if row < 0:
            InfoBar.warning("提示", "请先选择一个备份", parent=self)
            return

        backup_path = Path(self.backup_table.item(row, 3).text())

        w = FluentMessageBox("确认删除", "确定要删除此备份吗？", self)
        if w.exec_():
            if self.backup_manager.delete_backup(backup_path):
                InfoBar.success("成功", "备份已删除", parent=self)
                self._load_backups()
            else:
                InfoBar.error("错误", "删除失败", parent=self)


# ==================== 程序入口 ====================
def main():
    # 启用高DPI支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    app.setApplicationName("OpenCode Config Manager")
    app.setApplicationVersion(APP_VERSION)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
