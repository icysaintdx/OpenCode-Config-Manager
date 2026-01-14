#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenCode & Oh My OpenCode 配置管理器 v0.7.0
一个可视化的GUI工具，用于管理OpenCode和Oh My OpenCode的配置文件

更新日志 v0.7.0:
- 集成 ttkbootstrap 现代化 UI 框架
- 支持 10 种内置主题（深色/浅色各 5 种）
- 实时主题切换，无需重启应用
- 工具栏按钮美化，使用 bootstyle 样式
- 移除手动颜色配置，使用框架原生主题系统

更新日志 v0.6.5:
- 实现实时主题切换（深色/浅色模式无需重启）
- 优化主题配色（采用现代 Fluent Design 风格）
- 重构 ThemeManager 支持动态刷新
- 优化 ttk 样式配置，增强视觉一致性

更新日志 v0.6.4:
- 优化深色/浅色主题配色方案
- 新增 hover/press 状态颜色配置
- 完善 setup_modern_styles 函数

更新日志 v0.6.3:
- 新增顶部工具栏 GitHub 链接和作者信息
- 新增版本同步检查功能（自动检测 GitHub 最新版本）
- 新增更新提示徽章（有新版本时显示）
- 美化界面：统一输入框、下拉菜单、标签页样式
- 新增 ModernCombobox、ModernCheckbutton 组件
- 优化 Treeview、Notebook 等控件的现代化样式

更新日志 v0.6.2:
- 新增 Skill 管理功能（权限配置 + 创建SKILL.md文件）
- 新增 Rules 管理功能（instructions配置 + 编辑AGENTS.md文件）
- 优化 Options Tab，添加 Claude/Gemini thinking 快捷按钮
- 扩展 TOOLTIPS 字典，添加详细的白话中文解释
- 侧边栏文件路径只显示文件名，tooltip显示完整路径
- 修复 Gemini 模型 thinking 配置位置（从variants移到options）

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
from tkinter import messagebox, scrolledtext
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
import json
from pathlib import Path
from datetime import datetime
import shutil
import webbrowser
import urllib.request
import urllib.error
import threading
import re


# ==================== 版本和项目信息 ====================
APP_VERSION = "0.7.0"
GITHUB_REPO = "icysaintdx/OpenCode-Config-Manager"
GITHUB_URL = f"https://github.com/{GITHUB_REPO}"
GITHUB_RELEASES_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
AUTHOR_NAME = "IcySaint"
AUTHOR_GITHUB = "https://github.com/icysaintdx"

# ==================== 主题配置 ====================
# 浅色主题 - 现代 Fluent Design 风格
LIGHT_THEME = {
    # 背景色系
    "bg": "#F5F5F5",  # 主背景 - 柔和浅灰
    "card_bg": "#FFFFFF",  # 卡片背景 - 纯白
    "sidebar_bg": "#FAFAFA",  # 侧边栏背景
    "border": "#E0E0E0",  # 边框色
    # 文字色系
    "text": "#1A1A1A",  # 主文字 - 深灰黑
    "text_secondary": "#666666",  # 次要文字
    "text_muted": "#999999",  # 弱化文字
    # 主题色系 - 微软 Fluent 蓝
    "primary": "#0078D4",  # 主色调
    "primary_hover": "#106EBE",  # 悬浮色
    "primary_light": "#E6F2FB",  # 浅色背景
    # 状态色系
    "success": "#107C10",  # 成功绿
    "success_light": "#DFF6DD",
    "warning": "#FFB900",  # 警告黄
    "warning_light": "#FFF4CE",
    "danger": "#D13438",  # 危险红
    "danger_light": "#FDE7E9",
    "accent": "#8764B8",  # 强调紫
    "accent_light": "#F3E8FF",
    "github": "#24292F",
    # 输入控件
    "input_bg": "#FFFFFF",
    "input_border": "#D1D1D1",
    "input_focus": "#0078D4",
    # 滚动条
    "scrollbar_bg": "#F0F0F0",
    "scrollbar_fg": "#C8C8C8",
    # 选中状态
    "tree_selected": "#E6F2FB",
    "tree_selected_fg": "#0078D4",
    # 控件悬浮/按下
    "hover": "#F0F0F0",
    "press": "#E5E5E5",
}

# 深色主题 - 现代 Fluent Design 风格
DARK_THEME = {
    # 背景色系 - 柔和深色，不刺眼
    "bg": "#1E1E1E",  # 主背景 - VS Code 同款深灰
    "card_bg": "#2D2D2D",  # 卡片背景 - 浅一级
    "sidebar_bg": "#252526",  # 侧边栏背景
    "border": "#3E3E3E",  # 边框色
    # 文字色系
    "text": "#FFFFFF",  # 主文字 - 纯白
    "text_secondary": "#B0B0B0",  # 次要文字
    "text_muted": "#808080",  # 弱化文字
    # 主题色系 - 微软 Fluent 蓝
    "primary": "#0078D4",  # 主色调
    "primary_hover": "#1A86D9",  # 悬浮色
    "primary_light": "#264F78",  # 深色背景下的浅色
    # 状态色系
    "success": "#4CAF50",  # 成功绿
    "success_light": "#1B3D1B",
    "warning": "#FFB900",  # 警告黄
    "warning_light": "#3D3000",
    "danger": "#F44336",  # 危险红
    "danger_light": "#4A1A1A",
    "accent": "#B388FF",  # 强调紫
    "accent_light": "#2D2052",
    "github": "#FFFFFF",
    # 输入控件
    "input_bg": "#3C3C3C",
    "input_border": "#4E4E4E",
    "input_focus": "#0078D4",
    # 滚动条
    "scrollbar_bg": "#2D2D2D",
    "scrollbar_fg": "#5A5A5A",
    # 选中状态
    "tree_selected": "#264F78",
    "tree_selected_fg": "#FFFFFF",
    # 控件悬浮/按下
    "hover": "#3E3E3E",
    "press": "#4A4A4A",
}

# 当前使用的颜色（默认浅色）
COLORS = LIGHT_THEME.copy()

# 当前主题模式: "light", "dark", "system"
CURRENT_THEME = "system"

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


# ==================== 主题管理 ====================
class ThemeManager:
    """主题管理器 - 支持浅色/深色/跟随系统，实时切换无需重启"""

    _instance = None
    _callbacks = []
    _root = None  # 主窗口引用
    _style = None  # ttk.Style 引用

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.current_mode = "system"  # "light", "dark", "system"
        self._apply_theme()  # 初始化时应用主题

    def set_root(self, root):
        """设置主窗口引用，用于实时刷新"""
        self._root = root
        self._style = ttk.Style(root)

    def _detect_system_theme(self):
        """检测系统主题（Windows）"""
        try:
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            )
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            return "light" if value == 1 else "dark"
        except:
            return "light"

    def get_effective_theme(self):
        """获取实际使用的主题"""
        if self.current_mode == "system":
            return self._detect_system_theme()
        return self.current_mode

    def set_theme(self, mode):
        """设置主题模式"""
        self.current_mode = mode
        self._apply_theme()
        self._refresh_styles()
        for callback in self._callbacks:
            try:
                callback()
            except Exception as e:
                print(f"主题回调执行失败: {e}")

    def toggle_theme(self):
        """切换主题"""
        effective = self.get_effective_theme()
        if effective == "light":
            self.set_theme("dark")
        else:
            self.set_theme("light")

    def _apply_theme(self):
        """应用主题到全局 COLORS"""
        global COLORS
        if self.get_effective_theme() == "dark":
            COLORS.update(DARK_THEME)
        else:
            COLORS.update(LIGHT_THEME)

    def _refresh_styles(self):
        """刷新所有 ttk 样式"""
        if self._style is None:
            return

        # 重新配置所有样式
        setup_modern_styles(self._style)

    def register_callback(self, callback):
        """注册主题变更回调"""
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def unregister_callback(self, callback):
        """取消注册主题变更回调"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def is_dark(self):
        """是否为深色主题"""
        return self.get_effective_theme() == "dark"


# ==================== 版本检查服务 ====================
class VersionChecker:
    """GitHub 版本检查服务"""

    def __init__(self, callback=None):
        self.callback = callback
        self.latest_version = None
        self.release_url = None
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
                # 提取版本号 (v0.6.3 -> 0.6.3)
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
    def compare_versions(current, latest):
        """比较版本号，返回 True 如果有新版本"""
        try:
            current_parts = [int(x) for x in current.split(".")]
            latest_parts = [int(x) for x in latest.split(".")]
            return latest_parts > current_parts
        except:
            return False


# ==================== 自定义控件 ====================
class ToolTip:
    """鼠标悬停提示框 - 支持深色主题"""

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

        # 根据主题选择颜色
        tm = ThemeManager.get_instance()
        if tm.is_dark():
            bg_color = "#2D333B"
            fg_color = "#E6EDF3"
            border_color = "#444C56"
        else:
            bg_color = "#FFFFD0"
            fg_color = "#333333"
            border_color = "#CCCC00"

        label = tk.Label(
            tw,
            text=self.text,
            justify=tk.LEFT,
            background=bg_color,
            foreground=fg_color,
            relief=tk.SOLID,
            borderwidth=1,
            font=FONTS["small"],
            padx=8,
            pady=4,
            wraplength=350,
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


class IconButton(tk.Canvas):
    """图标按钮（用于工具栏）"""

    def __init__(
        self,
        parent,
        icon_text,
        command=None,
        tooltip="",
        width=32,
        height=32,
        bg_color=None,
    ):
        self.bg_color = bg_color or COLORS["card_bg"]
        super().__init__(
            parent, width=width, height=height, highlightthickness=0, bg=self.bg_color
        )
        self.command = command
        self.icon_text = icon_text
        self.width = width
        self.height = height
        self.hover = False
        self.tooltip_text = tooltip

        self.draw()
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)

        if tooltip:
            ToolTip(self, tooltip)

    def draw(self):
        self.delete("all")
        if self.hover:
            # 绘制悬停背景
            self.create_oval(
                2, 2, self.width - 2, self.height - 2, fill=COLORS["border"], outline=""
            )
        self.create_text(
            self.width // 2,
            self.height // 2,
            text=self.icon_text,
            fill=COLORS["text"],
            font=("Segoe UI Emoji", 12),
        )

    def on_enter(self, e):
        self.hover = True
        self.draw()

    def on_leave(self, e):
        self.hover = False
        self.draw()

    def on_click(self, e):
        if self.command:
            self.command()


class GitHubButton(tk.Canvas):
    """GitHub 图标按钮"""

    def __init__(self, parent, command=None, tooltip="", width=28, height=28):
        super().__init__(
            parent,
            width=width,
            height=height,
            highlightthickness=0,
            bg=COLORS["card_bg"],
        )
        self.command = command
        self.width = width
        self.height = height
        self.hover = False

        self.draw()
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)

        if tooltip:
            ToolTip(self, tooltip)

    def draw(self):
        self.delete("all")
        # 绘制 GitHub 图标（简化版圆形）
        cx, cy = self.width // 2, self.height // 2
        r = min(self.width, self.height) // 2 - 2
        fill_color = COLORS["primary"] if self.hover else COLORS["github"]
        self.create_oval(cx - r, cy - r, cx + r, cy + r, fill=fill_color, outline="")
        # 绘制 GitHub 猫头图标（使用文字代替）
        self.create_text(
            cx, cy, text="⌘", fill="#FFFFFF", font=("Segoe UI Symbol", 10, "bold")
        )

    def on_enter(self, e):
        self.hover = True
        self.draw()
        self.config(cursor="hand2")

    def on_leave(self, e):
        self.hover = False
        self.draw()

    def on_click(self, e):
        if self.command:
            self.command()


class UpdateBadge(tk.Frame):
    """版本更新提示徽章"""

    def __init__(self, parent, version="", url=""):
        super().__init__(parent, bg=COLORS["card_bg"])
        self.version = version
        self.url = url
        self.visible = False

        self.badge = tk.Label(
            self,
            text=f"🔔 新版本 v{version}",
            font=("Microsoft YaHei UI", 9),
            bg=COLORS["success_light"],
            fg=COLORS["success"],
            padx=8,
            pady=2,
            cursor="hand2",
        )
        self.badge.bind("<Button-1>", self.on_click)
        ToolTip(self.badge, f"点击下载新版本 v{version}")

    def show(self, version, url):
        self.version = version
        self.url = url
        self.badge.config(text=f"🔔 新版本 v{version}")
        self.badge.pack()
        self.visible = True

    def hide(self):
        self.badge.pack_forget()
        self.visible = False

    def on_click(self, e):
        if self.url:
            webbrowser.open(self.url)


class Card(tk.Frame):
    """卡片容器 - 现代化设计"""

    def __init__(self, parent, title=None, **kwargs):
        super().__init__(parent, bg=COLORS["card_bg"], **kwargs)
        self.configure(highlightbackground=COLORS["border"], highlightthickness=1)
        if title:
            title_frame = tk.Frame(self, bg=COLORS["card_bg"])
            title_frame.pack(fill=tk.X, padx=16, pady=(16, 8))
            title_label = tk.Label(
                title_frame,
                text=title,
                font=FONTS["subtitle"],
                bg=COLORS["card_bg"],
                fg=COLORS["text"],
                anchor="w",
            )
            title_label.pack(side=tk.LEFT)
            sep = tk.Frame(self, height=1, bg=COLORS["border"])
            sep.pack(fill=tk.X, padx=16)
        self.content = tk.Frame(self, bg=COLORS["card_bg"])
        self.content.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)


class ModernEntry(tk.Frame):
    """现代风格输入框 - 带圆角效果和聚焦动画"""

    def __init__(
        self,
        parent,
        textvariable=None,
        width=30,
        show=None,
        placeholder="",
        bg_color=None,
    ):
        bg = bg_color or COLORS["card_bg"]
        super().__init__(parent, bg=bg)
        self.var = textvariable or tk.StringVar()
        self.placeholder = placeholder
        self.showing_placeholder = False
        self.bg_color = bg

        self.container = tk.Frame(
            self,
            bg=COLORS["input_bg"],
            highlightbackground=COLORS["input_border"],
            highlightthickness=1,
        )
        self.container.pack(fill=tk.X)

        self.entry = tk.Entry(
            self.container,
            textvariable=self.var,
            font=FONTS["body"],
            width=width,
            bd=0,
            bg=COLORS["input_bg"],
            fg=COLORS["text"],
            insertbackground=COLORS["primary"],
            selectbackground=COLORS["primary_light"],
            selectforeground=COLORS["text"],
        )
        if show:
            self.entry.config(show=show)
        self.entry.pack(padx=10, pady=8)

        self.entry.bind("<FocusIn>", self.on_focus_in)
        self.entry.bind("<FocusOut>", self.on_focus_out)

        # 显示占位符
        if placeholder and not self.var.get():
            self._show_placeholder()

    def _show_placeholder(self):
        if not self.var.get():
            self.entry.config(fg=COLORS["text_muted"])
            self.var.set(self.placeholder)
            self.showing_placeholder = True

    def _hide_placeholder(self):
        if self.showing_placeholder:
            self.var.set("")
            self.entry.config(fg=COLORS["text"])
            self.showing_placeholder = False

    def on_focus_in(self, e):
        self.container.config(
            highlightbackground=COLORS["input_focus"], highlightthickness=2
        )
        self._hide_placeholder()

    def on_focus_out(self, e):
        self.container.config(
            highlightbackground=COLORS["input_border"], highlightthickness=1
        )
        if self.placeholder and not self.var.get():
            self._show_placeholder()

    def get(self):
        if self.showing_placeholder:
            return ""
        return self.var.get()

    def set(self, value):
        self._hide_placeholder()
        self.var.set(value)


class ModernCombobox(tk.Frame):
    """现代风格下拉框"""

    def __init__(
        self,
        parent,
        values=None,
        textvariable=None,
        width=28,
        state="readonly",
        bg_color=None,
    ):
        bg = bg_color or COLORS["card_bg"]
        super().__init__(parent, bg=bg)
        self.var = textvariable or tk.StringVar()

        # 配置下拉框样式
        style = ttk.Style()
        style.configure(
            "Modern.TCombobox",
            fieldbackground=COLORS["input_bg"],
            background=COLORS["input_bg"],
            foreground=COLORS["text"],
            arrowcolor=COLORS["text_secondary"],
            borderwidth=1,
            relief="flat",
            padding=(8, 6),
        )
        style.map(
            "Modern.TCombobox",
            fieldbackground=[
                ("readonly", COLORS["input_bg"]),
                ("disabled", COLORS["sidebar_bg"]),
            ],
            foreground=[("disabled", COLORS["text_muted"])],
            bordercolor=[("focus", COLORS["input_focus"])],
        )

        self.combobox = ttk.Combobox(
            self,
            textvariable=self.var,
            values=values or [],
            width=width,
            state=state,
            style="Modern.TCombobox",
            font=FONTS["body"],
        )
        self.combobox.pack(fill=tk.X)

    def get(self):
        return self.var.get()

    def set(self, value):
        self.var.set(value)

    def config(self, **kwargs):
        if "values" in kwargs:
            self.combobox["values"] = kwargs.pop("values")
        if "state" in kwargs:
            self.combobox["state"] = kwargs.pop("state")
        if kwargs:
            self.combobox.config(**kwargs)

    def bind(self, event, handler):
        self.combobox.bind(event, handler)

    def current(self, index=None):
        if index is not None:
            self.combobox.current(index)
        else:
            return self.combobox.current()


class ModernCheckbutton(tk.Frame):
    """现代风格复选框"""

    def __init__(self, parent, text="", variable=None, command=None, bg_color=None):
        bg = bg_color or COLORS["card_bg"]
        super().__init__(parent, bg=bg)
        self.var = variable or tk.BooleanVar()

        self.check = tk.Checkbutton(
            self,
            text=text,
            variable=self.var,
            command=command,
            font=FONTS["body"],
            bg=bg,
            fg=COLORS["text"],
            activebackground=bg,
            activeforeground=COLORS["text"],
            selectcolor=COLORS["input_bg"],
            highlightthickness=0,
            bd=0,
        )
        self.check.pack(side=tk.LEFT)

    def get(self):
        return self.var.get()

    def set(self, value):
        self.var.set(value)


def setup_modern_styles(style=None):
    """配置全局现代化样式，支持动态刷新

    Args:
        style: ttk.Style 实例，如果为 None 则创建新实例
    """
    if style is None:
        style = ttk.Style()

    # 使用 clam 主题作为基础（更现代）
    try:
        style.theme_use("clam")
    except:
        pass

    # ========== 通用基础样式 ==========
    style.configure(
        ".",
        background=COLORS["bg"],
        foreground=COLORS["text"],
        bordercolor=COLORS["border"],
        darkcolor=COLORS["border"],
        lightcolor=COLORS["border"],
        troughcolor=COLORS["sidebar_bg"],
        selectbackground=COLORS["primary"],
        selectforeground="#FFFFFF",
        fieldbackground=COLORS["input_bg"],
        font=FONTS["body"],
    )

    # ========== Treeview 样式 ==========
    style.configure(
        "Modern.Treeview",
        background=COLORS["card_bg"],
        foreground=COLORS["text"],
        fieldbackground=COLORS["card_bg"],
        rowheight=32,
        font=FONTS["body"],
        borderwidth=0,
        relief="flat",
    )
    style.configure(
        "Modern.Treeview.Heading",
        font=("Microsoft YaHei UI", 9, "bold"),
        background=COLORS["sidebar_bg"],
        foreground=COLORS["text_secondary"],
        borderwidth=0,
        relief="flat",
        padding=(8, 6),
    )
    style.map(
        "Modern.Treeview",
        background=[("selected", COLORS["tree_selected"])],
        foreground=[("selected", COLORS["tree_selected_fg"])],
    )
    style.map(
        "Modern.Treeview.Heading",
        background=[("active", COLORS["border"])],
    )

    # ========== Notebook (标签页) 样式 ==========
    style.configure(
        "Modern.TNotebook",
        background=COLORS["bg"],
        borderwidth=0,
        tabmargins=[4, 4, 4, 0],
    )
    style.configure(
        "Modern.TNotebook.Tab",
        background=COLORS["sidebar_bg"],
        foreground=COLORS["text_secondary"],
        padding=[20, 10],
        font=("Microsoft YaHei UI", 10),
        borderwidth=0,
    )
    style.map(
        "Modern.TNotebook.Tab",
        background=[("selected", COLORS["card_bg"]), ("active", COLORS["hover"])],
        foreground=[("selected", COLORS["primary"]), ("active", COLORS["text"])],
        expand=[("selected", [0, 0, 0, 2])],
    )

    # ========== Scrollbar 样式 ==========
    style.configure(
        "Modern.Vertical.TScrollbar",
        background=COLORS["scrollbar_fg"],
        troughcolor=COLORS["scrollbar_bg"],
        borderwidth=0,
        arrowsize=0,
        width=8,
    )
    style.map(
        "Modern.Vertical.TScrollbar",
        background=[
            ("active", COLORS["text_secondary"]),
            ("pressed", COLORS["primary"]),
        ],
    )

    # ========== Combobox 样式 ==========
    style.configure(
        "Modern.TCombobox",
        fieldbackground=COLORS["input_bg"],
        background=COLORS["input_bg"],
        foreground=COLORS["text"],
        arrowcolor=COLORS["text_secondary"],
        borderwidth=1,
        relief="flat",
        padding=(10, 8),
        arrowsize=14,
    )
    style.map(
        "Modern.TCombobox",
        fieldbackground=[
            ("readonly", COLORS["input_bg"]),
            ("disabled", COLORS["sidebar_bg"]),
            ("focus", COLORS["input_bg"]),
        ],
        foreground=[("disabled", COLORS["text_muted"])],
        bordercolor=[("focus", COLORS["input_focus"])],
    )

    # ========== Entry 样式 ==========
    style.configure(
        "Modern.TEntry",
        fieldbackground=COLORS["input_bg"],
        foreground=COLORS["text"],
        borderwidth=1,
        relief="flat",
        padding=(10, 8),
    )
    style.map(
        "Modern.TEntry",
        fieldbackground=[
            ("focus", COLORS["input_bg"]),
            ("disabled", COLORS["sidebar_bg"]),
        ],
        bordercolor=[("focus", COLORS["input_focus"])],
    )

    # ========== Button 样式 ==========
    style.configure(
        "Modern.TButton",
        background=COLORS["primary"],
        foreground="#FFFFFF",
        borderwidth=0,
        padding=(16, 8),
        font=FONTS["body"],
    )
    style.map(
        "Modern.TButton",
        background=[
            ("active", COLORS["primary_hover"]),
            ("pressed", COLORS["primary_hover"]),
        ],
    )

    # Secondary Button 样式
    style.configure(
        "Secondary.TButton",
        background=COLORS["sidebar_bg"],
        foreground=COLORS["text"],
        borderwidth=1,
        padding=(16, 8),
        font=FONTS["body"],
    )
    style.map(
        "Secondary.TButton",
        background=[
            ("active", COLORS["hover"]),
            ("pressed", COLORS["press"]),
        ],
    )

    # ========== Checkbutton 样式 ==========
    style.configure(
        "Modern.TCheckbutton",
        background=COLORS["card_bg"],
        foreground=COLORS["text"],
        font=FONTS["body"],
        indicatorbackground=COLORS["input_bg"],
        indicatorforeground=COLORS["primary"],
    )
    style.map(
        "Modern.TCheckbutton",
        background=[("active", COLORS["card_bg"])],
        indicatorbackground=[("selected", COLORS["primary"])],
    )

    # ========== Radiobutton 样式 ==========
    style.configure(
        "Modern.TRadiobutton",
        background=COLORS["card_bg"],
        foreground=COLORS["text"],
        font=FONTS["body"],
        indicatorbackground=COLORS["input_bg"],
    )
    style.map(
        "Modern.TRadiobutton",
        background=[("active", COLORS["card_bg"])],
        indicatorbackground=[("selected", COLORS["primary"])],
    )

    # ========== LabelFrame 样式 ==========
    style.configure(
        "Modern.TLabelframe",
        background=COLORS["card_bg"],
        foreground=COLORS["text"],
        borderwidth=1,
        relief="flat",
    )
    style.configure(
        "Modern.TLabelframe.Label",
        background=COLORS["card_bg"],
        foreground=COLORS["text_secondary"],
        font=("Microsoft YaHei UI", 9, "bold"),
    )

    # ========== Frame 样式 ==========
    style.configure(
        "Card.TFrame",
        background=COLORS["card_bg"],
    )
    style.configure(
        "Sidebar.TFrame",
        background=COLORS["sidebar_bg"],
    )

    # ========== Label 样式 ==========
    style.configure(
        "TLabel",
        background=COLORS["bg"],
        foreground=COLORS["text"],
    )
    style.configure(
        "Card.TLabel",
        background=COLORS["card_bg"],
        foreground=COLORS["text"],
    )
    style.configure(
        "Title.TLabel",
        background=COLORS["bg"],
        foreground=COLORS["text"],
        font=FONTS["title"],
    )
    style.configure(
        "Subtitle.TLabel",
        background=COLORS["bg"],
        foreground=COLORS["text_secondary"],
        font=FONTS["subtitle"],
    )

    return style


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

        # 标题带tooltip
        title_frame = tk.Frame(form, bg=COLORS["card_bg"])
        title_frame.pack(anchor=tk.W, pady=(0, 8))
        lbl = create_label_with_tooltip(
            title_frame,
            "模型 Options 配置 ⓘ",
            TOOLTIPS.get("model_options", ""),
            font=FONTS["subtitle"],
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
        )
        lbl.pack(side=tk.LEFT)

        # Claude Thinking 快捷添加
        claude_frame = tk.Frame(form, bg=COLORS["card_bg"])
        claude_frame.pack(fill=tk.X, pady=(0, 8))
        lbl = create_label_with_tooltip(
            claude_frame,
            "Claude Thinking ⓘ",
            TOOLTIPS.get("option_thinking_type", ""),
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["accent"],
        )
        lbl.pack(side=tk.LEFT)
        tk.Button(
            claude_frame,
            text="thinking.type=enabled",
            font=FONTS["small"],
            bd=0,
            bg=COLORS["accent"],
            fg="#FFFFFF",
            command=lambda: self.add_thinking_config("type", "enabled"),
            cursor="hand2",
        ).pack(side=tk.LEFT, padx=(8, 2))
        tk.Button(
            claude_frame,
            text="budgetTokens=16000",
            font=FONTS["small"],
            bd=0,
            bg=COLORS["accent"],
            fg="#FFFFFF",
            command=lambda: self.add_thinking_config("budgetTokens", 16000),
            cursor="hand2",
        ).pack(side=tk.LEFT, padx=2)
        tk.Button(
            claude_frame,
            text="一键添加Thinking",
            font=FONTS["small"],
            bd=0,
            bg=COLORS["success"],
            fg="#FFFFFF",
            command=self.add_full_thinking_config,
            cursor="hand2",
        ).pack(side=tk.LEFT, padx=(8, 0))

        # OpenAI 快捷添加
        openai_frame = tk.Frame(form, bg=COLORS["card_bg"])
        openai_frame.pack(fill=tk.X, pady=(0, 8))
        lbl = create_label_with_tooltip(
            openai_frame,
            "OpenAI 推理 ⓘ",
            TOOLTIPS.get("option_reasoningEffort", ""),
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["primary"],
        )
        lbl.pack(side=tk.LEFT)
        presets = [
            ("reasoningEffort", "high"),
            ("textVerbosity", "low"),
            ("reasoningSummary", "auto"),
        ]
        for key, val in presets:
            btn = tk.Button(
                openai_frame,
                text=f"{key}={val}",
                font=FONTS["small"],
                bd=0,
                bg=COLORS["sidebar_bg"],
                fg=COLORS["text"],
                command=lambda k=key, v=val: self.add_option_preset(k, v),
                cursor="hand2",
            )
            btn.pack(side=tk.LEFT, padx=2)

        # Gemini Thinking 快捷添加
        gemini_frame = tk.Frame(form, bg=COLORS["card_bg"])
        gemini_frame.pack(fill=tk.X, pady=(0, 8))
        lbl = create_label_with_tooltip(
            gemini_frame,
            "Gemini Thinking ⓘ",
            TOOLTIPS.get("option_thinking_budget", ""),
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["success"],
        )
        lbl.pack(side=tk.LEFT)
        tk.Button(
            gemini_frame,
            text="thinkingBudget=8000",
            font=FONTS["small"],
            bd=0,
            bg=COLORS["success"],
            fg="#FFFFFF",
            command=lambda: self.add_gemini_thinking_config(8000),
            cursor="hand2",
        ).pack(side=tk.LEFT, padx=(8, 2))
        tk.Button(
            gemini_frame,
            text="thinkingBudget=16000",
            font=FONTS["small"],
            bd=0,
            bg=COLORS["success"],
            fg="#FFFFFF",
            command=lambda: self.add_gemini_thinking_config(16000),
            cursor="hand2",
        ).pack(side=tk.LEFT, padx=2)

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

    def add_thinking_config(self, param, value):
        """添加Claude thinking配置参数"""
        options = self.current_model_data.setdefault("options", {})
        thinking = options.setdefault("thinking", {})
        thinking[param] = value
        self.refresh_options_tree()

    def add_full_thinking_config(self):
        """一键添加完整的Claude thinking配置"""
        options = self.current_model_data.setdefault("options", {})
        options["thinking"] = {"type": "enabled", "budgetTokens": 16000}
        self.refresh_options_tree()
        messagebox.showinfo(
            "成功",
            "已添加 Claude Thinking 配置:\nthinking.type = enabled\nthinking.budgetTokens = 16000",
        )

    def add_gemini_thinking_config(self, budget):
        """添加Gemini thinking配置"""
        options = self.current_model_data.setdefault("options", {})
        options["thinkingConfig"] = {"thinkingBudget": budget}
        self.refresh_options_tree()

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


# ==================== Skill 管理选项卡 ====================
class SkillTab(tk.Frame):
    """Skill权限管理和SKILL.md文件创建"""

    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        self.setup_ui()

    def setup_ui(self):
        main_frame = tk.Frame(self, bg=COLORS["bg"])
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 左侧：Skill权限配置
        left_frame = Card(main_frame, title="Skill 权限配置")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        # 说明
        desc_frame = tk.Frame(left_frame.content, bg=COLORS["card_bg"])
        desc_frame.pack(fill=tk.X, pady=(0, 12))
        tk.Label(
            desc_frame,
            text="配置Skill的加载权限。Skill是可复用的指令文件，Agent可按需加载。",
            font=FONTS["body"],
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
            wraplength=350,
            justify=tk.LEFT,
        ).pack(anchor=tk.W)

        # 权限列表
        btn_frame = tk.Frame(left_frame.content, bg=COLORS["card_bg"])
        btn_frame.pack(fill=tk.X, pady=(0, 8))
        ModernButton(
            btn_frame, "添加权限", self.add_permission, "primary", 90, 32
        ).pack(side=tk.LEFT, padx=(0, 8))
        ModernButton(btn_frame, "删除", self.delete_permission, "danger", 70, 32).pack(
            side=tk.LEFT
        )

        columns = ("pattern", "permission")
        self.tree = ttk.Treeview(
            left_frame.content,
            columns=columns,
            show="headings",
            height=8,
            style="Modern.Treeview",
        )
        self.tree.heading("pattern", text="模式")
        self.tree.heading("permission", text="权限")
        self.tree.column("pattern", width=150)
        self.tree.column("permission", width=80)
        scrollbar = ttk.Scrollbar(
            left_frame.content, orient=tk.VERTICAL, command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        # 编辑区域
        edit_frame = tk.Frame(left_frame.content, bg=COLORS["card_bg"])
        edit_frame.pack(fill=tk.X, pady=(12, 0))

        row = 0
        create_label_with_tooltip(
            edit_frame, "模式 ⓘ", TOOLTIPS.get("skill_pattern", "")
        ).grid(row=row, column=0, sticky=tk.W, pady=(0, 4))
        row += 1
        self.pattern_var = tk.StringVar(value="*")
        ModernEntry(edit_frame, textvariable=self.pattern_var, width=20).grid(
            row=row, column=0, sticky=tk.W, pady=(0, 8)
        )

        row += 1
        create_label_with_tooltip(
            edit_frame, "权限 ⓘ", TOOLTIPS.get("skill_permission", "")
        ).grid(row=row, column=0, sticky=tk.W, pady=(0, 4))
        row += 1
        self.perm_var = tk.StringVar(value="ask")
        perm_frame = tk.Frame(edit_frame, bg=COLORS["card_bg"])
        perm_frame.grid(row=row, column=0, sticky=tk.W, pady=(0, 8))
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
            ).pack(side=tk.LEFT, padx=(0, 12))

        row += 1
        ModernButton(
            edit_frame, "保存权限", self.save_permission, "success", 90, 32
        ).grid(row=row, column=0, sticky=tk.W, pady=(8, 0))

        # 右侧：创建SKILL.md
        right_frame = Card(main_frame, title="创建 SKILL.md")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0))

        form = tk.Frame(right_frame.content, bg=COLORS["card_bg"])
        form.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Skill名称
        create_label_with_tooltip(
            form, "Skill 名称 ⓘ", TOOLTIPS.get("skill_name", "")
        ).pack(anchor=tk.W)
        self.skill_name_var = tk.StringVar()
        ModernEntry(form, textvariable=self.skill_name_var, width=30).pack(
            anchor=tk.W, pady=(4, 8)
        )

        # Skill描述
        create_label_with_tooltip(
            form, "描述 ⓘ", TOOLTIPS.get("skill_description", "")
        ).pack(anchor=tk.W)
        self.skill_desc_var = tk.StringVar()
        ModernEntry(form, textvariable=self.skill_desc_var, width=40).pack(
            anchor=tk.W, pady=(4, 8)
        )

        # Skill内容
        tk.Label(
            form,
            text="Skill 内容（Markdown格式）",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        ).pack(anchor=tk.W)
        self.skill_content_text = scrolledtext.ScrolledText(
            form, height=10, width=45, font=FONTS["mono"], bd=1, relief=tk.SOLID
        )
        self.skill_content_text.pack(fill=tk.BOTH, expand=True, pady=(4, 8))
        self.skill_content_text.insert(
            "1.0",
            """## What I do
- 描述这个Skill的功能

## When to use me
- 描述何时使用这个Skill

## Instructions
- 具体的指令内容
""",
        )

        # 位置选择
        loc_frame = tk.Frame(form, bg=COLORS["card_bg"])
        loc_frame.pack(fill=tk.X, pady=(0, 8))
        tk.Label(
            loc_frame,
            text="保存位置:",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        ).pack(side=tk.LEFT)
        self.skill_location_var = tk.StringVar(value="global")
        tk.Radiobutton(
            loc_frame,
            text="全局 (~/.config/opencode/skill/)",
            variable=self.skill_location_var,
            value="global",
            bg=COLORS["card_bg"],
        ).pack(side=tk.LEFT, padx=(8, 0))
        tk.Radiobutton(
            loc_frame,
            text="项目 (.opencode/skill/)",
            variable=self.skill_location_var,
            value="project",
            bg=COLORS["card_bg"],
        ).pack(side=tk.LEFT, padx=(8, 0))

        # 按钮
        btn_frame2 = tk.Frame(form, bg=COLORS["card_bg"])
        btn_frame2.pack(fill=tk.X)
        ModernButton(
            btn_frame2, "创建 SKILL.md", self.create_skill, "success", 120, 36
        ).pack(side=tk.LEFT, padx=(0, 8))
        ModernButton(btn_frame2, "预览", self.preview_skill, "secondary", 70, 36).pack(
            side=tk.LEFT
        )

    def refresh_list(self):
        """刷新权限列表"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        permissions = self.app.opencode_config.get("permission", {}).get("skill", {})
        # 确保 permissions 是字典类型
        if isinstance(permissions, dict):
            for pattern, perm in permissions.items():
                self.tree.insert("", tk.END, values=(pattern, perm))
        elif isinstance(permissions, str):
            # 如果是字符串，显示为单条记录
            self.tree.insert("", tk.END, values=("*", permissions))

    def on_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        self.pattern_var.set(item["values"][0])
        self.perm_var.set(item["values"][1])

    def add_permission(self):
        self.pattern_var.set("")
        self.perm_var.set("ask")

    def delete_permission(self):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        pattern = item["values"][0]
        if messagebox.askyesno("确认", f"删除 Skill 权限 [{pattern}]?"):
            skill_perms = self.app.opencode_config.get("permission", {}).get(
                "skill", {}
            )
            if pattern in skill_perms:
                del skill_perms[pattern]
                self.app.save_configs_silent()
                self.refresh_list()

    def save_permission(self):
        pattern = self.pattern_var.get().strip()
        if not pattern:
            messagebox.showwarning("提示", "请输入模式")
            return
        perm = self.app.opencode_config.setdefault("permission", {})
        skill_perm = perm.setdefault("skill", {})
        skill_perm[pattern] = self.perm_var.get()
        self.app.save_configs_silent()
        self.refresh_list()
        messagebox.showinfo("成功", f"Skill 权限 [{pattern}] 已保存")

    def preview_skill(self):
        """预览SKILL.md内容"""
        name = self.skill_name_var.get().strip()
        desc = self.skill_desc_var.get().strip()
        content = self.skill_content_text.get("1.0", tk.END).strip()

        if not name or not desc:
            messagebox.showwarning("提示", "请填写Skill名称和描述")
            return

        preview = f"""---
name: {name}
description: {desc}
---

{content}
"""
        # 显示预览窗口
        preview_win = tk.Toplevel(self)
        preview_win.title(f"预览: {name}/SKILL.md")
        preview_win.geometry("500x400")
        text = scrolledtext.ScrolledText(preview_win, font=FONTS["mono"])
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text.insert("1.0", preview)
        text.config(state=tk.DISABLED)

    def create_skill(self):
        """创建SKILL.md文件"""
        name = self.skill_name_var.get().strip()
        desc = self.skill_desc_var.get().strip()
        content = self.skill_content_text.get("1.0", tk.END).strip()

        if not name:
            messagebox.showwarning("提示", "请输入Skill名称")
            return
        if not desc:
            messagebox.showwarning("提示", "请输入Skill描述")
            return

        # 验证名称格式
        import re

        if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", name):
            messagebox.showerror(
                "错误",
                "Skill名称格式错误！\n要求：小写字母、数字、连字符，不能以连字符开头或结尾",
            )
            return

        # 确定保存路径
        if self.skill_location_var.get() == "global":
            base_path = Path.home() / ".config" / "opencode" / "skill"
        else:
            base_path = Path.cwd() / ".opencode" / "skill"

        skill_dir = base_path / name
        skill_file = skill_dir / "SKILL.md"

        # 创建目录和文件
        try:
            skill_dir.mkdir(parents=True, exist_ok=True)
            skill_content = f"""---
name: {name}
description: {desc}
---

{content}
"""
            with open(skill_file, "w", encoding="utf-8") as f:
                f.write(skill_content)

            messagebox.showinfo("成功", f"Skill 已创建:\n{skill_file}")
        except Exception as e:
            messagebox.showerror("错误", f"创建失败: {e}")


# ==================== Rules/Instructions 管理选项卡 ====================
class RulesTab(tk.Frame):
    """Rules/Instructions管理和AGENTS.md文件编辑"""

    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        self.setup_ui()

    def setup_ui(self):
        main_frame = tk.Frame(self, bg=COLORS["bg"])
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 左侧：Instructions配置
        left_frame = Card(main_frame, title="Instructions 配置")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        # 说明
        desc_frame = tk.Frame(left_frame.content, bg=COLORS["card_bg"])
        desc_frame.pack(fill=tk.X, pady=(0, 12))
        tk.Label(
            desc_frame,
            text="配置额外的指令文件，这些文件会与AGENTS.md合并加载。",
            font=FONTS["body"],
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
            wraplength=350,
            justify=tk.LEFT,
        ).pack(anchor=tk.W)

        # Instructions列表
        btn_frame = tk.Frame(left_frame.content, bg=COLORS["card_bg"])
        btn_frame.pack(fill=tk.X, pady=(0, 8))
        ModernButton(btn_frame, "添加", self.add_instruction, "primary", 70, 32).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ModernButton(btn_frame, "删除", self.delete_instruction, "danger", 70, 32).pack(
            side=tk.LEFT
        )

        self.instructions_listbox = tk.Listbox(
            left_frame.content,
            height=8,
            font=FONTS["body"],
            bd=1,
            relief=tk.SOLID,
            selectmode=tk.SINGLE,
        )
        self.instructions_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        # 添加输入框
        add_frame = tk.Frame(left_frame.content, bg=COLORS["card_bg"])
        add_frame.pack(fill=tk.X, pady=(0, 8))
        create_label_with_tooltip(
            add_frame, "文件路径 ⓘ", TOOLTIPS.get("instructions_path", "")
        ).pack(anchor=tk.W)
        self.instruction_path_var = tk.StringVar()
        ModernEntry(add_frame, textvariable=self.instruction_path_var, width=35).pack(
            anchor=tk.W, pady=(4, 0)
        )

        # 常用路径快捷按钮
        quick_frame = tk.Frame(left_frame.content, bg=COLORS["card_bg"])
        quick_frame.pack(fill=tk.X, pady=(0, 8))
        tk.Label(
            quick_frame,
            text="快捷:",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        ).pack(side=tk.LEFT)
        for path in ["CONTRIBUTING.md", "docs/*.md", ".cursor/rules/*.md"]:
            tk.Button(
                quick_frame,
                text=path,
                font=FONTS["small"],
                bd=0,
                bg=COLORS["sidebar_bg"],
                fg=COLORS["text"],
                command=lambda p=path: self.instruction_path_var.set(p),
                cursor="hand2",
            ).pack(side=tk.LEFT, padx=2)

        ModernButton(
            left_frame.content, "保存配置", self.save_instructions, "success", 90, 32
        ).pack(anchor=tk.W)

        # 右侧：AGENTS.md编辑
        right_frame = Card(main_frame, title="AGENTS.md 编辑")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0))

        form = tk.Frame(right_frame.content, bg=COLORS["card_bg"])
        form.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 位置选择
        loc_frame = tk.Frame(form, bg=COLORS["card_bg"])
        loc_frame.pack(fill=tk.X, pady=(0, 8))
        tk.Label(
            loc_frame,
            text="编辑位置:",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        ).pack(side=tk.LEFT)
        self.agents_location_var = tk.StringVar(value="global")
        tk.Radiobutton(
            loc_frame,
            text="全局",
            variable=self.agents_location_var,
            value="global",
            bg=COLORS["card_bg"],
            command=self.load_agents_md,
        ).pack(side=tk.LEFT, padx=(8, 0))
        tk.Radiobutton(
            loc_frame,
            text="项目",
            variable=self.agents_location_var,
            value="project",
            bg=COLORS["card_bg"],
            command=self.load_agents_md,
        ).pack(side=tk.LEFT, padx=(8, 0))

        # 路径显示
        self.agents_path_label = tk.Label(
            form,
            text="",
            font=FONTS["small"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
        )
        self.agents_path_label.pack(anchor=tk.W, pady=(0, 8))

        # 编辑器
        self.agents_text = scrolledtext.ScrolledText(
            form, height=15, width=45, font=FONTS["mono"], bd=1, relief=tk.SOLID
        )
        self.agents_text.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        # 按钮
        btn_frame2 = tk.Frame(form, bg=COLORS["card_bg"])
        btn_frame2.pack(fill=tk.X)
        ModernButton(
            btn_frame2, "保存 AGENTS.md", self.save_agents_md, "success", 130, 36
        ).pack(side=tk.LEFT, padx=(0, 8))
        ModernButton(
            btn_frame2, "重新加载", self.load_agents_md, "secondary", 90, 36
        ).pack(side=tk.LEFT, padx=(0, 8))
        ModernButton(
            btn_frame2, "使用模板", self.use_template, "secondary", 90, 36
        ).pack(side=tk.LEFT)

        # 初始加载
        self.load_agents_md()

    def refresh_list(self):
        """刷新Instructions列表"""
        self.instructions_listbox.delete(0, tk.END)
        instructions = self.app.opencode_config.get("instructions", [])
        for path in instructions:
            self.instructions_listbox.insert(tk.END, path)

    def add_instruction(self):
        path = self.instruction_path_var.get().strip()
        if not path:
            messagebox.showwarning("提示", "请输入文件路径")
            return
        instructions = self.app.opencode_config.setdefault("instructions", [])
        if path not in instructions:
            instructions.append(path)
            self.refresh_list()
            self.instruction_path_var.set("")

    def delete_instruction(self):
        selection = self.instructions_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        instructions = self.app.opencode_config.get("instructions", [])
        if idx < len(instructions):
            del instructions[idx]
            self.refresh_list()

    def save_instructions(self):
        self.app.save_configs_silent()
        messagebox.showinfo("成功", "Instructions 配置已保存")

    def get_agents_path(self):
        """获取AGENTS.md路径"""
        if self.agents_location_var.get() == "global":
            return Path.home() / ".config" / "opencode" / "AGENTS.md"
        else:
            return Path.cwd() / "AGENTS.md"

    def load_agents_md(self):
        """加载AGENTS.md内容"""
        path = self.get_agents_path()
        self.agents_path_label.config(text=f"路径: {path}")

        self.agents_text.delete("1.0", tk.END)
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.agents_text.insert("1.0", content)
            except Exception as e:
                self.agents_text.insert("1.0", f"# 读取失败: {e}")
        else:
            self.agents_text.insert(
                "1.0", '# AGENTS.md 文件不存在\n# 点击"使用模板"创建新文件'
            )

    def save_agents_md(self):
        """保存AGENTS.md"""
        path = self.get_agents_path()
        content = self.agents_text.get("1.0", tk.END).strip()

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("成功", f"AGENTS.md 已保存:\n{path}")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {e}")

    def use_template(self):
        """使用模板"""
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

## External File Loading
When you encounter a file reference (e.g., @rules/general.md), use your Read tool to load it.
"""
        self.agents_text.delete("1.0", tk.END)
        self.agents_text.insert("1.0", template)


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
        notebook = ttk.Notebook(self, style="Modern.TNotebook")
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

        # Oh My OpenCode 说明 (新增)
        omo_frame = tk.Frame(notebook, bg=COLORS["card_bg"])
        notebook.add(omo_frame, text="  Oh My OpenCode  ")
        omo_card = Card(omo_frame)
        omo_card.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 使用滚动文本框
        omo_text = scrolledtext.ScrolledText(
            omo_card.content,
            wrap=tk.WORD,
            font=FONTS["body"],
            bd=0,
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
        )
        omo_text.pack(fill=tk.BOTH, expand=True)
        omo_content = """Oh My OpenCode 核心功能说明

═══════════════════════════════════════════════════════════════
🪄 魔法关键词: ultrawork (ulw)
═══════════════════════════════════════════════════════════════

只需在提示词中包含 "ultrawork" 或 "ulw"，即可激活所有高级功能：
• 并行 Agent 编排
• 后台任务执行
• 深度探索模式
• 持续执行直到完成

示例: "ulw 帮我重构这个模块" → Agent 自动分析、并行搜索、持续工作

═══════════════════════════════════════════════════════════════
🤖 内置 Agent 团队
═══════════════════════════════════════════════════════════════

• Sisyphus (主Agent): Claude Opus 4.5 - 任务编排和执行
• Oracle: GPT 5.2 - 架构设计、代码审查、策略规划
• Librarian: 文档查找、开源实现搜索、代码库分析
• Explore: 快速代码库探索和模式匹配
• Frontend UI/UX Engineer: Gemini 3 Pro - 前端开发
• Document Writer: 技术文档写作
• Multimodal Looker: 视觉内容分析（PDF、图片等）

═══════════════════════════════════════════════════════════════
🔧 LSP 工具集 (代码智能)
═══════════════════════════════════════════════════════════════

• lsp_hover: 获取符号的类型信息、文档、签名
• lsp_goto_definition: 跳转到符号定义位置
• lsp_find_references: 查找工作区中的所有引用
• lsp_document_symbols: 获取文件符号大纲
• lsp_workspace_symbols: 按名称搜索项目中的符号
• lsp_diagnostics: 构建前获取错误/警告
• lsp_servers: 列出可用的 LSP 服务器
• lsp_prepare_rename: 验证重命名操作
• lsp_rename: 跨工作区重命名符号
• lsp_code_actions: 获取可用的快速修复/重构
• lsp_code_action_resolve: 应用代码操作

═══════════════════════════════════════════════════════════════
🔍 AST 工具 (语法树搜索)
═══════════════════════════════════════════════════════════════

• ast_grep_search: AST 感知的代码模式搜索（支持 25 种语言）
• ast_grep_replace: AST 感知的代码替换

═══════════════════════════════════════════════════════════════
📚 会话管理工具
═══════════════════════════════════════════════════════════════

• session_list: 列出所有 OpenCode 会话（支持日期过滤）
• session_read: 读取特定会话的消息和历史
• session_search: 跨会话消息全文搜索
• session_info: 获取会话的元数据和统计信息

═══════════════════════════════════════════════════════════════
📁 配置加载器 (Claude Code 兼容)
═══════════════════════════════════════════════════════════════

【命令加载器】从以下目录加载 Markdown 斜杠命令:
• ~/.claude/commands/ (用户级)
• ./.claude/commands/ (项目级)
• ~/.config/opencode/command/ (OpenCode 全局)
• ./.opencode/command/ (OpenCode 项目)

【Skill 加载器】加载基于目录的 Skill (含 SKILL.md):
• ~/.claude/skills/ (用户级)
• ./.claude/skills/ (项目级)

【Agent 加载器】从 Markdown 文件加载自定义 Agent:
• ~/.claude/agents/*.md (用户级)
• ./.claude/agents/*.md (项目级)

【MCP 加载器】从 .mcp.json 加载 MCP 服务器配置:
• ~/.claude/.mcp.json (用户级)
• ./.mcp.json (项目级)
• ./.claude/.mcp.json (本地)
• 支持环境变量扩展 (${VAR} 语法)

═══════════════════════════════════════════════════════════════
⚙️ 兼容性开关
═══════════════════════════════════════════════════════════════

在 oh-my-opencode.json 中配置 claude_code 对象可禁用特定功能:

{
  "claude_code": {
    "mcp": false,      // 禁用 Claude Code MCP 加载
    "commands": false, // 禁用 Claude Code 命令加载
    "skills": false,   // 禁用 Claude Code Skill 加载
    "agents": false,   // 禁用 Claude Code Agent 加载
    "hooks": false,    // 禁用 Claude Code Hooks
    "plugins": false   // 禁用 Claude Code 插件
  }
}

注意: 这些开关仅影响 Claude Code 兼容层，不影响 OpenCode 原生功能

═══════════════════════════════════════════════════════════════
🎯 其他核心功能
═══════════════════════════════════════════════════════════════

• Todo 持续执行器: 强制 Agent 完成所有 TODO 才能停止
• 注释检查器: 防止 AI 添加过多注释，保持代码整洁
• 思考模式: 自动检测需要深度思考的场景并切换模式
• 上下文窗口监控: 70%+ 使用率时提醒 Agent 合理利用空间
• 自动压缩: Claude 模型达到 token 限制时自动压缩会话
• 会话恢复: 自动从会话错误中恢复
• 后台通知: 后台 Agent 任务完成时发送通知

═══════════════════════════════════════════════════════════════
📖 更多信息
═══════════════════════════════════════════════════════════════

GitHub: https://github.com/code-yeongyu/oh-my-opencode
Discord: https://discord.gg/PUwSMR9XNk
"""
        omo_text.insert("1.0", omo_content)
        omo_text.config(state=tk.DISABLED)

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
            text=f"v{APP_VERSION}",
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

        # GitHub 链接
        github_label = tk.Label(
            center_frame,
            text=f"⭐ GitHub: {GITHUB_URL}",
            font=FONTS["body"],
            bg=COLORS["card_bg"],
            fg=COLORS["primary"],
            cursor="hand2",
        )
        github_label.pack(pady=5)
        github_label.bind("<Button-1>", lambda e: webbrowser.open(GITHUB_URL))

        # 作者信息
        author_label = tk.Label(
            center_frame,
            text=f"作者: {AUTHOR_NAME}",
            font=FONTS["body"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"],
            cursor="hand2",
        )
        author_label.pack(pady=5)
        author_label.bind("<Button-1>", lambda e: webbrowser.open(AUTHOR_GITHUB))

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
        # Logo - 点击跳转到关于页面
        logo_frame = tk.Frame(self, bg=COLORS["sidebar_bg"])
        logo_frame.pack(fill=tk.X, padx=12, pady=(12, 8))

        self.logo_label = tk.Label(
            logo_frame,
            text="OpenCode",
            font=FONTS["title"],
            bg=COLORS["sidebar_bg"],
            fg=COLORS["primary"],
            cursor="hand2",
        )
        self.logo_label.pack(anchor=tk.W)
        self.logo_label.bind("<Button-1>", lambda e: self.app.show_page("help"))
        ToolTip(self.logo_label, "点击查看关于信息")

        self.version_label = tk.Label(
            logo_frame,
            text=f"配置管理器 v{APP_VERSION}",
            font=FONTS["small"],
            bg=COLORS["sidebar_bg"],
            fg=COLORS["text_secondary"],
            cursor="hand2",
        )
        self.version_label.pack(anchor=tk.W)
        self.version_label.bind("<Button-1>", lambda e: self.app.show_page("help"))

        # 分隔线
        tk.Frame(self, height=1, bg=COLORS["border"]).pack(
            fill=tk.X, padx=12, pady=(4, 8)
        )

        # OpenCode 分组
        opencode_header = tk.Frame(self, bg=COLORS["sidebar_bg"])
        opencode_header.pack(fill=tk.X, padx=12, pady=(0, 4))
        tk.Label(
            opencode_header,
            text="OpenCode",
            font=FONTS["small"],
            bg=COLORS["sidebar_bg"],
            fg=COLORS["text_secondary"],
        ).pack(anchor=tk.W)
        opencode_path = str(ConfigPaths.get_opencode_config())
        opencode_filename = ConfigPaths.get_opencode_config().name
        self.opencode_path_label = tk.Label(
            opencode_header,
            text=f"📄 {opencode_filename}",
            font=("Consolas", 8),
            bg=COLORS["sidebar_bg"],
            fg=COLORS["primary"],
            cursor="hand2",
        )
        self.opencode_path_label.pack(anchor=tk.W)
        ToolTip(
            self.opencode_path_label,
            f"配置文件完整路径:\n{opencode_path}\n\n点击复制完整路径",
        )
        self.opencode_path_label.bind(
            "<Button-1>", lambda e: self.copy_path(opencode_path)
        )

        self.add_nav_button("provider", "Provider 管理")
        self.add_nav_button("model", "Model 管理")
        self.add_nav_button("opencode_agent", "Agent 配置")
        self.add_nav_button("mcp", "MCP 服务器")
        self.add_nav_button("skill", "Skill 管理")
        self.add_nav_button("rules", "Rules 管理")
        self.add_nav_button("compaction", "上下文压缩")
        self.add_nav_button("permission", "权限管理")

        # Oh My OpenCode 分组
        ohmyopencode_header = tk.Frame(self, bg=COLORS["sidebar_bg"])
        ohmyopencode_header.pack(fill=tk.X, padx=12, pady=(12, 4))
        tk.Label(
            ohmyopencode_header,
            text="Oh My OpenCode",
            font=FONTS["small"],
            bg=COLORS["sidebar_bg"],
            fg=COLORS["text_secondary"],
        ).pack(anchor=tk.W)
        ohmyopencode_path = str(ConfigPaths.get_ohmyopencode_config())
        ohmyopencode_filename = ConfigPaths.get_ohmyopencode_config().name
        self.ohmyopencode_path_label = tk.Label(
            ohmyopencode_header,
            text=f"📄 {ohmyopencode_filename}",
            font=("Consolas", 8),
            bg=COLORS["sidebar_bg"],
            fg=COLORS["primary"],
            cursor="hand2",
        )
        self.ohmyopencode_path_label.pack(anchor=tk.W)
        ToolTip(
            self.ohmyopencode_path_label,
            f"配置文件完整路径:\n{ohmyopencode_path}\n\n点击复制完整路径",
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
        ).pack(anchor=tk.W, padx=12, pady=(12, 4))
        self.add_nav_button("import", "外部导入")
        self.add_nav_button("help", "帮助说明")

        # 底部状态
        bottom_frame = tk.Frame(self, bg=COLORS["sidebar_bg"])
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=12)
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
            padx=12,
            pady=6,  # 减少垂直间距
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

    def refresh_theme(self):
        """刷新侧边栏主题颜色"""
        self.configure(bg=COLORS["sidebar_bg"])

        # 刷新 logo
        if hasattr(self, "logo_label"):
            self.logo_label.configure(bg=COLORS["sidebar_bg"], fg=COLORS["primary"])
        if hasattr(self, "version_label"):
            self.version_label.configure(
                bg=COLORS["sidebar_bg"], fg=COLORS["text_secondary"]
            )

        # 刷新路径标签
        if hasattr(self, "opencode_path_label"):
            self.opencode_path_label.configure(
                bg=COLORS["sidebar_bg"], fg=COLORS["primary"]
            )
        if hasattr(self, "ohmyopencode_path_label"):
            self.ohmyopencode_path_label.configure(
                bg=COLORS["sidebar_bg"], fg=COLORS["primary"]
            )

        # 刷新状态标签
        if hasattr(self, "status_label"):
            self.status_label.configure(
                bg=COLORS["sidebar_bg"], fg=COLORS["text_secondary"]
            )

        # 刷新所有导航按钮
        for key, btn in self.buttons.items():
            if key == self.active:
                btn.configure(bg=COLORS["primary"], fg="#FFFFFF")
            else:
                btn.configure(bg=COLORS["sidebar_bg"], fg=COLORS["text"])

        # 刷新所有子 Frame
        for child in self.winfo_children():
            if isinstance(child, tk.Frame):
                child.configure(bg=COLORS["sidebar_bg"])
                for subchild in child.winfo_children():
                    if isinstance(subchild, tk.Label):
                        # 保持特殊标签的颜色
                        if subchild not in [
                            self.logo_label,
                            self.version_label,
                            self.opencode_path_label,
                            self.ohmyopencode_path_label,
                            self.status_label,
                        ]:
                            subchild.configure(
                                bg=COLORS["sidebar_bg"], fg=COLORS["text_secondary"]
                            )


# ==================== 主窗口 ====================
class MainWindow:
    # 可用主题列表
    THEMES = {
        "darkly": "深色 - Darkly",
        "superhero": "深色 - Superhero",
        "cyborg": "深色 - Cyborg",
        "vapor": "深色 - Vapor",
        "solar": "深色 - Solar",
        "cosmo": "浅色 - Cosmo",
        "flatly": "浅色 - Flatly",
        "litera": "浅色 - Litera",
        "minty": "浅色 - Minty",
        "pulse": "浅色 - Pulse",
    }

    def __init__(self):
        # 使用 ttkbootstrap 窗口，默认深色主题
        self.current_theme = "darkly"
        self.root = ttk.Window(
            title=f"OpenCode 配置管理器 v{APP_VERSION}",
            themename=self.current_theme,
            size=(1200, 750),
            minsize=(1000, 600),
        )

        # 设置窗口图标
        self.set_icon()

        self.opencode_config = {}
        self.ohmyopencode_config = {}
        self.modified = False
        self.backup_manager = BackupManager()
        self.pages = {}
        self.first_run_checked = False
        self.version_checker = VersionChecker(callback=self.on_version_check_complete)

        self.setup_ui()
        self.load_configs()
        self.check_first_run()

        # 启动版本检查
        self.version_checker.check_update_async()

    def on_version_check_complete(self, latest_version, release_url):
        """版本检查完成回调"""
        if VersionChecker.compare_versions(APP_VERSION, latest_version):
            # 在主线程中更新 UI
            self.root.after(
                0, lambda: self.show_update_available(latest_version, release_url)
            )

    def show_update_available(self, version, url):
        """显示有新版本可用"""
        if hasattr(self, "update_badge"):
            self.update_badge.show(version, url)

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
        # 主容器 - 使用 ttk.Frame
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=BOTH, expand=True)

        # 侧边栏
        self.sidebar = Sidebar(self.main_container, self)
        self.sidebar.pack(side=LEFT, fill=Y)

        # 右侧内容区
        self.right_container = ttk.Frame(self.main_container)
        self.right_container.pack(side=RIGHT, fill=BOTH, expand=True)

        # 顶部工具栏
        self.toolbar = ttk.Frame(self.right_container, bootstyle="secondary")
        self.toolbar.pack(fill=X, pady=(0, 1))

        self.toolbar_inner = ttk.Frame(self.toolbar)
        self.toolbar_inner.pack(fill=BOTH, expand=True, padx=20, pady=12)

        # 左侧按钮组
        left_buttons = ttk.Frame(self.toolbar_inner)
        left_buttons.pack(side=LEFT)

        ttk.Button(
            left_buttons,
            text="保存全部",
            command=self.save_configs,
            bootstyle="success",
        ).pack(side=LEFT, padx=(0, 8))
        ttk.Button(
            left_buttons, text="重新加载", command=self.load_configs, bootstyle="info"
        ).pack(side=LEFT, padx=(0, 8))
        ttk.Button(
            left_buttons,
            text="备份",
            command=self.backup_configs,
            bootstyle="secondary",
        ).pack(side=LEFT, padx=(0, 8))
        ttk.Button(
            left_buttons,
            text="恢复备份",
            command=self.show_restore_dialog,
            bootstyle="secondary",
        ).pack(side=LEFT)

        # 右侧信息区
        self.right_info = ttk.Frame(self.toolbar_inner)
        self.right_info.pack(side=RIGHT)

        # 更新提示徽章
        self.update_badge = UpdateBadge(self.right_info)
        self.update_badge.pack(side=RIGHT, padx=(0, 12))

        # GitHub 链接
        github_btn = ttk.Button(
            self.right_info,
            text="⭐ GitHub",
            command=lambda: webbrowser.open(GITHUB_URL),
            bootstyle="link",
        )
        github_btn.pack(side=RIGHT, padx=(0, 8))
        ToolTip(github_btn, f"访问项目主页\n{GITHUB_URL}")

        # 作者信息
        author_label = ttk.Label(
            self.right_info,
            text=f"by {AUTHOR_NAME}",
            font=("Microsoft YaHei UI", 9),
            cursor="hand2",
        )
        author_label.pack(side=RIGHT, padx=(0, 12))
        author_label.bind("<Button-1>", lambda e: webbrowser.open(AUTHOR_GITHUB))
        ToolTip(author_label, f"作者: {AUTHOR_NAME}\n点击访问 GitHub 主页")

        # 主题切换下拉菜单
        self.theme_var = tk.StringVar(value=self.current_theme)
        theme_menu = ttk.Menubutton(
            self.right_info,
            text="🎨 主题",
            bootstyle="outline",
        )
        theme_menu.pack(side=RIGHT, padx=(0, 12))

        # 创建主题菜单
        theme_dropdown = tk.Menu(theme_menu, tearoff=0)
        for theme_name, theme_label in self.THEMES.items():
            theme_dropdown.add_command(
                label=theme_label, command=lambda t=theme_name: self.change_theme(t)
            )
        theme_menu["menu"] = theme_dropdown
        ToolTip(theme_menu, "切换界面主题")

        # 分隔符
        ttk.Separator(self.right_info, orient=VERTICAL).pack(
            side=RIGHT, fill=Y, padx=12
        )

        self.modified_label = ttk.Label(
            self.right_info,
            text="",
            font=("Microsoft YaHei UI", 9),
            bootstyle="warning",
        )
        self.modified_label.pack(side=RIGHT, padx=(0, 8))

        self.config_status = ttk.Label(
            self.right_info,
            text="配置: 未加载",
            font=("Microsoft YaHei UI", 9),
        )
        self.config_status.pack(side=RIGHT, padx=(0, 12))

        # 分隔线
        ttk.Separator(self.right_container, orient=HORIZONTAL).pack(fill=X)

        # 内容区
        self.content_frame = ttk.Frame(self.right_container)
        self.content_frame.pack(fill=BOTH, expand=True, padx=20, pady=20)

        # 创建页面
        self.pages["provider"] = ProviderTab(self.content_frame, self)
        self.pages["model"] = ModelTab(self.content_frame, self)
        self.pages["opencode_agent"] = OpenCodeAgentTab(self.content_frame, self)
        self.pages["mcp"] = MCPTab(self.content_frame, self)
        self.pages["skill"] = SkillTab(self.content_frame, self)
        self.pages["rules"] = RulesTab(self.content_frame, self)
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

    def change_theme(self, theme_name):
        """切换主题"""
        self.current_theme = theme_name
        self.root.style.theme_use(theme_name)

    def show_page(self, key):
        for page in self.pages.values():
            page.pack_forget()
        if key in self.pages:
            self.pages[key].pack(fill=BOTH, expand=True)
        # 更新侧边栏选中状态
        self.sidebar.set_active(key)

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
        self.pages["skill"].refresh_list()
        self.pages["rules"].refresh_list()
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
