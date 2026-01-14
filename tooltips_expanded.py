# -*- coding: utf-8 -*-
"""
扩展的TOOLTIPS字典 - 包含白话中文解释
复制此内容替换 opencode_config_manager.py 中的 TOOLTIPS 字典
"""

# 参数说明提示（用于Tooltip）- 根据 OpenCode 官方文档
# 所有提示都包含：关键字 + 白话解释 + 使用场景 + 示例
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


def get_tooltip(key):
    """获取tooltip文本，如果不存在返回空字符串"""
    return TOOLTIPS.get(key, "")
