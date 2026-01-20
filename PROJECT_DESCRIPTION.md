# OpenCode Config Manager - 项目介绍 / Project Description

## 中文介绍

### 项目概述

OpenCode Config Manager (OCCM) 是一款专为 OpenCode 和 Oh My OpenCode 设计的可视化配置管理工具。它采用 Microsoft Fluent Design 设计语言，提供直观、现代化的图形界面，让用户无需手动编辑 JSON 配置文件即可轻松管理 AI 编程助手的各项配置。

### 核心特性

- **🎨 Fluent Design 风格界面** - 采用微软设计语言，现代化卡片布局，支持深浅色主题自动切换
- **🚀 零门槛上手** - 完全可视化操作，无需记忆复杂的 JSON 结构，小白用户也能轻松配置
- **🔧 一站式管理** - 统一管理 Provider、Model、MCP 服务器、Agent、权限等所有配置项
- **🛡️ 智能配置验证** - 启动时自动检测配置问题，一键修复格式错误，确保配置符合 OpenCode 规范
- **📦 跨平台支持** - 原生支持 Windows、macOS、Linux 三大平台
- **🔄 外部导入** - 一键导入 Claude Code、Codex、Gemini、cc-switch 等工具的配置

### 主要功能模块

#### 1. Provider 管理
- 添加、编辑、删除自定义 API 提供商
- 支持多种 SDK：Anthropic、OpenAI、Google、Azure
- API 密钥安全显示/隐藏
- SDK 兼容性智能提示

#### 2. Model 管理
- 预设常用模型快速选择（Claude、GPT、Gemini 系列）
- 完整的 options 和 variants 配置
- Thinking 模式支持（Claude、OpenAI、Gemini）
- 模型可用性监控

#### 3. MCP 服务器管理
- Local 和 Remote 两种类型支持
- 启动命令、环境变量、URL、请求头配置
- 预设常用 MCP 服务器模板
- Oh My MCP 可视化管理

#### 4. Skills 管理
- 内置 Skill 市场，20+ 精选 Skills
- 从 GitHub 或本地安装 Skills
- 一键检查更新，批量更新支持
- 安全扫描功能，检测危险代码模式

#### 5. Agent 配置
- 模式设置（primary / subagent / all）
- 参数配置（temperature、maxSteps 等）
- 工具权限管理
- 预设模板（build、plan、explore 等）

#### 6. 智能功能
- 配置验证器 - 自动检测格式问题
- 自动修复 - 一键修复缺失字段和格式错误
- JSONC 支持 - 完美兼容带注释的配置文件
- 备份恢复 - 多版本备份管理，一键恢复

### 技术栈

- **UI 框架**: PyQt5 + QFluentWidgets
- **设计语言**: Microsoft Fluent Design
- **编程语言**: Python 3.8+
- **配置格式**: JSON / JSONC

### 适用场景

- OpenCode 用户需要可视化管理配置
- 需要频繁切换不同 AI 模型和 Provider
- 需要管理多个 MCP 服务器
- 需要从其他 AI 工具迁移配置
- 需要团队协作共享配置

### 项目链接

- **GitHub**: https://github.com/icysaintdx/OpenCode-Config-Manager
- **最新版本**: v1.4.0
- **许可证**: MIT License

---

## English Description

### Project Overview

OpenCode Config Manager (OCCM) is a visual configuration management tool specifically designed for OpenCode and Oh My OpenCode. It adopts Microsoft Fluent Design language, providing an intuitive and modern graphical interface that allows users to easily manage various configurations of AI coding assistants without manually editing JSON configuration files.

### Core Features

- **🎨 Fluent Design Interface** - Adopts Microsoft design language, modern card layout, supports automatic dark/light theme switching
- **🚀 Zero Learning Curve** - Fully visual operations, no need to memorize complex JSON structures, easy for beginners
- **🔧 All-in-One Management** - Unified management of Provider, Model, MCP servers, Agent, permissions, and all configuration items
- **🛡️ Smart Configuration Validation** - Auto-detect configuration issues on startup, one-click fix format errors, ensure compliance with OpenCode specifications
- **📦 Cross-Platform Support** - Native support for Windows, macOS, and Linux
- **🔄 External Import** - One-click import configurations from Claude Code, Codex, Gemini, cc-switch, and other tools

### Main Function Modules

#### 1. Provider Management
- Add, edit, delete custom API providers
- Support multiple SDKs: Anthropic, OpenAI, Google, Azure
- API key secure show/hide
- SDK compatibility smart hints

#### 2. Model Management
- Preset common models quick select (Claude, GPT, Gemini series)
- Complete options and variants configuration
- Thinking mode support (Claude, OpenAI, Gemini)
- Model availability monitoring

#### 3. MCP Server Management
- Local and Remote type support
- Startup command, environment variables, URL, request headers configuration
- Preset common MCP server templates
- Oh My MCP visual management

#### 4. Skills Management
- Built-in Skill marketplace, 20+ curated Skills
- Install Skills from GitHub or local
- One-click check updates, batch update support
- Security scanning feature, detect dangerous code patterns

#### 5. Agent Configuration
- Mode settings (primary / subagent / all)
- Parameter configuration (temperature, maxSteps, etc.)
- Tool permission management
- Preset templates (build, plan, explore, etc.)

#### 6. Smart Features
- Config validator - Auto-detect format issues
- Auto fix - One-click fix missing fields and format errors
- JSONC support - Perfect compatibility with commented config files
- Backup & restore - Multi-version backup management, one-click restore

### Tech Stack

- **UI Framework**: PyQt5 + QFluentWidgets
- **Design Language**: Microsoft Fluent Design
- **Programming Language**: Python 3.8+
- **Config Format**: JSON / JSONC

### Use Cases

- OpenCode users need visual configuration management
- Need to frequently switch between different AI models and Providers
- Need to manage multiple MCP servers
- Need to migrate configurations from other AI tools
- Need team collaboration to share configurations

### Project Links

- **GitHub**: https://github.com/icysaintdx/OpenCode-Config-Manager
- **Latest Version**: v1.4.0
- **License**: MIT License

---

## 快速开始 / Quick Start

### 安装 / Installation

#### 方式一：下载预编译版本（推荐）/ Method 1: Download Pre-compiled Version (Recommended)

从 [Releases](https://github.com/icysaintdx/OpenCode-Config-Manager/releases) 下载对应平台的可执行文件 / Download the executable file for your platform from Releases:

- **Windows**: `OpenCodeConfigManager_windows.exe`
- **macOS**: `OpenCode-Config-Manager-MacOS.dmg`
- **Linux**: `OpenCode-Config-Manager-Linux-x64.tar.gz`

#### 方式二：从源码运行 / Method 2: Run from Source

```bash
# 克隆仓库 / Clone repository
git clone https://github.com/icysaintdx/OpenCode-Config-Manager.git
cd OpenCode-Config-Manager

# 安装依赖 / Install dependencies
pip install PyQt5 PyQt-Fluent-Widgets

# 运行 / Run
python opencode_config_manager_fluent.py
```

### 系统要求 / System Requirements

- Python 3.8+
- Windows 10/11, macOS 10.14+, or Linux (Ubuntu 20.04+)

---

## 贡献 / Contributing

欢迎提交 Issue 和 Pull Request！/ Issues and Pull Requests are welcome!

1. Fork 本仓库 / Fork this repository
2. 创建特性分支 / Create feature branch (`git checkout -b feature/AmazingFeature`)
3. 提交更改 / Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 / Push to branch (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request / Submit Pull Request

---

## 许可证 / License

MIT License

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/icysaintdx">IcySaint</a>
</p>
