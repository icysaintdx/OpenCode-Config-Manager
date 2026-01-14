#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenCode & Oh My OpenCode 配置管理器 v0.8.0 (QFluentWidgets版本)
一个可视化的GUI工具，用于管理OpenCode和Oh My OpenCode的配置文件

基于 PyQt5 + QFluentWidgets 重写
原版本 v0.7.0 使用 ttkbootstrap 框架

更新日志 v0.8.0:
- 完全重写为 PyQt5 + QFluentWidgets 框架
- 采用 Win11 Fluent Design 风格
- 支持深色/浅色/跟随系统主题
- 现代化导航界面
- 优化用户体验
"""

import sys
import json
import re
import shutil
import webbrowser
import urllib.request
import urllib.error
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

from PyQt5.QtCore import Qt, QSize, pyqtSignal, QThread, QTimer
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QStackedWidget,
    QFrame,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QDialog,
    QFileDialog,
    QMessageBox,
    QSizePolicy,
    QScrollArea,
    QGridLayout,
    QSpacerItem,
)
from PyQt5.QtGui import QIcon, QFont, QColor, QDesktopServices

# QFluentWidgets 导入
from qfluentwidgets import (
    # 窗口和导航
    FluentWindow,
    NavigationInterface,
    NavigationItemPosition,
    NavigationAvatarWidget,
    NavigationToolButton,
    qrouter,
    # 基础控件
    PushButton,
    PrimaryPushButton,
    TransparentPushButton,
    ToolButton,
    TransparentToolButton,
    DropDownPushButton,
    SplitPushButton,
    HyperlinkButton,
    RadioButton,
    CheckBox,
    ComboBox,
    LineEdit,
    PasswordLineEdit,
    SpinBox,
    DoubleSpinBox,
    Slider,
    SwitchButton,
    TextEdit,
    PlainTextEdit,
    # 卡片和容器
    CardWidget,
    SimpleCardWidget,
    ElevatedCardWidget,
    HeaderCardWidget,
    GroupHeaderCardWidget,
    ExpandGroupSettingCard,
    ExpandSettingCard,
    # 列表和表格
    ListWidget,
    TableWidget,
    TreeWidget,
    # 对话框和消息
    MessageBox,
    Dialog,
    Flyout,
    FlyoutView,
    InfoBar,
    InfoBarPosition,
    StateToolTip,
    # 滚动区域
    ScrollArea,
    SmoothScrollArea,
    SingleDirectionScrollArea,
    # 标签页
    TabBar,
    TabItem,
    # 图标
    FluentIcon as FIF,
    Icon,
    # 主题
    setTheme,
    setThemeColor,
    Theme,
    isDarkTheme,
    # 样式
    StyleSheet,
    FluentStyleSheet,
    # 其他
    ToolTipFilter,
    ToolTipPosition,
    Action,
    RoundMenu,
    MenuAnimationType,
    ProgressBar,
    IndeterminateProgressBar,
    Pivot,
    SegmentedWidget,
    SubtitleLabel,
    BodyLabel,
    CaptionLabel,
    StrongBodyLabel,
    TitleLabel,
    LargeTitleLabel,
    setFont,
    getFont,
)
from qfluentwidgets.components.widgets.frameless_window import FramelessWindow


# ==================== 版本和项目信息 ====================
APP_VERSION = "0.8.0"
GITHUB_REPO = "icysaintdx/OpenCode-Config-Manager"
GITHUB_URL = f"https://github.com/{GITHUB_REPO}"
GITHUB_RELEASES_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
AUTHOR_NAME = "IcySaint"
AUTHOR_GITHUB = "https://github.com/icysaintdx"


# ==================== 预设SDK列表 ====================
PRESET_SDKS = [
    "@ai-sdk/anthropic",
    "@ai-sdk/openai",
    "@ai-sdk/google",
    "@ai-sdk/azure",
    "@ai-sdk/openai-compatible",
]

# SDK与模型厂商的对应关系
SDK_MODEL_COMPATIBILITY = {
    "@ai-sdk/anthropic": ["Claude 系列"],
    "@ai-sdk/openai": ["OpenAI/Codex 系列", "其他模型"],
    "@ai-sdk/google": ["Gemini 系列"],
    "@ai-sdk/azure": ["OpenAI/Codex 系列"],
    "@ai-sdk/openai-compatible": ["其他模型"],
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
                # options: 默认启用 thinking 模式
                "options": {"thinkingConfig": {"thinkingBudget": 8000}},
                # variants: 不同 thinking 预算的变体
                "variants": {
                    "low": {"thinkingConfig": {"thinkingBudget": 4000}},
                    "high": {"thinkingConfig": {"thinkingBudget": 16000}},
                    "max": {"thinkingConfig": {"thinkingBudget": 32000}},
                },
                "description": "Google最新Pro模型，支持thinking模式\noptions.thinkingConfig.thinkingBudget 控制默认思考预算",
            },
            "gemini-2.0-flash": {
                "name": "Gemini 2.0 Flash",
                "attachment": True,
                "limit": {"context": 1048576, "output": 8192},
                "modalities": {"input": ["text", "image"], "output": ["text"]},
                # options: 默认启用 thinking 模式
                "options": {"thinkingConfig": {"thinkingBudget": 4000}},
                # variants: 不同 thinking 预算的变体
                "variants": {
                    "low": {"thinkingConfig": {"thinkingBudget": 2000}},
                    "high": {"thinkingConfig": {"thinkingBudget": 8000}},
                },
                "description": "Google Flash模型，支持thinking模式\noptions.thinkingConfig.thinkingBudget 控制默认思考预算",
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
# 所有提示都包含：关键字 + 白话解释 + 使用场景 + 示例
TOOLTIPS = {
    # Provider相关
    "provider_name": """Provider 名称 ⓘ

【作用】Provider的唯一标识符，用于在配置中引用

【格式】小写字母和连字符，如 anthropic, openai, my-proxy

【使用场景】配置模型时需要指定 provider/model-id 格式""",
    "provider_display": """显示名称 ⓘ

【作用】在界面中显示的友好名称

【示例】Anthropic (Claude)、OpenAI 官方、我的中转站""",
    "provider_sdk": """SDK 包名 ⓘ

【作用】指定使用哪个AI SDK来调用API

【选择指南】
• Claude系列 → @ai-sdk/anthropic
• GPT/OpenAI系列 → @ai-sdk/openai
• Gemini系列 → @ai-sdk/google
• Azure OpenAI → @ai-sdk/azure
• 其他兼容API → @ai-sdk/openai-compatible

【重要】SDK必须与模型厂商匹配！""",
    "provider_url": """API 地址 (baseURL) ⓘ

【作用】API服务的访问地址

【使用场景】
• 官方API → 留空（自动使用默认地址）
• 中转站 → 填写中转站地址
• 私有部署 → 填写私有服务地址""",
    "provider_apikey": """API 密钥 ⓘ

【作用】用于身份验证的密钥

【安全提示】
• 支持环境变量: {env:ANTHROPIC_API_KEY}
• 不要提交到代码仓库""",
    "provider_timeout": """请求超时 ⓘ

【单位】毫秒 (ms)
【默认】300000 (5分钟)
【特殊值】false = 禁用超时""",
    # Model相关
    "model_id": """模型 ID ⓘ

【作用】模型的唯一标识符，必须与API提供商一致

【示例】
• Claude: claude-sonnet-4-5-20250929
• GPT: gpt-5, gpt-4o
• Gemini: gemini-3-pro

【重要】模型ID错误会导致API调用失败！""",
    "model_name": """显示名称 ⓘ

【作用】在界面中显示的友好名称

【示例】Claude Sonnet 4.5、GPT-5 旗舰版""",
    "model_attachment": """支持附件 ⓘ

【作用】是否支持上传文件（图片、文档等）

【支持情况】
✓ 多模态模型支持（Claude、GPT-4o、Gemini）
✗ 纯文本模型不支持（o1系列）""",
    "model_context": """上下文窗口 ⓘ

【作用】模型能处理的最大输入长度（tokens）

【常见大小】
• 128K ≈ 10万字
• 200K ≈ 15万字
• 1M ≈ 80万字
• 2M ≈ 160万字""",
    "model_output": """最大输出 ⓘ

【作用】模型单次回复的最大长度（tokens）

【常见大小】
• 8K ≈ 6000字
• 16K ≈ 12000字
• 32K ≈ 24000字
• 64K ≈ 48000字""",
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

【切换方式】使用 variant_cycle 快捷键

【与Options的区别】
Options是默认值，Variants是可选预设""",
    # Options快捷添加
    "option_reasoningEffort": """推理强度 (reasoningEffort) ⓘ

【作用】控制模型的推理深度（OpenAI模型）

【可选值】
• xhigh - 超高强度（GPT-5专属）
• high - 高强度，更准确但更慢
• medium - 中等强度
• low - 低强度，更快

【使用建议】
• 复杂问题 → high/xhigh
• 简单问题 → low/medium""",
    "option_textVerbosity": """输出详细程度 (textVerbosity) ⓘ

【作用】控制回复的详细程度（OpenAI模型）

【可选值】
• low - 简洁输出
• high - 详细输出

【使用建议】
• 代码生成 → low
• 学习解释 → high""",
    "option_reasoningSummary": """推理摘要 (reasoningSummary) ⓘ

【作用】是否生成推理过程的摘要（OpenAI模型）

【可选值】
• auto - 自动决定
• none - 不生成摘要""",
    "option_thinking_type": """Thinking模式 (thinking.type) ⓘ

【作用】是否启用Claude的extended thinking功能

【可选值】
• enabled - 启用thinking模式
• disabled - 禁用thinking模式

【什么是Thinking模式？】
让Claude在回答前进行深度思考

【适用模型】Claude Opus 4.5、Claude Sonnet 4.5

【使用建议】
• 复杂推理/编程 → enabled
• 简单对话 → disabled""",
    "option_thinking_budget": """Thinking预算 (budgetTokens) ⓘ

【作用】控制模型思考的token数量

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
    # Agent相关 (Oh My OpenCode)
    "agent_name": """Agent 名称 ⓘ

【作用】Agent的唯一标识符

【预设Agent】oracle, librarian, explore, code-reviewer""",
    "agent_model": """绑定模型 ⓘ

【格式】provider/model-id

【示例】anthropic/claude-sonnet-4-5-20250929""",
    "agent_description": """Agent 描述 ⓘ

【作用】描述Agent的功能和适用场景""",
    # Agent相关 (OpenCode原生)
    "opencode_agent_mode": """Agent 模式 ⓘ

【可选值】
• primary - 主Agent，可通过Tab键切换
• subagent - 子Agent，通过@提及调用
• all - 两种模式都支持""",
    "opencode_agent_temperature": """生成温度 ⓘ

【取值范围】0.0 - 2.0

【推荐设置】
• 0.0-0.2: 适合代码/分析
• 0.3-0.5: 平衡创造性和准确性
• 0.6-1.0: 适合创意任务""",
    "opencode_agent_maxSteps": """最大步数 ⓘ

【作用】限制Agent执行的工具调用次数

【推荐设置】
• 留空 = 无限制
• 10-20: 简单任务
• 50-100: 复杂任务""",
    "opencode_agent_prompt": """系统提示词 ⓘ

【作用】定义Agent的行为和专长

【支持格式】
• 直接写入提示词文本
• 文件引用: {file:./prompts/agent.txt}""",
    "opencode_agent_tools": """工具配置 ⓘ

【格式】JSON对象

【配置方式】
• true - 启用工具
• false - 禁用工具

【支持通配符】mcp_* 匹配所有MCP工具""",
    "opencode_agent_permission": """权限配置 ⓘ

【权限级别】
• allow - 允许，无需确认
• ask - 每次询问用户
• deny - 禁止使用""",
    "opencode_agent_hidden": """隐藏 ⓘ

【作用】是否在@自动完成中隐藏此Agent

【仅对subagent有效】

【注意】隐藏的Agent仍可被其他Agent调用""",
    # Category相关
    "category_name": """Category 名称 ⓘ

【预设分类】visual, business-logic, documentation, code-analysis""",
    "category_model": """绑定模型 ⓘ

【格式】provider/model-id""",
    "category_temperature": """Temperature ⓘ

【推荐设置】
• visual (前端): 0.7
• business-logic (后端): 0.1
• documentation (文档): 0.3""",
    "category_description": """分类描述 ⓘ

【作用】说明该分类的用途和适用场景""",
    # Permission相关
    "permission_tool": """工具名称 ⓘ

【内置工具】Bash, Read, Write, Edit, Glob, Grep, WebFetch, WebSearch, Task

【MCP工具格式】mcp_servername_toolname""",
    "permission_level": """权限级别 ⓘ

【可选值】
• allow - 直接使用，无需确认
• ask - 每次使用前询问用户
• deny - 禁止使用

【安全建议】
• 危险操作 → ask 或 deny
• 只读操作 → allow""",
    "permission_bash_pattern": """Bash 命令模式 ⓘ

【支持通配符】
• * - 匹配所有命令
• git * - 匹配所有git命令
• git push - 匹配特定命令""",
    # MCP相关
    "mcp_name": """MCP 名称 ⓘ

【作用】MCP服务器的唯一标识符

【示例】context7, sentry, gh_grep, filesystem""",
    "mcp_type": """MCP 类型 ⓘ

【可选值】
• local - 本地进程，通过命令启动
• remote - 远程服务，通过URL连接""",
    "mcp_enabled": """启用状态 ⓘ

【作用】是否启用此MCP服务器

禁用后保留配置但不加载""",
    "mcp_command": """启动命令 (Local类型) ⓘ

【格式】JSON数组

【示例】
["npx", "-y", "@mcp/server"]
["bun", "x", "my-mcp"]
["python", "-m", "mcp_server"]""",
    "mcp_url": """服务器 URL (Remote类型) ⓘ

【格式】完整的HTTP/HTTPS URL

【示例】https://mcp.context7.com/mcp""",
    "mcp_headers": """请求头 (Remote类型) ⓘ

【格式】JSON对象

【示例】{"Authorization": "Bearer your-api-key"}""",
    "mcp_environment": """环境变量 (Local类型) ⓘ

【格式】JSON对象

【示例】{"API_KEY": "xxx", "DEBUG": "true"}""",
    "mcp_timeout": """超时时间 ⓘ

【单位】毫秒 (ms)
【默认值】5000 (5秒)""",
    "mcp_oauth": """OAuth 配置 ⓘ

【可选值】
• 留空 - 自动检测
• false - 禁用OAuth
• JSON对象 - 预注册凭证""",
    # Skill相关
    "skill_name": """Skill 名称 ⓘ

【格式要求】
• 1-64字符
• 小写字母、数字、连字符
• 不能以连字符开头或结尾

【示例】git-release, pr-review, code-format""",
    "skill_permission": """Skill 权限 ⓘ

【可选值】
• allow - 立即加载，无需确认
• deny - 隐藏并拒绝访问
• ask - 加载前询问用户""",
    "skill_pattern": """权限模式 ⓘ

【支持通配符】
• * - 匹配所有Skill
• internal-* - 匹配internal-开头的Skill""",
    "skill_description": """Skill 描述 ⓘ

【作用】描述Skill的功能，帮助Agent选择

【要求】1-1024字符，具体明确""",
    "skill_frontmatter": """SKILL.md Frontmatter ⓘ

【必填字段】
• name - Skill名称（必须与目录名一致）
• description - 功能描述

【可选字段】
• license - 许可证
• compatibility - 兼容性
• metadata - 自定义元数据""",
    # Instructions/Rules相关
    "instructions_path": """指令文件路径 ⓘ

【支持格式】
• 相对路径: CONTRIBUTING.md
• 绝对路径: /path/to/rules.md
• Glob模式: docs/*.md
• 远程URL: https://example.com/rules.md""",
    "rules_agents_md": """AGENTS.md 文件 ⓘ

【文件位置】
• 项目级: 项目根目录/AGENTS.md
• 全局级: ~/.config/opencode/AGENTS.md

【内容建议】
• 项目结构说明
• 代码规范要求
• 特殊约定说明

【创建方式】运行 /init 命令自动生成""",
    # Compaction相关
    "compaction_auto": """自动压缩 ⓘ

【作用】当上下文接近满时自动压缩会话

【建议】
• 长对话 → 启用
• 短对话 → 可以禁用

【默认值】true (启用)""",
    "compaction_prune": """修剪旧输出 ⓘ

【作用】删除旧的工具输出以节省tokens

【好处】
• 节省tokens
• 保持对话连续性
• 减少成本

【默认值】true (启用)""",
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


# ==================== 版本检查服务 ====================
class VersionCheckThread(QThread):
    """版本检查线程"""

    versionChecked = pyqtSignal(str, str)  # latest_version, release_url

    def run(self):
        try:
            req = urllib.request.Request(
                GITHUB_RELEASES_API, headers={"User-Agent": "OpenCode-Config-Manager"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                tag_name = data.get("tag_name", "")
                version_match = re.search(r"v?(\d+\.\d+\.\d+)", tag_name)
                if version_match:
                    latest_version = version_match.group(1)
                    release_url = data.get("html_url", GITHUB_URL + "/releases")
                    self.versionChecked.emit(latest_version, release_url)
        except Exception as e:
            print(f"Version check failed: {e}")


def compare_versions(current: str, latest: str) -> bool:
    """比较版本号，返回 True 如果有新版本"""
    try:
        current_parts = [int(x) for x in current.split(".")]
        latest_parts = [int(x) for x in latest.split(".")]
        return latest_parts > current_parts
    except:
        return False


# ==================== 基础页面类 ====================
class BasePage(ScrollArea):
    """所有页面的基类"""

    def __init__(self, title: str, subtitle: str, parent=None):
        super().__init__(parent)
        self.setObjectName(title.replace(" ", ""))
        self.setWidgetResizable(True)

        # 主容器
        self.scrollWidget = QWidget()
        self.setWidget(self.scrollWidget)

        # 主布局
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)
        self.vBoxLayout.setContentsMargins(36, 20, 36, 36)
        self.vBoxLayout.setSpacing(16)

        # 标题
        self.titleLabel = LargeTitleLabel(title, self.scrollWidget)
        self.subtitleLabel = CaptionLabel(subtitle, self.scrollWidget)

        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addWidget(self.subtitleLabel)
        self.vBoxLayout.addSpacing(16)

        # 设置样式
        self.setStyleSheet("""
            BasePage {
                background-color: transparent;
                border: none;
            }
        """)


# ==================== Provider 页面 ====================
class ProviderPage(BasePage):
    def __init__(self, parent=None):
        super().__init__("Provider 管理", "管理 API 提供商配置", parent)
        self.app = parent
        self.current_provider_name = None
        self.setup_ui()

    def setup_ui(self):
        splitter = QSplitter(Qt.Horizontal)
        self.vBoxLayout.addWidget(splitter, 1)

        left_card = CardWidget()
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(12)

        toolbar = QHBoxLayout()
        self.add_btn = PrimaryPushButton(FIF.ADD, "添加")
        self.add_btn.clicked.connect(self.add_provider)
        self.delete_btn = PushButton(FIF.DELETE, "删除")
        self.delete_btn.clicked.connect(self.delete_provider)
        toolbar.addWidget(self.add_btn)
        toolbar.addWidget(self.delete_btn)
        toolbar.addStretch()
        left_layout.addLayout(toolbar)

        self.provider_table = TableWidget()
        self.provider_table.setColumnCount(4)
        self.provider_table.setHorizontalHeaderLabels(
            ["名称", "显示名", "SDK", "模型数"]
        )
        self.provider_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.provider_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.provider_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.provider_table.itemSelectionChanged.connect(self.on_select)
        left_layout.addWidget(self.provider_table)
        splitter.addWidget(left_card)

        right_card = CardWidget()
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(12)

        detail_title = SubtitleLabel("Provider 详情")
        right_layout.addWidget(detail_title)

        form_layout = QGridLayout()
        form_layout.setSpacing(12)
        row = 0

        form_layout.addWidget(BodyLabel("名称:"), row, 0)
        self.name_edit = LineEdit()
        self.name_edit.setPlaceholderText("如: anthropic, openai")
        form_layout.addWidget(self.name_edit, row, 1)
        row += 1

        form_layout.addWidget(BodyLabel("显示名:"), row, 0)
        self.display_edit = LineEdit()
        self.display_edit.setPlaceholderText("如: Anthropic (Claude)")
        form_layout.addWidget(self.display_edit, row, 1)
        row += 1

        form_layout.addWidget(BodyLabel("SDK:"), row, 0)
        self.sdk_combo = ComboBox()
        self.sdk_combo.addItems(PRESET_SDKS)
        self.sdk_combo.currentTextChanged.connect(self.on_sdk_change)
        form_layout.addWidget(self.sdk_combo, row, 1)
        row += 1

        self.sdk_hint = CaptionLabel("")
        self.sdk_hint.setStyleSheet("color: #107C10;")
        form_layout.addWidget(self.sdk_hint, row, 0, 1, 2)
        row += 1

        form_layout.addWidget(BodyLabel("API 地址:"), row, 0)
        self.url_edit = LineEdit()
        self.url_edit.setPlaceholderText("留空使用默认地址")
        form_layout.addWidget(self.url_edit, row, 1)
        row += 1

        form_layout.addWidget(BodyLabel("API 密钥:"), row, 0)
        key_layout = QHBoxLayout()
        self.key_edit = PasswordLineEdit()
        self.key_edit.setPlaceholderText("支持环境变量")
        self.show_key_btn = ToolButton(FIF.VIEW)
        self.show_key_btn.setCheckable(True)
        self.show_key_btn.clicked.connect(self.toggle_key_visibility)
        key_layout.addWidget(self.key_edit)
        key_layout.addWidget(self.show_key_btn)
        form_layout.addLayout(key_layout, row, 1)

        right_layout.addLayout(form_layout)
        right_layout.addStretch()

        self.save_btn = PrimaryPushButton(FIF.SAVE, "保存修改")
        self.save_btn.clicked.connect(self.save_changes)
        right_layout.addWidget(self.save_btn)

        splitter.addWidget(right_card)
        splitter.setSizes([400, 500])

    def on_sdk_change(self, sdk):
        if sdk in SDK_MODEL_COMPATIBILITY:
            compatible = SDK_MODEL_COMPATIBILITY[sdk]
            self.sdk_hint.setText("适用于: " + ", ".join(compatible))
        else:
            self.sdk_hint.setText("")

    def toggle_key_visibility(self):
        if self.show_key_btn.isChecked():
            self.key_edit.setEchoMode(LineEdit.Normal)
        else:
            self.key_edit.setEchoMode(LineEdit.Password)

    def refresh_list(self):
        self.provider_table.setRowCount(0)
        if not self.app:
            return
        providers = self.app.opencode_config.get("provider", {})
        for name, data in providers.items():
            row = self.provider_table.rowCount()
            self.provider_table.insertRow(row)
            self.provider_table.setItem(row, 0, QTableWidgetItem(name))
            self.provider_table.setItem(row, 1, QTableWidgetItem(data.get("name", "")))
            self.provider_table.setItem(row, 2, QTableWidgetItem(data.get("npm", "")))
            self.provider_table.setItem(
                row, 3, QTableWidgetItem(str(len(data.get("models", {}))))
            )

    def on_select(self):
        rows = self.provider_table.selectedItems()
        if not rows:
            return
        row = rows[0].row()
        name = self.provider_table.item(row, 0).text()
        self.current_provider_name = name
        providers = self.app.opencode_config.get("provider", {})
        if name in providers:
            data = providers[name]
            self.name_edit.setText(name)
            self.display_edit.setText(data.get("name", ""))
            self.sdk_combo.setCurrentText(data.get("npm", ""))
            self.url_edit.setText(data.get("options", {}).get("baseURL", ""))
            self.key_edit.setText(data.get("options", {}).get("apiKey", ""))
            self.on_sdk_change(data.get("npm", ""))

    def add_provider(self):
        self.current_provider_name = None
        self.name_edit.clear()
        self.display_edit.clear()
        self.sdk_combo.setCurrentIndex(0)
        self.url_edit.clear()
        self.key_edit.clear()
        self.sdk_hint.clear()
        self.provider_table.clearSelection()

    def delete_provider(self):
        rows = self.provider_table.selectedItems()
        if not rows:
            return
        row = rows[0].row()
        name = self.provider_table.item(row, 0).text()
        w = MessageBox("确认删除", "删除 Provider [" + name + "] 及其所有模型?", self)
        if w.exec():
            del self.app.opencode_config["provider"][name]
            self.current_provider_name = None
            self.app.save_configs_silent()
            self.refresh_list()
            InfoBar.success("成功", "Provider [" + name + "] 已删除", parent=self)

    def save_changes(self):
        name = self.name_edit.text().strip()
        if not name:
            InfoBar.warning("提示", "名称不能为空", parent=self)
            return
        providers = self.app.opencode_config.setdefault("provider", {})
        if self.current_provider_name and self.current_provider_name != name:
            if self.current_provider_name in providers:
                old_models = providers[self.current_provider_name].get("models", {})
                del providers[self.current_provider_name]
                providers[name] = {"models": old_models}
        if name not in providers:
            providers[name] = {"models": {}}
        providers[name]["npm"] = self.sdk_combo.currentText()
        providers[name]["name"] = self.display_edit.text()
        providers[name]["options"] = {
            "baseURL": self.url_edit.text(),
            "apiKey": self.key_edit.text(),
        }
        self.current_provider_name = name
        if self.app.save_configs_silent():
            self.refresh_list()
            InfoBar.success("成功", "Provider 已保存", parent=self)


# ==================== 简化页面类 ====================
class SimplePage(BasePage):
    """简化的页面基类，用于快速创建页面"""

    def __init__(self, title: str, subtitle: str, parent=None):
        super().__init__(title, subtitle, parent)
        self.app = parent


class MCPPage(SimplePage):
    """MCP 服务器配置页面"""

    def __init__(self, parent=None):
        super().__init__("MCP 服务器", "管理 MCP 服务器配置", parent)
        self.current_mcp = None
        self.setup_ui()

    def setup_ui(self):
        info_label = BodyLabel("MCP 服务器配置功能 - 支持 Local 和 Remote 类型")
        self.vBoxLayout.addWidget(info_label)

        splitter = QSplitter(Qt.Horizontal)
        self.vBoxLayout.addWidget(splitter, 1)

        # 左侧列表
        left_card = CardWidget()
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(16, 16, 16, 16)

        toolbar = QHBoxLayout()
        self.add_btn = PrimaryPushButton(FIF.ADD, "添加")
        self.add_btn.clicked.connect(self.add_mcp)
        self.delete_btn = PushButton(FIF.DELETE, "删除")
        self.delete_btn.clicked.connect(self.delete_mcp)
        toolbar.addWidget(self.add_btn)
        toolbar.addWidget(self.delete_btn)
        toolbar.addStretch()
        left_layout.addLayout(toolbar)

        self.mcp_table = TableWidget()
        self.mcp_table.setColumnCount(3)
        self.mcp_table.setHorizontalHeaderLabels(["名称", "类型", "启用"])
        self.mcp_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.mcp_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.mcp_table.itemSelectionChanged.connect(self.on_select)
        left_layout.addWidget(self.mcp_table)
        splitter.addWidget(left_card)

        # 右侧详情
        right_card = CardWidget()
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(16, 16, 16, 16)

        form = QGridLayout()
        form.setSpacing(12)
        row = 0

        form.addWidget(BodyLabel("MCP 名称:"), row, 0)
        self.name_edit = LineEdit()
        form.addWidget(self.name_edit, row, 1)
        row += 1

        form.addWidget(BodyLabel("类型:"), row, 0)
        type_layout = QHBoxLayout()
        self.local_radio = RadioButton("Local")
        self.local_radio.setChecked(True)
        self.remote_radio = RadioButton("Remote")
        type_layout.addWidget(self.local_radio)
        type_layout.addWidget(self.remote_radio)
        type_layout.addStretch()
        form.addLayout(type_layout, row, 1)
        row += 1

        form.addWidget(BodyLabel("启用:"), row, 0)
        self.enabled_switch = SwitchButton()
        self.enabled_switch.setChecked(True)
        form.addWidget(self.enabled_switch, row, 1)
        row += 1

        form.addWidget(BodyLabel("命令/URL:"), row, 0)
        self.command_edit = LineEdit()
        self.command_edit.setPlaceholderText(
            '["npx", "-y", "@mcp/server"] 或 https://...'
        )
        form.addWidget(self.command_edit, row, 1)
        row += 1

        form.addWidget(BodyLabel("环境变量/请求头:"), row, 0)
        self.env_edit = LineEdit()
        self.env_edit.setPlaceholderText('{"KEY": "value"}')
        form.addWidget(self.env_edit, row, 1)
        row += 1

        form.addWidget(BodyLabel("超时 (ms):"), row, 0)
        self.timeout_spin = SpinBox()
        self.timeout_spin.setRange(1000, 300000)
        self.timeout_spin.setValue(5000)
        form.addWidget(self.timeout_spin, row, 1)

        right_layout.addLayout(form)
        right_layout.addStretch()

        self.save_btn = PrimaryPushButton(FIF.SAVE, "保存")
        self.save_btn.clicked.connect(self.save_mcp)
        right_layout.addWidget(self.save_btn)

        splitter.addWidget(right_card)

    def refresh_list(self):
        self.mcp_table.setRowCount(0)
        if not self.app:
            return
        mcps = self.app.opencode_config.get("mcp", {})
        for name, data in mcps.items():
            row = self.mcp_table.rowCount()
            self.mcp_table.insertRow(row)
            self.mcp_table.setItem(row, 0, QTableWidgetItem(name))
            self.mcp_table.setItem(row, 1, QTableWidgetItem(data.get("type", "local")))
            self.mcp_table.setItem(
                row, 2, QTableWidgetItem("是" if data.get("enabled", True) else "否")
            )

    def on_select(self):
        rows = self.mcp_table.selectedItems()
        if not rows:
            return
        row = rows[0].row()
        name = self.mcp_table.item(row, 0).text()
        self.current_mcp = name
        mcps = self.app.opencode_config.get("mcp", {})
        if name in mcps:
            data = mcps[name]
            self.name_edit.setText(name)
            is_remote = data.get("type") == "remote"
            self.remote_radio.setChecked(is_remote)
            self.local_radio.setChecked(not is_remote)
            self.enabled_switch.setChecked(data.get("enabled", True))
            if is_remote:
                self.command_edit.setText(data.get("url", ""))
                self.env_edit.setText(
                    json.dumps(data.get("headers", {}), ensure_ascii=False)
                )
            else:
                self.command_edit.setText(
                    json.dumps(data.get("command", []), ensure_ascii=False)
                )
                self.env_edit.setText(
                    json.dumps(data.get("environment", {}), ensure_ascii=False)
                )
            self.timeout_spin.setValue(data.get("timeout", 5000))

    def add_mcp(self):
        self.current_mcp = None
        self.name_edit.clear()
        self.local_radio.setChecked(True)
        self.enabled_switch.setChecked(True)
        self.command_edit.clear()
        self.env_edit.clear()
        self.timeout_spin.setValue(5000)
        self.mcp_table.clearSelection()

    def delete_mcp(self):
        rows = self.mcp_table.selectedItems()
        if not rows:
            return
        row = rows[0].row()
        name = self.mcp_table.item(row, 0).text()
        w = MessageBox("确认删除", f"删除 MCP [{name}]?", self)
        if w.exec():
            if name in self.app.opencode_config.get("mcp", {}):
                del self.app.opencode_config["mcp"][name]
                self.app.save_configs_silent()
                self.refresh_list()

    def save_mcp(self):
        name = self.name_edit.text().strip()
        if not name:
            InfoBar.warning("提示", "请输入 MCP 名称", parent=self)
            return

        is_remote = self.remote_radio.isChecked()
        data = {
            "type": "remote" if is_remote else "local",
            "enabled": self.enabled_switch.isChecked(),
        }

        timeout = self.timeout_spin.value()
        if timeout != 5000:
            data["timeout"] = timeout

        if is_remote:
            data["url"] = self.command_edit.text()
            try:
                headers = json.loads(self.env_edit.text() or "{}")
                if headers:
                    data["headers"] = headers
            except:
                pass
        else:
            try:
                data["command"] = json.loads(self.command_edit.text() or "[]")
            except:
                InfoBar.error("错误", "命令格式错误，需要JSON数组", parent=self)
                return
            try:
                env = json.loads(self.env_edit.text() or "{}")
                if env:
                    data["environment"] = env
            except:
                pass

        self.app.opencode_config.setdefault("mcp", {})[name] = data
        if self.current_mcp and self.current_mcp != name:
            del self.app.opencode_config["mcp"][self.current_mcp]
        self.current_mcp = name
        self.app.save_configs_silent()
        self.refresh_list()
        InfoBar.success("成功", f"MCP [{name}] 已保存", parent=self)


class PermissionPage(SimplePage):
    """权限管理页面"""

    def __init__(self, parent=None):
        super().__init__("权限管理", "配置工具使用权限", parent)
        self.setup_ui()

    def setup_ui(self):
        splitter = QSplitter(Qt.Horizontal)
        self.vBoxLayout.addWidget(splitter, 1)

        # 左侧列表
        left_card = CardWidget()
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(16, 16, 16, 16)

        toolbar = QHBoxLayout()
        self.add_btn = PrimaryPushButton(FIF.ADD, "添加")
        self.add_btn.clicked.connect(self.add_permission)
        self.delete_btn = PushButton(FIF.DELETE, "删除")
        self.delete_btn.clicked.connect(self.delete_permission)
        toolbar.addWidget(self.add_btn)
        toolbar.addWidget(self.delete_btn)
        toolbar.addStretch()
        left_layout.addLayout(toolbar)

        self.perm_table = TableWidget()
        self.perm_table.setColumnCount(2)
        self.perm_table.setHorizontalHeaderLabels(["工具名称", "权限"])
        self.perm_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.perm_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.perm_table.itemSelectionChanged.connect(self.on_select)
        left_layout.addWidget(self.perm_table)
        splitter.addWidget(left_card)

        # 右侧详情
        right_card = CardWidget()
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(16, 16, 16, 16)

        form = QGridLayout()
        form.setSpacing(12)
        row = 0

        form.addWidget(BodyLabel("工具名称:"), row, 0)
        self.tool_edit = LineEdit()
        form.addWidget(self.tool_edit, row, 1)
        row += 1

        form.addWidget(BodyLabel("权限:"), row, 0)
        perm_layout = QHBoxLayout()
        self.allow_radio = RadioButton("允许")
        self.ask_radio = RadioButton("询问")
        self.ask_radio.setChecked(True)
        self.deny_radio = RadioButton("拒绝")
        perm_layout.addWidget(self.allow_radio)
        perm_layout.addWidget(self.ask_radio)
        perm_layout.addWidget(self.deny_radio)
        perm_layout.addStretch()
        form.addLayout(perm_layout, row, 1)
        row += 1

        # 常用工具快捷按钮
        form.addWidget(BodyLabel("常用工具:"), row, 0)
        tools_layout = QHBoxLayout()
        for tool in ["Bash", "Read", "Write", "Edit", "Glob", "Grep"]:
            btn = PushButton(tool)
            btn.clicked.connect(lambda checked, t=tool: self.tool_edit.setText(t))
            tools_layout.addWidget(btn)
        tools_layout.addStretch()
        form.addLayout(tools_layout, row, 1)

        right_layout.addLayout(form)
        right_layout.addStretch()

        self.save_btn = PrimaryPushButton(FIF.SAVE, "保存")
        self.save_btn.clicked.connect(self.save_permission)
        right_layout.addWidget(self.save_btn)

        splitter.addWidget(right_card)

    def refresh_list(self):
        self.perm_table.setRowCount(0)
        if not self.app:
            return
        permissions = self.app.opencode_config.get("permission", {})
        for tool, perm in permissions.items():
            if isinstance(perm, str):
                row = self.perm_table.rowCount()
                self.perm_table.insertRow(row)
                self.perm_table.setItem(row, 0, QTableWidgetItem(tool))
                self.perm_table.setItem(row, 1, QTableWidgetItem(perm))

    def on_select(self):
        rows = self.perm_table.selectedItems()
        if not rows:
            return
        row = rows[0].row()
        tool = self.perm_table.item(row, 0).text()
        perm = self.perm_table.item(row, 1).text()
        self.tool_edit.setText(tool)
        if perm == "allow":
            self.allow_radio.setChecked(True)
        elif perm == "deny":
            self.deny_radio.setChecked(True)
        else:
            self.ask_radio.setChecked(True)

    def add_permission(self):
        self.tool_edit.clear()
        self.ask_radio.setChecked(True)
        self.perm_table.clearSelection()

    def delete_permission(self):
        rows = self.perm_table.selectedItems()
        if not rows:
            return
        row = rows[0].row()
        tool = self.perm_table.item(row, 0).text()
        w = MessageBox("确认删除", f"删除权限 [{tool}]?", self)
        if w.exec():
            if tool in self.app.opencode_config.get("permission", {}):
                del self.app.opencode_config["permission"][tool]
                self.app.save_configs_silent()
                self.refresh_list()

    def save_permission(self):
        tool = self.tool_edit.text().strip()
        if not tool:
            InfoBar.warning("提示", "工具名称不能为空", parent=self)
            return

        if self.allow_radio.isChecked():
            perm = "allow"
        elif self.deny_radio.isChecked():
            perm = "deny"
        else:
            perm = "ask"

        self.app.opencode_config.setdefault("permission", {})[tool] = perm
        self.app.save_configs_silent()
        self.refresh_list()
        InfoBar.success("成功", "权限已保存", parent=self)


class HelpPage(SimplePage):
    """帮助说明页面"""

    def __init__(self, parent=None):
        super().__init__("帮助说明", "配置优先级和使用说明", parent)
        self.setup_ui()

    def setup_ui(self):
        # 配置优先级卡片
        priority_card = HeaderCardWidget(self)
        priority_card.setTitle("配置优先级（从高到低）")
        priority_layout = QVBoxLayout()

        priorities = [
            "1. 远程配置 (Remote) - 通过 API 获取",
            "2. 全局配置 (Global) - ~/.config/opencode/opencode.json",
            "3. 自定义配置 (Custom) - --config 参数指定",
            "4. 项目配置 (Project) - <项目>/opencode.json",
            "5. .opencode 目录 - <项目>/.opencode/config.json",
            "6. 内联配置 (Inline) - 命令行参数",
        ]

        for p in priorities:
            priority_layout.addWidget(BodyLabel(p))

        priority_card.viewLayout.addLayout(priority_layout)
        self.vBoxLayout.addWidget(priority_card)

        # 关于卡片
        about_card = HeaderCardWidget(self)
        about_card.setTitle("关于")
        about_layout = QVBoxLayout()

        about_layout.addWidget(TitleLabel("OpenCode 配置管理器"))
        about_layout.addWidget(BodyLabel(f"版本: v{APP_VERSION}"))
        about_layout.addWidget(BodyLabel("基于 PyQt5 + QFluentWidgets"))
        about_layout.addWidget(BodyLabel(f"作者: {AUTHOR_NAME}"))

        github_btn = HyperlinkButton(GITHUB_URL, "访问 GitHub")
        about_layout.addWidget(github_btn)

        about_card.viewLayout.addLayout(about_layout)
        self.vBoxLayout.addWidget(about_card)

        self.vBoxLayout.addStretch()


# ==================== 主窗口 ====================
class MainWindow(FluentWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"OpenCode 配置管理器 v{APP_VERSION}")
        self.resize(1200, 750)
        self.setMinimumSize(1000, 600)

        # 配置数据
        self.opencode_config = {}
        self.ohmyopencode_config = {}
        self.backup_manager = BackupManager()

        # 初始化界面
        self.init_navigation()
        self.init_window()

        # 加载配置
        self.load_configs()

        # 版本检查
        self.version_thread = VersionCheckThread()
        self.version_thread.versionChecked.connect(self.on_version_checked)
        self.version_thread.start()

    def init_navigation(self):
        """初始化导航"""
        # 创建页面
        self.provider_page = ProviderPage(self)
        self.mcp_page = MCPPage(self)
        self.permission_page = PermissionPage(self)
        self.help_page = HelpPage(self)

        # 添加导航项
        self.addSubInterface(self.provider_page, FIF.PEOPLE, "Provider")
        self.addSubInterface(self.mcp_page, FIF.CONNECT, "MCP 服务器")
        self.addSubInterface(self.permission_page, FIF.CERTIFICATE, "权限管理")

        self.navigationInterface.addSeparator()

        self.addSubInterface(
            self.help_page, FIF.HELP, "帮助", NavigationItemPosition.BOTTOM
        )

        # 添加主题切换按钮
        self.navigationInterface.addWidget(
            "themeButton",
            NavigationToolButton(FIF.CONSTRACT),
            self.toggle_theme,
            NavigationItemPosition.BOTTOM,
        )

    def init_window(self):
        """初始化窗口"""
        # 设置默认深色主题
        setTheme(Theme.DARK)

        # 设置主题色
        setThemeColor("#0078D4")

    def toggle_theme(self):
        """切换主题"""
        if isDarkTheme():
            setTheme(Theme.LIGHT)
        else:
            setTheme(Theme.DARK)

    def load_configs(self):
        """加载配置"""
        opencode_path = ConfigPaths.get_opencode_config()
        ohmyopencode_path = ConfigPaths.get_ohmyopencode_config()

        self.opencode_config = ConfigManager.load_json(opencode_path) or {}
        self.ohmyopencode_config = ConfigManager.load_json(ohmyopencode_path) or {}

        self.refresh_all_pages()

    def refresh_all_pages(self):
        """刷新所有页面"""
        self.provider_page.refresh_list()
        self.mcp_page.refresh_list()
        self.permission_page.refresh_list()

    def save_configs_silent(self):
        """静默保存配置"""
        opencode_path = ConfigPaths.get_opencode_config()
        ohmyopencode_path = ConfigPaths.get_ohmyopencode_config()

        success = ConfigManager.save_json(opencode_path, self.opencode_config)
        success = success and ConfigManager.save_json(
            ohmyopencode_path, self.ohmyopencode_config
        )

        return success

    def on_version_checked(self, latest_version, release_url):
        """版本检查完成"""
        if compare_versions(APP_VERSION, latest_version):
            InfoBar.info(
                "发现新版本",
                f"v{latest_version} 可用，点击查看",
                duration=5000,
                parent=self,
            )


# ==================== 程序入口 ====================
if __name__ == "__main__":
    # 启用高DPI支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)

    # 设置应用信息
    app.setApplicationName("OpenCode Config Manager")
    app.setApplicationVersion(APP_VERSION)

    # 创建主窗口
    window = MainWindow()
    window.show()

    sys.exit(app.exec_())
