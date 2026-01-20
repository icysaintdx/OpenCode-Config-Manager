## [v1.4.0] - 2026-01-20 18:00
**版本代号**: Skills 市场与安全扫描版

### 🆕 新增功能 (P2)
#### **Skill 市场功能** ⭐
- **内置 Skill 市场**：
  - 扩展 Skill 市场 - 新增 12 个精选 Skills
  - 从 8 个扩展到 20 个
  - 新增 3 个分类（UI/UX、DevOps、性能优化）
  - 覆盖前端、后端、测试、部署、优化全场景
  ---------------------------------------------------------------
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