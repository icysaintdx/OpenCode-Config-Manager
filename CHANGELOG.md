# 更新日志

所有版本的更新记录。

---

## [v1.5.0] - 2026-01-24 00:52
**版本代号**: 多语言支持版

### 🌐 新增功能
#### **完整的多语言支持** ⭐⭐⭐
- **双语支持**：
  - 简体中文（zh_CN）
  - English（en_US）
  - 自动识别系统语言
  - **动态语言切换**：点击即切换，无需重启软件

- **翻译覆盖范围**：
  - 15 个主要页面（完整翻译）
  - 17 个对话框（完整翻译）
  - 400+ 处 tr() 函数调用
  - 900+ 个翻译键值对

- **已翻译页面**：
  - ✅ HomePage（首页）
  - ✅ HelpPage（帮助页面）
  - ✅ PermissionPage（权限管理）
  - ✅ CompactionPage（上下文压缩）
  - ✅ ProviderPage（Provider 管理）
  - ✅ ModelPage（Model 管理）
  - ✅ MCPPage（MCP 服务器）
  - ✅ OpenCodeAgentPage（Agent 配置）
  - ✅ CategoryPage（Category 管理）
  - ✅ OhMyAgentPage（Oh My Agent）
  - ✅ RulesPage（Rules 管理）
  - ✅ ImportPage（外部导入）
  - ✅ MonitorPage（监控页面）
  - ✅ CLIExportPage（CLI 导出）
  - ✅ SkillPage（Skill 管理）

#### **国内AI平台支持** ⭐
- **新增 5 个国内平台**：
  - 智谱 GLM（glm-4-plus、glm-4-flash 等）
  - 千问 Qwen（qwen-max、qwen-turbo 等）
  - Kimi（月之暗面）（moonshot-v1-8k、moonshot-v1-32k 等）
  - 零一万物 Yi（yi-lightning、yi-large 等）
  - MiniMax（abab6.5s-chat、abab6.5g-chat 等）
- **技术实现**：
  - 所有平台使用 OpenAI 兼容 SDK
  - 支持环境变量自动检测
  - 预设常用模型快速选择

### 🐛 Bug 修复
- **修复 Win10 启动报错** - `'bool' object has no attribute 'get'`
  - 在所有页面添加配置类型检查
  - 防止配置文件格式错误导致崩溃
- **修复软件版本号显示错误** - 版本号从 1.4.0 更新到 1.5.0
- **修复 GitHub API 速率限制** - 添加冷却机制（默认1小时），403错误时延长到6小时
- **修复多语言图标显示** - 改用 TransparentToolButton，图标居中显示
- **修复备份管理对话框** - 优化列宽，路径列完整显示
- **修复 Skill 市场** - 移除无法安装的 ComposioHQ Skills，保留12个可用 Skills
- **修复语言切换页面错位** - 移除强制重绘逻辑，避免布局错乱

### 🎨 UI 优化
- **优化菜单字体** - 减少字体粗度（font-weight: 900 → normal）
- **调整导航栏宽度** - 设置为 200px，适应中英文菜单
- **统一标题栏图标** - 窗口图标统一为 18x18
- **优化 Skill 市场表格** - 调整列宽，描述列获得更多空间
- **语言切换按钮** - 移到导航栏底部，符合设计规范
- **启动时菜单展开** - 默认展开状态，无需手动点击
- **窗口高度增加** - 从 820px 增加到 870px

### 🔧 技术实现
- **LanguageManager**：单例模式的翻译管理器
- **tr() 函数**：全局翻译函数，支持参数格式化
- **语言文件**：JSON 格式，支持嵌套键值对
- **自动识别**：启动时自动识别系统语言
- **动态切换**：运行时切换语言，无需重启

### 📁 文件变更
- 更新：`opencode_config_manager_fluent.py`
- 新增：`locales/zh_CN.json`
- 新增：`locales/en_US.json`
- 更新：`.github/workflows/build.yml` - 添加 locales 到构建配置

---

## [v1.4.5] - 2026-01-23
**版本代号**: 单语言最终版

### 📝 说明
- 这是最后一个单语言（仅中文）版本
- 后续版本开始支持多语言

---

## [v1.4.4] - 2026-01-22
**版本代号**: CLI 工具增强版

### 🆕 新增功能
#### **CLI 工具导出增强** ⭐
- **支持导出到多个 CLI 工具**：
  - Claude Code（支持 4 个模型字段）
  - Codex（auth.json + config.toml）
  - Gemini（.env + settings.json）
- **Base URL 临时修改** - 可临时修改用于导出，不影响原始配置
- **模型自定义输入** - 支持手动输入自定义模型名称
- **语法高亮与格式化** - JSON/TOML/ENV 格式语法高亮 + 格式化按钮
- **通用配置功能** - 写入通用配置复选框 + 编辑通用配置对话框
- **双文件预览** - Codex/Gemini 双文件标签页预览

### 🎨 UI 优化
- **导航菜单字体加粗** - 提升菜单可读性和视觉层次
- **CLI 导出页面标签页布局** - 采用主标签页设计更清晰直观
- **监控页面启动/停止切换** - 默认不启动，需手动点击启动按钮

### 🐛 Bug 修复
- 模型留空处理优化
- 外部导入功能修复

---

## [v1.4.3] - 2026-01-21
**版本代号**: Oh My MCP 支持版

### 🆕 新增功能
#### **Oh My MCP 管理功能** ⭐
- **可视化管理 Oh My OpenCode 自带的 MCP 服务器**：
  - websearch（网页搜索）
  - context7（编程库文档检索）
  - grep_app（代码搜索）
- **功能特性**：
  - 在 MCP 服务器页面新增 "Oh My MCP" 按钮
  - 支持启用/禁用操作
  - 配置自动保存到 `oh-my-opencode.json`
  - 独立于 OpenCode 配置管理

---

## [v1.4.2] - 2026-01-21
**版本代号**: Skill 市场扩展版

### 🆕 新增功能
#### **Skill 市场扩展** ⭐
- **新增 12 个精选 Skills**：
  - 开发工具类：git-release、sequential-thinking
  - 代码质量类：code-review、linting
  - 测试类：test-generation
  - 文档类：documentation
  - 安全类：security-scan
  - API 类：api-testing
  - 数据库类：database-query
  - 等等...
- **远程市场链接** - 添加外部 Skill 商场链接（SkillsMP.com）
- **分类浏览** - 按功能分类展示 Skills
- **搜索功能** - 快速查找需要的 Skills

#### **安全扫描功能** ⭐
- **代码安全扫描**：
  - 检测 9 种危险代码模式
  - 安全评分系统（0-100 分）
  - 风险等级可视化（安全/低/中/高/严重）
  - 详细问题列表（行号、风险等级、描述、代码）

### 🐛 Bug 修复
- **修复 Skill 市场 404 错误** - 替换为 Anthropic 官方 Skills
- **修复 Skill 发现错误处理** - 添加调试脚本
- **修复已发现的 Skill 列表缺少滚动条**
- **修复 Skill 市场安装** - 自动检测分支（main/master）
- **修复 HyperlinkLabel 构造函数参数错误**

---
  - ✅ MCPPage（MCP 服务器）
  - ✅ OpenCodeAgentPage（Agent 配置）
  - ✅ CategoryPage（Category 管理）
  - ✅ OhMyAgentPage（Oh My Agent）
  - ✅ RulesPage（Rules 管理）
  - ✅ ImportPage（外部导入）
  - ⚠️ MonitorPage（监控页面 - 部分）
  - ⚠️ CLIExportPage（CLI 导出 - 部分）
  - ⚠️ SkillPage（Skill 管理 - 部分）

- **已翻译对话框**：
  - 所有 Provider、Model、MCP、Agent 相关对话框
  - 所有 Skill 相关对话框（市场、安装、更新、安全扫描）
  - 权限编辑对话框
  - 预设选择对话框

### 🔧 技术实现
- **LanguageManager**：单例模式的翻译管理器
- **tr() 函数**：全局翻译函数，支持参数格式化
- **语言文件**：JSON 格式，支持嵌套键值对
- **自动识别**：启动时自动识别系统语言
- **实时切换**：支持运行时切换语言（未来版本）

### 📝 翻译键命名规范
- 页面：`{page_name}.{key}` 例如：`home.title`
- 对话框：`{dialog_name}.{key}` 例如：`provider.add_provider`
- 通用：`common.{key}` 例如：`common.save`

### 📊 翻译统计
- **翻译完成度**：约 80%
- **Git 提交**：5 个 commit
- **代码行数**：400+ 处替换
- **语言文件大小**：zh_CN.json (23KB), en_US.json (11KB)

### 📁 文件变更
- 更新：`opencode_config_manager_fluent.py`
- 新增：`locales/zh_CN.json`
- 新增：`locales/en_US.json`
- 新增：`I18N_PROGRESS.md`
- 新增：`home_page_i18n_replacements.py`
- 新增：`batch_i18n_replacements.py`
- 新增：`batch_i18n_replacements_part2.py`

### 🎯 下一步计划
- 完成 MonitorPage 和 CLIExportPage 的完整翻译
- 完成 SkillPage 的完整翻译
- 添加语言切换 UI
- 支持更多语言（日语、韩语等）

---

## [v1.4.1] - 2026-01-20 15:35
**版本代号**: 依赖修复版

### 🐛 Bug 修复
- **修复 Skill 市场功能依赖缺失问题** ⭐
  - 问题：用户点击 Skill 市场时报错 `No module named 'requests'`
  - 原因：`requirements.txt` 中缺少 `requests` 依赖
  - 修复：在 `requirements.txt` 中添加 `requests>=2.25.0`
  - 影响功能：
    - Skill 市场安装功能
    - 从 GitHub 安装 Skills
    - Skill 更新检测功能
  - 文件：`requirements.txt`

### 📝 技术说明
- `SkillInstaller.install_from_github()` 方法需要 `requests` 库下载 GitHub 仓库
- `SkillUpdater.check_updates()` 方法需要 `requests` 库调用 GitHub API
- 建议用户重新安装依赖：`pip install -r requirements.txt`

---

## [v1.4.0] - 2026-01-20 18:00
**版本代号**: Skills 市场与安全扫描版

### 🆕 新增功能 (P2)
#### **Skill 市场功能** ⭐
- **内置 Skill 市场**：
  - 8 个精选 Skills（开发工具、代码质量、测试、文档、安全、API、数据库）
  - 分类浏览：按类别筛选 Skills
  - 搜索功能：按名称、描述、标签搜索
  - 表格展示：名称、描述、分类、仓库信息
  - 一键安装：选中后直接安装到指定位置

- **市场对话框**：
  - 搜索框 + 分类下拉框
  - 表格选择 + 详情显示
  - 安装位置选择
  - 自动填充仓库地址

#### **安全扫描功能** ⭐
- **代码安全扫描**：
  - 检测 9 种危险代码模式
  - 风险等级：critical（严重）、high（高）、medium（中）、low（低）
  - 安全评分：0-100 分
  - 详细问题列表：行号、风险等级、描述、代码片段

- **扫描模式**：
  - 系统命令执行（os.system、subprocess）
  - 动态代码执行（eval、exec）
  - 文件删除（os.remove、shutil.rmtree）
  - 网络请求（requests、socket）
  - 动态导入（__import__）

- **扫描结果对话框**：
  - 安全评分 + 风险等级（颜色标识）
  - 问题表格：行号、风险等级、描述、代码
  - 风险等级颜色：安全（绿）、低风险（浅绿）、中风险（橙）、高风险（红）、严重（深红）

### 🎨 UI 改进
- **Skill 浏览页面工具栏**：
  - 新增 "Skill 市场" 按钮（主按钮，蓝色高亮）
  - 调整按钮顺序：市场 → 安装 → 更新 → 刷新

- **Skill 详情操作按钮**：
  - 新增 "安全扫描" 按钮（盾牌图标）
  - 按钮顺序：编辑 → 安全扫描 → 删除 → 打开目录

### 📝 技术实现
- **新增类**：
  - `SkillMarket`：Skill 市场数据管理
  - `SkillMarketDialog`：市场浏览对话框
  - `SkillSecurityScanner`：安全扫描器
  - `SecurityScanDialog`：扫描结果对话框

- **核心方法**：
  - `SkillMarket.get_all_skills()`：获取所有市场 Skills
  - `SkillMarket.search_skills()`：搜索 Skills
  - `SkillMarket.get_by_category()`：按分类获取
  - `SkillSecurityScanner.scan_skill()`：扫描 Skill 安全风险
  - `SkillPage._on_open_market()`：打开市场
  - `SkillPage._on_scan_skill()`：扫描 Skill

### 🔧 功能特性
- ✅ 内置 8 个精选 Skills
- ✅ 分类 + 搜索功能
- ✅ 一键安装市场 Skills
- ✅ 9 种危险模式检测
- ✅ 安全评分系统
- ✅ 详细扫描报告
- ✅ 风险等级可视化

### 📚 使用说明
1. **浏览 Skill 市场**：
   - 点击 "Skill 市场" 按钮
   - 浏览或搜索 Skills
   - 选择 Skill 后点击 "安装选中"
   - 选择安装位置并确认

2. **安全扫描**：
   - 选择一个已安装的 Skill
   - 点击 "安全扫描" 按钮
   - 查看安全评分和问题列表
   - 根据风险等级决定是否使用

---

## [v1.3.0] - 2026-01-20 17:00
**版本代号**: Skills 安装与更新功能版

### 🆕 新增功能
#### **Skills 安装功能** ⭐
- **从 GitHub 安装 Skills**：
  - 支持 GitHub shorthand 格式：`user/repo`（如 `vercel-labs/git-release`）
  - 支持完整 GitHub URL：`https://github.com/user/repo`
  - 自动下载、解压、解析 SKILL.md
  - 自动获取最新 commit hash 用于更新检测
  - 支持安装到 4 个位置：OpenCode 全局/项目、Claude 全局/项目

- **从本地导入 Skills**：
  - 支持从本地路径导入：`./my-skill` 或 `/path/to/skill`
  - 自动复制到目标目录
  - 验证 SKILL.md 格式

- **元数据管理**：
  - 自动生成 `.skill-meta.json` 文件记录安装信息
  - GitHub 来源记录：owner、repo、branch、url、commit_hash、installed_at
  - 本地来源记录：original_path、installed_at

#### **Skills 更新功能** ⭐
- **更新检测**：
  - 一键检查所有已安装 Skills 的更新
  - 通过 GitHub API 获取最新 commit hash
  - 对比本地 commit hash 判断是否有更新
  - 显示更新状态：有更新 / 最新 / 本地 / 检查失败

- **批量更新**：
  - 表格显示所有 Skills 的更新状态
  - 支持选择性更新（复选框）
  - 全选 / 取消全选快捷操作
  - 显示当前版本和最新版本（commit hash 前 7 位）
  - 进度提示和结果统计

### 🎨 UI 改进
- **Skill 浏览页面工具栏**：
  - 新增 "安装 Skill" 按钮（主按钮，蓝色高亮）
  - 新增 "检查更新" 按钮
  - 优化按钮布局和间距

- **安装对话框**：
  - 清晰的输入提示和格式说明
  - 安装位置下拉选择
  - 实时进度提示

- **更新对话框**：
  - 表格展示所有 Skills 的更新信息
  - 统计信息显示（总数、有更新数）
  - 自动勾选有更新的 Skills
  - 禁用无更新的 Skills 复选框

### 📝 技术实现
- **新增类**：
  - `SkillInstaller`：Skills 安装器，支持 GitHub 和本地安装
  - `SkillUpdater`：Skills 更新器，检查和更新 Skills
  - `SkillInstallDialog`：安装对话框
  - `SkillUpdateDialog`：更新对话框
  - `ProgressDialog`：简单进度对话框

- **核心方法**：
  - `SkillInstaller.parse_source()`：解析安装源（GitHub/本地）
  - `SkillInstaller.install_from_github()`：从 GitHub 下载并安装
  - `SkillInstaller.install_from_local()`：从本地路径导入
  - `SkillUpdater.check_updates()`：检查所有 Skills 的更新
  - `SkillUpdater.update_skill()`：更新单个 Skill

- **依赖库**：
  - `requests`：HTTP 请求（下载 ZIP、调用 GitHub API）
  - `zipfile`：解压 GitHub 仓库 ZIP
  - `tempfile`：临时目录管理

### 🔧 功能特性
- ✅ 支持多种安装源格式
- ✅ 自动元数据管理
- ✅ 智能更新检测
- ✅ 批量操作支持
- ✅ 详细的错误提示
- ✅ 进度实时反馈
- ✅ 兼容现有 Skill 管理功能

### 📚 使用说明
1. **安装 Skill**：
   - 点击 "安装 Skill" 按钮
   - 输入 GitHub shorthand（如 `vercel-labs/git-release`）或本地路径
   - 选择安装位置
   - 点击 "安装" 等待完成

2. **更新 Skills**：
   - 点击 "检查更新" 按钮
   - 查看更新列表，自动勾选有更新的 Skills
   - 点击 "更新选中" 批量更新
   - 查看更新结果统计

3. **元数据文件**：
   - 每个 Skill 目录下会生成 `.skill-meta.json`
   - 记录安装来源和版本信息
   - 用于更新检测和管理

---

## [v1.2.0] - 2026-01-20 16:00
**版本代号**: Oh My MCP 管理功能版

### 🆕 新增功能
- **Oh My MCP 管理功能**：
  - 在 MCP 服务器页面新增 "Oh My MCP" 按钮
  - 点击后弹出对话框，显示 Oh My OpenCode 自带的 3 个 MCP 服务器：
    - **websearch** - 实时网页搜索（Exa AI）
    - **context7** - 获取最新官方文档
    - **grep_app** - 超快代码搜索（grep.app）
  - 可视化管理每个 MCP 的启用/禁用状态
  - 支持单个切换、全部启用、全部禁用操作
  - 通过 `disabled_mcps` 字段在 `oh-my-opencode.json` 中保存配置

### 📝 功能说明
- Oh My OpenCode 默认启用这 3 个 MCP 服务器
- 用户可以通过 UI 界面方便地禁用不需要的服务器
- 状态实时显示：✓ 启用（绿色）/ ✗ 禁用（红色）
- 配置自动保存到 Oh My OpenCode 配置文件

---

## [v1.1.9] - 2026-01-20 15:30
**版本代号**: MCP 配置规范修复版

### 🐛 Bug 修复
- **修复 MCP 配置不符合 OpenCode 官方规范导致的启动失败问题**：
  - **问题根因**：用户使用软件添加 MCP 后，OpenCode 启动报错 `Invalid input mcp.@modelcontextprotocol/server-sequential-thinking`
  - **修复 1 - MCP 键名规范化**：预设 MCP 模板使用简化的键名（如 `sequential-thinking`）而不是包含特殊字符的 npm 包名（如 `@modelcontextprotocol/server-sequential-thinking`），符合 OpenCode 配置规范
  - **修复 2 - 移除非标准字段**：根据 OpenCode 官方文档，MCP 配置只能包含固定的标准字段：
    - Local MCP: `type`, `command`, `environment`, `enabled`, `timeout`
    - Remote MCP: `type`, `url`, `headers`, `oauth`, `enabled`, `timeout`
  - 移除了 `description`、`tags`、`homepage`、`docs` 等非标准字段的写入，这些字段仅用于 UI 显示，不再写入配置文件

### 📝 技术细节
- **OpenCode 配置验证规则**：OpenCode 会严格验证配置文件，不接受包含特殊字符（`@`、`/`）的 MCP 键名，也不接受非标准字段
- **修复策略**：
  1. 预设模板的键名直接用作 MCP 名称，不再使用 `name` 字段
  2. `_update_extra_info()` 方法不再写入任何非标准字段
  3. 额外信息（描述、标签等）仅在 UI 中显示，不影响配置文件
- **影响范围**：v1.1.8 及之前版本均存在此问题，v1.1.9 完全修复

---

## [v1.1.8] - 2026-01-20 14:18
**版本代号**: 配置加载容错修复版

### 🐛 Bug 修复
- **修复配置文件格式异常导致的启动崩溃问题**：
  - 修复 `PermissionPage._load_data()` 方法：当 `permission` 字段为字符串等非字典类型时，程序启动会报错 `AttributeError: 'str' object has no attribute 'items'`
  - 修复 `MCPPage._load_data()` 方法：添加 `mcp` 字段类型检查
  - 修复 `OpenCodeAgentPage._load_data()` 方法：添加 `agent` 字段类型检查
  - 修复 `OhMyAgentPage._load_data()` 方法：添加 `agents` 字段类型检查
  - 修复 `CategoryPage._load_data()` 方法：添加 `categories` 字段类型检查
  - 所有修复均添加 `isinstance(data, dict)` 类型检查，当配置格式异常时使用空字典，避免程序崩溃

### 📝 技术细节
- 问题根因：用户配置文件中某些字段（如 `permission`）可能因手动编辑或外部工具导入而变成非字典类型（如字符串 `"allow"`），导致调用 `.items()` 方法时抛出 `AttributeError`
- 修复策略：在所有 `_load_data()` 方法中，对从配置文件读取的字典类型字段添加类型检查，确保程序健壮性
- 影响范围：v1.1.6 和 v1.1.7 版本均存在此问题，v1.1.8 完全修复

---

## [v1.1.7] - 2026-01-20 02:54
**版本代号**: CLI 导出与 UI 优化版

### 🆕 CLI 工具导出功能
- **Claude Code 多模型配置**：
  - 支持 4 个模型字段：主模型 (ANTHROPIC_MODEL)、Haiku、Sonnet、Opus
  - 每个模型可独立配置或留空使用默认值
  - 留空时配置文件不包含占位符文本
  
- **Codex/Gemini 双文件预览**：
  - Codex CLI：auth.json + config.toml 双文件标签页预览
  - Gemini CLI：.env + settings.json 双文件标签页预览
  - 每个文件独立显示和编辑

- **Base URL 临时修改**：
  - 每个 CLI 工具标签页显示 Provider 的 Base URL
  - 支持临时修改用于导出，不影响 OpenCode 原始配置
  - 修改后预览配置实时更新

- **模型自定义输入**：
  - 模型下拉框支持手动输入自定义模型名称
  - 使用原生 QComboBox 实现可编辑功能
  - 深色主题下文字颜色优化为白色

- **语法高亮与格式化**：
  - 新增 ConfigSyntaxHighlighter 类支持 JSON/TOML/ENV 格式
  - 颜色方案：字符串(绿色)、数字(橙色)、关键字(紫色)、键名(蓝色)、注释(灰色)
  - 添加"格式化"按钮可格式化 JSON 配置

- **通用配置功能**：
  - 添加"写入通用配置"复选框
  - 添加"编辑通用配置"链接按钮
  - 新增 CommonConfigEditDialog 对话框编辑通用配置

- **配置检测动画**：
  - 切换 Provider 时显示"⏳ 配置检测中..."状态
  - 300ms 延迟后显示检测结果

### 🎨 UI 优化
- **导航菜单字体加粗**：所有导航菜单项字体设置为 bold 提升可读性
- **CLI 导出页面标签页布局**：采用主标签页设计 (Claude/Codex/Gemini)
- **CLI 工具状态显示**：固定宽度 150px、高度 100px，居中对齐，状态文字加粗
- **配置预览框优化**：最小高度 350px，移除最大高度限制
- **模型下拉框宽度**：从 200px 增加到 300px

### 🔧 监控页面优化
- **启动/停止按钮切换**：
  - 默认不启动对话延迟检测
  - 将"停止"按钮改为"启动"按钮
  - 点击后切换为"停止"，再点击切换回"启动"
  - 只有手动点击"启动"才会开始自动检测

### 🐛 Bug 修复
- **模型留空处理**：选择"(留空使用默认)"时配置预览不包含占位符文本
- **删除重复样式**：Codex 和 Gemini 标签页中的重复样式定义已删除
- **外部导入功能修复**：修复外部配置导入相关问题

### 📁 文件变更
- 更新：`opencode_config_manager_fluent.py`

---

## [v1.1.6] - 2026-01-19 12:00
**版本代号**: 原生 Provider 支持版

### 🆕 新增功能
- **原生 Provider 支持**：
  - 新增"原生 Provider"页面 管理 OpenCode 官方支持的 AI 服务提供商
  - 支持 12 个原生 Provider：Anthropic、OpenAI、Gemini、Amazon Bedrock、Azure OpenAI、GitHub Copilot、xAI、Groq、OpenRouter、Vertex AI、DeepSeek、OpenCode Zen
  - 认证信息存储在独立的 `auth.json` 文件中 与 `opencode.json` 分离
  - 跨平台路径支持：Windows (`%LOCALAPPDATA%/opencode`)、Unix (`~/.local/share/opencode`)

- **AuthManager 认证管理器**：
  - `read_auth()` / `write_auth()` - 读写 auth.json
  - `get_provider_auth()` / `set_provider_auth()` / `delete_provider_auth()` - Provider 认证 CRUD
  - `mask_api_key()` - API Key 遮蔽显示 (首尾 4 字符）

- **环境变量检测与导入**：
  - `EnvVarDetector` 类自动检测系统环境变量
  - 支持 `{env:VARIABLE_NAME}` 格式引用环境变量
  - 一键导入检测到的环境变量

- **NativeProviderPage 页面**：
  - 表格布局显示 Provider 列表 (名称、SDK、状态、环境变量）
  - 状态颜色区分：已配置 (绿色）/ 未配置 (灰色）
  - 工具栏：配置、测试连接、删除按钮
  - 双击行打开配置对话框

- **NativeProviderDialog 配置对话框**：
  - 动态生成认证字段 (支持 text、password、file 类型）
  - 动态生成选项字段 (支持 text、select 类型）
  - 深色主题适配 使用 SimpleCardWidget 卡片布局
  - 环境变量导入按钮

- **连接测试功能**：
  - 调用 Provider 的 models 端点验证凭证
  - 显示成功/失败状态和响应时间

- **配置同步与去重**：
  - 在 Agent 模型选择中显示已配置的原生 Provider
  - 检测原生与自定义 Provider 重复 提示用户处理

- **Skill 发现与浏览**：
  - 扫描所有 4 个路径：OpenCode 全局/项目、Claude 全局/项目
  - 显示已发现的 Skill 列表 包含来源标识 (🌐 全局 / 📁 项目）
  - 点击查看详情：名称、描述、许可证、兼容性、路径、内容预览
  - 支持编辑、删除、打开目录操作

- **完整的 SKILL.md 创建/编辑**：
  - 支持完整 frontmatter：name、description、license、compatibility
  - 4 种保存位置选择 (OpenCode/Claude × 全局/项目）
  - 名称验证 (1-64字符 小写字母数字+单连字符 符合官方规范）
  - 描述验证 (1-1024字符）

- **权限配置增强**：
  - 全局权限配置 (permission.skill）
  - Agent 级别权限覆盖 (agent.xxx.permission.skill）
  - 禁用 Skill 工具 (agent.xxx.tools.skill: false）

- **SkillDiscovery 类**：
  - `discover_all()` - 发现所有路径下的 Skill
  - `parse_skill_file()` - 解析 SKILL.md frontmatter
  - `validate_skill_name()` / `validate_description()` - 验证名称和描述

### 🔧 优化改进
- **Skill 页面重构**：采用 3 标签页布局 (浏览 Skill、创建 Skill、权限配置）
- **Claude 兼容路径支持**：完整支持 `.claude/skills/` 路径
- **DiscoveredSkill 数据类**：统一 Skill 信息结构

### 📁 文件变更
- 更新：`opencode_config_manager_fluent.py`
- 新增：`assets/512x512.ico` (从 PNG 转换）

### 📋 新增数据类
- `AuthField` - 认证字段定义
- `OptionField` - 选项字段定义
- `NativeProviderConfig` - 原生 Provider 配置结构
- `NATIVE_PROVIDERS` - 12 个原生 Provider 定义列表

---

## [v1.1.2] - 2026-01-18 18:30
**版本代号**: UI 样式优化版

### 🎨 样式优化
- **主题色调整**：主题色改为 `#2979FF` 与主流设计风格一致
- **浅色模式优化**：背景色调整为奶白色 `#F7F8FA` 更加柔和护眼
- **窗口尺寸调整**：默认窗口高度调整为 820px 显示更多内容
- **对话框主题适配**：备份管理等对话框支持深浅色主题自动切换
- **状态颜色统一**：监控页面状态颜色与全局配色方案保持一致

### 🔧 技术改进
- **UIConfig 配置类**：新增全局 UI 配置类 统一管理字体、颜色、布局参数
- **字体配置**：默认使用 JetBrains Mono 等宽字体 提升代码可读性
- **导航栏优化**：紧凑布局 确保底部菜单项完整显示

### 📁 文件变更
- 更新：`opencode_config_manager_fluent.py`

---

## [v1.1.1] - 2026-01-17 21:49
**版本代号**: 配置检测与导入增强版

### 🆕 新增功能
- **首页配置检测**：新增“配置检测”按钮与详情面板 支持手动检查 OpenCode 与 Oh My OpenCode 配置并展示问题列表
- **列表批量模型**：Oh My Agent/Category 支持批量模型下拉选择 即时生效
- **默认描述展示**：列表内描述为空时展示预设描述 (仅显示 不写入配置）
- **监控页面**：新增模型可用性监控与历史记录显示 支持手动检测
- **MCP 预设扩展**：新增 chrome-devtools、open-web-mcp、serena 等常用预设
- **MCP 附加信息**：新增描述/标签/主页/文档字段 支持预设自动填充
- **MCP 资源入口**：MCP 页面新增 awesome MCP 集合入口按钮

### 🐛 Bug 修复
- **外部导入路径兼容**：Claude/Codex/cc-switch 导入在默认路径不存在时自动回退到 `D:\opcdcfg\test\...`
- **cc-switch 模型 ID 过滤**：忽略 GUID 形式的模型 ID 避免污染模型列表
- **导入映射对话框滚动**：ImportMappingDialog 固定高度并可滚动

### 🔧 优化改进
- **模型批量配置**：新增 thinking/options/variants 批量配置逻辑
- **模型 ID 解析增强**：从多种字段提取模型 ID 覆盖更多外部配置格式
- **配置验证增强**：补充空值校验并新增 Oh My OpenCode 配置结构校验
- **监控页面布局**：监控列表布局压缩与列宽优化

### 📁 文件变更
- 更新：`opencode_config_manager_fluent.py`

---

## [v1.1.0] - 2026-01-15 22:00
**版本代号**: 模态与更新提示增强版

### 🆕 新增功能
- **模型 Modalities 配置**：
  - 模型编辑对话框新增输入/输出模态设置
  - 输入模态支持：text、image、audio、video
  - 输出模态支持：text、image、audio
  - 编辑时自动加载已有配置 保存时写入 `modalities` 字段

- **更新提示增强**：
  - 提示条不再自动消失 需手动关闭
  - 点击提示条可直接打开 GitHub 发布页面
  - 浅色模式使用琥珀色背景 深色模式使用蓝色背景
  - 定时检查间隔改为 1 分钟

### 📁 文件变更
- 更新：`opencode_config_manager_fluent.py`

---

## [v1.0.9] - 2026-01-15 19:00
**版本代号**: 配置冲突检测版

### 🆕 新增功能
- **配置文件冲突检测**：
  - 启动时自动检测是否同时存在 `.json` 和 `.jsonc` 配置文件
  - 弹窗显示两个文件的大小和修改时间 帮助用户判断
  - 用户可选择使用哪个文件 另一个会被备份后删除
  - 解决了因 `.jsonc` 优先级更高导致加载旧配置的问题

- **ConfigPaths 类增强**：
  - `check_config_conflict()` - 检测配置文件冲突
  - `get_config_file_info()` - 获取文件大小和修改时间

### 🐛 Bug 修复
- **Category 和 Agent 描述丢失问题**：
  - 根因：同时存在 `.json` 和 `.jsonc` 时 程序优先加载旧的 `.jsonc` 文件
  - 现在会提示用户选择要使用的配置文件

### 📁 文件变更
- 更新：`opencode_config_manager_fluent.py`

---

## [v1.0.8] - 2026-01-15 18:30
**版本代号**: 版本检查修复版

### 🐛 Bug 修复
- **版本检查线程安全问题**：
  - 修复版本检查回调在子线程调用导致程序卡死的问题
  - 使用 `pyqtSignal` 从子线程安全地通知主线程更新 UI
  - `VersionChecker` 改为继承 `QObject` 支持信号槽机制

- **PyInstaller 打包资源路径问题**：
  - 新增 `get_resource_path()` 函数 正确处理打包后的资源路径
  - 修复打包后 logo/icon 图片加载失败导致的 temp 目录错误
  - 兼容开发环境和 PyInstaller 打包环境

### 🔧 优化改进
- **APP_VERSION 同步更新**：版本号从 1.0.5 更新到 1.0.8

### 📁 文件变更
- 更新：`opencode_config_manager_fluent.py`
- 新增：`OpenCodeConfigManager_v1.0.8.spec`

---

## [v1.0.7] - 2026-01-15 17:50
**版本代号**: 配置验证修复版

### 🆕 新增功能
- **配置格式验证器 (ConfigValidator)**：
  - 启动时自动检查配置文件格式是否符合 OpenCode 规范
  - 验证 Provider 必需字段 (npm, options, baseURL, apiKey）
  - 验证 Model 结构和 limit 字段类型
  - 验证 MCP 配置 (local/remote 类型对应字段）
  - 显示错误和警告列表 帮助用户定位问题

- **配置自动修复功能**：
  - 检测到问题时弹窗提示用户是否修复
  - 修复前自动备份原配置 (标签: `before-fix`）
  - 自动补全缺失的必需字段 (npm, options, models）
  - 规范化字段顺序 (npm → name → options → models）

### 🐛 Bug 修复
- **防御性类型检查**：修复配置异常时 `'str' object has no attribute 'get'` 崩溃
  - `_load_stats()` - 统计时检查 provider_data 类型
  - `ModelRegistry.refresh()` - 刷新模型列表时检查类型
  - `ProviderPage._load_data()` - 加载 Provider 时检查类型
  - `ModelPage._load_models()` - 加载模型时检查类型
  - `ModelDialog._load_model_data()` - 加载模型数据时检查类型

### 🔧 优化改进
- **SpinBox 显示优化**：设置最小宽度 改善 Win10 上的显示问题

### 📁 文件变更
- 更新：`opencode_config_manager_fluent.py`
- 新增：`OpenCodeConfigManager_v1.0.7.spec`

---

## [v1.0.6] - 2026-01-15 15:00
**版本代号**: MCP 类型修复版

### 🐛 Bug 修复
- **MCP 服务器 type 字段缺失**：修复添加/编辑 MCP 服务器时未写入 `type` 字段的问题
  - Local MCP 现在正确写入 `"type": "local"`
  - Remote MCP 现在正确写入 `"type": "remote"`

### 🔧 优化改进
- **GitHub Actions 构建配置更新**：
  - macOS 构建从 `macos-latest` 切换到 `macos-15-intel` (Intel 架构 PyQt5 有预编译 wheel）
  - 解决 ARM64 macOS 上 PyQt5 编译失败的问题

### 📁 文件变更
- 更新：`opencode_config_manager_fluent.py`
- 更新：`.github/workflows/build.yml`
- 更新：`.github/workflows/build_all.yml`
- 新增：`OpenCodeConfigManager_v1.0.6.spec`

---

## [v1.0.5] - 2026-01-14 19:50
**版本代号**: UI 优化增强版

### 🆕 新增功能
- **JSONC 注释丢失警告**：
  - 保存 JSONC 文件时自动检测是否包含注释
  - 首次保存时显示黄色警告 InfoBar 提示注释将丢失
  - 保存前自动创建备份 (标签: `jsonc-auto`）
  - `has_jsonc_comments()` 方法精确检测 `//` 和 `/* */` 注释

### 🐛 Bug 修复
- **预设模型 Variants 配置修复**：移除 Claude 系列预设中多余的 `variants` 内容 现在预设模型只在 `options` 中设置 thinking

### 🔧 优化改进
- **Options Tab 布局重构**：
  - 使用 `QScrollArea` 包裹内容 解决垂直空间不足问题
  - 键值输入改为单行紧凑布局 (键: [输入框] 值: [输入框]）
  - 表头高度优化为 32px 数据行高度 28px
  - 按钮高度统一为 32px
- **外部导入列表列宽调整**：
  - 第一列 (来源）：固定 180px
  - 第二列 (配置路径）：自动填充剩余空间
  - 第三列 (状态）：固定 100px
- **深色主题对比度增强**：
  - 滚动区域和内容容器设置透明背景
  - 卡片内边距优化 (8,6,8,6）

### 📁 文件变更
- 更新：`opencode_config_manager_fluent.py`
- 新增：`OpenCodeConfigManager_v1.0.5.spec`

---

## [v1.0.4] - 2026-01-14 13:57
**版本代号**: 备份目录自定义版

### 🆕 新增功能
- **备份目录手动选择**：
  - 首页新增备份目录浏览和重置按钮
  - `ConfigPaths.set_backup_dir()` 设置自定义备份路径
  - `ConfigPaths.get_backup_dir()` 支持自定义路径优先
  - `ConfigPaths.is_custom_path("backup")` 检测是否使用自定义路径

### 🔧 优化改进
- 文件重命名：`opencode_config_manager_fluent_v1.0.0.py` → `opencode_config_manager_fluent.py`
- 构建脚本同步更新文件名引用

### 📁 文件变更
- 重命名：`opencode_config_manager_fluent.py` (原 `opencode_config_manager_fluent_v1.0.0.py`)
- 更新：`build_windows.bat`
- 更新：`build_unix.sh`

---

## [v1.0.3] - 2026-01-14 13:00
**版本代号**: 跨平台增强版

### 🆕 新增功能
- **跨平台路径支持**：
  - Windows/Linux/macOS 统一使用 `~/.config/opencode/` 目录
  - `ConfigPaths.get_platform()` 获取当前平台
  - `ConfigPaths.get_config_base_dir()` 获取配置基础目录
- **完善构建脚本**：
  - `build_unix.sh`：Linux + macOS 统一构建脚本
  - `build_windows.bat`：Windows 构建脚本
  - Linux 无头服务器自动检测并使用 xvfb

### 🔧 优化改进
- 构建脚本自动检测 Python 版本
- 构建脚本自动安装缺失依赖
- 构建完成后显示文件大小

### 📁 文件变更
- 更新：`opencode_config_manager_fluent_v1.0.0.py`
- 更新：`build_unix.sh`
- 新增：`build_windows.bat`

---

## [v1.0.2] - 2026-01-14 12:30
**版本代号**: 自定义路径版

### 🆕 新增功能
- **首页配置路径手动选择**：
  - 点击文件夹图标可选择任意 JSON/JSONC 配置文件
  - 支持切换到项目级配置或其他自定义配置
  - 点击重置按钮可恢复默认路径
- **ConfigPaths 类增强**：
  - `set_opencode_config()` / `set_ohmyopencode_config()` 设置自定义路径
  - `is_custom_path()` 检查是否使用自定义路径
  - `reset_to_default()` 重置为默认路径
- **ConfigManager 增强**：
  - `is_jsonc_file()` 检测文件是否为 JSONC 格式

### 🔧 优化改进
- 配置路径标签动态更新
- 选择配置文件时自动验证 JSON/JSONC 格式
- 切换配置后自动重新加载并更新统计信息

### 📁 文件变更
- 更新：`opencode_config_manager_fluent_v1.0.0.py`
- 更新：`build_unix.sh`

---

## [v1.0.1] - 2026-01-14 12:00
**版本代号**: JSONC 支持版

### 🆕 新增功能
- **JSONC 格式支持**：配置文件支持带注释的 JSON 格式
  - 支持 `//` 单行注释
  - 支持 `/* */` 多行注释
  - 自动检测并解析 JSONC 文件
- **双扩展名检测**：自动检测 `.jsonc` 和 `.json` 配置文件
  - 优先加载 `.jsonc` 文件
  - 兼容现有 `.json` 配置

### 🔧 优化改进
- `ConfigPaths` 类重构 支持灵活的配置文件路径检测
- `ConfigManager.strip_jsonc_comments()` 方法：安全移除 JSONC 注释
- `build_unix.sh` 更新为 Fluent 版本构建脚本

### 📁 文件变更
- 更新：`opencode_config_manager_fluent_v1.0.0.py`
- 更新：`build_unix.sh` (Linux/macOS 构建脚本)

---

## [v1.0.0] - 2026-01-14 08:00
**版本代号**: Fluent Design 全面重构版

### 🎨 重大更新 - UI 框架全面重构
- **全新 UI 框架**：从 ttkbootstrap 迁移至 PyQt5 + QFluentWidgets
- **Fluent Design 风格**：采用微软 Fluent Design 设计语言
- **深浅色主题**：
  - 默认跟随系统主题自动切换
  - 支持手动切换深色/浅色模式
  - 使用 SystemThemeListener 实时监听系统主题变化
- **现代化卡片布局**：所有页面采用 SimpleCardWidget 卡片式设计
- **侧边栏导航**：FluentWindow 原生导航栏 图标 + 文字

### 🆕 新增功能
- **首页 Logo 展示**：显示 OCCM 品牌 Logo
- **主题切换按钮**：导航栏底部一键切换深浅色
- **窗口图标**：任务栏和标题栏显示自定义图标

### 📦 技术栈变更
- **移除依赖**：ttkbootstrap
- **新增依赖**：
  - PyQt5 >= 5.15.0
  - PyQt5-Fluent-Widgets >= 1.5.0

### 🔧 优化改进
- 所有对话框统一深色主题基类 (BaseDialog)
- 列表组件列宽优化 信息展示更清晰
- Tooltip 提示系统完整保留
- 配置保存逻辑优化

### 📁 文件变更
- 新增：`opencode_config_manager_fluent_v1.0.0.py` (Fluent 版本主程序)
- 新增：`assets/logo1.png` (首页 Logo)
- 新增：`assets/logo.png`, `assets/logo.ico` (品牌资源)
- 保留：`opencode_config_manager_v0.7.0.py` (ttkbootstrap 版本 兼容旧系统)

---

## [v0.8.0] - 2025-01-10
**版本代号**: Oh My OpenCode 支持版

### 🆕 新增功能
- **Oh My OpenCode 配置支持**：
  - Agent 管理 - 绑定 Provider/Model
  - Category 管理 - Temperature 滑块调节
  - 预设模板 - oracle、librarian、explore 等

---

## [v0.7.0] - 2025-01-09
**版本代号**: 主题系统增强版

### 🆕 新增功能
- 集成 ttkbootstrap 现代化 UI 框架
- 支持 10 种内置主题 (深色/浅色各 5 种）
  - 深色：Darkly、Superhero、Cyborg、Vapor、Solar
  - 浅色：Cosmo、Flatly、Litera、Minty、Pulse
- 实时主题切换 无需重启应用

---

## [v0.6.3 - v0.6.5] - 2025-01-08
**版本代号**: 版本检查增强版

### 🆕 新增功能
- GitHub 版本检查和更新提示
- 优化主题配色 (Fluent Design 风格）
- 实现实时主题切换

---

## [v0.6.0 - v0.6.2] - 2025-01-07
**版本代号**: MCP 与 Agent 配置版

### 🆕 新增功能
- MCP 服务器配置管理
  - Local 类型：配置启动命令和环境变量
  - Remote 类型：配置服务器 URL 和请求头
- OpenCode Agent 配置
  - 模式设置：primary / subagent / all
  - 参数配置：temperature、maxSteps、hidden、disable
  - 工具权限配置
- Skill/Rules 管理功能
- 上下文压缩配置

---

## [v0.5.0] - 2025-01-05
**版本代号**: 预设与备份版

### 🆕 新增功能
- 完善模型预设配置
- 备份恢复功能
- 外部导入重构

---

## [v0.4.0] - 2025-01-03
**版本代号**: 基础功能版

### 🆕 新增功能
- Provider 管理
- Model 管理
- 权限管理
- 外部导入 (Claude Code、Codex、Gemini）

---

## 版本命名规范

- **主版本号 (Major)**：重大架构变更、不兼容的 API 修改
- **次版本号 (Minor)**：新增功能、向后兼容的功能迭代
- **补丁版本号 (Patch)**：Bug 修复、小优化
