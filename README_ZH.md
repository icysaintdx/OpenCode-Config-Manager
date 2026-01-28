# OpenCode Config Manager

<p align="center">
  <img src="https://github.com/user-attachments/assets/fe4b0399-1cf8-4617-b45d-469cd656f8e0" alt="OCCM Logo" width="180" height="180">
</p>

<p align="center">
  <strong>🎨 可视化管理 OpenCode 和 Oh My OpenCode 配置文件的 GUI 工具</strong>
</p>

<p align="center">
  <a href="https://github.com/icysaintdx/OpenCode-Config-Manager/releases"><img src="https://img.shields.io/github/v/release/icysaintdx/OpenCode-Config-Manager?style=flat-square&color=blue" alt="Release"></a>
  <a href="https://github.com/icysaintdx/OpenCode-Config-Manager/blob/main/LICENSE"><img src="https://img.shields.io/github/license/icysaintdx/OpenCode-Config-Manager?style=flat-square" alt="License"></a>
  <a href="https://github.com/icysaintdx/OpenCode-Config-Manager/stargazers"><img src="https://img.shields.io/github/stars/icysaintdx/OpenCode-Config-Manager?style=flat-square" alt="Stars"></a>
  <a href="https://github.com/icysaintdx/OpenCode-Config-Manager/releases/latest"><img src="https://img.shields.io/github/downloads/icysaintdx/OpenCode-Config-Manager/total?style=flat-square&color=green" alt="Downloads"></a>
</p>

<p align="center">
  <a href="#-核心亮点">核心亮点</a> •
  <a href="#-功能特性">功能特性</a> •
  <a href="#-安装使用">安装使用</a> •
  <a href="#-配置说明">配置说明</a> •
  <a href="#-版本历史">版本历史</a>
</p>

<p align="center">
  <a href="README.md">English</a> | <a href="README_ZH.md">简体中文</a>
</p>

---

## ✨ 核心亮点

> **告别手写 JSON 一键配置 AI 编程助手！**

- 🎨 **Fluent Design 风格** - 微软设计语言 现代化卡片布局 深浅色主题自动切换
- 🚀 **零门槛上手** - 可视化操作 无需记忆 JSON 结构 小白也能轻松配置
- 🔧 **一站式管理** - Provider、Model、MCP、Agent、权限 全部搞定
- 🛡️ **智能配置验证** - 启动时自动检测配置问题 一键修复格式错误
- 📦 **跨平台支持** - Windows / macOS / Linux 三平台原生支持
- 🔄 **外部导入** - 一键导入 Claude Code、Codex、Gemini 等配置

---

## 🎯 v1.7.1 最新版本

### 🆕 新增功能
#### **Agent分组管理系统** ⭐⭐⭐
- **完整的Agent组合管理**：
  - 创建和管理Agent分组（OpenCode + Oh My OpenCode agents组合）
  - 一键应用预设分组到Agent配置页面
  - 支持自定义分组的创建、编辑、删除
- **6个预设分组模板**：
  - Minimal (最小配置): 1+1 agents
  - Standard (标准配置): 2+2 agents
  - Common (常用配置): 4+5 agents
  - Complete (完整配置): 7+7 agents
  - Frontend (前端开发): 3+4 agents
  - Backend (后端开发): 4+3 agents
- **技术实现**：
  - Pivot标签页UI切换OpenCode/OMO agents
  - 动态加载agent列表
  - Agent计数显示和tooltip
  - 移除必选agent限制

---

## 🎯 v1.7.0 版本回顾

### 🆕 新增功能
#### **Provider配置标准化** ⭐⭐⭐
- **完整的插件管理功能**：
  - 从GitHub URL安装插件
  - 一键卸载已安装插件
  - 浏览和搜索插件市场
  - 查看插件详情、版本、作者
- **技术实现**：
  - 集成GitHub API获取插件信息
  - 基于JSON的插件元数据管理
  - 支持插件名称、描述、作者的模糊搜索

#### **配置文件查看器** ⭐⭐
- **可视化配置查看**：
  - JSON语法高亮显示
  - 深色主题适配
  - 跨行括号高亮
  - 括号匹配提示
  - 一键编辑配置文件
- **位置**：首页 → 配置文件查看区域

#### **自动检测已配置的原生Provider** ⭐
- **环境变量检测**：
  - 自动检测12个官方Provider（Anthropic、OpenAI、Google、Azure等）
  - 通过"检测已配置"按钮一键检测
  - 以表格形式展示检测结果
- **位置**：原生Provider页面 → "检测已配置"按钮

### 🐛 Bug修复
- **翻译缺失问题** - 修复中文模式下部分字段显示英文
  - 添加缺失的翻译键（common.sdk、common.provider等）
  - 替换所有硬编码文本为tr()函数调用
- **Plugin页面启动错误** - 修复缺失QTableWidget和SearchLineEdit导入
- **macOS崩溃问题** - 修复导航栏展开时机问题
- **Mac安装脚本** - 支持多种目录结构
- **配置检测问题** - 添加@ai-sdk/openai-compatible到有效npm包列表
- **Skill市场问题** - 修复4个问题（选择逻辑、安装显示等）
- **智谱GLM配置** - 移除非标准modelListUrl字段

### 🎨 UI优化
- **Oh My OpenCode界面** - 使用Pivot标签页切换Agent和Category
- **导航菜单精简** - 合并相关功能页面，减少菜单项
- **配置查看器优化** - 深色主题、跨行括号高亮、括号匹配

---

### 📝 v1.5.0 功能回顾

#### **完整的多语言支持** ⭐⭐⭐
- **双语支持**：简体中文 + English
- **自动识别系统语言**
- **动态语言切换**：点击即切换，无需重启软件
- **翻译覆盖**：15个页面 + 17个对话框完整翻译

#### **国内AI平台支持** ⭐
- 在原生Provider页面新增5个国内平台
- 智谱 GLM、千问 Qwen、Kimi (月之暗面)、零一万物 Yi、MiniMax
- 所有平台使用 OpenAI 兼容 SDK
- 支持环境变量自动检测

---

### 📝 v1.4.5 功能回顾
- 这是最后一个单语言（仅中文）版本

### 📝 v1.4.4 功能回顾

#### 🆕 CLI 工具导出增强
- **支持导出到多个 CLI 工具** - Claude Code、Codex、Gemini
- **Claude Code 多模型配置** - 支持 4 个模型字段 (主模型、Haiku、Sonnet、Opus)
- **Codex/Gemini 双文件预览** - 双文件标签页预览 (auth.json + config.toml / .env + settings.json)
- **Base URL 临时修改** - 可临时修改用于导出 不影响原始配置
- **模型自定义输入** - 支持手动输入自定义模型名称
- **语法高亮与格式化** - JSON/TOML/ENV 格式语法高亮 + 格式化按钮
- **通用配置功能** - 写入通用配置复选框 + 编辑通用配置对话框

#### 🎨 UI 优化
- **导航菜单字体加粗** - 提升菜单可读性和视觉层次
- **CLI 导出页面标签页布局** - 采用主标签页设计更清晰直观
- **监控页面启动/停止切换** - 默认不启动 需手动点击启动按钮

### 📝 v1.4.3 功能回顾

#### 🆕 Oh My MCP 管理功能
- **可视化管理 Oh My OpenCode 自带的 MCP 服务器**
- 在 MCP 服务器页面新增 "Oh My MCP" 按钮
- 支持管理 websearch、context7、grep_app 三个服务器
- 支持启用/禁用操作
- 配置自动保存到 `oh-my-opencode.json`

### 📝 v1.4.2 功能回顾

#### 🆕 Skill 市场扩展
- **新增 12 个精选 Skills** - 开发工具、代码质量、测试、文档、安全、API、数据库等
- **远程市场链接** - 添加外部 Skill 商场链接（SkillsMP.com）
- **分类浏览** - 按功能分类展示 Skills
- **搜索功能** - 快速查找需要的 Skills

#### 🆕 安全扫描功能
- **代码安全扫描**：
  - 检测 9 种危险代码模式
  - 安全评分系统（0-100 分）
  - 风险等级可视化（安全/低/中/高/严重）
  - 详细问题列表（行号、风险等级、描述、代码）

### 📝 v1.4.1 功能回顾

#### 🐛 Bug 修复
- **修复 Skill 市场功能依赖缺失问题** - 在 `requirements.txt` 中添加 `requests>=2.25.0`

### 📝 v1.4.0 功能回顾

#### 🆕 Skill 市场功能
- **内置 Skill 市场**：
  - 8 个精选 Skills（开发工具、代码质量、测试、文档、安全、API、数据库）
  - 分类浏览 + 搜索功能
  - 一键安装到指定位置

### 📝 v1.3.0 功能回顾

#### **Skills 安装与更新功能** ⭐
- **从 GitHub 安装 Skills**：
  - 支持 GitHub shorthand：`user/repo`（如 `vercel-labs/git-release`）
  - 支持完整 URL：`https://github.com/user/repo`
  - 自动下载、解压、解析 SKILL.md
  - 支持安装到 4 个位置：OpenCode 全局/项目、Claude 全局/项目

- **从本地导入 Skills**：
  - 支持从本地路径导入：`./my-skill` 或 `/path/to/skill`
  - 自动验证 SKILL.md 格式

- **更新检测与批量更新**：
  - 一键检查所有已安装 Skills 的更新
  - 通过 GitHub API 对比 commit hash
  - 表格显示更新状态（有更新/最新/本地）
  - 支持选择性批量更新

- **元数据管理**：
  - 自动生成 `.skill-meta.json` 记录安装信息
  - 记录来源、版本、安装时间等

### 📝 v1.2.0 功能回顾

#### 🆕 新增功能
- **Oh My MCP 管理功能** - 在 MCP 服务器页面新增 "Oh My MCP" 按钮，可视化管理 Oh My OpenCode 自带的 3 个 MCP 服务器（websearch、context7、grep_app），支持启用/禁用操作，配置自动保存到 `oh-my-opencode.json`

### 📝 v1.1.9 功能回顾

#### 🐛 Bug 修复
- **修复 MCP 配置不符合 OpenCode 官方规范导致的启动失败** - 当使用软件添加 MCP 后，OpenCode 启动报错 `Invalid input mcp.@modelcontextprotocol/server-sequential-thinking`。现已修复：
  - MCP 键名规范化：使用简化键名（如 `sequential-thinking`）而不是包含特殊字符的 npm 包名
  - 移除非标准字段：`description`、`tags`、`homepage`、`docs` 等字段不再写入配置文件，仅用于 UI 显示
  - 完全符合 OpenCode 官方 MCP 配置规范

### 📝 v1.1.8 功能回顾

#### 🐛 Bug 修复
- **修复配置文件格式异常导致的启动崩溃问题** - 当配置文件中 `permission`、`mcp`、`agent` 等字段为非字典类型时，程序启动会报错 `AttributeError: 'str' object has no attribute 'items'`，现已添加类型检查，确保程序健壮性

### 📝 v1.1.7 功能回顾

#### 🆕 CLI 工具导出功能
- **Claude Code 多模型配置** - 支持 4 个模型字段 (主模型、Haiku、Sonnet、Opus)
- **Codex/Gemini 双文件预览** - 双文件标签页预览 (auth.json + config.toml / .env + settings.json)
- **Base URL 临时修改** - 可临时修改用于导出 不影响原始配置
- **模型自定义输入** - 支持手动输入自定义模型名称
- **语法高亮与格式化** - JSON/TOML/ENV 格式语法高亮 + 格式化按钮
- **通用配置功能** - 写入通用配置复选框 + 编辑通用配置对话框

### 🎨 UI 优化
- **导航菜单字体加粗** - 提升菜单可读性和视觉层次
- **CLI 导出页面标签页布局** - 采用主标签页设计更清晰直观
- **监控页面启动/停止切换** - 默认不启动 需手动点击启动按钮

### 🐛 Bug 修复
- 模型留空处理优化
- 外部导入功能修复

---

## 🎨 功能特性

### Provider 管理
- ✅ 添加/编辑/删除自定义 API 提供商
- ✅ 支持多种 SDK：`@ai-sdk/anthropic`、`@ai-sdk/openai`、`@ai-sdk/google`、`@ai-sdk/azure`
- ✅ API 密钥安全显示/隐藏
- ✅ SDK 兼容性智能提示

### Model 管理
- ✅ **预设常用模型快速选择** - Claude、GPT-5、Gemini 系列一键添加
- ✅ **完整预设配置** - 选择预设模型自动填充 options 和 variants
- ✅ **Thinking 模式支持**：
  - Claude: `thinking.type`, `thinking.budgetTokens`
  - OpenAI: `reasoningEffort` (high/medium/low/xhigh)
  - Gemini: `thinkingConfig.thinkingBudget`

### MCP 服务器管理
- ✅ **Local 类型** - 配置启动命令和环境变量
- ✅ **Remote 类型** - 配置服务器 URL 和请求头
- ✅ 支持启用/禁用、超时设置
- ✅ 预设常用 MCP 服务器 (Context7、Sentry 等）

### OpenCode Agent 配置
- ✅ **模式设置** - primary / subagent / all
- ✅ **参数配置** - temperature、maxSteps、hidden、disable
- ✅ **工具权限** - 配置 Agent 可用的工具
- ✅ **预设模板** - build、plan、explore、code-reviewer 等

### Oh My OpenCode 支持
- ✅ Agent 管理 - 绑定 Provider/Model
- ✅ Category 管理 - Temperature 滑块调节
- ✅ 预设模板 - oracle、librarian、explore 等

### 智能功能
- ✅ **配置验证器** - 启动时自动检测格式问题
- ✅ **自动修复** - 一键修复缺失字段和格式错误
- ✅ **JSONC 支持** - 完美兼容带注释的配置文件
- ✅ **外部导入** - 支持 Claude Code、Codex、Gemini、cc-switch
- ✅ **备份恢复** - 多版本备份管理 一键恢复

### 其他特性
- ✅ **GitHub 版本检查** - 自动检测最新版本
- ✅ **深浅色主题** - 跟随系统自动切换
- ✅ **全局 Tooltip** - 鼠标悬停显示参数说明
- ✅ **统一保存逻辑** - 保存修改直接写入文件

---

## 📦 安装使用

### 方式一：下载预编译版本 (推荐）

从 [Releases](https://github.com/icysaintdx/OpenCode-Config-Manager/releases) 下载对应平台的可执行文件：

| 平台 | 文件 | 说明 |
|------|------|------|
| Windows | `OpenCodeConfigManager_windows.exe` | 单文件版 双击运行 |
| macOS | `OpenCode-Config-Manager-MacOS.dmg` | DMG 镜像 拖入应用程序 |
| Linux | `OpenCode-Config-Manager-Linux-x64.tar.gz` | 解压后运行 |

### 方式二：从源码运行

```bash
# 克隆仓库
git clone https://github.com/icysaintdx/OpenCode-Config-Manager.git
cd OpenCode-Config-Manager

# 安装依赖
pip install PyQt5 PyQt-Fluent-Widgets

# 运行
python opencode_config_manager_fluent.py
```

**系统要求**：Python 3.8+

---

## ⚙️ 配置说明

### 配置文件位置

| 配置文件 | 路径 |
|---------|------|
| OpenCode | `~/.config/opencode/opencode.json` |
| Oh My OpenCode | `~/.config/opencode/oh-my-opencode.json` |
| 备份目录 | `~/.config/opencode/backups/` |

### 配置优先级 (从高到低）

1. **远程配置** - 通过 `.well-known/opencode` 获取
2. **全局配置** - `~/.config/opencode/opencode.json`
3. **自定义配置** - `OPENCODE_CONFIG` 环境变量指定
4. **项目配置** - `<项目>/opencode.json`
5. **.opencode 目录** - `<项目>/.opencode/config.json`

### Options vs Variants

根据 [OpenCode 官方文档](https://opencode.ai/docs/models/)：

- **options**: 模型的默认配置参数 每次调用都会使用
- **variants**: 可切换的变体配置 通过 `variant_cycle` 快捷键切换

```json
{
  "provider": {
    "anthropic": {
      "models": {
        "claude-sonnet-4-5-20250929": {
          "options": {
            "thinking": {"type": "enabled", "budgetTokens": 16000}
          },
          "variants": {
            "high": {"thinking": {"type": "enabled", "budgetTokens": 32000}},
            "max": {"thinking": {"type": "enabled", "budgetTokens": 64000}}
          }
        }
      }
    }
  }
}
```

---

## 📋 版本历史

### 最新版本

**[v1.7.1](https://github.com/icysaintdx/OpenCode-Config-Manager/releases/tag/v1.7.1)** - 2026-01-28
- 🎯 Agent分组管理系统 - 创建和管理Agent组合，6个预设模板
- 🎨 Pivot标签页UI - 切换OpenCode/OMO agents
- 🔢 Agent计数显示 - 显示已选择/总数，tooltip显示详情
- 🐛 Bug修复 - 对话框布局优化、OMO描述显示修复

**[v1.7.0](https://github.com/icysaintdx/OpenCode-Config-Manager/releases/tag/v1.7.0)** - 2026-01-28
- 🔧 Provider配置标准化 - auth.json格式修正，Provider命名修正
- 🆕 Z.AI Provider支持 - 新增zai和zai-coding-plan两个Provider
- 📝 技术文档 - 新增5篇Provider配置相关技术文档

**[v1.6.0](https://github.com/icysaintdx/OpenCode-Config-Manager/releases/tag/v1.6.0)** - 2026-01-27
- 🔌 Plugin插件管理系统 - 完整的插件安装/卸载/市场功能
- 📄 配置文件查看器 - JSON语法高亮、深色主题、括号匹配
- 🔍 自动检测原生Provider - 环境变量检测12个官方Provider
- 🐛 Bug修复 - 修复翻译问题、Plugin页面启动错误、macOS崩溃
- 🎨 UI优化 - Oh My OpenCode使用Pivot标签页、导航菜单精简

**[v1.5.0](https://github.com/icysaintdx/OpenCode-Config-Manager/releases/tag/v1.5.0)** - 2026-01-24
- 🌐 多语言支持 - 简体中文 + English，动态切换无需重启
- 🇨🇳 国内AI平台支持 - 新增智谱GLM、千问Qwen、Kimi、零一万物Yi、MiniMax
- 🐛 Bug修复 - 修复Win10启动报错、语言切换页面错位
- 🎨 UI优化 - 导航栏宽度200px，菜单默认展开

**[v1.4.0](https://github.com/icysaintdx/OpenCode-Config-Manager/releases/tag/v1.4.0)** - 2026-01-20
- ⭐ Skill 市场功能 - 内置 12 个精选 Skills，分类浏览 + 搜索
- 🛡️ 安全扫描功能 - 检测 9 种危险代码模式，安全评分系统
- 🎨 UI 改进 - 新增市场按钮和安全扫描按钮

**[v1.3.0](https://github.com/icysaintdx/OpenCode-Config-Manager/releases/tag/v1.3.0)** - 2026-01-20
- 📦 Skills 安装功能 - 支持从 GitHub 和本地安装 Skills
- 🔄 Skills 更新功能 - 一键检查更新，批量更新支持
- 📝 元数据管理 - 自动生成 `.skill-meta.json` 记录安装信息

**[v1.2.0](https://github.com/icysaintdx/OpenCode-Config-Manager/releases/tag/v1.2.0)** - 2026-01-20
- 🔧 Oh My MCP 管理 - 可视化管理 Oh My OpenCode 自带的 3 个 MCP 服务器

**[v1.1.9](https://github.com/icysaintdx/OpenCode-Config-Manager/releases/tag/v1.1.9)** - 2026-01-20
- 🐛 修复 MCP 配置不符合 OpenCode 官方规范导致的启动失败

**[v1.1.8](https://github.com/icysaintdx/OpenCode-Config-Manager/releases/tag/v1.1.8)** - 2026-01-20
- 🐛 修复配置文件格式异常导致的启动崩溃问题

**[v1.1.7](https://github.com/icysaintdx/OpenCode-Config-Manager/releases/tag/v1.1.7)** - 2026-01-20
- 🆕 CLI 工具导出功能 - Claude Code、Codex、Gemini 配置导出
- 🎨 UI 优化 - 导航菜单字体加粗，CLI 导出页面标签页布局

**[v1.1.6](https://github.com/icysaintdx/OpenCode-Config-Manager/releases/tag/v1.1.6)** - 2026-01-19
- 🆕 原生 Provider 支持 - 管理 12 个 OpenCode 官方 AI 服务提供商
- 🔐 AuthManager 认证管理器 - 独立的 auth.json 文件管理

**[v1.0.0](https://github.com/icysaintdx/OpenCode-Config-Manager/releases/tag/v1.0.0)** - 2026-01-14
- 🎨 Fluent Design 全面重构 - 从 ttkbootstrap 迁移至 PyQt5 + QFluentWidgets
- 🌓 深浅色主题 - 跟随系统自动切换

[查看完整更新日志 →](CHANGELOG.md) | [View English Changelog →](CHANGELOG_EN.md)

---

---

## 🔗 相关项目

- [OpenCode](https://github.com/anomalyco/opencode) - AI 编程助手
- [Oh My OpenCode](https://github.com/code-yeongyu/oh-my-opencode) - OpenCode 增强插件

---

## 📄 许可证

MIT License

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/icysaintdx">IcySaint</a>
</p>
