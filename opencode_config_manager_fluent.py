#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenCode & Oh My OpenCode 配置管理器 v1.0.5 (QFluentWidgets 版本)
一个可视化的GUI工具，用于管理OpenCode和Oh My OpenCode的配置文件

基于 PyQt5 + QFluentWidgets 重写，提供现代化 Fluent Design 界面

v1.0.5 更新：
- 跨页面数据同步：新增/编辑/删除配置后自动刷新所有相关页面
- 版本检查改为 30 分钟定时触发（启动后 5 秒首次检查）
- 修复首页 MCP 统计显示 0 的问题

v1.0.4 更新：
- 备份目录支持手动选择和重置
- 文件重命名为 opencode_config_manager_fluent.py

v1.0.3 更新：
- 跨平台路径支持 (Windows/Linux/macOS 统一)
- 完善构建脚本 (build_unix.sh + build_windows.bat)
- Linux 无头服务器自动使用 xvfb

v1.0.2 更新：
- 首页配置文件路径支持手动选择
- 支持切换到任意 JSON/JSONC 配置文件
- 支持重置为默认路径

v1.0.1 更新：
- 支持 JSONC 格式配置文件（带注释的 JSON）
- 支持 // 单行注释和 /* */ 多行注释
- 自动检测 .jsonc 和 .json 双扩展名
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
from typing import Dict, List, Optional, Any, Tuple

from PyQt5.QtCore import Qt, QUrl, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QDesktopServices, QFont, QPixmap
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


APP_VERSION = "1.0.5"
GITHUB_REPO = "icysaintdx/OpenCode-Config-Manager"
GITHUB_URL = f"https://github.com/{GITHUB_REPO}"
GITHUB_RELEASES_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
AUTHOR_NAME = "IcySaint"
AUTHOR_GITHUB = "https://github.com/icysaintdx"

# ==================== 版本检查配置 ====================
STARTUP_VERSION_CHECK_ENABLED = True  # 启动时是否检查版本
IMMEDIATE_VERSION_CHECK_MS = 5000  # 启动后首次检查延迟 (5秒)
UPDATE_INTERVAL_MS = 30 * 60 * 1000  # 定时检查间隔 (30分钟)


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
            # 检测是否为 JSONC 文件（包含注释）
            if path.exists() and ConfigManager.has_jsonc_comments(path):
                jsonc_warning = True
                # 自动备份 JSONC 文件
                if backup_manager:
                    backup_manager.backup(path, tag="jsonc-auto")

            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
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
class BaseDialog(QDialog):
    """对话框基类 - 所有对话框继承此类，自动适配深色主题"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._apply_theme()

    def _apply_theme(self):
        """应用深色主题样式 - 增强对比度和层次感"""
        if isDarkTheme():
            self.setStyleSheet("""
                QDialog {
                    background-color: #1e1e1e;
                    color: #ffffff;
                }
                QLabel {
                    color: #e0e0e0;
                }
                QLineEdit, QTextEdit, QSpinBox, QComboBox {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    border: 1px solid #4a4a4a;
                    border-radius: 6px;
                    padding: 8px;
                    min-height: 20px;
                }
                QLineEdit:focus, QTextEdit:focus {
                    border: 2px solid #0078d4;
                    background-color: #333333;
                }
                QCheckBox, QRadioButton {
                    color: #ffffff;
                }
                /* Tab/Pivot 样式增强 - 更明显的对比 */
                Pivot {
                    background-color: #2a2a2a;
                    border-radius: 8px;
                    padding: 6px;
                    margin-bottom: 8px;
                }
                PivotItem {
                    padding: 8px 16px;
                    border-radius: 6px;
                }
                PivotItem:checked {
                    background-color: #0078d4;
                    color: #ffffff;
                }
                /* 卡片样式增强 */
                CardWidget {
                    background-color: #2d2d2d;
                    border: 1px solid #404040;
                    border-radius: 10px;
                    margin: 6px 0;
                }
                /* 表格样式增强 - 更明显的层次 */
                QTableWidget {
                    background-color: #252525;
                    color: #ffffff;
                    border: 1px solid #404040;
                    border-radius: 8px;
                    gridline-color: #3a3a3a;
                    selection-background-color: #0078d4;
                }
                QTableWidget::item {
                    color: #e0e0e0;
                    padding: 10px 8px;
                    border-bottom: 1px solid #333333;
                }
                QTableWidget::item:selected {
                    background-color: #0078d4;
                    color: #ffffff;
                }
                QTableWidget::item:hover {
                    background-color: #353535;
                }
                /* 表头样式 - 更突出 */
                QHeaderView::section {
                    background-color: #383838;
                    color: #ffffff;
                    border: none;
                    border-bottom: 2px solid #0078d4;
                    padding: 10px 8px;
                    font-weight: bold;
                    font-size: 13px;
                }
                QHeaderView::section:horizontal {
                    border-right: 1px solid #4a4a4a;
                }
                QHeaderView::section:horizontal:last {
                    border-right: none;
                }
                /* 分组标题样式 */
                CaptionLabel {
                    color: #0078d4;
                    font-weight: bold;
                    font-size: 13px;
                    padding: 4px 0;
                }
                QScrollArea {
                    background-color: #1e1e1e;
                    border: none;
                }
                /* 列表样式 */
                QListWidget {
                    background-color: #252525;
                    border: 1px solid #404040;
                    border-radius: 6px;
                }
                QListWidget::item {
                    padding: 8px;
                    border-bottom: 1px solid #333333;
                }
                QListWidget::item:selected {
                    background-color: #0078d4;
                }
                QListWidget::item:hover {
                    background-color: #353535;
                }
            """)
        else:
            self.setStyleSheet("")


class BasePage(QWidget):
    """页面基类 - 所有页面继承此类"""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName(title.replace(" ", "_").lower())
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
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


# ==================== 首页 ====================
class HomePage(BasePage):
    """首页 - 显示配置文件路径、统计信息、工具栏"""

    def __init__(self, main_window, parent=None):
        super().__init__("首页", parent)
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

        # Logo 图片 - 保持原始比例，设置固定尺寸确保完整显示
        logo_path = Path(__file__).parent / "assets" / "logo1.png"
        logo_label = QLabel(about_card)
        logo_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path))
            # 缩放到高度 100，保持比例 (原始 383x146，缩放后约 262x100)
            scaled_pixmap = pixmap.scaledToHeight(100, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
            # 设置固定尺寸确保完整显示
            logo_label.setFixedSize(scaled_pixmap.width(), scaled_pixmap.height())
        else:
            logo_label.setText("{ }")
            logo_label.setStyleSheet(
                "font-size: 36px; font-weight: bold; color: #3498DB;"
            )
        about_layout.addWidget(logo_label)

        # OCCM 和全称放同一行
        title_layout = QHBoxLayout()
        occm_label = TitleLabel("OCCM", about_card)
        occm_label.setStyleSheet("font-size: 32px; font-weight: bold;")
        title_layout.addWidget(occm_label)
        title_layout.addWidget(
            SubtitleLabel(f"OpenCode Config Manager v{APP_VERSION}", about_card)
        )
        title_layout.addStretch()
        about_layout.addLayout(title_layout)

        about_layout.addWidget(
            BodyLabel(
                "一个可视化的GUI工具，用于管理OpenCode和Oh My OpenCode的配置文件",
                about_card,
            )
        )

        # 链接按钮
        link_layout = QHBoxLayout()
        github_btn = PrimaryPushButton(FIF.GITHUB, "GitHub 项目主页", about_card)
        github_btn.clicked.connect(lambda: webbrowser.open(GITHUB_URL))
        link_layout.addWidget(github_btn)

        author_btn = PushButton(FIF.PEOPLE, f"作者: {AUTHOR_NAME}", about_card)
        author_btn.clicked.connect(lambda: webbrowser.open(AUTHOR_GITHUB))
        link_layout.addWidget(author_btn)

        link_layout.addStretch()
        about_layout.addLayout(link_layout)

        # ===== 配置文件路径卡片 =====
        paths_card = self.add_card("配置文件路径")
        paths_layout = paths_card.layout()

        # OpenCode 配置路径
        oc_layout = QHBoxLayout()
        oc_layout.addWidget(BodyLabel("OpenCode:", paths_card))
        self.oc_path_label = CaptionLabel(
            str(ConfigPaths.get_opencode_config()), paths_card
        )
        self.oc_path_label.setToolTip(str(ConfigPaths.get_opencode_config()))
        oc_layout.addWidget(self.oc_path_label, 1)

        oc_copy_btn = ToolButton(FIF.COPY, paths_card)
        oc_copy_btn.setToolTip("复制路径")
        oc_copy_btn.clicked.connect(
            lambda: self._copy_to_clipboard(self.oc_path_label.text())
        )
        oc_layout.addWidget(oc_copy_btn)

        oc_browse_btn = ToolButton(FIF.FOLDER, paths_card)
        oc_browse_btn.setToolTip("选择配置文件")
        oc_browse_btn.clicked.connect(lambda: self._browse_config("opencode"))
        oc_layout.addWidget(oc_browse_btn)

        self.oc_reset_btn = ToolButton(FIF.SYNC, paths_card)
        self.oc_reset_btn.setToolTip("重置为默认路径")
        self.oc_reset_btn.clicked.connect(lambda: self._reset_config_path("opencode"))
        self.oc_reset_btn.setVisible(ConfigPaths.is_custom_path("opencode"))
        oc_layout.addWidget(self.oc_reset_btn)

        paths_layout.addLayout(oc_layout)

        # Oh My OpenCode 配置路径
        ohmy_layout = QHBoxLayout()
        ohmy_layout.addWidget(BodyLabel("Oh My OpenCode:", paths_card))
        self.ohmy_path_label = CaptionLabel(
            str(ConfigPaths.get_ohmyopencode_config()), paths_card
        )
        self.ohmy_path_label.setToolTip(str(ConfigPaths.get_ohmyopencode_config()))
        ohmy_layout.addWidget(self.ohmy_path_label, 1)

        ohmy_copy_btn = ToolButton(FIF.COPY, paths_card)
        ohmy_copy_btn.setToolTip("复制路径")
        ohmy_copy_btn.clicked.connect(
            lambda: self._copy_to_clipboard(self.ohmy_path_label.text())
        )
        ohmy_layout.addWidget(ohmy_copy_btn)

        ohmy_browse_btn = ToolButton(FIF.FOLDER, paths_card)
        ohmy_browse_btn.setToolTip("选择配置文件")
        ohmy_browse_btn.clicked.connect(lambda: self._browse_config("ohmyopencode"))
        ohmy_layout.addWidget(ohmy_browse_btn)

        self.ohmy_reset_btn = ToolButton(FIF.SYNC, paths_card)
        self.ohmy_reset_btn.setToolTip("重置为默认路径")
        self.ohmy_reset_btn.clicked.connect(
            lambda: self._reset_config_path("ohmyopencode")
        )
        self.ohmy_reset_btn.setVisible(ConfigPaths.is_custom_path("ohmyopencode"))
        ohmy_layout.addWidget(self.ohmy_reset_btn)

        paths_layout.addLayout(ohmy_layout)

        # 备份目录路径
        backup_layout = QHBoxLayout()
        backup_layout.addWidget(BodyLabel("备份目录:", paths_card))
        self.backup_path_label = CaptionLabel(
            str(ConfigPaths.get_backup_dir()), paths_card
        )
        self.backup_path_label.setToolTip(str(ConfigPaths.get_backup_dir()))
        backup_layout.addWidget(self.backup_path_label, 1)

        backup_copy_btn = ToolButton(FIF.COPY, paths_card)
        backup_copy_btn.setToolTip("复制路径")
        backup_copy_btn.clicked.connect(
            lambda: self._copy_to_clipboard(self.backup_path_label.text())
        )
        backup_layout.addWidget(backup_copy_btn)

        backup_browse_btn = ToolButton(FIF.FOLDER, paths_card)
        backup_browse_btn.setToolTip("选择备份目录")
        backup_browse_btn.clicked.connect(self._browse_backup_dir)
        backup_layout.addWidget(backup_browse_btn)

        self.backup_reset_btn = ToolButton(FIF.SYNC, paths_card)
        self.backup_reset_btn.setToolTip("重置为默认路径")
        self.backup_reset_btn.clicked.connect(self._reset_backup_dir)
        self.backup_reset_btn.setVisible(ConfigPaths.is_custom_path("backup"))
        backup_layout.addWidget(self.backup_reset_btn)

        paths_layout.addLayout(backup_layout)

        # ===== 统计信息卡片 =====
        stats_card = self.add_card("配置统计")
        stats_layout = stats_card.layout()

        self.stats_grid = QGridLayout()
        self.stats_grid.setSpacing(16)

        # 统计项标签
        self.provider_count_label = BodyLabel("0", stats_card)
        self.model_count_label = BodyLabel("0", stats_card)
        self.mcp_count_label = BodyLabel("0", stats_card)
        self.agent_count_label = BodyLabel("0", stats_card)
        self.ohmy_agent_count_label = BodyLabel("0", stats_card)
        self.category_count_label = BodyLabel("0", stats_card)

        stats_items = [
            ("Provider 数量:", self.provider_count_label),
            ("Model 数量:", self.model_count_label),
            ("MCP 服务器:", self.mcp_count_label),
            ("OpenCode Agent:", self.agent_count_label),
            ("Oh My Agent:", self.ohmy_agent_count_label),
            ("Category:", self.category_count_label),
        ]

        for i, (label_text, value_label) in enumerate(stats_items):
            row = i // 3
            col = (i % 3) * 2
            self.stats_grid.addWidget(BodyLabel(label_text, stats_card), row, col)
            self.stats_grid.addWidget(value_label, row, col + 1)

        stats_layout.addLayout(self.stats_grid)

        # ===== 操作按钮卡片 =====
        action_card = self.add_card("快捷操作")
        action_layout = action_card.layout()

        btn_layout = QHBoxLayout()

        reload_btn = PrimaryPushButton(FIF.SYNC, "重新加载配置", action_card)
        reload_btn.clicked.connect(self._on_reload)
        btn_layout.addWidget(reload_btn)

        backup_btn = PushButton(FIF.SAVE, "备份配置", action_card)
        backup_btn.clicked.connect(self._on_backup)
        btn_layout.addWidget(backup_btn)

        btn_layout.addStretch()
        action_layout.addLayout(btn_layout)

        self.layout.addStretch()

    def _copy_to_clipboard(self, text: str):
        """复制文本到剪贴板"""
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        self.show_success("成功", "路径已复制到剪贴板")

    def _browse_config(self, config_type: str):
        """浏览并选择配置文件"""
        title = (
            "选择 OpenCode 配置文件"
            if config_type == "opencode"
            else "选择 Oh My OpenCode 配置文件"
        )
        file_filter = "JSON/JSONC 文件 (*.json *.jsonc);;所有文件 (*)"

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
                self.show_error(
                    "错误", "无法解析配置文件，请确保是有效的 JSON/JSONC 格式"
                )
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
            self.show_success("成功", f"已切换到自定义配置文件: {path.name}")

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
        self.show_success("成功", "已重置为默认配置路径")

    def _browse_backup_dir(self):
        """浏览并选择备份目录"""
        start_path = str(ConfigPaths.get_backup_dir())
        dir_path = QFileDialog.getExistingDirectory(self, "选择备份目录", start_path)

        if dir_path:
            path = Path(dir_path)
            ConfigPaths.set_backup_dir(path)
            self.backup_path_label.setText(str(path))
            self.backup_path_label.setToolTip(str(path))
            self.backup_reset_btn.setVisible(True)
            # 更新备份管理器的目录
            self.main_window.backup_manager.backup_dir = path
            path.mkdir(parents=True, exist_ok=True)
            self.show_success("成功", f"已切换到自定义备份目录: {path.name}")

    def _reset_backup_dir(self):
        """重置为默认备份目录"""
        ConfigPaths.reset_to_default("backup")
        default_path = ConfigPaths.get_backup_dir()
        self.backup_path_label.setText(str(default_path))
        self.backup_path_label.setToolTip(str(default_path))
        self.backup_reset_btn.setVisible(False)
        # 更新备份管理器的目录
        self.main_window.backup_manager.backup_dir = default_path
        self.show_success("成功", "已重置为默认备份目录")

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

        self._load_stats()
        self.show_success("成功", "配置已重新加载")

    def _on_backup(self):
        """备份配置"""
        backup_manager = self.main_window.backup_manager
        oc_path = backup_manager.backup(ConfigPaths.get_opencode_config(), tag="manual")
        ohmy_path = backup_manager.backup(
            ConfigPaths.get_ohmyopencode_config(), tag="manual"
        )

        if oc_path and ohmy_path:
            self.show_success("成功", "配置已备份")
        else:
            self.show_error("错误", "备份失败")


# ==================== Provider 页面 ====================
class ProviderPage(BasePage):
    """Provider 管理页面"""

    def __init__(self, main_window, parent=None):
        super().__init__("Provider 管理", parent)
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
            # API地址添加tooltip显示全部
            api_url = data.get("options", {}).get("baseURL", "")
            api_item = QTableWidgetItem(api_url)
            api_item.setToolTip(api_url if api_url else "使用默认地址")
            self.table.setItem(row, 3, api_item)
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


class ProviderDialog(BaseDialog):
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
        self.name_edit.setToolTip(get_tooltip("provider_name"))
        if self.is_edit:
            self.name_edit.setEnabled(False)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        # 显示名称
        display_layout = QHBoxLayout()
        display_layout.addWidget(BodyLabel("显示名称:", self))
        self.display_edit = LineEdit(self)
        self.display_edit.setPlaceholderText("如: Anthropic (Claude)")
        self.display_edit.setToolTip(get_tooltip("provider_display"))
        display_layout.addWidget(self.display_edit)
        layout.addLayout(display_layout)

        # SDK 选择
        sdk_layout = QHBoxLayout()
        sdk_layout.addWidget(BodyLabel("SDK:", self))
        self.sdk_combo = ComboBox(self)
        self.sdk_combo.addItems(PRESET_SDKS)
        self.sdk_combo.setToolTip(get_tooltip("provider_sdk"))
        sdk_layout.addWidget(self.sdk_combo)
        layout.addLayout(sdk_layout)

        # API 地址
        url_layout = QHBoxLayout()
        url_layout.addWidget(BodyLabel("API 地址:", self))
        self.url_edit = LineEdit(self)
        self.url_edit.setPlaceholderText("留空使用默认地址")
        self.url_edit.setToolTip(get_tooltip("provider_url"))
        url_layout.addWidget(self.url_edit)
        layout.addLayout(url_layout)

        # API 密钥
        key_layout = QHBoxLayout()
        key_layout.addWidget(BodyLabel("API 密钥:", self))
        self.key_edit = LineEdit(self)
        self.key_edit.setPlaceholderText("支持环境变量: {env:API_KEY}")
        self.key_edit.setToolTip(get_tooltip("provider_apikey"))
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

        self.setWindowTitle("编辑模型" if self.is_edit else "添加模型")
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
                    background-color: #3d3d3d;
                    border-radius: 6px;
                    padding: 4px;
                }
                /* 卡片样式增强 */
                CardWidget {
                    background-color: #363636;
                    border: 1px solid #4a4a4a;
                    border-radius: 8px;
                    margin: 4px 0;
                }
                /* 表格样式增强 */
                QTableWidget {
                    background-color: #2a2a2a;
                    border: 1px solid #4a4a4a;
                    border-radius: 6px;
                    gridline-color: #404040;
                }
                QTableWidget::item {
                    padding: 6px;
                    border-bottom: 1px solid #3a3a3a;
                }
                QTableWidget::item:selected {
                    background-color: #0078d4;
                }
                QHeaderView::section {
                    background-color: #404040;
                    color: #ffffff;
                    border: none;
                    border-bottom: 2px solid #0078d4;
                    padding: 8px;
                    font-weight: bold;
                }
                /* 分组标题样式 */
                CaptionLabel {
                    color: #0078d4;
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
        basic_layout.addWidget(SubtitleLabel("基本信息", basic_card))

        # 模型ID
        id_layout = QHBoxLayout()
        id_layout.addWidget(BodyLabel("模型 ID:", self))
        self.id_edit = LineEdit(self)
        self.id_edit.setPlaceholderText("如: claude-sonnet-4-5-20250929")
        self.id_edit.setToolTip(get_tooltip("model_id"))
        if self.is_edit:
            self.id_edit.setEnabled(False)
        id_layout.addWidget(self.id_edit)
        basic_layout.addLayout(id_layout)

        # 显示名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(BodyLabel("显示名称:", self))
        self.name_edit = LineEdit(self)
        self.name_edit.setToolTip(get_tooltip("model_name"))
        name_layout.addWidget(self.name_edit)
        basic_layout.addLayout(name_layout)

        # 支持附件
        self.attachment_check = CheckBox("支持附件 (图片/文档)", self)
        self.attachment_check.setToolTip(get_tooltip("model_attachment"))
        basic_layout.addWidget(self.attachment_check)

        # 上下文窗口和最大输出
        limit_layout = QHBoxLayout()
        limit_layout.addWidget(BodyLabel("上下文窗口:", self))
        self.context_spin = SpinBox(self)
        self.context_spin.setRange(0, 10000000)
        self.context_spin.setValue(200000)
        self.context_spin.setToolTip(get_tooltip("model_context"))
        limit_layout.addWidget(self.context_spin)
        limit_layout.addSpacing(20)
        limit_layout.addWidget(BodyLabel("最大输出:", self))
        self.output_spin = SpinBox(self)
        self.output_spin.setRange(0, 1000000)
        self.output_spin.setValue(16000)
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

        tab_layout.addWidget(self.pivot)
        tab_layout.addWidget(self.stacked_widget, 1)

        layout.addWidget(tab_container, 1)

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
        claude_layout.addWidget(CaptionLabel("Claude Thinking 配置", claude_card))
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

        btn_full = PrimaryPushButton("一键添加", claude_card)
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
        openai_layout.addWidget(CaptionLabel("OpenAI 推理配置", openai_card))
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
        gemini_layout.addWidget(CaptionLabel("Gemini Thinking 配置", gemini_card))
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
        options_label = BodyLabel("Options 键值对列表:", scroll_content)
        options_label.setToolTip(get_tooltip("model_options"))
        layout.addWidget(options_label)

        self.options_table = TableWidget(scroll_content)
        self.options_table.setColumnCount(2)
        self.options_table.setHorizontalHeaderLabels(["键", "值"])
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

        key_label = BodyLabel("键:", scroll_content)
        key_label.setFixedWidth(24)
        input_layout.addWidget(key_label)

        self.option_key_edit = LineEdit(scroll_content)
        self.option_key_edit.setPlaceholderText("temperature")
        self.option_key_edit.setFixedHeight(32)
        input_layout.addWidget(self.option_key_edit, 1)

        value_label = BodyLabel("值:", scroll_content)
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
        add_opt_btn = PrimaryPushButton("添加", scroll_content)
        add_opt_btn.setFixedHeight(32)
        add_opt_btn.clicked.connect(self._add_option)
        opt_btn_layout.addWidget(add_opt_btn)
        del_opt_btn = PushButton("删除选中", scroll_content)
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

        variants_label = BodyLabel("模型变体配置 (Variants):", parent)
        variants_label.setToolTip(get_tooltip("model_variants"))
        layout.addWidget(variants_label)

        # Variants 列表
        self.variants_table = TableWidget(parent)
        self.variants_table.setColumnCount(2)
        self.variants_table.setHorizontalHeaderLabels(["变体名称", "配置"])
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
        name_label = BodyLabel("变体名:", parent)
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
        preset_layout.addWidget(CaptionLabel("预设:", parent))
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
        layout.addWidget(BodyLabel("配置 (JSON):", parent))
        self.variant_config_edit = TextEdit(parent)
        self.variant_config_edit.setPlaceholderText('{"reasoningEffort": "high"}')
        self.variant_config_edit.setMinimumHeight(80)
        self.variant_config_edit.setMaximumHeight(100)
        layout.addWidget(self.variant_config_edit)

        # 添加/删除按钮
        var_btn_layout = QHBoxLayout()
        var_btn_layout.setSpacing(8)
        add_var_btn = PrimaryPushButton("添加变体", parent)
        add_var_btn.setMinimumHeight(36)
        add_var_btn.clicked.connect(self._add_variant)
        var_btn_layout.addWidget(add_var_btn)
        del_var_btn = PushButton("删除变体", parent)
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
        # 连接配置变更信号
        self.main_window.config_changed.connect(self._on_config_changed)

    def _on_config_changed(self):
        """配置变更时刷新数据"""
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
            ["名称", "类型", "启用", "超时", "命令/URL"]
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


class MCPDialog(BaseDialog):
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
        self.name_edit.setToolTip(get_tooltip("mcp_name"))
        if self.is_edit:
            self.name_edit.setEnabled(False)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        # 启用状态
        self.enabled_check = CheckBox("启用此 MCP 服务器", self)
        self.enabled_check.setChecked(True)
        self.enabled_check.setToolTip(get_tooltip("mcp_enabled"))
        layout.addWidget(self.enabled_check)

        if self.mcp_type == "local":
            # 启动命令
            cmd_label = BodyLabel("启动命令 (JSON数组):", self)
            cmd_label.setToolTip(get_tooltip("mcp_command"))
            layout.addWidget(cmd_label)
            self.command_edit = TextEdit(self)
            self.command_edit.setPlaceholderText('["npx", "-y", "@mcp/server"]')
            self.command_edit.setMaximumHeight(80)
            layout.addWidget(self.command_edit)

            # 环境变量
            env_label = BodyLabel("环境变量 (JSON对象):", self)
            env_label.setToolTip(get_tooltip("mcp_environment"))
            layout.addWidget(env_label)
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
            self.url_edit.setToolTip(get_tooltip("mcp_url"))
            url_layout.addWidget(self.url_edit)
            layout.addLayout(url_layout)

            # Headers
            headers_label = BodyLabel("请求头 (JSON对象):", self)
            headers_label.setToolTip(get_tooltip("mcp_headers"))
            layout.addWidget(headers_label)
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
        self.timeout_spin.setToolTip(get_tooltip("mcp_timeout"))
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
        # 连接配置变更信号
        self.main_window.config_changed.connect(self._on_config_changed)

    def _on_config_changed(self):
        """配置变更时刷新数据"""
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


class OpenCodeAgentDialog(BaseDialog):
    """OpenCode Agent 编辑对话框 - 完整版本"""

    def __init__(self, main_window, agent_name: str = None, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.agent_name = agent_name
        self.is_edit = agent_name is not None

        self.setWindowTitle("编辑 Agent" if self.is_edit else "添加 Agent")
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
                QScrollArea { background-color: #2d2d2d; border: none; }
                QScrollArea > QWidget > QWidget { background-color: #2d2d2d; }
                QWidget { background-color: transparent; }
                CardWidget { background-color: #363636; border: 1px solid #4a4a4a; border-radius: 8px; }
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
                "QWidget#scrollContent { background-color: #2d2d2d; }"
            )
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(10)

        # ===== 基本信息 =====
        basic_card = CardWidget(content)
        basic_layout = QVBoxLayout(basic_card)
        basic_layout.setSpacing(10)
        basic_layout.addWidget(SubtitleLabel("基本信息", basic_card))

        # Agent 名称
        name_layout = QHBoxLayout()
        name_layout.setSpacing(8)
        name_label = BodyLabel("Agent 名称:", basic_card)
        name_label.setMinimumWidth(80)
        name_layout.addWidget(name_label)
        self.name_edit = LineEdit(basic_card)
        self.name_edit.setPlaceholderText("build, plan, explore")
        self.name_edit.setMinimumHeight(36)
        self.name_edit.setToolTip(get_tooltip("agent_name"))
        if self.is_edit:
            self.name_edit.setEnabled(False)
        name_layout.addWidget(self.name_edit)
        basic_layout.addLayout(name_layout)

        # 描述
        desc_layout = QHBoxLayout()
        desc_layout.setSpacing(8)
        desc_label = BodyLabel("描述:", basic_card)
        desc_label.setMinimumWidth(80)
        desc_layout.addWidget(desc_label)
        self.desc_edit = LineEdit(basic_card)
        self.desc_edit.setPlaceholderText("Agent 功能描述")
        self.desc_edit.setMinimumHeight(36)
        self.desc_edit.setToolTip(get_tooltip("agent_description"))
        desc_layout.addWidget(self.desc_edit)
        basic_layout.addLayout(desc_layout)

        # 模式
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(8)
        mode_label = BodyLabel("模式:", basic_card)
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
        model_label = BodyLabel("模型 (可选):", basic_card)
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
        param_layout.addWidget(SubtitleLabel("参数配置", param_card))

        # Temperature
        temp_layout = QHBoxLayout()
        temp_layout.setSpacing(8)
        temp_layout.addWidget(BodyLabel("Temperature:", param_card))
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
        steps_layout.addWidget(BodyLabel("最大步数 (可选):", param_card))
        self.maxsteps_spin = SpinBox(param_card)
        self.maxsteps_spin.setRange(0, 1000)
        self.maxsteps_spin.setValue(0)
        self.maxsteps_spin.setSpecialValueText("不限制")
        self.maxsteps_spin.setMinimumHeight(36)
        self.maxsteps_spin.setToolTip(get_tooltip("opencode_agent_maxSteps"))
        steps_layout.addWidget(self.maxsteps_spin)
        steps_layout.addStretch()
        param_layout.addLayout(steps_layout)

        # 复选框
        check_layout = QHBoxLayout()
        check_layout.setSpacing(16)
        self.hidden_check = CheckBox("隐藏 (仅 subagent)", param_card)
        self.hidden_check.setToolTip(get_tooltip("opencode_agent_hidden"))
        check_layout.addWidget(self.hidden_check)
        self.disable_check = CheckBox("禁用此 Agent", param_card)
        self.disable_check.setToolTip(get_tooltip("opencode_agent_disable"))
        check_layout.addWidget(self.disable_check)
        check_layout.addStretch()
        param_layout.addLayout(check_layout)

        content_layout.addWidget(param_card)

        # ===== 工具和权限配置 =====
        tools_card = CardWidget(content)
        tools_layout = QVBoxLayout(tools_card)
        tools_layout.setSpacing(8)
        tools_layout.addWidget(SubtitleLabel("工具和权限配置", tools_card))

        # 工具配置 (JSON)
        tools_label = BodyLabel("工具配置 (JSON):", tools_card)
        tools_label.setToolTip(get_tooltip("opencode_agent_tools"))
        tools_layout.addWidget(tools_label)
        self.tools_edit = TextEdit(tools_card)
        self.tools_edit.setPlaceholderText('{"write": true, "edit": true}')
        self.tools_edit.setMinimumHeight(100)
        self.tools_edit.setMaximumHeight(150)
        tools_layout.addWidget(self.tools_edit)

        # 权限配置 (JSON)
        perm_label = BodyLabel("权限配置 (JSON):", tools_card)
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
        prompt_label = SubtitleLabel("系统提示词", prompt_card)
        prompt_label.setToolTip(get_tooltip("opencode_agent_prompt"))
        prompt_layout.addWidget(prompt_label)
        self.prompt_edit = TextEdit(prompt_card)
        self.prompt_edit.setPlaceholderText("自定义系统提示词...")
        self.prompt_edit.setMinimumHeight(80)
        prompt_layout.addWidget(self.prompt_edit)

        content_layout.addWidget(prompt_card)
        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        # ===== 按钮 =====
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = PushButton("取消", self)
        self.cancel_btn.setMinimumHeight(36)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.save_btn = PrimaryPushButton("保存", self)
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


class PresetOpenCodeAgentDialog(BaseDialog):
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

        self.edit_btn = PushButton(FIF.EDIT, "编辑", self)
        self.edit_btn.clicked.connect(self._on_edit)
        toolbar.addWidget(self.edit_btn)

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
        self.table.doubleClicked.connect(self._on_edit)
        self.layout.addWidget(self.table)

    def _load_data(self):
        self.table.setRowCount(0)
        config = self.main_window.opencode_config or {}
        permissions = config.get("permission", {})

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
            self.show_success("成功", "权限已添加")

    def _on_edit(self):
        row = self.table.currentRow()
        if row < 0:
            self.show_warning("提示", "请先选择一个权限")
            return

        tool = self.table.item(row, 0).text()
        level = self.table.item(row, 1).text()
        dialog = PermissionDialog(self.main_window, tool=tool, level=level, parent=self)
        if dialog.exec_():
            self._load_data()
            self.show_success("成功", "权限已更新")

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


class PermissionDialog(BaseDialog):
    """权限编辑对话框"""

    def __init__(self, main_window, tool: str = None, level: str = None, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.original_tool = tool
        self.is_edit = tool is not None

        self.setWindowTitle("编辑权限" if self.is_edit else "添加权限")
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
        tool_layout.addWidget(BodyLabel("工具名称:", self))
        self.tool_edit = LineEdit(self)
        self.tool_edit.setPlaceholderText("如: Bash, Read, mcp_*")
        self.tool_edit.setToolTip(get_tooltip("permission_tool"))
        tool_layout.addWidget(self.tool_edit)
        layout.addLayout(tool_layout)

        # 权限级别
        level_layout = QHBoxLayout()
        level_layout.addWidget(BodyLabel("权限级别:", self))
        self.level_combo = ComboBox(self)
        self.level_combo.addItems(["allow", "ask", "deny"])
        self.level_combo.setToolTip(get_tooltip("permission_level"))
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
        # 隐藏页面标题
        self.title_label.hide()
        self._setup_ui()

    def _setup_ui(self):
        # ===== 关于卡片 (无标题) - 不扩展 =====
        about_card = SimpleCardWidget(self)
        about_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        about_card_layout = QVBoxLayout(about_card)
        about_card_layout.setContentsMargins(20, 16, 20, 16)
        about_card_layout.setSpacing(12)

        # Logo 图片
        logo_path = Path(__file__).parent / "assets" / "logo1.png"
        logo_label = QLabel(about_card)
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path))
            logo_label.setPixmap(pixmap.scaledToHeight(120, Qt.SmoothTransformation))
        else:
            logo_label.setText("{ }")
            logo_label.setStyleSheet(
                "font-size: 36px; font-weight: bold; color: #9B59B6;"
            )
        about_card_layout.addWidget(logo_label)

        # OCCM 和全称放同一行 - 渐变色样式
        title_layout = QHBoxLayout()
        occm_label = TitleLabel("OCCM", about_card)
        occm_label.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
            color: #9B59B6;
        """)
        title_layout.addWidget(occm_label)
        title_layout.addWidget(
            SubtitleLabel(f"OpenCode Config Manager v{APP_VERSION}", about_card)
        )
        title_layout.addStretch()
        about_card_layout.addLayout(title_layout)

        about_card_layout.addWidget(
            BodyLabel(
                "一个可视化的GUI工具，用于管理OpenCode和Oh My OpenCode的配置文件",
                about_card,
            )
        )
        about_card_layout.addWidget(BodyLabel(f"作者: {AUTHOR_NAME}", about_card))

        link_layout = QHBoxLayout()
        github_btn = PrimaryPushButton(FIF.GITHUB, "GitHub 项目主页", about_card)
        github_btn.clicked.connect(lambda: webbrowser.open(GITHUB_URL))
        link_layout.addWidget(github_btn)

        author_btn = PushButton(FIF.PEOPLE, f"作者: {AUTHOR_NAME}", about_card)
        author_btn.clicked.connect(lambda: webbrowser.open(AUTHOR_GITHUB))
        link_layout.addWidget(author_btn)

        link_layout.addStretch()
        about_card_layout.addLayout(link_layout)

        self.layout.addWidget(about_card)  # 不设置 stretch factor，不扩展

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
            SubtitleLabel("配置优先顺序（从高到低）", priority_widget)
        )
        priority_content = """
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
- Provider 和 Model 配置会进行深度合并
"""
        priority_text = PlainTextEdit(priority_widget)
        priority_text.setPlainText(priority_content.strip())
        priority_text.setReadOnly(True)
        priority_layout.addWidget(priority_text, 1)
        self.stacked_widget.addWidget(priority_widget)
        self.pivot.addItem(routeKey="priority", text="配置优先级")

        # 使用说明 Tab
        usage_widget = QWidget()
        usage_layout = QVBoxLayout(usage_widget)
        usage_layout.addWidget(
            SubtitleLabel("OpenCode 配置管理器 使用说明", usage_widget)
        )
        usage_content = """
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
- Agent/Category 的模型必须是已配置的 Provider/Model
"""
        usage_text = PlainTextEdit(usage_widget)
        usage_text.setPlainText(usage_content.strip())
        usage_text.setReadOnly(True)
        usage_layout.addWidget(usage_text, 1)
        self.stacked_widget.addWidget(usage_widget)
        self.pivot.addItem(routeKey="usage", text="使用说明")

        # Options vs Variants Tab
        options_widget = QWidget()
        options_layout = QVBoxLayout(options_widget)
        options_layout.addWidget(
            SubtitleLabel("Options vs Variants 说明", options_widget)
        )
        options_content = """
根据 OpenCode 官方文档:

【Options】模型的默认配置参数
- 每次调用模型时都会使用这些配置
- 适合放置常用的固定配置
- 例如: thinking.type, thinking.budgetTokens

【Variants】可切换的变体配置
- 用户可通过 variant_cycle 快捷键切换
- 适合放置不同场景的配置组合
- 例如: high/medium/low 不同的 budgetTokens

═══════════════════════════════════════════════════════════════
Thinking 模式配置示例
═══════════════════════════════════════════════════════════════

【Claude】
  options:
    thinking:
      type: "enabled"
      budgetTokens: 16000
  variants:
    high:
      thinking:
        budgetTokens: 32000
    max:
      thinking:
        budgetTokens: 64000

【OpenAI】
  options:
    reasoningEffort: "high"
  variants:
    medium:
      reasoningEffort: "medium"
    low:
      reasoningEffort: "low"

【Gemini】
  options:
    thinkingConfig:
      thinkingBudget: 8000
  variants:
    high:
      thinkingConfig:
        thinkingBudget: 16000
"""
        options_text = PlainTextEdit(options_widget)
        options_text.setPlainText(options_content.strip())
        options_text.setReadOnly(True)
        options_layout.addWidget(options_text, 1)
        self.stacked_widget.addWidget(options_widget)
        self.pivot.addItem(routeKey="options", text="Options/Variants")

        # Tab 切换连接
        def on_tab_changed(key):
            index_map = {"priority": 0, "usage": 1, "options": 2}
            self.stacked_widget.setCurrentIndex(index_map.get(key, 0))

        self.pivot.currentItemChanged.connect(on_tab_changed)
        self.pivot.setCurrentItem("priority")

        tab_layout.addWidget(self.pivot)
        tab_layout.addWidget(self.stacked_widget, 1)

        self.layout.addWidget(tab_container, 1)


# ==================== 主窗口 ====================
class MainWindow(FluentWindow):
    """主窗口"""

    # 配置变更信号 - 用于跨页面数据同步
    config_changed = pyqtSignal()

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
        self.latest_version = None
        self.release_url = None

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

    def _init_window(self):
        self.setWindowTitle(f"OCCM - OpenCode Config Manager v{APP_VERSION}")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 820)

        # 设置主题跟随系统
        setTheme(Theme.AUTO)

        # 创建系统主题监听器，自动跟随系统深浅色变化
        self.themeListener = SystemThemeListener(self)
        self.themeListener.start()

        # 设置窗口图标 - 使用 assets/icon.png
        icon_path = Path(__file__).parent / "assets" / "icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        else:
            # 备用 icon.ico
            icon_path = Path(__file__).parent / "assets" / "icon.ico"
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
            else:
                self.setWindowIcon(FIF.CODE.icon())

        # 设置导航栏始终展开，不折叠
        self.navigationInterface.setExpandWidth(200)
        self.navigationInterface.setCollapsible(False)

        # 减少导航菜单项间距，让底部菜单能完整显示
        self.navigationInterface.setStyleSheet("""
            NavigationTreeWidget {
                font-size: 13px;
            }
            NavigationTreeWidget::item {
                height: 36px;
                margin: 2px 0px;
            }
            NavigationSeparator {
                height: 1px;
                margin: 4px 0px;
            }
        """)

    def _init_navigation(self):
        # ===== 顶部工具栏区域 =====
        # 添加首页/状态页面
        self.home_page = HomePage(self)
        self.addSubInterface(self.home_page, FIF.HOME, "首页")

        # ===== OpenCode 配置分组 =====
        # Provider 页面
        self.provider_page = ProviderPage(self)
        self.addSubInterface(self.provider_page, FIF.PEOPLE, "Provider 管理")

        # Model 页面
        self.model_page = ModelPage(self)
        self.addSubInterface(self.model_page, FIF.ROBOT, "Model 管理")

        # MCP 页面
        self.mcp_page = MCPPage(self)
        self.addSubInterface(self.mcp_page, FIF.CLOUD, "MCP 服务器")

        # OpenCode Agent 页面
        self.opencode_agent_page = OpenCodeAgentPage(self)
        self.addSubInterface(self.opencode_agent_page, FIF.COMMAND_PROMPT, "Agent 配置")

        # Permission 页面
        self.permission_page = PermissionPage(self)
        self.addSubInterface(self.permission_page, FIF.CERTIFICATE, "权限管理")

        # Skill 页面
        self.skill_page = SkillPage(self)
        self.addSubInterface(self.skill_page, FIF.BOOK_SHELF, "Skill 管理")

        # Rules 页面
        self.rules_page = RulesPage(self)
        self.addSubInterface(self.rules_page, FIF.DOCUMENT, "Rules 管理")

        # Compaction 页面
        self.compaction_page = CompactionPage(self)
        self.addSubInterface(self.compaction_page, FIF.ZIP_FOLDER, "上下文压缩")

        # ===== Oh My OpenCode 配置分组 =====
        # Oh My Agent 页面
        self.ohmy_agent_page = OhMyAgentPage(self)
        self.addSubInterface(self.ohmy_agent_page, FIF.EMOJI_TAB_SYMBOLS, "Oh My Agent")

        # Category 页面
        self.category_page = CategoryPage(self)
        self.addSubInterface(self.category_page, FIF.TAG, "Category 管理")

        # ===== 工具分组 =====
        # Import 页面
        self.import_page = ImportPage(self)
        self.addSubInterface(self.import_page, FIF.DOWNLOAD, "外部导入")

        # ===== 底部导航 =====
        # 主题切换按钮
        self.navigationInterface.addItem(
            routeKey="theme",
            icon=FIF.CONSTRACT,
            text="切换主题",
            onClick=self._toggle_theme,
            position=NavigationItemPosition.BOTTOM,
        )

        # Backup 按钮
        self.navigationInterface.addItem(
            routeKey="backup",
            icon=FIF.HISTORY,
            text="备份管理",
            onClick=self._show_backup_dialog,
            position=NavigationItemPosition.BOTTOM,
        )

        # Help 页面 (底部)
        self.help_page = HelpPage(self)
        self.addSubInterface(
            self.help_page, FIF.HELP, "帮助说明", NavigationItemPosition.BOTTOM
        )

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
            InfoBar.info(
                title="发现新版本",
                content=f"v{latest_version} 可用，点击查看",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=10000,
                parent=self,
            )

    def _toggle_theme(self):
        """切换深浅色主题 (手动切换会停止跟随系统)"""
        if isDarkTheme():
            setTheme(Theme.LIGHT)
        else:
            setTheme(Theme.DARK)

    def closeEvent(self, e):
        """关闭窗口时停止主题监听器"""
        if hasattr(self, "themeListener"):
            self.themeListener.terminate()
            self.themeListener.deleteLater()
        super().closeEvent(e)


# ==================== Oh My Agent 页面 ====================
class OhMyAgentPage(BasePage):
    """Oh My OpenCode Agent 管理页面"""

    def __init__(self, main_window, parent=None):
        super().__init__("Oh My Agent", parent)
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
            # 描述列添加 tooltip 显示全部
            desc = data.get("description", "")
            desc_item = QTableWidgetItem(desc[:50] + "..." if len(desc) > 50 else desc)
            desc_item.setToolTip(desc)
            self.table.setItem(row, 2, desc_item)

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


class OhMyAgentDialog(BaseDialog):
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
        self.name_edit.setToolTip(get_tooltip("ohmyopencode_agent_name"))
        if self.is_edit:
            self.name_edit.setEnabled(False)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        # 绑定模型
        model_layout = QHBoxLayout()
        model_layout.addWidget(BodyLabel("绑定模型:", self))
        self.model_combo = ComboBox(self)
        self.model_combo.setToolTip(get_tooltip("ohmyopencode_agent_model"))
        self._load_models()
        model_layout.addWidget(self.model_combo)
        layout.addLayout(model_layout)

        # 描述
        desc_label = BodyLabel("描述:", self)
        desc_label.setToolTip(get_tooltip("ohmyopencode_agent_description"))
        layout.addWidget(desc_label)
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


class PresetOhMyAgentDialog(BaseDialog):
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
        # 连接配置变更信号
        self.main_window.config_changed.connect(self._on_config_changed)

    def _on_config_changed(self):
        """配置变更时刷新数据"""
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
            # 描述列添加 tooltip 显示全部
            desc = data.get("description", "")
            desc_item = QTableWidgetItem(desc[:30] + "..." if len(desc) > 30 else desc)
            desc_item.setToolTip(desc)
            self.table.setItem(row, 3, desc_item)

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


class CategoryDialog(BaseDialog):
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
        self.name_edit.setToolTip(get_tooltip("category_name"))
        if self.is_edit:
            self.name_edit.setEnabled(False)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        # 绑定模型
        model_layout = QHBoxLayout()
        model_layout.addWidget(BodyLabel("绑定模型:", self))
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
        desc_label = BodyLabel("描述:", self)
        desc_label.setToolTip(get_tooltip("category_description"))
        layout.addWidget(desc_label)
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


class PresetCategoryDialog(BaseDialog):
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
    """Skill 权限配置和 SKILL.md 创建页面 - 左右分栏布局"""

    def __init__(self, main_window, parent=None):
        super().__init__("Skill 管理", parent)
        self.main_window = main_window
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        # 使用 QSplitter 实现左右分栏
        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # ===== 左侧：Skill 权限配置 =====
        left_widget = QWidget()
        left_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 8, 0)

        # 左侧标题
        left_layout.addWidget(SubtitleLabel("Skill 权限配置", left_widget))
        left_layout.addWidget(
            CaptionLabel(
                "配置 Skill 的加载权限。Skill 是可复用的指令文件，Agent 可按需加载。",
                left_widget,
            )
        )

        # 权限列表工具栏
        toolbar = QHBoxLayout()
        self.add_btn = PrimaryPushButton(FIF.ADD, "添加", left_widget)
        self.add_btn.clicked.connect(self._on_add)
        toolbar.addWidget(self.add_btn)

        self.delete_btn = PushButton(FIF.DELETE, "删除", left_widget)
        self.delete_btn.clicked.connect(self._on_delete)
        toolbar.addWidget(self.delete_btn)

        toolbar.addStretch()
        left_layout.addLayout(toolbar)

        # 权限列表
        self.table = TableWidget(left_widget)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["模式", "权限"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self._on_select)
        left_layout.addWidget(self.table, 1)  # 添加 stretch factor

        # 编辑区域
        edit_card = SimpleCardWidget(left_widget)
        edit_layout = QVBoxLayout(edit_card)
        edit_layout.setContentsMargins(12, 8, 12, 8)
        edit_layout.addWidget(CaptionLabel("编辑权限", edit_card))

        # 模式输入
        pattern_layout = QHBoxLayout()
        pattern_layout.addWidget(BodyLabel("模式:", edit_card))
        self.pattern_edit = LineEdit(edit_card)
        self.pattern_edit.setPlaceholderText("如: *, internal-*, my-skill")
        self.pattern_edit.setToolTip(get_tooltip("skill_pattern"))
        pattern_layout.addWidget(self.pattern_edit)
        edit_layout.addLayout(pattern_layout)

        # 权限选择
        perm_layout = QHBoxLayout()
        perm_layout.addWidget(BodyLabel("权限:", edit_card))
        self.perm_combo = ComboBox(edit_card)
        self.perm_combo.addItems(["allow", "ask", "deny"])
        self.perm_combo.setToolTip(get_tooltip("skill_permission"))
        perm_layout.addWidget(self.perm_combo)
        perm_layout.addStretch()
        edit_layout.addLayout(perm_layout)

        # 保存按钮
        save_btn = PrimaryPushButton("保存权限", edit_card)
        save_btn.clicked.connect(self._on_save)
        edit_layout.addWidget(save_btn)

        left_layout.addWidget(edit_card)

        # ===== 右侧：创建 SKILL.md =====
        right_widget = QWidget()
        right_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(8, 0, 0, 0)

        # 右侧标题
        right_layout.addWidget(SubtitleLabel("创建 SKILL.md", right_widget))

        # Skill 名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(BodyLabel("Skill 名称:", right_widget))
        self.skill_name_edit = LineEdit(right_widget)
        self.skill_name_edit.setPlaceholderText(
            "小写字母、数字、连字符，如: git-release"
        )
        self.skill_name_edit.setToolTip(get_tooltip("skill_name"))
        name_layout.addWidget(self.skill_name_edit)
        right_layout.addLayout(name_layout)

        # Skill 描述
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(BodyLabel("描述:", right_widget))
        self.skill_desc_edit = LineEdit(right_widget)
        self.skill_desc_edit.setPlaceholderText("描述 Skill 的功能")
        desc_layout.addWidget(self.skill_desc_edit)
        right_layout.addLayout(desc_layout)

        # Skill 内容
        right_layout.addWidget(BodyLabel("Skill 内容 (Markdown):", right_widget))
        self.skill_content_edit = TextEdit(right_widget)
        self.skill_content_edit.setPlaceholderText(
            "## What I do\n- 描述功能\n\n## Instructions\n- 具体指令"
        )
        right_layout.addWidget(self.skill_content_edit, 1)

        # 保存位置
        loc_layout = QHBoxLayout()
        loc_layout.addWidget(BodyLabel("保存位置:", right_widget))
        self.global_radio = RadioButton(
            "全局 (~/.config/opencode/skill/)", right_widget
        )
        self.global_radio.setChecked(True)
        loc_layout.addWidget(self.global_radio)
        self.project_radio = RadioButton("项目 (.opencode/skill/)", right_widget)
        loc_layout.addWidget(self.project_radio)
        loc_layout.addStretch()
        right_layout.addLayout(loc_layout)

        # 创建按钮
        create_btn = PrimaryPushButton("创建 SKILL.md", right_widget)
        create_btn.clicked.connect(self._on_create_skill)
        right_layout.addWidget(create_btn)

        # 添加到 splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([400, 400])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        self.layout.addWidget(
            splitter, 1
        )  # 添加 stretch factor 让 splitter 占满剩余空间

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
        inst_layout.setSpacing(12)

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
        add_layout.setSpacing(8)
        self.inst_path_edit = LineEdit(inst_card)
        self.inst_path_edit.setPlaceholderText(
            "文件路径，如: CONTRIBUTING.md, docs/*.md"
        )
        self.inst_path_edit.setFixedHeight(36)
        add_layout.addWidget(self.inst_path_edit)

        add_btn = PushButton(FIF.ADD, "添加", inst_card)
        add_btn.setFixedHeight(36)
        add_btn.clicked.connect(self._on_add_instruction)
        add_layout.addWidget(add_btn)

        del_btn = PushButton(FIF.DELETE, "删除", inst_card)
        del_btn.setFixedHeight(36)
        del_btn.clicked.connect(self._on_delete_instruction)
        add_layout.addWidget(del_btn)

        inst_layout.addLayout(add_layout)

        # 快捷路径
        quick_layout = QHBoxLayout()
        quick_layout.setSpacing(8)
        quick_layout.addWidget(BodyLabel("快捷:", inst_card))
        for path in ["CONTRIBUTING.md", "docs/*.md", ".cursor/rules/*.md"]:
            btn = PushButton(path, inst_card)
            btn.setFixedHeight(32)
            btn.clicked.connect(lambda checked, p=path: self.inst_path_edit.setText(p))
            quick_layout.addWidget(btn)
        quick_layout.addStretch()
        inst_layout.addLayout(quick_layout)

        # 保存按钮
        save_inst_btn = PrimaryPushButton("保存 Instructions", inst_card)
        save_inst_btn.setFixedHeight(36)
        save_inst_btn.clicked.connect(self._on_save_instructions)
        inst_layout.addWidget(save_inst_btn)

        # AGENTS.md 编辑卡片
        agents_card = self.add_card("AGENTS.md 编辑")
        agents_layout = agents_card.layout()
        agents_layout.setSpacing(12)

        # 位置选择
        loc_layout = QHBoxLayout()
        loc_layout.setSpacing(12)
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
        btn_layout.setSpacing(8)
        save_btn = PrimaryPushButton("保存 AGENTS.md", agents_card)
        save_btn.setFixedHeight(36)
        save_btn.clicked.connect(self._on_save_agents_md)
        btn_layout.addWidget(save_btn)

        reload_btn = PushButton("重新加载", agents_card)
        reload_btn.setFixedHeight(36)
        reload_btn.clicked.connect(self._load_agents_md)
        btn_layout.addWidget(reload_btn)

        template_btn = PushButton("使用模板", agents_card)
        template_btn.setFixedHeight(36)
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
class BackupDialog(BaseDialog):
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
