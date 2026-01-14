#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenCode & Oh My OpenCode 配置管理器 v0.6.1
一个可视化的GUI工具，用于管理OpenCode和Oh My OpenCode的配置文件

更新日志 v0.6.1:
- 新增上下文压缩 (compaction) 配置功能
- 侧边栏显示配置文件完整路径（点击可复制）
- exe 文件名带版本号，支持增量构建
- 修复若干界面问题

更新日志 v0.6.0:
- 修正 options/variants 配置结构，符合 OpenCode 官方规范
  - options: 模型默认配置（thinking、reasoningEffort等）
  - variants: 可切换变体配置（high/low/thinking等预设）
- 新增 MCP 服务器配置管理（支持 local/remote 类型）
- 新增 OpenCode 原生 Agent 配置（mode/temperature/maxSteps/tools/permission）
- 新增 Skill 权限配置管理
- 新增 Instructions/Rules 配置管理
- 完善所有位置的 Tooltip 提示说明
- 更新预设模型配置，添加 GPT-5、Claude Opus 4.5 等最新模型

更新日志 v0.5.0:
- 完善模型预设配置，支持Claude/OpenAI/Gemini thinking模式参数
- 修复Provider保存逻辑，点击保存修改直接写入文件
- 统一所有保存逻辑，保存修改即时生效
- 添加首次启动备份提示弹窗
- 添加恢复备份功能，支持多版本备份管理
- 添加全局Tooltip提示，解释各参数含义
- 重构外部导入功能，支持Claude/Codex/Gemini/cc-switch配置解析转换
- UI优化，添加SDK兼容性提示
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
from pathlib import Path
from datetime import datetime
import shutil


# ==================== 配色方案 ====================
COLORS = {
    "bg": "#FAFBFC",  # 主背景色
    "card_bg": "#FFFFFF",  # 卡片背景
    "sidebar_bg": "#F6F8FA",  # 侧边栏背景
    "border": "#E1E4E8",  # 边框色
    "text": "#24292E",  # 主文字
    "text_secondary": "#586069",  # 次要文字
    "primary": "#0366D6",  # 主色调（蓝色）
    "primary_hover": "#0256B9",  # 主色调悬停
    "success": "#28A745",  # 成功色
    "warning": "#F9A825",  # 警告色
    "danger": "#D73A49",  # 危险色
    "accent": "#6F42C1",  # 强调色（紫色）
}

FONTS = {
    "title": ("Microsoft YaHei UI", 14, "bold"),
    "subtitle": ("Microsoft YaHei UI", 11, "bold"),
    "body": ("Microsoft YaHei UI", 10),
    "small": ("Microsoft YaHei UI", 9),
    "mono": ("Consolas", 10),
}


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
                # options: 默认启用 thinking 模式
                "options": {"thinking": {"type": "enabled", "budgetTokens": 16000}},
                # variants: 不同 thinking 预算的变体
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
                # options: 默认配置
                "options": {
                    "reasoningEffort": "high",
                    "textVerbosity": "low",
                    "reasoningSummary": "auto",
                },
                # variants: 不同推理强度的变体
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
                "description": "OpenAI最新旗舰模型\noptions.reasoningEffort: high/medium/low/xhigh\noptions.textVerbosity: low/high\noptions.reasoningSummary: auto/none",
            },
            "gpt-5.1-codex": {
                "name": "GPT-5.1 Codex",
                "attachment": True,
                "limit": {"context": 256000, "output": 65536},
                "modalities": {"input": ["text", "image"], "output": ["text"]},
                "options": {
                    "reasoningEffort": "high",
                    "textVerbosity": "low",
                },
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
                "options": {},
                "variants": {
                    "low": {"thinkingConfig": {"thinkingBudget": 4000}},
                    "high": {"thinkingConfig": {"thinkingBudget": 16000}},
                },
                "description": "Google最新Pro模型，支持thinking模式",
            },
            "gemini-2.0-flash": {
                "name": "Gemini 2.0 Flash",
                "attachment": True,
                "limit": {"context": 1048576, "output": 8192},
                "modalities": {"input": ["text", "image"], "output": ["text"]},
                "options": {},
                "variants": {
                    "low": {"thinkingConfig": {"thinkingBudget": 4000}},
                    "high": {"thinkingConfig": {"thinkingBudget": 8000}},
                },
                "description": "Google Flash模型，支持thinking模式\nvariants.thinkingConfig.thinkingBudget 控制思考预算",
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

# 参数说明提示（用于Tooltip）- 根据 OpenCode 官方文档
TOOLTIPS = {
    # Provider相关
    "provider_name": "Provider的唯一标识符，用于在配置中引用此Provider\n格式: 小写字母和连字符，如 anthropic, openai, my-custom",
    "provider_display": "Provider的显示名称，在界面中展示",
    "provider_sdk": "使用的AI SDK包名，不同厂商使用不同SDK:\n• Claude → @ai-sdk/anthropic\n• OpenAI/GPT → @ai-sdk/openai\n• Gemini → @ai-sdk/google\n• Azure → @ai-sdk/azure\n• 其他兼容 → @ai-sdk/openai-compatible",
    "provider_url": "API服务地址 (baseURL)\n如使用中转站需填写中转站地址\n留空则使用SDK默认地址",
    "provider_apikey": "API密钥，用于身份验证\n支持环境变量引用: {env:ANTHROPIC_API_KEY}",
    "provider_timeout": "请求超时时间（毫秒）\n默认: 300000 (5分钟)\n设为 false 禁用超时",
    # Model相关
    "model_id": "模型的唯一标识符\n需与API提供商的模型ID一致\n如: claude-sonnet-4-5-20250929, gpt-5",
    "model_name": "模型的显示名称，用于界面展示",
    "model_attachment": "是否支持文件附件（图片、文档等）\n多模态模型通常支持",
    "model_context": "上下文窗口大小（tokens）\n决定模型能处理的最大输入长度\n如: 200000, 1048576",
    "model_output": "最大输出长度（tokens）\n决定模型单次回复的最大长度\n如: 8192, 65536",
    # Model Options (默认配置)
    "model_options": "模型的默认配置参数\n每次调用都会使用这些参数\n\nClaude thinking模式:\n  thinking.type: enabled\n  thinking.budgetTokens: 16000\n\nOpenAI推理模式:\n  reasoningEffort: high/medium/low\n  textVerbosity: low/high\n  reasoningSummary: auto/none\n\nGemini thinking模式:\n  thinkingConfig.thinkingBudget: 8000",
    # Model Variants (可切换变体)
    "model_variants": "模型变体配置 - 可通过快捷键切换的预设\n\n用途: 为同一模型定义不同配置组合\n如: high/low推理强度, thinking开关等\n\n切换方式: 使用 variant_cycle 快捷键\n\n示例:\n  high: {reasoningEffort: high}\n  low: {reasoningEffort: low}",
    # Options快捷添加
    "option_reasoningEffort": "推理强度 (OpenAI模型)\n• high: 高强度推理，更准确但更慢\n• medium: 中等强度\n• low: 低强度，更快但可能不够准确\n• xhigh: 超高强度 (GPT-5)",
    "option_textVerbosity": "输出详细程度 (OpenAI模型)\n• low: 简洁输出\n• high: 详细输出",
    "option_reasoningSummary": "推理摘要 (OpenAI模型)\n• auto: 自动生成摘要\n• none: 不生成摘要",
    "option_thinking_type": "Thinking模式类型 (Claude)\n• enabled: 启用thinking\n• disabled: 禁用thinking",
    "option_thinking_budget": "Thinking预算 (Claude/Gemini)\n控制模型思考的token数量\n更高的预算 = 更深入的思考",
    # Agent相关 (Oh My OpenCode)
    "agent_name": "Agent的唯一标识符\n用于在oh-my-opencode中引用\n如: oracle, librarian, explore",
    "agent_model": "Agent使用的模型\n格式: provider/model-id\n如: anthropic/claude-sonnet-4-5-20250929",
    "agent_description": "Agent的功能描述\n帮助理解其用途和适用场景",
    # Agent相关 (OpenCode原生)
    "opencode_agent_mode": "Agent模式:\n• primary: 主Agent，可通过Tab切换\n• subagent: 子Agent，通过@提及调用\n• all: 两种模式都支持",
    "opencode_agent_temperature": "生成温度 (0.0-2.0):\n• 0.0-0.2: 确定性高，适合代码/分析\n• 0.3-0.5: 平衡创造性和准确性\n• 0.6-1.0: 创造性高，适合创意任务",
    "opencode_agent_maxSteps": "最大迭代步数\n限制Agent执行的工具调用次数\n达到限制后强制返回文本响应\n留空则无限制",
    "opencode_agent_prompt": "Agent的系统提示词\n定义Agent的行为和专长\n支持文件引用: {file:./prompts/agent.txt}",
    "opencode_agent_tools": "Agent可用的工具配置\n• true: 启用工具\n• false: 禁用工具\n支持通配符: mcp_* 匹配所有MCP工具",
    "opencode_agent_permission": "Agent的权限配置\n• allow: 允许，无需确认\n• ask: 每次询问\n• deny: 禁止使用",
    "opencode_agent_hidden": "是否在@自动完成中隐藏\n仅对subagent有效\n隐藏的Agent仍可被其他Agent调用",
    # Category相关
    "category_name": "Category的唯一标识符\n用于任务分类\n如: visual, business-logic",
    "category_model": "该分类使用的默认模型",
    "category_temperature": "生成温度(0.0-2.0):\n• 0.0-0.3: 确定性高，适合代码/逻辑任务\n• 0.4-0.7: 平衡创造性和准确性\n• 0.8-2.0: 创造性高，适合创意写作",
    "category_description": "分类的用途说明",
    # Permission相关
    "permission_tool": "工具名称\n内置工具: bash, read, write, edit, glob, grep, webfetch\nMCP工具: mcp_servername_toolname",
    "permission_level": "权限级别:\n• allow: 允许使用，无需确认\n• ask: 每次使用前询问\n• deny: 禁止使用",
    "permission_bash_pattern": "Bash命令权限模式\n支持通配符匹配:\n• *: 所有命令\n• git *: 所有git命令\n• git push: 特定命令",
    # MCP相关
    "mcp_name": "MCP服务器名称\n唯一标识符，用于引用此MCP\n如: context7, sentry, gh_grep",
    "mcp_type": "MCP类型:\n• local: 本地进程，通过命令启动\n• remote: 远程服务，通过URL连接",
    "mcp_enabled": "是否启用此MCP服务器\n禁用后不会加载，但保留配置",
    "mcp_command": '本地MCP启动命令\n数组格式: ["npx", "-y", "@mcp/server"]\n或: ["bun", "x", "my-mcp"]',
    "mcp_url": "远程MCP服务器URL\n如: https://mcp.context7.com/mcp",
    "mcp_headers": '远程MCP请求头\n用于认证等\n如: {"Authorization": "Bearer xxx"}',
    "mcp_environment": '本地MCP环境变量\n如: {"API_KEY": "xxx"}',
    "mcp_timeout": "MCP工具获取超时（毫秒）\n默认: 5000 (5秒)",
    "mcp_oauth": "OAuth认证配置\n• 留空: 自动检测\n• false: 禁用OAuth\n• {clientId, clientSecret, scope}: 预注册凭证",
    # Skill相关
    "skill_name": "Skill名称\n1-64字符，小写字母数字和连字符\n如: git-release, pr-review",
    "skill_permission": "Skill权限:\n• allow: 立即加载\n• deny: 隐藏并拒绝访问\n• ask: 加载前询问用户",
    "skill_pattern": "Skill权限模式\n支持通配符:\n• *: 所有skill\n• internal-*: 匹配internal-开头的skill",
    # Instructions/Rules相关
    "instructions_path": "指令文件路径\n支持相对路径、绝对路径、glob模式\n如: CONTRIBUTING.md, docs/*.md\n也支持远程URL",
    "rules_agents_md": "AGENTS.md 文件\n项目级: 项目根目录/AGENTS.md\n全局级: ~/.config/opencode/AGENTS.md\n包含项目特定的AI指令",
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

PRESET_CATEGORIES = {
    "visual": {"temperature": 0.7, "description": "前端、UI/UX、设计相关任务"},
    "business-logic": {
        "temperature": 0.1,
        "description": "后端逻辑、架构设计、战略推理",
    },
    "documentation": {"temperature": 0.3, "description": "文档编写、技术写作任务"},
    "code-analysis": {"temperature": 0.2, "description": "代码审查、重构分析任务"},
}


# ==================== 核心服务类 ====================
class ConfigPaths:
    @staticmethod
    def get_user_home():
        return Path.home()

    @classmethod
    def get_opencode_config(cls):
        return cls.get_user_home() / ".config" / "opencode" / "opencode.json"

    @classmethod
    def get_ohmyopencode_config(cls):
        return cls.get_user_home() / ".config" / "opencode" / "oh-my-opencode.json"

    @classmethod
    def get_claude_settings(cls):
        return cls.get_user_home() / ".claude" / "settings.json"

    @classmethod
    def get_claude_providers(cls):
        return cls.get_user_home() / ".claude" / "providers.json"

    @classmethod
    def get_backup_dir(cls):
        return cls.get_user_home() / ".config" / "opencode" / "backups"


class ConfigManager:
    @staticmethod
    def load_json(path):
        try:
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Load failed {path}: {e}")
        return None

    @staticmethod
    def save_json(path, data):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Save failed {path}: {e}")
            return False


class BackupManager:
    def __init__(self):
        self.backup_dir = ConfigPaths.get_backup_dir()
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def backup(self, config_path, tag="auto"):
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

    def list_backups(self, config_name=None):
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

    def restore(self, backup_path, target_path):
        """从备份恢复配置"""
        try:
            if not backup_path.exists():
                return False
            # 先备份当前配置
            self.backup(target_path, tag="before_restore")
            shutil.copy2(backup_path, target_path)
            return True
        except Exception as e:
            print(f"Restore failed: {e}")
            return False

    def delete_backup(self, backup_path):
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
    def __init__(self, opencode_config):
        self.config = opencode_config or {}
        self.models = {}
        self.refresh()

    def refresh(self):
        self.models = {}
        providers = self.config.get("provider", {})
        for provider_name, provider_data in providers.items():
            models = provider_data.get("models", {})
            for model_id in models.keys():
                full_ref = f"{provider_name}/{model_id}"
                self.models[full_ref] = True

    def get_all_models(self):
        return list(self.models.keys())


class ImportService:
    """外部配置导入服务 - 支持Claude Code、Codex、Gemini、cc-switch等配置格式"""

    def scan_external_configs(self):
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

    def _parse_toml(self, path):
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

    def convert_to_opencode(self, source_type, source_data):
        """将外部配置转换为OpenCode格式"""
        if not source_data:
            return None

        result = {"provider": {}, "permission": {}}

        if source_type == "claude":
            # Claude Code settings.json转换
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
            # Claude providers.json转换
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
            # Codex config.toml转换
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
            # Gemini配置转换
            if "apiKey" in source_data:
                result["provider"]["google"] = {
                    "npm": "@ai-sdk/google",
                    "name": "Google (Gemini)",
                    "options": {"apiKey": source_data["apiKey"]},
                    "models": {},
                }

        elif source_type == "ccswitch":
            # cc-switch配置转换
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


# ==================== 自定义控件 ====================
class ToolTip:
    """鼠标悬停提示框"""

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        x, y, _, _ = (
            self.widget.bbox("insert") if hasattr(self.widget, "bbox") else (0, 0, 0, 0)
        )
        x = x + self.widget.winfo_rootx() + 25
        y = y + self.widget.winfo_rooty() + 25
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw,
            text=self.text,
            justify=tk.LEFT,
            background="#FFFFD0",
            foreground="#333333",
            relief=tk.SOLID,
            borderwidth=1,
            font=FONTS["small"],
            padx=8,
            pady=4,
            wraplength=300,
        )
        label.pack()

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


def create_label_with_tooltip(parent, text, tooltip_text, **kwargs):
    """创建带Tooltip的标签"""
    default_kwargs = {
        "font": FONTS["small"],
        "bg": COLORS["card_bg"],
        "fg": COLORS["text_secondary"],
    }
    default_kwargs.update(kwargs)
    label = tk.Label(parent, text=text, **default_kwargs)
    if tooltip_text:
        ToolTip(label, tooltip_text)
    return label


class ModernButton(tk.Canvas):
    """现代风格按钮"""

    def __init__(
        self, parent, text, command=None, style="primary", width=100, height=32
    ):
        super().__init__(
            parent, width=width, height=height, highlightthickness=0, bg=COLORS["bg"]
        )
        self.command = command
        self.text = text
        self.style = style
        self.width = width
        self.height = height
        self.hover = False

        self.colors = {
            "primary": (COLORS["primary"], COLORS["primary_hover"], "#FFFFFF"),
            "secondary": (COLORS["sidebar_bg"], COLORS["border"], COLORS["text"]),
            "danger": (COLORS["danger"], "#C82333", "#FFFFFF"),
            "success": (COLORS["success"], "#218838", "#FFFFFF"),
        }

        self.draw()
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)

    def draw(self):
        self.delete("all")
        bg, hover_bg, fg = self.colors.get(self.style, self.colors["primary"])
        color = hover_bg if self.hover else bg
        r = 6
        self.create_rounded_rect(
            2, 2, self.width - 2, self.height - 2, r, fill=color, outline=""
        )
        self.create_text(
            self.width // 2,
            self.height // 2,
            text=self.text,
            fill=fg,
            font=FONTS["body"],
        )

    def create_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1 + r,
            y1,
            x2 - r,
            y1,
            x2,
            y1,
            x2,
            y1 + r,
            x2,
            y2 - r,
            x2,
            y2,
            x2 - r,
            y2,
            x1 + r,
            y2,
            x1,
            y2,
            x1,
            y2 - r,
            x1,
            y1 + r,
            x1,
            y1,
        ]
        return self.create_polygon(points, smooth=True, **kwargs)

    def on_enter(self, e):
        self.hover = True
        self.draw()

    def on_leave(self, e):
        self.hover = False
        self.draw()

    def on_click(self, e):
        if self.command:
            self.command()


class Card(tk.Frame):
    """卡片容器"""

    def __init__(self, parent, title=None, **kwargs):
        super().__init__(parent, bg=COLORS["card_bg"], **kwargs)
        self.configure(highlightbackground=COLORS["border"], highlightthickness=1)
        if title:
            title_label = tk.Label(
                self,
                text=title,
                font=FONTS["subtitle"],
                bg=COLORS["card_bg"],
                fg=COLORS["text"],
                anchor="w",
            )
            title_label.pack(fill=tk.X, padx=16, pady=(16, 8))
            sep = tk.Frame(self, height=1, bg=COLORS["border"])
            sep.pack(fill=tk.X, padx=16)
        self.content = tk.Frame(self, bg=COLORS["card_bg"])
        self.content.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)


class ModernEntry(tk.Frame):
    """现代风格输入框"""

    def __init__(self, parent, textvariable=None, width=30, show=None, placeholder=""):
        super().__init__(parent, bg=COLORS["card_bg"])
        self.var = textvariable or tk.StringVar()
        self.placeholder = placeholder
        self.showing_placeholder = False

        self.container = tk.Frame(
            self,
            bg=COLORS["card_bg"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        self.container.pack(fill=tk.X)

        self.entry = tk.Entry(
            self.container,
            textvariable=self.var,
            font=FONTS["body"],
            width=width,
            bd=0,
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
        )
        if show:
            self.entry.config(show=show)
        self.entry.pack(padx=10, pady=8)

        self.entry.bind("<FocusIn>", self.on_focus_in)
        self.entry.bind("<FocusOut>", self.on_focus_out)

    def on_focus_in(self, e):
        self.container.config(
            highlightbackground=COLORS["primary"], highlightthickness=2
        )

    def on_focus_out(self, e):
        self.container.config(
            highlightbackground=COLORS["border"], highlightthickness=1
        )

    def get(self):
        return self.var.get()

    def set(self, value):
        self.var.set(value)


# ==================== Provider 管理选项卡 ====================
class ProviderTab(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        self.current_provider_name = None  # 记录当前选中的Provider名称
        self.setup_ui()

    def setup_ui(self):
        # 左侧列表
        left_frame = Card(self, title="Provider 列表")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8), pady=0)

        toolbar = tk.Frame(left_frame.content, bg=COLORS["card_bg"])
        toolbar.pack(fill=tk.X, pady=(0, 12))
        ModernButton(toolbar, "+ 添加", self.add_provider, "primary", 80, 30).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ModernButton(toolbar, "删除", self.delete_provider, "danger", 70, 30).pack(
            side=tk.LEFT
        )

        # Treeview 样式
        style = ttk.Style()
        style.configure(
            "Modern.Treeview",
            background=COLORS["card_bg"],
            foreground=COLORS["text"],
            fieldbackground=COLORS["card_bg"],
            rowheight=36,
            font=FONTS["body"],
        )
        style.configure(
            "Modern.Treeview.Heading",
            font=FONTS["small"],
            background=COLORS["sidebar_bg"],
            foreground=COLORS["text_secondary"],
        )
        style.map(
            "Modern.Treeview",
            background=[("selected", COLORS["primary"])],
            foreground=[("selected", "#FFFFFF")],
        )

        columns = ("name", "display", "sdk", "models")
        self.tree = ttk.Treeview(
            left_frame.content,
            columns=columns,
            show="headings",
            height=12,
            style="Modern.Treeview",
        )
        self.tree.heading("name", text="名称")
        self.tree.heading("display", text="显示名")
        self.tree.heading("sdk", text="SDK")
        self.tree.heading("models", text="模型数")
        self.tree.column("name", width=80)
        self.tree.column("display", width=100)
        self.tree.column("sdk", width=120)
        self.tree.column("models", width=50)

        scrollbar = ttk.Scrollbar(
            left_frame.content, orient=tk.VERTICAL, command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        # 右侧详情
        right_frame = Card(self, title="Provider 详情")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0), pady=0)

        form = right_frame.content
        row = 0

        # 名称
        lbl = create_label_with_tooltip(
            form,
            "名称 ⓘ",
            "provider_name",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        )
        lbl.grid(row=row, column=0, sticky=tk.W, pady=(0, 4))
        row += 1
        self.name_var = tk.StringVar()
        ModernEntry(form, textvariable=self.name_var, width=28).grid(
            row=row, column=0, sticky=tk.W, pady=(0, 12)
        )

        row += 1
        lbl = create_label_with_tooltip(
            form,
            "显示名 ⓘ",
            "provider_display",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        )
        lbl.grid(row=row, column=0, sticky=tk.W, pady=(0, 4))
        row += 1
        self.display_var = tk.StringVar()
        ModernEntry(form, textvariable=self.display_var, width=28).grid(
            row=row, column=0, sticky=tk.W, pady=(0, 12)
        )

        row += 1
        lbl = create_label_with_tooltip(
            form,
            "SDK ⓘ",
            "provider_sdk",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        )
        lbl.grid(row=row, column=0, sticky=tk.W, pady=(0, 4))
        row += 1
        self.sdk_var = tk.StringVar()
        sdk_combo = ttk.Combobox(
            form,
            textvariable=self.sdk_var,
            values=PRESET_SDKS,
            width=26,
            font=FONTS["body"],
        )
        sdk_combo.grid(row=row, column=0, sticky=tk.W, pady=(0, 12))
        sdk_combo.bind("<<ComboboxSelected>>", self.on_sdk_change)

        # SDK兼容性提示
        row += 1
        self.sdk_hint_label = tk.Label(
            form,
            text="",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
            wraplength=250,
            justify=tk.LEFT,
        )
        self.sdk_hint_label.grid(row=row, column=0, sticky=tk.W, pady=(0, 8))

        row += 1
        lbl = create_label_with_tooltip(
            form,
            "API 地址 ⓘ",
            "provider_url",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        )
        lbl.grid(row=row, column=0, sticky=tk.W, pady=(0, 4))
        row += 1
        self.url_var = tk.StringVar()
        ModernEntry(form, textvariable=self.url_var, width=28).grid(
            row=row, column=0, sticky=tk.W, pady=(0, 12)
        )

        row += 1
        lbl = create_label_with_tooltip(
            form,
            "API 密钥 ⓘ",
            "provider_apikey",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        )
        lbl.grid(row=row, column=0, sticky=tk.W, pady=(0, 4))
        row += 1
        key_frame = tk.Frame(form, bg=COLORS["card_bg"])
        key_frame.grid(row=row, column=0, sticky=tk.W, pady=(0, 16))
        self.key_var = tk.StringVar()
        self.key_entry = ModernEntry(
            key_frame, textvariable=self.key_var, width=22, show="*"
        )
        self.key_entry.pack(side=tk.LEFT)
        self.show_key = tk.BooleanVar(value=False)
        tk.Checkbutton(
            key_frame,
            text="显示",
            variable=self.show_key,
            command=self.toggle_key,
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
            font=FONTS["small"],
            activebackground=COLORS["card_bg"],
        ).pack(side=tk.LEFT, padx=(8, 0))

        row += 1
        btn_frame = tk.Frame(form, bg=COLORS["card_bg"])
        btn_frame.grid(row=row, column=0, sticky=tk.W, pady=(8, 0))
        ModernButton(btn_frame, "保存修改", self.save_changes, "success", 100, 36).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        # 提示文字
        tk.Label(
            btn_frame,
            text="(直接保存到文件)",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        ).pack(side=tk.LEFT)

    def on_sdk_change(self, event=None):
        """SDK选择变化时显示兼容性提示"""
        sdk = self.sdk_var.get()
        if sdk in SDK_MODEL_COMPATIBILITY:
            compatible = SDK_MODEL_COMPATIBILITY[sdk]
            self.sdk_hint_label.config(
                text=f"适用于: {', '.join(compatible)}", fg=COLORS["success"]
            )
        else:
            self.sdk_hint_label.config(text="")

    def toggle_key(self):
        self.key_entry.entry.config(show="" if self.show_key.get() else "*")

    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        providers = self.app.opencode_config.get("provider", {})
        for name, data in providers.items():
            model_count = len(data.get("models", {}))
            display_name = data.get("name", name)
            sdk = data.get("npm", "")
            self.tree.insert("", tk.END, values=(name, display_name, sdk, model_count))

    def on_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        name = item["values"][0]
        self.current_provider_name = name  # 记录当前选中的Provider
        providers = self.app.opencode_config.get("provider", {})
        if name in providers:
            data = providers[name]
            self.name_var.set(name)
            self.display_var.set(data.get("name", ""))
            self.sdk_var.set(data.get("npm", ""))
            self.url_var.set(data.get("options", {}).get("baseURL", ""))
            self.key_var.set(data.get("options", {}).get("apiKey", ""))
            self.on_sdk_change()

    def add_provider(self):
        """添加新Provider"""
        self.current_provider_name = None  # 清除当前选中，表示新建
        self.name_var.set("")
        self.display_var.set("")
        self.sdk_var.set("@ai-sdk/anthropic")
        self.url_var.set("")
        self.key_var.set("")
        self.sdk_hint_label.config(text="")
        # 取消列表选中
        for item in self.tree.selection():
            self.tree.selection_remove(item)

    def delete_provider(self):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        name = item["values"][0]
        if messagebox.askyesno("确认删除", f"删除 Provider [{name}] 及其所有模型?"):
            del self.app.opencode_config["provider"][name]
            self.current_provider_name = None
            self.app.save_configs_silent()  # 直接保存到文件
            self.refresh_list()

    def save_changes(self):
        """保存修改 - 直接写入文件"""
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("提示", "名称不能为空")
            return

        providers = self.app.opencode_config.setdefault("provider", {})

        # 如果是编辑现有Provider且名称改变了，需要删除旧的
        if self.current_provider_name and self.current_provider_name != name:
            if self.current_provider_name in providers:
                # 保留原有的models
                old_models = providers[self.current_provider_name].get("models", {})
                del providers[self.current_provider_name]
                providers[name] = {"models": old_models}

        # 更新或创建Provider
        if name not in providers:
            providers[name] = {"models": {}}

        providers[name]["npm"] = self.sdk_var.get()
        providers[name]["name"] = self.display_var.get()
        providers[name]["options"] = {
            "baseURL": self.url_var.get(),
            "apiKey": self.key_var.get(),
        }

        self.current_provider_name = name  # 更新当前选中

        # 直接保存到文件
        if self.app.save_configs_silent():
            self.refresh_list()
            # 重新选中当前项
            for item in self.tree.get_children():
                if self.tree.item(item)["values"][0] == name:
                    self.tree.selection_set(item)
                    break
            messagebox.showinfo("成功", "Provider 已保存到文件")


# ==================== Model 管理选项卡 ====================
class ModelTab(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        self.current_provider = None
        self.current_model_data = {}
        self.setup_ui()

    def setup_ui(self):
        top_bar = tk.Frame(self, bg=COLORS["bg"])
        top_bar.pack(fill=tk.X, pady=(0, 12))
        tk.Label(
            top_bar,
            text="选择 Provider:",
            font=FONTS["body"],
            bg=COLORS["bg"],
            fg=COLORS["text"],
        ).pack(side=tk.LEFT)
        self.provider_var = tk.StringVar()
        self.provider_combo = ttk.Combobox(
            top_bar,
            textvariable=self.provider_var,
            width=20,
            state="readonly",
            font=FONTS["body"],
        )
        self.provider_combo.pack(side=tk.LEFT, padx=(8, 0))
        self.provider_combo.bind("<<ComboboxSelected>>", self.on_provider_change)

        main_frame = tk.Frame(self, bg=COLORS["bg"])
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = Card(main_frame, title="模型列表")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        toolbar = tk.Frame(left_frame.content, bg=COLORS["card_bg"])
        toolbar.pack(fill=tk.X, pady=(0, 12))
        ModernButton(toolbar, "+ 添加", self.add_model, "primary", 80, 30).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ModernButton(toolbar, "删除", self.delete_model, "danger", 70, 30).pack(
            side=tk.LEFT
        )

        columns = ("model_id", "name", "options_count")
        self.tree = ttk.Treeview(
            left_frame.content,
            columns=columns,
            show="headings",
            height=10,
            style="Modern.Treeview",
        )
        self.tree.heading("model_id", text="模型ID")
        self.tree.heading("name", text="显示名称")
        self.tree.heading("options_count", text="配置项")
        self.tree.column("model_id", width=180)
        self.tree.column("name", width=120)
        self.tree.column("options_count", width=60)
        scrollbar = ttk.Scrollbar(
            left_frame.content, orient=tk.VERTICAL, command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        right_frame = Card(main_frame, title="模型详情")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0))

        self.detail_notebook = ttk.Notebook(right_frame.content)
        self.detail_notebook.pack(fill=tk.BOTH, expand=True)

        basic_frame = tk.Frame(self.detail_notebook, bg=COLORS["card_bg"])
        self.detail_notebook.add(basic_frame, text="基本信息")
        self.setup_basic_tab(basic_frame)

        options_frame = tk.Frame(self.detail_notebook, bg=COLORS["card_bg"])
        self.detail_notebook.add(options_frame, text="Options")
        self.setup_options_tab(options_frame)

        variants_frame = tk.Frame(self.detail_notebook, bg=COLORS["card_bg"])
        self.detail_notebook.add(variants_frame, text="Variants")
        self.setup_variants_tab(variants_frame)

    def setup_basic_tab(self, parent):
        form = tk.Frame(parent, bg=COLORS["card_bg"])
        form.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        row = 0
        tk.Label(
            form,
            text="预设模型",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        ).grid(row=row, column=0, sticky=tk.W, pady=(0, 4))
        row += 1
        preset_frame = tk.Frame(form, bg=COLORS["card_bg"])
        preset_frame.grid(row=row, column=0, sticky=tk.W, pady=(0, 12))
        self.preset_category_var = tk.StringVar(value="自定义")
        self.preset_category_combo = ttk.Combobox(
            preset_frame,
            textvariable=self.preset_category_var,
            values=["自定义"] + list(PRESET_MODELS.keys()),
            width=10,
            state="readonly",
            font=FONTS["small"],
        )
        self.preset_category_combo.pack(side=tk.LEFT, padx=(0, 8))
        self.preset_category_combo.bind(
            "<<ComboboxSelected>>", self.on_preset_category_change
        )
        self.preset_model_var = tk.StringVar()
        self.preset_model_combo = ttk.Combobox(
            preset_frame,
            textvariable=self.preset_model_var,
            width=22,
            state="disabled",
            font=FONTS["small"],
        )
        self.preset_model_combo.pack(side=tk.LEFT)
        self.preset_model_combo.bind(
            "<<ComboboxSelected>>", self.on_preset_model_select
        )

        row += 1
        tk.Label(
            form,
            text="模型ID",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        ).grid(row=row, column=0, sticky=tk.W, pady=(0, 4))
        row += 1
        self.model_id_var = tk.StringVar()
        ModernEntry(form, textvariable=self.model_id_var, width=28).grid(
            row=row, column=0, sticky=tk.W, pady=(0, 8)
        )

        row += 1
        tk.Label(
            form,
            text="显示名称",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        ).grid(row=row, column=0, sticky=tk.W, pady=(0, 4))
        row += 1
        self.model_name_var = tk.StringVar()
        ModernEntry(form, textvariable=self.model_name_var, width=28).grid(
            row=row, column=0, sticky=tk.W, pady=(0, 8)
        )

        row += 1
        self.attachment_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            form,
            text="支持附件",
            variable=self.attachment_var,
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
            font=FONTS["body"],
            activebackground=COLORS["card_bg"],
        ).grid(row=row, column=0, sticky=tk.W, pady=(0, 8))

        row += 1
        limit_frame = tk.Frame(form, bg=COLORS["card_bg"])
        limit_frame.grid(row=row, column=0, sticky=tk.W, pady=(0, 8))
        tk.Label(
            limit_frame,
            text="上下文:",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        ).pack(side=tk.LEFT)
        self.context_var = tk.StringVar(value="1048576")
        tk.Entry(
            limit_frame,
            textvariable=self.context_var,
            width=10,
            font=FONTS["small"],
            bd=1,
            relief=tk.SOLID,
        ).pack(side=tk.LEFT, padx=(4, 12))
        tk.Label(
            limit_frame,
            text="输出:",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        ).pack(side=tk.LEFT)
        self.output_var = tk.StringVar(value="65535")
        tk.Entry(
            limit_frame,
            textvariable=self.output_var,
            width=10,
            font=FONTS["small"],
            bd=1,
            relief=tk.SOLID,
        ).pack(side=tk.LEFT, padx=(4, 0))

        row += 1
        ModernButton(form, "保存模型", self.save_model, "success", 100, 36).grid(
            row=row, column=0, sticky=tk.W, pady=(12, 0)
        )

    def setup_options_tab(self, parent):
        form = tk.Frame(parent, bg=COLORS["card_bg"])
        form.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(
            form,
            text="模型 Options 配置（键值对）",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        ).pack(anchor=tk.W, pady=(0, 8))

        preset_frame = tk.Frame(form, bg=COLORS["card_bg"])
        preset_frame.pack(fill=tk.X, pady=(0, 8))
        tk.Label(
            preset_frame,
            text="快捷添加:",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        ).pack(side=tk.LEFT)
        presets = [
            ("reasoningEffort", "high"),
            ("textVerbosity", "low"),
            ("reasoningSummary", "auto"),
        ]
        for key, val in presets:
            btn = tk.Button(
                preset_frame,
                text=key,
                font=FONTS["small"],
                bd=0,
                bg=COLORS["sidebar_bg"],
                fg=COLORS["text"],
                command=lambda k=key, v=val: self.add_option_preset(k, v),
                cursor="hand2",
            )
            btn.pack(side=tk.LEFT, padx=2)

        list_frame = tk.Frame(form, bg=COLORS["card_bg"])
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        columns = ("key", "value")
        self.options_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=6,
            style="Modern.Treeview",
        )
        self.options_tree.heading("key", text="键")
        self.options_tree.heading("value", text="值")
        self.options_tree.column("key", width=150)
        self.options_tree.column("value", width=150)
        scrollbar = ttk.Scrollbar(
            list_frame, orient=tk.VERTICAL, command=self.options_tree.yview
        )
        self.options_tree.configure(yscrollcommand=scrollbar.set)
        self.options_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        edit_frame = tk.Frame(form, bg=COLORS["card_bg"])
        edit_frame.pack(fill=tk.X, pady=(0, 8))
        tk.Label(
            edit_frame,
            text="键:",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        ).pack(side=tk.LEFT)
        self.option_key_var = tk.StringVar()
        tk.Entry(
            edit_frame,
            textvariable=self.option_key_var,
            width=15,
            font=FONTS["small"],
            bd=1,
            relief=tk.SOLID,
        ).pack(side=tk.LEFT, padx=(4, 8))
        tk.Label(
            edit_frame,
            text="值:",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        ).pack(side=tk.LEFT)
        self.option_value_var = tk.StringVar()
        tk.Entry(
            edit_frame,
            textvariable=self.option_value_var,
            width=15,
            font=FONTS["small"],
            bd=1,
            relief=tk.SOLID,
        ).pack(side=tk.LEFT, padx=(4, 8))

        btn_frame = tk.Frame(form, bg=COLORS["card_bg"])
        btn_frame.pack(fill=tk.X)
        ModernButton(btn_frame, "添加", self.add_option, "primary", 70, 28).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ModernButton(btn_frame, "删除", self.delete_option, "danger", 70, 28).pack(
            side=tk.LEFT
        )

    def setup_variants_tab(self, parent):
        form = tk.Frame(parent, bg=COLORS["card_bg"])
        form.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(
            form,
            text="模型变体配置（Variants）",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        ).pack(anchor=tk.W, pady=(0, 8))

        list_frame = tk.Frame(form, bg=COLORS["card_bg"])
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        columns = ("name", "config")
        self.variants_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=5,
            style="Modern.Treeview",
        )
        self.variants_tree.heading("name", text="变体名称")
        self.variants_tree.heading("config", text="配置")
        self.variants_tree.column("name", width=100)
        self.variants_tree.column("config", width=200)
        scrollbar = ttk.Scrollbar(
            list_frame, orient=tk.VERTICAL, command=self.variants_tree.yview
        )
        self.variants_tree.configure(yscrollcommand=scrollbar.set)
        self.variants_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.variants_tree.bind("<<TreeviewSelect>>", self.on_variant_select)

        add_frame = tk.Frame(form, bg=COLORS["card_bg"])
        add_frame.pack(fill=tk.X, pady=(0, 8))
        tk.Label(
            add_frame,
            text="变体名:",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        ).pack(side=tk.LEFT)
        self.variant_name_var = tk.StringVar()
        tk.Entry(
            add_frame,
            textvariable=self.variant_name_var,
            width=12,
            font=FONTS["small"],
            bd=1,
            relief=tk.SOLID,
        ).pack(side=tk.LEFT, padx=(4, 8))

        preset_frame = tk.Frame(form, bg=COLORS["card_bg"])
        preset_frame.pack(fill=tk.X, pady=(0, 8))
        tk.Label(
            preset_frame,
            text="预设:",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        ).pack(side=tk.LEFT)
        for name in ["high", "low", "thinking", "fast", "default"]:
            btn = tk.Button(
                preset_frame,
                text=name,
                font=FONTS["small"],
                bd=0,
                bg=COLORS["sidebar_bg"],
                fg=COLORS["text"],
                command=lambda n=name: self.variant_name_var.set(n),
                cursor="hand2",
            )
            btn.pack(side=tk.LEFT, padx=2)

        config_frame = tk.Frame(form, bg=COLORS["card_bg"])
        config_frame.pack(fill=tk.X, pady=(0, 8))
        tk.Label(
            config_frame,
            text="配置 (JSON):",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        ).pack(anchor=tk.W)
        self.variant_config_text = tk.Text(
            config_frame, height=3, width=35, font=FONTS["mono"], bd=1, relief=tk.SOLID
        )
        self.variant_config_text.pack(fill=tk.X, pady=(4, 0))
        self.variant_config_text.insert("1.0", '{"reasoningEffort": "high"}')

        btn_frame = tk.Frame(form, bg=COLORS["card_bg"])
        btn_frame.pack(fill=tk.X)
        ModernButton(btn_frame, "添加变体", self.add_variant, "primary", 80, 28).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ModernButton(btn_frame, "删除变体", self.delete_variant, "danger", 80, 28).pack(
            side=tk.LEFT
        )

    def add_option_preset(self, key, value):
        self.option_key_var.set(key)
        self.option_value_var.set(value)

    def add_option(self):
        key = self.option_key_var.get().strip()
        value = self.option_value_var.get().strip()
        if not key:
            return
        try:
            if value.lower() == "true":
                value = True
            elif value.lower() == "false":
                value = False
            elif value.isdigit():
                value = int(value)
            elif value.replace(".", "").isdigit():
                value = float(value)
        except:
            pass
        self.current_model_data.setdefault("options", {})[key] = value
        self.refresh_options_tree()
        self.option_key_var.set("")
        self.option_value_var.set("")

    def delete_option(self):
        selection = self.options_tree.selection()
        if not selection:
            return
        item = self.options_tree.item(selection[0])
        key = item["values"][0]
        if (
            "options" in self.current_model_data
            and key in self.current_model_data["options"]
        ):
            del self.current_model_data["options"][key]
            self.refresh_options_tree()

    def refresh_options_tree(self):
        for item in self.options_tree.get_children():
            self.options_tree.delete(item)
        options = self.current_model_data.get("options", {})
        for key, value in options.items():
            self.options_tree.insert("", tk.END, values=(key, str(value)))

    def on_variant_select(self, event):
        selection = self.variants_tree.selection()
        if not selection:
            return
        item = self.variants_tree.item(selection[0])
        name = item["values"][0]
        variants = self.current_model_data.get("variants", {})
        if name in variants:
            self.variant_name_var.set(name)
            self.variant_config_text.delete("1.0", tk.END)
            self.variant_config_text.insert(
                "1.0", json.dumps(variants[name], indent=2, ensure_ascii=False)
            )

    def add_variant(self):
        name = self.variant_name_var.get().strip()
        if not name:
            messagebox.showwarning("提示", "请输入变体名称")
            return
        try:
            config = json.loads(self.variant_config_text.get("1.0", tk.END).strip())
        except json.JSONDecodeError as e:
            messagebox.showerror("错误", f"JSON 格式错误: {e}")
            return
        self.current_model_data.setdefault("variants", {})[name] = config
        self.refresh_variants_tree()
        self.variant_name_var.set("")

    def delete_variant(self):
        selection = self.variants_tree.selection()
        if not selection:
            return
        item = self.variants_tree.item(selection[0])
        name = item["values"][0]
        if (
            "variants" in self.current_model_data
            and name in self.current_model_data["variants"]
        ):
            del self.current_model_data["variants"][name]
            self.refresh_variants_tree()

    def refresh_variants_tree(self):
        for item in self.variants_tree.get_children():
            self.variants_tree.delete(item)
        variants = self.current_model_data.get("variants", {})
        for name, config in variants.items():
            config_str = json.dumps(config, ensure_ascii=False)[:50]
            self.variants_tree.insert("", tk.END, values=(name, config_str))

    def on_preset_category_change(self, event):
        category = self.preset_category_var.get()
        if category == "自定义":
            self.preset_model_combo.config(state="disabled", values=[])
            self.preset_model_var.set("")
        else:
            models = PRESET_MODELS.get(category, [])
            self.preset_model_combo.config(state="readonly", values=models)
            if models:
                self.preset_model_var.set(models[0])
                self.on_preset_model_select(None)

    def on_preset_model_select(self, event):
        """选择预设模型时自动填充完整配置"""
        model_id = self.preset_model_var.get()
        category = self.preset_category_var.get()
        if not model_id or category == "自定义":
            return

        # 从预设配置中获取完整模型信息
        if category in PRESET_MODEL_CONFIGS:
            model_config = PRESET_MODEL_CONFIGS[category]["models"].get(model_id, {})
            if model_config:
                self.model_id_var.set(model_id)
                self.model_name_var.set(model_config.get("name", model_id))
                self.attachment_var.set(model_config.get("attachment", True))
                limit = model_config.get("limit", {})
                self.context_var.set(str(limit.get("context", 1048576)))
                self.output_var.set(str(limit.get("output", 65535)))

                # 填充options
                self.current_model_data["options"] = model_config.get(
                    "options", {}
                ).copy()
                self.refresh_options_tree()

                # 填充variants
                self.current_model_data["variants"] = model_config.get(
                    "variants", {}
                ).copy()
                self.refresh_variants_tree()

                # 显示模型描述
                desc = model_config.get("description", "")
                if desc:
                    messagebox.showinfo(
                        "模型说明", f"{model_config.get('name', model_id)}\n\n{desc}"
                    )

    def refresh_providers(self):
        providers = list(self.app.opencode_config.get("provider", {}).keys())
        self.provider_combo.config(values=providers)
        if providers and not self.current_provider:
            self.provider_var.set(providers[0])
            self.current_provider = providers[0]
            self.refresh_models()

    def on_provider_change(self, event):
        self.current_provider = self.provider_var.get()
        self.refresh_models()

    def refresh_models(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        if not self.current_provider:
            return
        providers = self.app.opencode_config.get("provider", {})
        if self.current_provider in providers:
            models = providers[self.current_provider].get("models", {})
            for model_id, data in models.items():
                name = data.get("name", model_id)
                opts_count = len(data.get("options", {})) + len(
                    data.get("variants", {})
                )
                self.tree.insert("", tk.END, values=(model_id, name, opts_count))

    def on_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        model_id = item["values"][0]
        providers = self.app.opencode_config.get("provider", {})
        if self.current_provider in providers:
            models = providers[self.current_provider].get("models", {})
            if model_id in models:
                data = models[model_id]
                self.current_model_data = data.copy()
                self.model_id_var.set(model_id)
                self.model_name_var.set(data.get("name", ""))
                self.attachment_var.set(data.get("attachment", False))
                limit = data.get("limit", {})
                self.context_var.set(str(limit.get("context", 1048576)))
                self.output_var.set(str(limit.get("output", 65535)))
                self.refresh_options_tree()
                self.refresh_variants_tree()

    def add_model(self):
        if not self.current_provider:
            messagebox.showwarning("提示", "请先选择 Provider")
            return
        self.current_model_data = {"options": {}, "variants": {}}
        self.model_id_var.set("")
        self.model_name_var.set("")
        self.attachment_var.set(True)
        self.context_var.set("1048576")
        self.output_var.set("65535")
        self.preset_category_var.set("自定义")
        self.preset_model_combo.config(state="disabled", values=[])
        self.refresh_options_tree()
        self.refresh_variants_tree()

    def delete_model(self):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        model_id = item["values"][0]
        if messagebox.askyesno("确认删除", f"删除模型 [{model_id}]?"):
            del self.app.opencode_config["provider"][self.current_provider]["models"][
                model_id
            ]
            self.app.save_configs_silent()  # 直接保存到文件
            self.refresh_models()

    def save_model(self):
        """保存模型 - 直接写入文件"""
        if not self.current_provider:
            messagebox.showwarning("提示", "请先选择 Provider")
            return
        model_id = self.model_id_var.get().strip()
        if not model_id:
            messagebox.showwarning("提示", "模型ID不能为空")
            return
        providers = self.app.opencode_config.setdefault("provider", {})
        if self.current_provider not in providers:
            providers[self.current_provider] = {"models": {}}
        models = providers[self.current_provider].setdefault("models", {})

        model_data = {
            "name": self.model_name_var.get(),
            "attachment": self.attachment_var.get(),
            "limit": {
                "context": int(self.context_var.get() or 1048576),
                "output": int(self.output_var.get() or 65535),
            },
            "modalities": {"input": ["text", "image"], "output": ["text"]},
        }

        # 只有非空的options才添加
        if self.current_model_data.get("options"):
            model_data["options"] = self.current_model_data["options"]

        # 只有非空的variants才添加
        if self.current_model_data.get("variants"):
            model_data["variants"] = self.current_model_data["variants"]

        models[model_id] = model_data

        # 直接保存到文件
        if self.app.save_configs_silent():
            self.refresh_models()
            messagebox.showinfo("成功", "模型已保存到文件")


# ==================== Agent 管理选项卡 ====================
class AgentTab(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        self.setup_ui()

    def setup_ui(self):
        left_frame = Card(self, title="Agent 列表")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        toolbar = tk.Frame(left_frame.content, bg=COLORS["card_bg"])
        toolbar.pack(fill=tk.X, pady=(0, 12))
        ModernButton(toolbar, "+ 添加", self.add_agent, "primary", 80, 30).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ModernButton(toolbar, "删除", self.delete_agent, "danger", 70, 30).pack(
            side=tk.LEFT
        )

        columns = ("name", "model", "description")
        self.tree = ttk.Treeview(
            left_frame.content,
            columns=columns,
            show="headings",
            height=12,
            style="Modern.Treeview",
        )
        self.tree.heading("name", text="名称")
        self.tree.heading("model", text="绑定模型")
        self.tree.heading("description", text="描述")
        self.tree.column("name", width=100)
        self.tree.column("model", width=180)
        self.tree.column("description", width=200)
        scrollbar = ttk.Scrollbar(
            left_frame.content, orient=tk.VERTICAL, command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        right_frame = Card(self, title="Agent 详情")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0))
        form = right_frame.content
        row = 0

        tk.Label(
            form,
            text="预设 Agent",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        ).grid(row=row, column=0, sticky=tk.W, pady=(0, 4))
        row += 1
        self.preset_agent_var = tk.StringVar(value="自定义")
        preset_values = ["自定义"] + list(PRESET_AGENTS.keys())
        self.preset_combo = ttk.Combobox(
            form,
            textvariable=self.preset_agent_var,
            values=preset_values,
            width=26,
            state="readonly",
            font=FONTS["body"],
        )
        self.preset_combo.grid(row=row, column=0, sticky=tk.W, pady=(0, 12))
        self.preset_combo.bind("<<ComboboxSelected>>", self.on_preset_select)

        row += 1
        tk.Label(
            form,
            text="名称",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        ).grid(row=row, column=0, sticky=tk.W, pady=(0, 4))
        row += 1
        self.name_var = tk.StringVar()
        ModernEntry(form, textvariable=self.name_var, width=28).grid(
            row=row, column=0, sticky=tk.W, pady=(0, 12)
        )

        row += 1
        tk.Label(
            form,
            text="绑定模型",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        ).grid(row=row, column=0, sticky=tk.W, pady=(0, 4))
        row += 1
        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(
            form, textvariable=self.model_var, width=26, font=FONTS["body"]
        )
        self.model_combo.grid(row=row, column=0, sticky=tk.W, pady=(0, 12))

        row += 1
        tk.Label(
            form,
            text="描述",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        ).grid(row=row, column=0, sticky=tk.W, pady=(0, 4))
        row += 1
        self.desc_text = tk.Text(
            form,
            width=30,
            height=4,
            font=FONTS["body"],
            bd=1,
            relief=tk.SOLID,
            bg=COLORS["card_bg"],
        )
        self.desc_text.grid(row=row, column=0, sticky=tk.W, pady=(0, 12))

        row += 1
        ModernButton(form, "保存修改", self.save_changes, "success", 100, 36).grid(
            row=row, column=0, sticky=tk.W, pady=(8, 0)
        )

    def on_preset_select(self, event):
        preset = self.preset_agent_var.get()
        if preset != "自定义" and preset in PRESET_AGENTS:
            self.name_var.set(preset)
            self.desc_text.delete("1.0", tk.END)
            self.desc_text.insert("1.0", PRESET_AGENTS[preset])

    def refresh_models(self):
        registry = ModelRegistry(self.app.opencode_config)
        models = registry.get_all_models()
        self.model_combo.config(values=models)

    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        agents = self.app.ohmyopencode_config.get("agents", {})
        for name, data in agents.items():
            model = data.get("model", "")
            desc = data.get("description", "")[:30]
            self.tree.insert("", tk.END, values=(name, model, desc))

    def on_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        name = item["values"][0]
        agents = self.app.ohmyopencode_config.get("agents", {})
        if name in agents:
            data = agents[name]
            self.name_var.set(name)
            self.model_var.set(data.get("model", ""))
            self.desc_text.delete("1.0", tk.END)
            self.desc_text.insert("1.0", data.get("description", ""))

    def add_agent(self):
        self.name_var.set("")
        self.model_var.set("")
        self.desc_text.delete("1.0", tk.END)
        self.preset_agent_var.set("自定义")

    def delete_agent(self):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        name = item["values"][0]
        if messagebox.askyesno("确认删除", f"删除 Agent [{name}]?"):
            del self.app.ohmyopencode_config["agents"][name]
            self.app.save_configs_silent()  # 直接保存到文件
            self.refresh_list()

    def save_changes(self):
        """保存Agent - 直接写入文件"""
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("提示", "名称不能为空")
            return
        agents = self.app.ohmyopencode_config.setdefault("agents", {})
        agents[name] = {
            "model": self.model_var.get(),
            "description": self.desc_text.get("1.0", tk.END).strip(),
        }
        self.app.save_configs_silent()  # 直接保存到文件
        self.refresh_list()
        messagebox.showinfo("成功", "Agent 已保存到文件")


# ==================== Category 管理选项卡 ====================
class CategoryTab(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        self.setup_ui()

    def setup_ui(self):
        left_frame = Card(self, title="Category 列表")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        toolbar = tk.Frame(left_frame.content, bg=COLORS["card_bg"])
        toolbar.pack(fill=tk.X, pady=(0, 12))
        ModernButton(toolbar, "+ 添加", self.add_category, "primary", 80, 30).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ModernButton(toolbar, "删除", self.delete_category, "danger", 70, 30).pack(
            side=tk.LEFT
        )

        columns = ("name", "model", "temp", "description")
        self.tree = ttk.Treeview(
            left_frame.content,
            columns=columns,
            show="headings",
            height=12,
            style="Modern.Treeview",
        )
        self.tree.heading("name", text="名称")
        self.tree.heading("model", text="绑定模型")
        self.tree.heading("temp", text="Temp")
        self.tree.heading("description", text="描述")
        self.tree.column("name", width=100)
        self.tree.column("model", width=150)
        self.tree.column("temp", width=60)
        self.tree.column("description", width=150)
        scrollbar = ttk.Scrollbar(
            left_frame.content, orient=tk.VERTICAL, command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        right_frame = Card(self, title="Category 详情")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0))
        form = right_frame.content
        row = 0

        tk.Label(
            form,
            text="预设分类",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        ).grid(row=row, column=0, sticky=tk.W, pady=(0, 4))
        row += 1
        self.preset_var = tk.StringVar(value="自定义")
        preset_values = ["自定义"] + list(PRESET_CATEGORIES.keys())
        self.preset_combo = ttk.Combobox(
            form,
            textvariable=self.preset_var,
            values=preset_values,
            width=26,
            state="readonly",
            font=FONTS["body"],
        )
        self.preset_combo.grid(row=row, column=0, sticky=tk.W, pady=(0, 12))
        self.preset_combo.bind("<<ComboboxSelected>>", self.on_preset_select)

        row += 1
        tk.Label(
            form,
            text="名称",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        ).grid(row=row, column=0, sticky=tk.W, pady=(0, 4))
        row += 1
        self.name_var = tk.StringVar()
        ModernEntry(form, textvariable=self.name_var, width=28).grid(
            row=row, column=0, sticky=tk.W, pady=(0, 12)
        )

        row += 1
        tk.Label(
            form,
            text="绑定模型",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        ).grid(row=row, column=0, sticky=tk.W, pady=(0, 4))
        row += 1
        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(
            form, textvariable=self.model_var, width=26, font=FONTS["body"]
        )
        self.model_combo.grid(row=row, column=0, sticky=tk.W, pady=(0, 12))

        row += 1
        tk.Label(
            form,
            text="Temperature",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        ).grid(row=row, column=0, sticky=tk.W, pady=(0, 4))
        row += 1
        temp_frame = tk.Frame(form, bg=COLORS["card_bg"])
        temp_frame.grid(row=row, column=0, sticky=tk.W, pady=(0, 12))
        self.temp_var = tk.DoubleVar(value=0.7)
        self.temp_scale = ttk.Scale(
            temp_frame,
            from_=0.0,
            to=2.0,
            variable=self.temp_var,
            orient=tk.HORIZONTAL,
            length=180,
            command=self.on_temp_change,
        )
        self.temp_scale.pack(side=tk.LEFT)
        self.temp_label = tk.Label(
            temp_frame,
            text="0.7",
            width=5,
            font=FONTS["body"],
            bg=COLORS["card_bg"],
            fg=COLORS["primary"],
        )
        self.temp_label.pack(side=tk.LEFT, padx=(8, 0))

        row += 1
        tk.Label(
            form,
            text="描述",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        ).grid(row=row, column=0, sticky=tk.W, pady=(0, 4))
        row += 1
        self.desc_text = tk.Text(
            form,
            width=30,
            height=3,
            font=FONTS["body"],
            bd=1,
            relief=tk.SOLID,
            bg=COLORS["card_bg"],
        )
        self.desc_text.grid(row=row, column=0, sticky=tk.W, pady=(0, 12))

        row += 1
        ModernButton(form, "保存修改", self.save_changes, "success", 100, 36).grid(
            row=row, column=0, sticky=tk.W, pady=(8, 0)
        )

    def on_temp_change(self, value):
        self.temp_label.config(text=f"{float(value):.1f}")

    def on_preset_select(self, event):
        preset = self.preset_var.get()
        if preset != "自定义" and preset in PRESET_CATEGORIES:
            data = PRESET_CATEGORIES[preset]
            self.name_var.set(preset)
            self.temp_var.set(data["temperature"])
            self.temp_label.config(text=f"{data['temperature']:.1f}")
            self.desc_text.delete("1.0", tk.END)
            self.desc_text.insert("1.0", data["description"])

    def refresh_models(self):
        registry = ModelRegistry(self.app.opencode_config)
        models = registry.get_all_models()
        self.model_combo.config(values=models)

    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        categories = self.app.ohmyopencode_config.get("categories", {})
        for name, data in categories.items():
            model = data.get("model", "")
            temp = data.get("temperature", 0.7)
            desc = data.get("description", "")[:20]
            self.tree.insert("", tk.END, values=(name, model, temp, desc))

    def on_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        name = item["values"][0]
        categories = self.app.ohmyopencode_config.get("categories", {})
        if name in categories:
            data = categories[name]
            self.name_var.set(name)
            self.model_var.set(data.get("model", ""))
            temp = data.get("temperature", 0.7)
            self.temp_var.set(temp)
            self.temp_label.config(text=f"{temp:.1f}")
            self.desc_text.delete("1.0", tk.END)
            self.desc_text.insert("1.0", data.get("description", ""))

    def add_category(self):
        self.name_var.set("")
        self.model_var.set("")
        self.temp_var.set(0.7)
        self.temp_label.config(text="0.7")
        self.desc_text.delete("1.0", tk.END)
        self.preset_var.set("自定义")

    def delete_category(self):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        name = item["values"][0]
        if messagebox.askyesno("确认删除", f"删除 Category [{name}]?"):
            del self.app.ohmyopencode_config["categories"][name]
            self.app.save_configs_silent()  # 直接保存到文件
            self.refresh_list()

    def save_changes(self):
        """保存Category - 直接写入文件"""
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("提示", "名称不能为空")
            return
        categories = self.app.ohmyopencode_config.setdefault("categories", {})
        categories[name] = {
            "model": self.model_var.get(),
            "temperature": round(self.temp_var.get(), 1),
            "description": self.desc_text.get("1.0", tk.END).strip(),
        }
        self.app.save_configs_silent()  # 直接保存到文件
        self.refresh_list()
        messagebox.showinfo("成功", "Category 已保存到文件")


# ==================== 权限管理选项卡 ====================
class PermissionTab(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        self.setup_ui()

    def setup_ui(self):
        left_frame = Card(self, title="权限列表")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        toolbar = tk.Frame(left_frame.content, bg=COLORS["card_bg"])
        toolbar.pack(fill=tk.X, pady=(0, 12))
        ModernButton(toolbar, "+ 添加", self.add_permission, "primary", 80, 30).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ModernButton(toolbar, "删除", self.delete_permission, "danger", 70, 30).pack(
            side=tk.LEFT
        )

        columns = ("tool", "permission")
        self.tree = ttk.Treeview(
            left_frame.content,
            columns=columns,
            show="headings",
            height=15,
            style="Modern.Treeview",
        )
        self.tree.heading("tool", text="工具名称")
        self.tree.heading("permission", text="权限")
        self.tree.column("tool", width=200)
        self.tree.column("permission", width=100)
        scrollbar = ttk.Scrollbar(
            left_frame.content, orient=tk.VERTICAL, command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        right_frame = Card(self, title="权限详情")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0))
        form = right_frame.content
        row = 0

        tk.Label(
            form,
            text="工具名称",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        ).grid(row=row, column=0, sticky=tk.W, pady=(0, 4))
        row += 1
        self.tool_var = tk.StringVar()
        ModernEntry(form, textvariable=self.tool_var, width=28).grid(
            row=row, column=0, sticky=tk.W, pady=(0, 12)
        )

        row += 1
        tk.Label(
            form,
            text="权限设置",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        ).grid(row=row, column=0, sticky=tk.W, pady=(0, 4))
        row += 1
        self.perm_var = tk.StringVar(value="ask")
        perm_frame = tk.Frame(form, bg=COLORS["card_bg"])
        perm_frame.grid(row=row, column=0, sticky=tk.W, pady=(0, 16))
        for val, txt, color in [
            ("allow", "允许", COLORS["success"]),
            ("ask", "询问", COLORS["warning"]),
            ("deny", "拒绝", COLORS["danger"]),
        ]:
            tk.Radiobutton(
                perm_frame,
                text=txt,
                variable=self.perm_var,
                value=val,
                bg=COLORS["card_bg"],
                fg=color,
                font=FONTS["body"],
                activebackground=COLORS["card_bg"],
                selectcolor=COLORS["card_bg"],
            ).pack(side=tk.LEFT, padx=(0, 16))

        row += 1
        tk.Label(
            form,
            text="常用工具",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        ).grid(row=row, column=0, sticky=tk.W, pady=(0, 4))
        row += 1
        preset_frame = tk.Frame(form, bg=COLORS["card_bg"])
        preset_frame.grid(row=row, column=0, sticky=tk.W, pady=(0, 16))
        presets = [
            "Bash",
            "Read",
            "Write",
            "Edit",
            "Glob",
            "Grep",
            "WebFetch",
            "WebSearch",
            "Task",
        ]
        for i, preset in enumerate(presets):
            btn = tk.Button(
                preset_frame,
                text=preset,
                width=9,
                font=FONTS["small"],
                bd=0,
                bg=COLORS["sidebar_bg"],
                fg=COLORS["text"],
                activebackground=COLORS["border"],
                cursor="hand2",
                command=lambda p=preset: self.tool_var.set(p),
            )
            btn.grid(row=i // 3, column=i % 3, padx=2, pady=2)

        row += 1
        ModernButton(form, "保存修改", self.save_changes, "success", 100, 36).grid(
            row=row, column=0, sticky=tk.W, pady=(8, 0)
        )

    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        permissions = self.app.opencode_config.get("permission", {})
        for tool, perm in permissions.items():
            self.tree.insert("", tk.END, values=(tool, perm))

    def on_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        self.tool_var.set(item["values"][0])
        self.perm_var.set(item["values"][1])

    def add_permission(self):
        self.tool_var.set("")
        self.perm_var.set("ask")

    def delete_permission(self):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        tool = item["values"][0]
        if messagebox.askyesno("确认删除", f"删除权限 [{tool}]?"):
            del self.app.opencode_config["permission"][tool]
            self.app.save_configs_silent()  # 直接保存到文件
            self.refresh_list()

    def save_changes(self):
        """保存权限 - 直接写入文件"""
        tool = self.tool_var.get().strip()
        if not tool:
            messagebox.showwarning("提示", "工具名称不能为空")
            return
        permissions = self.app.opencode_config.setdefault("permission", {})
        permissions[tool] = self.perm_var.get()
        self.app.save_configs_silent()  # 直接保存到文件
        self.refresh_list()
        messagebox.showinfo("成功", "权限已保存到文件")


# ==================== 外部导入选项卡 ====================
class ImportTab(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        self.import_service = ImportService()
        self.setup_ui()

    def setup_ui(self):
        top_frame = Card(self, title="检测到的外部配置")
        top_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        toolbar = tk.Frame(top_frame.content, bg=COLORS["card_bg"])
        toolbar.pack(fill=tk.X, pady=(0, 12))
        ModernButton(toolbar, "刷新检测", self.refresh_scan, "primary", 100, 30).pack(
            side=tk.LEFT
        )

        columns = ("source", "path", "status")
        self.tree = ttk.Treeview(
            top_frame.content,
            columns=columns,
            show="headings",
            height=5,
            style="Modern.Treeview",
        )
        self.tree.heading("source", text="来源")
        self.tree.heading("path", text="配置路径")
        self.tree.heading("status", text="状态")
        self.tree.column("source", width=120)
        self.tree.column("path", width=350)
        self.tree.column("status", width=80)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        bottom_frame = Card(self, title="配置预览与转换结果")
        bottom_frame.pack(fill=tk.BOTH, expand=True, pady=(8, 0))

        # 预览区域
        preview_label = tk.Label(
            bottom_frame.content,
            text="原始配置:",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        )
        preview_label.pack(anchor=tk.W)
        self.preview_text = tk.Text(
            bottom_frame.content,
            height=8,
            font=FONTS["mono"],
            bd=1,
            relief=tk.SOLID,
            bg=COLORS["sidebar_bg"],
        )
        self.preview_text.pack(fill=tk.BOTH, expand=True, pady=(4, 8))

        # 转换结果区域
        convert_label = tk.Label(
            bottom_frame.content,
            text="转换为OpenCode格式:",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        )
        convert_label.pack(anchor=tk.W)
        self.convert_text = tk.Text(
            bottom_frame.content,
            height=6,
            font=FONTS["mono"],
            bd=1,
            relief=tk.SOLID,
            bg=COLORS["sidebar_bg"],
        )
        self.convert_text.pack(fill=tk.BOTH, expand=True, pady=(4, 8))

        btn_frame = tk.Frame(bottom_frame.content, bg=COLORS["card_bg"])
        btn_frame.pack(fill=tk.X, pady=(8, 0))
        ModernButton(
            btn_frame, "预览转换", self.preview_convert, "secondary", 100, 36
        ).pack(side=tk.LEFT, padx=(0, 8))
        ModernButton(
            btn_frame, "导入到OpenCode", self.import_selected, "success", 130, 36
        ).pack(side=tk.LEFT)

    def refresh_scan(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        results = self.import_service.scan_external_configs()
        for key, info in results.items():
            status = "✓ 已检测" if info["exists"] else "✗ 未找到"
            self.tree.insert("", tk.END, values=(key, info["path"], status))

    def on_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        source = item["values"][0]
        results = self.import_service.scan_external_configs()
        if source in results and results[source]["data"]:
            self.preview_text.delete("1.0", tk.END)
            self.preview_text.insert(
                "1.0", json.dumps(results[source]["data"], indent=2, ensure_ascii=False)
            )
            self.convert_text.delete("1.0", tk.END)

    def preview_convert(self):
        """预览转换结果"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择要转换的配置")
            return
        item = self.tree.item(selection[0])
        source = item["values"][0]
        results = self.import_service.scan_external_configs()
        if source in results and results[source]["data"]:
            source_type = results[source].get("type", "")
            converted = self.import_service.convert_to_opencode(
                source_type, results[source]["data"]
            )
            if converted:
                self.convert_text.delete("1.0", tk.END)
                self.convert_text.insert(
                    "1.0", json.dumps(converted, indent=2, ensure_ascii=False)
                )
            else:
                messagebox.showwarning("提示", "无法转换此配置格式")

    def import_selected(self):
        """导入选中的配置到OpenCode"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择要导入的配置")
            return
        item = self.tree.item(selection[0])
        source = item["values"][0]
        results = self.import_service.scan_external_configs()

        if source not in results or not results[source]["data"]:
            messagebox.showwarning("提示", "所选配置不存在或为空")
            return

        source_type = results[source].get("type", "")
        converted = self.import_service.convert_to_opencode(
            source_type, results[source]["data"]
        )

        if not converted:
            messagebox.showwarning("提示", "无法转换此配置格式")
            return

        # 确认导入
        provider_count = len(converted.get("provider", {}))
        perm_count = len(converted.get("permission", {}))

        msg = f"将导入以下配置:\n• Provider: {provider_count} 个\n• 权限: {perm_count} 个\n\n是否继续?"
        if not messagebox.askyesno("确认导入", msg):
            return

        # 合并配置
        for provider_name, provider_data in converted.get("provider", {}).items():
            if provider_name in self.app.opencode_config.get("provider", {}):
                if not messagebox.askyesno(
                    "冲突", f"Provider [{provider_name}] 已存在，是否覆盖?"
                ):
                    continue
            self.app.opencode_config.setdefault("provider", {})[provider_name] = (
                provider_data
            )

        for tool, perm in converted.get("permission", {}).items():
            self.app.opencode_config.setdefault("permission", {})[tool] = perm

        # 保存到文件
        if self.app.save_configs_silent():
            self.app.refresh_all_tabs()
            messagebox.showinfo("成功", f"已导入 {source} 的配置")


# ==================== 上下文压缩配置选项卡 ====================
class CompactionTab(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        self.setup_ui()

    def setup_ui(self):
        main_frame = tk.Frame(self, bg=COLORS["bg"])
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 上下文压缩配置
        compaction_card = Card(main_frame, title="上下文压缩 (Compaction)")
        compaction_card.pack(fill=tk.X, pady=(0, 16))

        form = tk.Frame(compaction_card.content, bg=COLORS["card_bg"])
        form.pack(fill=tk.X, padx=10, pady=10)

        # 说明
        tk.Label(
            form,
            text="上下文压缩用于在会话上下文接近满时自动压缩，以节省 tokens 并保持会话连续性。",
            font=FONTS["body"],
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
            wraplength=500,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(0, 16))

        # auto 选项
        auto_frame = tk.Frame(form, bg=COLORS["card_bg"])
        auto_frame.pack(fill=tk.X, pady=(0, 8))
        self.auto_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            auto_frame,
            text="自动压缩 (auto)",
            variable=self.auto_var,
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
            font=FONTS["body"],
            activebackground=COLORS["card_bg"],
        ).pack(side=tk.LEFT)
        tk.Label(
            auto_frame,
            text="当上下文已满时自动压缩会话",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        ).pack(side=tk.LEFT, padx=(8, 0))

        # prune 选项
        prune_frame = tk.Frame(form, bg=COLORS["card_bg"])
        prune_frame.pack(fill=tk.X, pady=(0, 16))
        self.prune_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            prune_frame,
            text="修剪旧输出 (prune)",
            variable=self.prune_var,
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
            font=FONTS["body"],
            activebackground=COLORS["card_bg"],
        ).pack(side=tk.LEFT)
        tk.Label(
            prune_frame,
            text="删除旧的工具输出以节省 tokens",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        ).pack(side=tk.LEFT, padx=(8, 0))

        # 保存按钮
        ModernButton(form, "保存设置", self.save_compaction, "success", 100, 36).pack(
            anchor=tk.W
        )

        # 配置预览
        preview_card = Card(main_frame, title="配置预览")
        preview_card.pack(fill=tk.BOTH, expand=True)

        self.preview_text = tk.Text(
            preview_card.content,
            height=8,
            font=FONTS["mono"],
            bd=1,
            relief=tk.SOLID,
            bg=COLORS["sidebar_bg"],
            fg=COLORS["text"],
        )
        self.preview_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.refresh_preview()

    def refresh_list(self):
        """刷新显示（供 MainWindow 调用）"""
        compaction = self.app.opencode_config.get("compaction", {})
        self.auto_var.set(compaction.get("auto", True))
        self.prune_var.set(compaction.get("prune", True))
        self.refresh_preview()

    def refresh_preview(self):
        """刷新配置预览"""
        config = {
            "compaction": {"auto": self.auto_var.get(), "prune": self.prune_var.get()}
        }
        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert(
            "1.0", json.dumps(config, indent=2, ensure_ascii=False)
        )
        self.preview_text.config(state=tk.DISABLED)

    def save_compaction(self):
        """保存上下文压缩配置"""
        self.app.opencode_config["compaction"] = {
            "auto": self.auto_var.get(),
            "prune": self.prune_var.get(),
        }
        self.refresh_preview()
        self.app.save_configs_silent()
        messagebox.showinfo("成功", "上下文压缩配置已保存")


# ==================== MCP 服务器配置选项卡 ====================
class MCPTab(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        self.current_mcp = None
        self.setup_ui()

    def setup_ui(self):
        main_frame = tk.Frame(self, bg=COLORS["bg"])
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = Card(main_frame, title="MCP 服务器列表")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        btn_frame = tk.Frame(left_frame.content, bg=COLORS["card_bg"])
        btn_frame.pack(fill=tk.X, pady=(0, 8))
        ModernButton(btn_frame, "添加 MCP", self.add_mcp, "primary", 90, 32).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ModernButton(btn_frame, "删除", self.delete_mcp, "danger", 70, 32).pack(
            side=tk.LEFT
        )

        columns = ("name", "type", "enabled")
        self.tree = ttk.Treeview(
            left_frame.content,
            columns=columns,
            show="headings",
            height=15,
            style="Modern.Treeview",
        )
        self.tree.heading("name", text="名称")
        self.tree.heading("type", text="类型")
        self.tree.heading("enabled", text="启用")
        self.tree.column("name", width=120)
        self.tree.column("type", width=80)
        self.tree.column("enabled", width=60)
        scrollbar = ttk.Scrollbar(
            left_frame.content, orient=tk.VERTICAL, command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        right_frame = Card(main_frame, title="MCP 详情")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0))

        form = tk.Frame(right_frame.content, bg=COLORS["card_bg"])
        form.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        row = 0
        create_label_with_tooltip(form, "MCP 名称", TOOLTIPS["mcp_name"]).grid(
            row=row, column=0, sticky=tk.W, pady=(0, 4)
        )
        row += 1
        self.name_var = tk.StringVar()
        ModernEntry(form, textvariable=self.name_var, width=30).grid(
            row=row, column=0, sticky=tk.W, pady=(0, 8)
        )

        row += 1
        create_label_with_tooltip(form, "类型", TOOLTIPS["mcp_type"]).grid(
            row=row, column=0, sticky=tk.W, pady=(0, 4)
        )
        row += 1
        self.type_var = tk.StringVar(value="local")
        type_frame = tk.Frame(form, bg=COLORS["card_bg"])
        type_frame.grid(row=row, column=0, sticky=tk.W, pady=(0, 8))
        tk.Radiobutton(
            type_frame,
            text="Local",
            variable=self.type_var,
            value="local",
            bg=COLORS["card_bg"],
            command=self.on_type_change,
        ).pack(side=tk.LEFT)
        tk.Radiobutton(
            type_frame,
            text="Remote",
            variable=self.type_var,
            value="remote",
            bg=COLORS["card_bg"],
            command=self.on_type_change,
        ).pack(side=tk.LEFT, padx=(16, 0))

        row += 1
        self.enabled_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            form,
            text="启用",
            variable=self.enabled_var,
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
            font=FONTS["body"],
        ).grid(row=row, column=0, sticky=tk.W, pady=(0, 8))

        row += 1
        self.local_frame = tk.Frame(form, bg=COLORS["card_bg"])
        self.local_frame.grid(row=row, column=0, sticky=tk.W + tk.E, pady=(0, 8))
        create_label_with_tooltip(
            self.local_frame, "启动命令 (JSON数组)", TOOLTIPS["mcp_command"]
        ).pack(anchor=tk.W)
        self.command_var = tk.StringVar(value='["npx", "-y", "@mcp/server"]')
        ModernEntry(self.local_frame, textvariable=self.command_var, width=40).pack(
            anchor=tk.W, pady=(4, 8)
        )
        create_label_with_tooltip(
            self.local_frame, "环境变量 (JSON)", TOOLTIPS["mcp_environment"]
        ).pack(anchor=tk.W)
        self.env_var = tk.StringVar(value="{}")
        ModernEntry(self.local_frame, textvariable=self.env_var, width=40).pack(
            anchor=tk.W, pady=(4, 0)
        )

        row += 1
        self.remote_frame = tk.Frame(form, bg=COLORS["card_bg"])
        self.remote_frame.grid(row=row, column=0, sticky=tk.W + tk.E, pady=(0, 8))
        create_label_with_tooltip(
            self.remote_frame, "服务器 URL", TOOLTIPS["mcp_url"]
        ).pack(anchor=tk.W)
        self.url_var = tk.StringVar()
        ModernEntry(self.remote_frame, textvariable=self.url_var, width=40).pack(
            anchor=tk.W, pady=(4, 8)
        )
        create_label_with_tooltip(
            self.remote_frame, "请求头 (JSON)", TOOLTIPS["mcp_headers"]
        ).pack(anchor=tk.W)
        self.headers_var = tk.StringVar(value="{}")
        ModernEntry(self.remote_frame, textvariable=self.headers_var, width=40).pack(
            anchor=tk.W, pady=(4, 0)
        )
        self.remote_frame.grid_remove()

        row += 1
        create_label_with_tooltip(form, "超时 (毫秒)", TOOLTIPS["mcp_timeout"]).grid(
            row=row, column=0, sticky=tk.W, pady=(0, 4)
        )
        row += 1
        self.timeout_var = tk.StringVar(value="5000")
        ModernEntry(form, textvariable=self.timeout_var, width=15).grid(
            row=row, column=0, sticky=tk.W, pady=(0, 12)
        )

        row += 1
        ModernButton(form, "保存 MCP", self.save_mcp, "success", 100, 36).grid(
            row=row, column=0, sticky=tk.W
        )

    def on_type_change(self):
        if self.type_var.get() == "local":
            self.remote_frame.grid_remove()
            self.local_frame.grid()
        else:
            self.local_frame.grid_remove()
            self.remote_frame.grid()

    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        mcps = self.app.opencode_config.get("mcp", {})
        for name, data in mcps.items():
            mcp_type = data.get("type", "local")
            enabled = "是" if data.get("enabled", True) else "否"
            self.tree.insert("", tk.END, values=(name, mcp_type, enabled))

    def on_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        name = item["values"][0]
        self.current_mcp = name
        mcps = self.app.opencode_config.get("mcp", {})
        if name in mcps:
            data = mcps[name]
            self.name_var.set(name)
            self.type_var.set(data.get("type", "local"))
            self.enabled_var.set(data.get("enabled", True))
            self.timeout_var.set(str(data.get("timeout", 5000)))
            if data.get("type") == "remote":
                self.url_var.set(data.get("url", ""))
                self.headers_var.set(
                    json.dumps(data.get("headers", {}), ensure_ascii=False)
                )
            else:
                self.command_var.set(
                    json.dumps(data.get("command", []), ensure_ascii=False)
                )
                self.env_var.set(
                    json.dumps(data.get("environment", {}), ensure_ascii=False)
                )
            self.on_type_change()

    def add_mcp(self):
        self.current_mcp = None
        self.name_var.set("")
        self.type_var.set("local")
        self.enabled_var.set(True)
        self.command_var.set('["npx", "-y", "@mcp/server"]')
        self.env_var.set("{}")
        self.url_var.set("")
        self.headers_var.set("{}")
        self.timeout_var.set("5000")
        self.on_type_change()

    def save_mcp(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("提示", "请输入 MCP 名称")
            return
        mcp_type = self.type_var.get()
        data = {"type": mcp_type, "enabled": self.enabled_var.get()}
        try:
            timeout = int(self.timeout_var.get())
            if timeout != 5000:
                data["timeout"] = timeout
        except:
            pass
        if mcp_type == "local":
            try:
                data["command"] = json.loads(self.command_var.get())
            except:
                messagebox.showerror("错误", "启动命令格式错误，需要JSON数组")
                return
            try:
                env = json.loads(self.env_var.get())
                if env:
                    data["environment"] = env
            except:
                pass
        else:
            url = self.url_var.get().strip()
            if not url:
                messagebox.showwarning("提示", "请输入服务器 URL")
                return
            data["url"] = url
            try:
                headers = json.loads(self.headers_var.get())
                if headers:
                    data["headers"] = headers
            except:
                pass
        self.app.opencode_config.setdefault("mcp", {})[name] = data
        if self.current_mcp and self.current_mcp != name:
            del self.app.opencode_config["mcp"][self.current_mcp]
        self.current_mcp = name
        self.refresh_list()
        self.app.save_configs_silent()
        messagebox.showinfo("成功", f"MCP [{name}] 已保存")

    def delete_mcp(self):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        name = item["values"][0]
        if messagebox.askyesno("确认", f"确定删除 MCP [{name}]?"):
            if name in self.app.opencode_config.get("mcp", {}):
                del self.app.opencode_config["mcp"][name]
                self.refresh_list()
                self.app.save_configs_silent()


# ==================== OpenCode Agent 配置选项卡 ====================
class OpenCodeAgentTab(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        self.current_agent = None
        self.setup_ui()

    def setup_ui(self):
        main_frame = tk.Frame(self, bg=COLORS["bg"])
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = Card(main_frame, title="Agent 列表")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        btn_frame = tk.Frame(left_frame.content, bg=COLORS["card_bg"])
        btn_frame.pack(fill=tk.X, pady=(0, 8))
        ModernButton(btn_frame, "添加 Agent", self.add_agent, "primary", 100, 32).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ModernButton(btn_frame, "删除", self.delete_agent, "danger", 70, 32).pack(
            side=tk.LEFT
        )

        preset_frame = tk.Frame(left_frame.content, bg=COLORS["card_bg"])
        preset_frame.pack(fill=tk.X, pady=(0, 8))
        tk.Label(
            preset_frame,
            text="预设:",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        ).pack(side=tk.LEFT)
        for name in list(PRESET_OPENCODE_AGENTS.keys())[:4]:
            btn = tk.Button(
                preset_frame,
                text=name,
                font=FONTS["small"],
                bd=0,
                bg=COLORS["sidebar_bg"],
                fg=COLORS["text"],
                command=lambda n=name: self.load_preset(n),
                cursor="hand2",
            )
            btn.pack(side=tk.LEFT, padx=2)

        columns = ("name", "mode", "model")
        self.tree = ttk.Treeview(
            left_frame.content,
            columns=columns,
            show="headings",
            height=12,
            style="Modern.Treeview",
        )
        self.tree.heading("name", text="名称")
        self.tree.heading("mode", text="模式")
        self.tree.heading("model", text="模型")
        self.tree.column("name", width=100)
        self.tree.column("mode", width=80)
        self.tree.column("model", width=150)
        scrollbar = ttk.Scrollbar(
            left_frame.content, orient=tk.VERTICAL, command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        right_frame = Card(main_frame, title="Agent 详情")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0))

        canvas = tk.Canvas(
            right_frame.content, bg=COLORS["card_bg"], highlightthickness=0
        )
        scrollbar_r = ttk.Scrollbar(
            right_frame.content, orient=tk.VERTICAL, command=canvas.yview
        )
        form = tk.Frame(canvas, bg=COLORS["card_bg"])
        canvas.create_window((0, 0), window=form, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar_r.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_r.pack(side=tk.RIGHT, fill=tk.Y)
        form.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        row = 0
        create_label_with_tooltip(form, "Agent 名称", TOOLTIPS["agent_name"]).grid(
            row=row, column=0, sticky=tk.W, padx=10, pady=(10, 4)
        )
        row += 1
        self.name_var = tk.StringVar()
        ModernEntry(form, textvariable=self.name_var, width=25).grid(
            row=row, column=0, sticky=tk.W, padx=10, pady=(0, 8)
        )

        row += 1
        create_label_with_tooltip(form, "描述", TOOLTIPS["agent_description"]).grid(
            row=row, column=0, sticky=tk.W, padx=10, pady=(0, 4)
        )
        row += 1
        self.desc_var = tk.StringVar()
        ModernEntry(form, textvariable=self.desc_var, width=35).grid(
            row=row, column=0, sticky=tk.W, padx=10, pady=(0, 8)
        )

        row += 1
        create_label_with_tooltip(form, "模式", TOOLTIPS["opencode_agent_mode"]).grid(
            row=row, column=0, sticky=tk.W, padx=10, pady=(0, 4)
        )
        row += 1
        self.mode_var = tk.StringVar(value="subagent")
        mode_frame = tk.Frame(form, bg=COLORS["card_bg"])
        mode_frame.grid(row=row, column=0, sticky=tk.W, padx=10, pady=(0, 8))
        for mode in ["primary", "subagent", "all"]:
            tk.Radiobutton(
                mode_frame,
                text=mode,
                variable=self.mode_var,
                value=mode,
                bg=COLORS["card_bg"],
            ).pack(side=tk.LEFT, padx=(0, 12))

        row += 1
        create_label_with_tooltip(form, "模型 (可选)", TOOLTIPS["agent_model"]).grid(
            row=row, column=0, sticky=tk.W, padx=10, pady=(0, 4)
        )
        row += 1
        self.model_var = tk.StringVar()
        ModernEntry(form, textvariable=self.model_var, width=30).grid(
            row=row, column=0, sticky=tk.W, padx=10, pady=(0, 8)
        )

        row += 1
        create_label_with_tooltip(
            form, "Temperature", TOOLTIPS["opencode_agent_temperature"]
        ).grid(row=row, column=0, sticky=tk.W, padx=10, pady=(0, 4))
        row += 1
        temp_frame = tk.Frame(form, bg=COLORS["card_bg"])
        temp_frame.grid(row=row, column=0, sticky=tk.W, padx=10, pady=(0, 8))
        self.temp_var = tk.DoubleVar(value=0.3)
        self.temp_scale = tk.Scale(
            temp_frame,
            from_=0,
            to=2,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            variable=self.temp_var,
            length=150,
            bg=COLORS["card_bg"],
            highlightthickness=0,
        )
        self.temp_scale.pack(side=tk.LEFT)
        self.temp_label = tk.Label(
            temp_frame,
            text="0.3",
            font=FONTS["body"],
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
        )
        self.temp_label.pack(side=tk.LEFT, padx=(8, 0))
        self.temp_var.trace_add(
            "write",
            lambda *args: self.temp_label.config(text=f"{self.temp_var.get():.1f}"),
        )

        row += 1
        create_label_with_tooltip(
            form, "最大步数 (可选)", TOOLTIPS["opencode_agent_maxSteps"]
        ).grid(row=row, column=0, sticky=tk.W, padx=10, pady=(0, 4))
        row += 1
        self.maxsteps_var = tk.StringVar()
        ModernEntry(form, textvariable=self.maxsteps_var, width=10).grid(
            row=row, column=0, sticky=tk.W, padx=10, pady=(0, 8)
        )

        row += 1
        self.hidden_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            form,
            text="隐藏 (仅subagent)",
            variable=self.hidden_var,
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
            font=FONTS["body"],
        ).grid(row=row, column=0, sticky=tk.W, padx=10, pady=(0, 8))

        row += 1
        self.disable_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            form,
            text="禁用此Agent",
            variable=self.disable_var,
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
            font=FONTS["body"],
        ).grid(row=row, column=0, sticky=tk.W, padx=10, pady=(0, 8))

        row += 1
        create_label_with_tooltip(
            form, "工具配置 (JSON)", TOOLTIPS["opencode_agent_tools"]
        ).grid(row=row, column=0, sticky=tk.W, padx=10, pady=(0, 4))
        row += 1
        self.tools_text = tk.Text(
            form, height=3, width=35, font=FONTS["mono"], bd=1, relief=tk.SOLID
        )
        self.tools_text.grid(row=row, column=0, sticky=tk.W, padx=10, pady=(0, 8))
        self.tools_text.insert("1.0", '{"write": true, "edit": true, "bash": true}')

        row += 1
        create_label_with_tooltip(
            form, "权限配置 (JSON)", TOOLTIPS["opencode_agent_permission"]
        ).grid(row=row, column=0, sticky=tk.W, padx=10, pady=(0, 4))
        row += 1
        self.perm_text = tk.Text(
            form, height=3, width=35, font=FONTS["mono"], bd=1, relief=tk.SOLID
        )
        self.perm_text.grid(row=row, column=0, sticky=tk.W, padx=10, pady=(0, 8))
        self.perm_text.insert("1.0", "{}")

        row += 1
        create_label_with_tooltip(
            form, "系统提示词", TOOLTIPS["opencode_agent_prompt"]
        ).grid(row=row, column=0, sticky=tk.W, padx=10, pady=(0, 4))
        row += 1
        self.prompt_text = tk.Text(
            form, height=4, width=35, font=FONTS["mono"], bd=1, relief=tk.SOLID
        )
        self.prompt_text.grid(row=row, column=0, sticky=tk.W, padx=10, pady=(0, 12))

        row += 1
        ModernButton(form, "保存 Agent", self.save_agent, "success", 100, 36).grid(
            row=row, column=0, sticky=tk.W, padx=10, pady=(0, 20)
        )

    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        agents = self.app.opencode_config.get("agent", {})
        for name, data in agents.items():
            mode = data.get("mode", "all")
            model = data.get("model", "-")
            self.tree.insert("", tk.END, values=(name, mode, model))

    def on_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        name = item["values"][0]
        self.current_agent = name
        agents = self.app.opencode_config.get("agent", {})
        if name in agents:
            data = agents[name]
            self.name_var.set(name)
            self.desc_var.set(data.get("description", ""))
            self.mode_var.set(data.get("mode", "all"))
            self.model_var.set(data.get("model", ""))
            self.temp_var.set(data.get("temperature", 0.3))
            self.maxsteps_var.set(
                str(data.get("maxSteps", "")) if "maxSteps" in data else ""
            )
            self.hidden_var.set(data.get("hidden", False))
            self.disable_var.set(data.get("disable", False))
            self.tools_text.delete("1.0", tk.END)
            self.tools_text.insert(
                "1.0", json.dumps(data.get("tools", {}), indent=2, ensure_ascii=False)
            )
            self.perm_text.delete("1.0", tk.END)
            self.perm_text.insert(
                "1.0",
                json.dumps(data.get("permission", {}), indent=2, ensure_ascii=False),
            )
            self.prompt_text.delete("1.0", tk.END)
            self.prompt_text.insert("1.0", data.get("prompt", ""))

    def load_preset(self, preset_name):
        if preset_name in PRESET_OPENCODE_AGENTS:
            preset = PRESET_OPENCODE_AGENTS[preset_name]
            self.name_var.set(preset_name)
            self.desc_var.set(preset.get("description", ""))
            self.mode_var.set(preset.get("mode", "subagent"))
            self.tools_text.delete("1.0", tk.END)
            self.tools_text.insert(
                "1.0", json.dumps(preset.get("tools", {}), indent=2, ensure_ascii=False)
            )
            self.perm_text.delete("1.0", tk.END)
            self.perm_text.insert(
                "1.0",
                json.dumps(preset.get("permission", {}), indent=2, ensure_ascii=False),
            )

    def add_agent(self):
        self.current_agent = None
        self.name_var.set("")
        self.desc_var.set("")
        self.mode_var.set("subagent")
        self.model_var.set("")
        self.temp_var.set(0.3)
        self.maxsteps_var.set("")
        self.hidden_var.set(False)
        self.disable_var.set(False)
        self.tools_text.delete("1.0", tk.END)
        self.tools_text.insert("1.0", "{}")
        self.perm_text.delete("1.0", tk.END)
        self.perm_text.insert("1.0", "{}")
        self.prompt_text.delete("1.0", tk.END)

    def save_agent(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("提示", "请输入 Agent 名称")
            return
        desc = self.desc_var.get().strip()
        if not desc:
            messagebox.showwarning("提示", "请输入 Agent 描述")
            return
        data = {"description": desc, "mode": self.mode_var.get()}
        model = self.model_var.get().strip()
        if model:
            data["model"] = model
        temp = self.temp_var.get()
        if temp != 0.3:
            data["temperature"] = temp
        maxsteps = self.maxsteps_var.get().strip()
        if maxsteps:
            try:
                data["maxSteps"] = int(maxsteps)
            except:
                pass
        if self.hidden_var.get():
            data["hidden"] = True
        if self.disable_var.get():
            data["disable"] = True
        try:
            tools = json.loads(self.tools_text.get("1.0", tk.END).strip())
            if tools:
                data["tools"] = tools
        except:
            pass
        try:
            perm = json.loads(self.perm_text.get("1.0", tk.END).strip())
            if perm:
                data["permission"] = perm
        except:
            pass
        prompt = self.prompt_text.get("1.0", tk.END).strip()
        if prompt:
            data["prompt"] = prompt
        self.app.opencode_config.setdefault("agent", {})[name] = data
        if self.current_agent and self.current_agent != name:
            del self.app.opencode_config["agent"][self.current_agent]
        self.current_agent = name
        self.refresh_list()
        self.app.save_configs_silent()
        messagebox.showinfo("成功", f"Agent [{name}] 已保存")

    def delete_agent(self):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        name = item["values"][0]
        if messagebox.askyesno("确认", f"确定删除 Agent [{name}]?"):
            if name in self.app.opencode_config.get("agent", {}):
                del self.app.opencode_config["agent"][name]
                self.refresh_list()
                self.app.save_configs_silent()


# ==================== 帮助说明选项卡 ====================
class HelpTab(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        self.setup_ui()

    def setup_ui(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True)

        # 配置优先级说明
        priority_frame = tk.Frame(notebook, bg=COLORS["card_bg"])
        notebook.add(priority_frame, text="  配置优先级  ")
        priority_card = Card(priority_frame)
        priority_card.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        priority_text = tk.Text(
            priority_card.content,
            wrap=tk.WORD,
            font=FONTS["body"],
            bd=0,
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
        )
        priority_text.pack(fill=tk.BOTH, expand=True)
        priority_content = """配置优先顺序（从高到低）

1. 远程配置 (Remote)
   通过 API 或远程服务器获取的配置
   优先级最高，会覆盖所有本地配置

2. 全局配置 (Global)
   位置: ~/.config/opencode/opencode.json
   影响所有项目的默认配置

3. 自定义配置 (Custom)
   通过 --config 参数指定的配置文件
   用于特定场景的配置覆盖

4. 项目配置 (Project)
   位置: <项目根目录>/opencode.json
   项目级别的配置，仅影响当前项目

5. .opencode 目录配置
   位置: <项目根目录>/.opencode/config.json
   项目内的隐藏配置目录

6. 内联配置 (Inline)
   通过命令行参数直接指定的配置
   优先级最低，但最灵活

配置合并规则:
- 高优先级配置会覆盖低优先级的同名配置项
- 未指定的配置项会继承低优先级的值
- Provider 和 Model 配置会进行深度合并"""
        priority_text.insert("1.0", priority_content)
        priority_text.config(state=tk.DISABLED)

        # 使用说明
        usage_frame = tk.Frame(notebook, bg=COLORS["card_bg"])
        notebook.add(usage_frame, text="  使用说明  ")
        usage_card = Card(usage_frame)
        usage_card.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        usage_text = tk.Text(
            usage_card.content,
            wrap=tk.WORD,
            font=FONTS["body"],
            bd=0,
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
        )
        usage_text.pack(fill=tk.BOTH, expand=True)
        usage_content = """OpenCode 配置管理器 使用说明

一、Provider 管理
   添加自定义 API 提供商
   配置 API 地址和密钥
   支持多种 SDK: @ai-sdk/anthropic, @ai-sdk/openai 等

二、Model 管理
   在 Provider 下添加模型
   支持预设常用模型快速选择
   配置模型参数（上下文限制、输出限制等）

三、Agent 管理 (Oh My OpenCode)
   配置不同用途的 Agent
   绑定已配置的 Provider/Model
   支持预设 Agent 模板

四、Category 管理 (Oh My OpenCode)
   配置任务分类
   设置不同分类的 Temperature
   绑定对应的模型

五、权限管理
   配置工具的使用权限
   allow: 允许使用
   ask: 每次询问
   deny: 禁止使用

六、外部导入
   检测 Claude Code 等工具的配置
   一键导入已有配置

注意事项:
- 修改后请点击保存按钮
- 建议定期备份配置文件
- Agent/Category 的模型必须是已配置的 Provider/Model"""
        usage_text.insert("1.0", usage_content)
        usage_text.config(state=tk.DISABLED)

        # 关于
        about_frame = tk.Frame(notebook, bg=COLORS["card_bg"])
        notebook.add(about_frame, text="  关于  ")
        about_card = Card(about_frame)
        about_card.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        center_frame = tk.Frame(about_card.content, bg=COLORS["card_bg"])
        center_frame.pack(expand=True)

        tk.Label(
            center_frame,
            text="OpenCode 配置管理器",
            font=FONTS["title"],
            bg=COLORS["card_bg"],
            fg=COLORS["primary"],
        ).pack(pady=(20, 5))
        tk.Label(
            center_frame,
            text="v0.6.1",
            font=FONTS["subtitle"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        ).pack(pady=(0, 20))
        tk.Label(
            center_frame,
            text="可视化管理 OpenCode 和 Oh My OpenCode 配置文件",
            font=FONTS["body"],
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
        ).pack(pady=5)
        tk.Label(
            center_frame,
            text="支持 Provider、Model、Agent、MCP、Compaction 管理",
            font=FONTS["body"],
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
        ).pack(pady=5)
        tk.Label(
            center_frame,
            text="支持从 Claude Code 等工具导入配置",
            font=FONTS["body"],
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
        ).pack(pady=5)
        tk.Label(center_frame, text="", font=FONTS["body"], bg=COLORS["card_bg"]).pack(
            pady=10
        )
        tk.Label(
            center_frame,
            text="开发日期: 2026-01-14",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        ).pack(pady=5)


# ==================== 侧边栏导航 ====================
class Sidebar(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["sidebar_bg"], width=200)
        self.app = app
        self.pack_propagate(False)
        self.buttons = {}
        self.active = None
        self.setup_ui()

    def setup_ui(self):
        # Logo
        logo_frame = tk.Frame(self, bg=COLORS["sidebar_bg"])
        logo_frame.pack(fill=tk.X, padx=16, pady=20)
        tk.Label(
            logo_frame,
            text="OpenCode",
            font=FONTS["title"],
            bg=COLORS["sidebar_bg"],
            fg=COLORS["primary"],
        ).pack(anchor=tk.W)
        tk.Label(
            logo_frame,
            text="配置管理器 v0.6.1",
            font=FONTS["small"],
            bg=COLORS["sidebar_bg"],
            fg=COLORS["text_secondary"],
        ).pack(anchor=tk.W)

        # 分隔线
        tk.Frame(self, height=1, bg=COLORS["border"]).pack(
            fill=tk.X, padx=16, pady=(0, 16)
        )

        # OpenCode 分组 - 显示配置文件路径
        opencode_header = tk.Frame(self, bg=COLORS["sidebar_bg"])
        opencode_header.pack(fill=tk.X, padx=16, pady=(0, 8))
        tk.Label(
            opencode_header,
            text="OpenCode",
            font=FONTS["small"],
            bg=COLORS["sidebar_bg"],
            fg=COLORS["text_secondary"],
        ).pack(anchor=tk.W)
        opencode_path = str(ConfigPaths.get_opencode_config())
        self.opencode_path_label = tk.Label(
            opencode_header,
            text=opencode_path[:40] + "..."
            if len(opencode_path) > 40
            else opencode_path,
            font=("Consolas", 8),
            bg=COLORS["sidebar_bg"],
            fg=COLORS["text_secondary"],
            cursor="hand2",
        )
        self.opencode_path_label.pack(anchor=tk.W)
        ToolTip(
            self.opencode_path_label, f"配置文件路径:\n{opencode_path}\n\n点击复制路径"
        )
        self.opencode_path_label.bind(
            "<Button-1>", lambda e: self.copy_path(opencode_path)
        )

        self.add_nav_button("provider", "Provider 管理")
        self.add_nav_button("model", "Model 管理")
        self.add_nav_button("opencode_agent", "Agent 配置")
        self.add_nav_button("mcp", "MCP 服务器")
        self.add_nav_button("compaction", "上下文压缩")
        self.add_nav_button("permission", "权限管理")

        # Oh My OpenCode 分组 - 显示配置文件路径
        ohmyopencode_header = tk.Frame(self, bg=COLORS["sidebar_bg"])
        ohmyopencode_header.pack(fill=tk.X, padx=16, pady=(20, 8))
        tk.Label(
            ohmyopencode_header,
            text="Oh My OpenCode",
            font=FONTS["small"],
            bg=COLORS["sidebar_bg"],
            fg=COLORS["text_secondary"],
        ).pack(anchor=tk.W)
        ohmyopencode_path = str(ConfigPaths.get_ohmyopencode_config())
        self.ohmyopencode_path_label = tk.Label(
            ohmyopencode_header,
            text=ohmyopencode_path[:40] + "..."
            if len(ohmyopencode_path) > 40
            else ohmyopencode_path,
            font=("Consolas", 8),
            bg=COLORS["sidebar_bg"],
            fg=COLORS["text_secondary"],
            cursor="hand2",
        )
        self.ohmyopencode_path_label.pack(anchor=tk.W)
        ToolTip(
            self.ohmyopencode_path_label,
            f"配置文件路径:\n{ohmyopencode_path}\n\n点击复制路径",
        )
        self.ohmyopencode_path_label.bind(
            "<Button-1>", lambda e: self.copy_path(ohmyopencode_path)
        )

        self.add_nav_button("agent", "Agent 管理")
        self.add_nav_button("category", "Category 管理")

        # 其他
        tk.Label(
            self,
            text="其他",
            font=FONTS["small"],
            bg=COLORS["sidebar_bg"],
            fg=COLORS["text_secondary"],
        ).pack(anchor=tk.W, padx=16, pady=(20, 8))
        self.add_nav_button("import", "外部导入")
        self.add_nav_button("help", "帮助说明")

        # 底部状态
        bottom_frame = tk.Frame(self, bg=COLORS["sidebar_bg"])
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=16, pady=16)
        self.status_label = tk.Label(
            bottom_frame,
            text="就绪",
            font=FONTS["small"],
            bg=COLORS["sidebar_bg"],
            fg=COLORS["text_secondary"],
        )
        self.status_label.pack(anchor=tk.W)

    def copy_path(self, path):
        """复制路径到剪贴板"""
        self.app.root.clipboard_clear()
        self.app.root.clipboard_append(path)
        self.status_label.config(text="路径已复制")

    def add_nav_button(self, key, text):
        btn = tk.Label(
            self,
            text=text,
            font=FONTS["body"],
            bg=COLORS["sidebar_bg"],
            fg=COLORS["text"],
            cursor="hand2",
            anchor=tk.W,
            padx=16,
            pady=10,
        )
        btn.pack(fill=tk.X)
        btn.bind("<Enter>", lambda e, b=btn, k=key: self.on_hover(b, k, True))
        btn.bind("<Leave>", lambda e, b=btn, k=key: self.on_hover(b, k, False))
        btn.bind("<Button-1>", lambda e, k=key: self.on_click(k))
        self.buttons[key] = btn

    def on_hover(self, btn, key, enter):
        if key != self.active:
            btn.config(bg=COLORS["border"] if enter else COLORS["sidebar_bg"])

    def on_click(self, key):
        if self.active:
            self.buttons[self.active].config(bg=COLORS["sidebar_bg"], fg=COLORS["text"])
        self.active = key
        self.buttons[key].config(bg=COLORS["primary"], fg="#FFFFFF")
        self.app.show_page(key)

    def set_active(self, key):
        if self.active:
            self.buttons[self.active].config(bg=COLORS["sidebar_bg"], fg=COLORS["text"])
        self.active = key
        self.buttons[key].config(bg=COLORS["primary"], fg="#FFFFFF")


# ==================== 主窗口 ====================
class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("OpenCode 配置管理器 v0.6.1")
        self.root.geometry("1200x750")
        self.root.minsize(1000, 600)
        self.root.configure(bg=COLORS["bg"])

        # 设置窗口图标
        self.set_icon()

        self.opencode_config = {}
        self.ohmyopencode_config = {}
        self.modified = False
        self.backup_manager = BackupManager()
        self.pages = {}
        self.first_run_checked = False

        self.setup_ui()
        self.load_configs()
        self.check_first_run()

    def check_first_run(self):
        """首次运行检查，提示备份"""
        if self.first_run_checked:
            return
        self.first_run_checked = True

        # 检查是否有配置文件但没有备份
        opencode_path = ConfigPaths.get_opencode_config()
        backups = self.backup_manager.list_backups()

        if opencode_path.exists() and len(backups) == 0:
            if messagebox.askyesno(
                "首次使用提示",
                "检测到已有配置文件，建议先备份原配置以防意外。\n\n是否立即创建备份？",
            ):
                self.backup_configs()

    def set_icon(self):
        """设置窗口图标（支持 PyInstaller 打包后的资源路径）"""
        import sys

        try:
            # PyInstaller 打包后的资源路径
            if getattr(sys, "frozen", False):
                base_path = Path(sys._MEIPASS)
            else:
                base_path = Path(__file__).parent

            icon_paths = [
                base_path / "assets" / "icon.ico",
                Path(__file__).parent / "assets" / "icon.ico",
                Path.home() / ".config" / "opencode" / "icon.ico",
                Path("assets/icon.ico"),
            ]
            for icon_path in icon_paths:
                if icon_path.exists():
                    self.root.iconbitmap(str(icon_path))
                    return
            png_paths = [
                base_path / "assets" / "icon.png",
                Path(__file__).parent / "assets" / "icon.png",
                Path("assets/icon.png"),
            ]
            for png_path in png_paths:
                if png_path.exists():
                    icon = tk.PhotoImage(file=str(png_path))
                    self.root.iconphoto(True, icon)
                    return
        except Exception as e:
            print(f"Failed to set icon: {e}")

    def setup_ui(self):
        # 主容器
        main_container = tk.Frame(self.root, bg=COLORS["bg"])
        main_container.pack(fill=tk.BOTH, expand=True)

        # 侧边栏
        self.sidebar = Sidebar(main_container, self)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)

        # 右侧内容区
        right_container = tk.Frame(main_container, bg=COLORS["bg"])
        right_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 顶部工具栏
        toolbar = tk.Frame(right_container, bg=COLORS["card_bg"], height=60)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)

        toolbar_inner = tk.Frame(toolbar, bg=COLORS["card_bg"])
        toolbar_inner.pack(fill=tk.BOTH, expand=True, padx=20, pady=12)

        ModernButton(
            toolbar_inner, "保存全部", self.save_configs, "primary", 90, 36
        ).pack(side=tk.LEFT, padx=(0, 8))
        ModernButton(
            toolbar_inner, "重新加载", self.load_configs, "secondary", 90, 36
        ).pack(side=tk.LEFT, padx=(0, 8))
        ModernButton(
            toolbar_inner, "备份", self.backup_configs, "secondary", 70, 36
        ).pack(side=tk.LEFT, padx=(0, 8))
        ModernButton(
            toolbar_inner, "恢复备份", self.show_restore_dialog, "secondary", 90, 36
        ).pack(side=tk.LEFT)

        self.modified_label = tk.Label(
            toolbar_inner,
            text="",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["warning"],
        )
        self.modified_label.pack(side=tk.RIGHT)

        self.config_status = tk.Label(
            toolbar_inner,
            text="配置: 未加载",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        )
        self.config_status.pack(side=tk.RIGHT, padx=(0, 20))

        # 分隔线
        tk.Frame(right_container, height=1, bg=COLORS["border"]).pack(fill=tk.X)

        # 内容区
        self.content_frame = tk.Frame(right_container, bg=COLORS["bg"])
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 创建页面
        self.pages["provider"] = ProviderTab(self.content_frame, self)
        self.pages["model"] = ModelTab(self.content_frame, self)
        self.pages["opencode_agent"] = OpenCodeAgentTab(self.content_frame, self)
        self.pages["mcp"] = MCPTab(self.content_frame, self)
        self.pages["compaction"] = CompactionTab(self.content_frame, self)
        self.pages["permission"] = PermissionTab(self.content_frame, self)
        self.pages["agent"] = AgentTab(self.content_frame, self)
        self.pages["category"] = CategoryTab(self.content_frame, self)
        self.pages["import"] = ImportTab(self.content_frame, self)
        self.pages["help"] = HelpTab(self.content_frame, self)

        # 默认显示 Provider 页面
        self.show_page("provider")
        self.sidebar.set_active("provider")

        # 快捷键
        self.root.bind("<Control-s>", lambda e: self.save_configs())

    def show_page(self, key):
        for page in self.pages.values():
            page.pack_forget()
        if key in self.pages:
            self.pages[key].pack(fill=tk.BOTH, expand=True)

    def load_configs(self):
        opencode_path = ConfigPaths.get_opencode_config()
        ohmyopencode_path = ConfigPaths.get_ohmyopencode_config()
        self.opencode_config = ConfigManager.load_json(opencode_path) or {}
        self.ohmyopencode_config = ConfigManager.load_json(ohmyopencode_path) or {}
        self.refresh_all_tabs()
        provider_count = len(self.opencode_config.get("provider", {}))
        agent_count = len(self.ohmyopencode_config.get("agents", {}))
        self.config_status.config(
            text=f"Provider: {provider_count} | Agent: {agent_count}"
        )
        self.modified = False
        self.modified_label.config(text="")
        self.sidebar.status_label.config(text="配置已加载")

    def refresh_all_tabs(self):
        self.pages["provider"].refresh_list()
        self.pages["model"].refresh_providers()
        self.pages["opencode_agent"].refresh_list()
        self.pages["mcp"].refresh_list()
        self.pages["compaction"].refresh_list()
        self.pages["permission"].refresh_list()
        self.pages["agent"].refresh_models()
        self.pages["agent"].refresh_list()
        self.pages["category"].refresh_models()
        self.pages["category"].refresh_list()
        self.pages["import"].refresh_scan()

    def save_configs(self):
        """保存所有配置（带提示）"""
        opencode_path = ConfigPaths.get_opencode_config()
        ohmyopencode_path = ConfigPaths.get_ohmyopencode_config()
        self.backup_manager.backup(opencode_path, "before_save")
        self.backup_manager.backup(ohmyopencode_path, "before_save")
        if ConfigManager.save_json(opencode_path, self.opencode_config):
            if ConfigManager.save_json(ohmyopencode_path, self.ohmyopencode_config):
                self.modified = False
                self.modified_label.config(text="")
                self.sidebar.status_label.config(text="配置已保存")
                messagebox.showinfo("成功", "所有配置已保存到文件")
                return True
        messagebox.showerror("错误", "保存配置失败")
        return False

    def save_configs_silent(self):
        """静默保存配置（不弹窗）"""
        opencode_path = ConfigPaths.get_opencode_config()
        ohmyopencode_path = ConfigPaths.get_ohmyopencode_config()
        success = True
        if ConfigManager.save_json(opencode_path, self.opencode_config):
            if ConfigManager.save_json(ohmyopencode_path, self.ohmyopencode_config):
                self.modified = False
                self.modified_label.config(text="")
                self.sidebar.status_label.config(text="配置已保存")
                # 更新状态栏
                provider_count = len(self.opencode_config.get("provider", {}))
                agent_count = len(self.ohmyopencode_config.get("agents", {}))
                self.config_status.config(
                    text=f"Provider: {provider_count} | Agent: {agent_count}"
                )
                return True
        return False

    def backup_configs(self):
        """手动备份配置"""
        opencode_path = ConfigPaths.get_opencode_config()
        ohmyopencode_path = ConfigPaths.get_ohmyopencode_config()
        b1 = self.backup_manager.backup(opencode_path, "manual")
        b2 = self.backup_manager.backup(ohmyopencode_path, "manual")
        if b1 or b2:
            backup_dir = ConfigPaths.get_backup_dir()
            messagebox.showinfo("成功", f"备份已创建\n\n备份目录: {backup_dir}")
        else:
            messagebox.showwarning("提示", "没有配置文件需要备份")

    def show_restore_dialog(self):
        """显示恢复备份对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("恢复备份")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=COLORS["bg"])

        # 标题
        tk.Label(
            dialog,
            text="选择要恢复的备份",
            font=FONTS["subtitle"],
            bg=COLORS["bg"],
            fg=COLORS["text"],
        ).pack(pady=(20, 10))

        # 备份列表
        list_frame = tk.Frame(dialog, bg=COLORS["bg"])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        columns = ("display", "path")
        tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=10,
            style="Modern.Treeview",
        )
        tree.heading("display", text="备份信息")
        tree.heading("path", text="文件路径")
        tree.column("display", width=250)
        tree.column("path", width=300)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 加载备份列表
        backups = self.backup_manager.list_backups()
        for backup in backups:
            tree.insert("", tk.END, values=(backup["display"], str(backup["path"])))

        # 按钮区
        btn_frame = tk.Frame(dialog, bg=COLORS["bg"])
        btn_frame.pack(fill=tk.X, padx=20, pady=20)

        def do_restore():
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("提示", "请选择要恢复的备份")
                return
            item = tree.item(selection[0])
            backup_path = Path(item["values"][1])

            # 确定目标文件
            if "opencode" in backup_path.stem and "oh-my" not in backup_path.stem:
                target_path = ConfigPaths.get_opencode_config()
            else:
                target_path = ConfigPaths.get_ohmyopencode_config()

            if messagebox.askyesno(
                "确认恢复", f"确定要恢复此备份吗？\n\n当前配置将被覆盖。"
            ):
                if self.backup_manager.restore(backup_path, target_path):
                    self.load_configs()
                    dialog.destroy()
                    messagebox.showinfo("成功", "备份已恢复")
                else:
                    messagebox.showerror("错误", "恢复失败")

        def do_delete():
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("提示", "请选择要删除的备份")
                return
            item = tree.item(selection[0])
            backup_path = Path(item["values"][1])

            if messagebox.askyesno("确认删除", f"确定要删除此备份吗？"):
                if self.backup_manager.delete_backup(backup_path):
                    tree.delete(selection[0])
                    messagebox.showinfo("成功", "备份已删除")

        ModernButton(btn_frame, "恢复选中", do_restore, "success", 100, 36).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ModernButton(btn_frame, "删除选中", do_delete, "danger", 100, 36).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ModernButton(btn_frame, "关闭", dialog.destroy, "secondary", 80, 36).pack(
            side=tk.RIGHT
        )

    def mark_modified(self):
        self.modified = True
        self.modified_label.config(text="● 已修改")

    def on_close(self):
        if self.modified:
            if messagebox.askyesno("确认", "有未保存的修改，确定要退出吗?"):
                self.root.destroy()
        else:
            self.root.destroy()

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()


if __name__ == "__main__":
    app = MainWindow()
    app.run()
