# OpenCode Config Manager

<p align="center">
  <img src="https://github.com/user-attachments/assets/fe4b0399-1cf8-4617-b45d-469cd656f8e0" alt="OCCM Logo" width="180" height="180">
</p>

<p align="center">
  <strong>🎨 Visual GUI Tool for Managing OpenCode and Oh My OpenCode Configuration Files</strong>
</p>

<p align="center">
  <a href="https://github.com/icysaintdx/OpenCode-Config-Manager/releases"><img src="https://img.shields.io/github/v/release/icysaintdx/OpenCode-Config-Manager?style=flat-square&color=blue" alt="Release"></a>
  <a href="https://github.com/icysaintdx/OpenCode-Config-Manager/blob/main/LICENSE"><img src="https://img.shields.io/github/license/icysaintdx/OpenCode-Config-Manager?style=flat-square" alt="License"></a>
  <a href="https://github.com/icysaintdx/OpenCode-Config-Manager/stargazers"><img src="https://img.shields.io/github/stars/icysaintdx/OpenCode-Config-Manager?style=flat-square" alt="Stars"></a>
  <a href="https://github.com/icysaintdx/OpenCode-Config-Manager/releases/latest"><img src="https://img.shields.io/github/downloads/icysaintdx/OpenCode-Config-Manager/total?style=flat-square&color=green" alt="Downloads"></a>
</p>

<p align="center">
  <a href="#-highlights">Highlights</a> •
  <a href="#-features">Features</a> •
  <a href="#-installation">Installation</a> •
  <a href="#-configuration">Configuration</a> •
  <a href="#-version-history">Version History</a>
</p>

<p align="center">
  <a href="README.md">简体中文</a> | <a href="README_EN.md">English</a>
</p>

---

## ✨ Highlights

> **Say goodbye to manual JSON editing - Configure your AI coding assistant with one click!**

- 🎨 **Fluent Design Style** - Microsoft design language, modern card layout, automatic dark/light theme switching
- 🚀 **Zero Learning Curve** - Visual operations, no need to memorize JSON structure, easy for beginners
- 🔧 **All-in-One Management** - Provider, Model, MCP, Agent, Permissions - all in one place
- 🛡️ **Smart Configuration Validation** - Auto-detect configuration issues on startup, one-click format error fixes
- 📦 **Cross-Platform Support** - Native support for Windows / macOS / Linux
- 🔄 **External Import** - One-click import from Claude Code, Codex, Gemini, and more

---

## 🎯 v1.4.0 Latest Version

### 🆕 New Features
#### **Skill Marketplace** ⭐
- **Built-in Skill Marketplace**:
  - 8 curated Skills (Dev Tools, Code Quality, Testing, Documentation, Security, API, Database)
  - Browse by category + search functionality
  - One-click installation to specified location

#### **Security Scanning** ⭐
- **Code Security Scanning**:
  - Detects 9 types of dangerous code patterns
  - Security scoring system (0-100 points)
  - Risk level visualization (Safe/Low/Medium/High/Critical)
  - Detailed issue list (line number, risk level, description, code)

### 📝 v1.3.0 Feature Recap

#### **Skills Installation & Update** ⭐
- **Install Skills from GitHub**:
  - Support GitHub shorthand: `user/repo` (e.g., `vercel-labs/git-release`)
  - Support full URL: `https://github.com/user/repo`
  - Auto download, extract, parse SKILL.md
  - Install to 4 locations: OpenCode global/project, Claude global/project

- **Import Skills from Local**:
  - Support local path import: `./my-skill` or `/path/to/skill`
  - Auto validate SKILL.md format

- **Update Detection & Batch Update**:
  - One-click check updates for all installed Skills
  - Compare commit hash via GitHub API
  - Table display update status (Has Update/Latest/Local)
  - Support selective batch update

- **Metadata Management**:
  - Auto generate `.skill-meta.json` to record installation info
  - Record source, version, installation time, etc.

### 📝 v1.2.0 Feature Recap

#### 🆕 New Features
- **Oh My MCP Management** - New "Oh My MCP" button in MCP Server page, visually manage 3 built-in MCP servers (websearch, context7, grep_app) from Oh My OpenCode, support enable/disable operations, config auto-saved to `oh-my-opencode.json`

### 📝 v1.1.9 Feature Recap

#### 🐛 Bug Fixes
- **Fixed MCP config non-compliance causing OpenCode startup failure** - When adding MCP via software, OpenCode startup error `Invalid input mcp.@modelcontextprotocol/server-sequential-thinking`. Now fixed:
  - MCP key name standardization: Use simplified key names (e.g., `sequential-thinking`) instead of npm package names with special characters
  - Remove non-standard fields: `description`, `tags`, `homepage`, `docs` no longer written to config file, only used for UI display
  - Fully compliant with OpenCode official MCP config specification

### 📝 v1.1.8 Feature Recap

#### 🐛 Bug Fixes
- **Fixed startup crash due to abnormal config file format** - When `permission`, `mcp`, `agent` fields are non-dict types in config file, program startup error `AttributeError: 'str' object has no attribute 'items'`, now added type checking to ensure program robustness

### 📝 v1.1.7 Feature Recap

#### 🆕 CLI Tool Export
- **Claude Code Multi-Model Config** - Support 4 model fields (main model, Haiku, Sonnet, Opus)
- **Codex/Gemini Dual-File Preview** - Dual-file tab preview (auth.json + config.toml / .env + settings.json)
- **Base URL Temporary Modification** - Can temporarily modify for export without affecting original config
- **Custom Model Input** - Support manual input of custom model names
- **Syntax Highlighting & Formatting** - JSON/TOML/ENV format syntax highlighting + format button
- **Common Config Feature** - Write common config checkbox + edit common config dialog

### 🎨 UI Improvements
- **Navigation Menu Font Bold** - Improve menu readability and visual hierarchy
- **CLI Export Page Tab Layout** - Adopt main tab design for clearer intuition
- **Monitor Page Start/Stop Toggle** - Default not started, need manual start button click

### 🐛 Bug Fixes
- Model empty handling optimization
- External import feature fixes

---

## 🎨 Features

### Provider Management
- ✅ Add/Edit/Delete custom API providers
- ✅ Support multiple SDKs: `@ai-sdk/anthropic`, `@ai-sdk/openai`, `@ai-sdk/google`, `@ai-sdk/azure`
- ✅ API key secure show/hide
- ✅ SDK compatibility smart hints

### Model Management
- ✅ **Preset Common Models Quick Select** - Claude, GPT-5, Gemini series one-click add
- ✅ **Complete Preset Config** - Select preset model auto-fill options and variants
- ✅ **Thinking Mode Support**:
  - Claude: `thinking.type`, `thinking.budgetTokens`
  - OpenAI: `reasoningEffort` (high/medium/low/xhigh)
  - Gemini: `thinkingConfig.thinkingBudget`

### MCP Server Management
- ✅ **Local Type** - Configure startup command and environment variables
- ✅ **Remote Type** - Configure server URL and request headers
- ✅ Support enable/disable, timeout settings
- ✅ Preset common MCP servers (Context7, Sentry, etc.)

### OpenCode Agent Configuration
- ✅ **Mode Settings** - primary / subagent / all
- ✅ **Parameter Config** - temperature, maxSteps, hidden, disable
- ✅ **Tool Permissions** - Configure available tools for Agent
- ✅ **Preset Templates** - build, plan, explore, code-reviewer, etc.

### Oh My OpenCode Support
- ✅ Agent Management - Bind Provider/Model
- ✅ Category Management - Temperature slider adjustment
- ✅ Preset Templates - oracle, librarian, explore, etc.

### Smart Features
- ✅ **Config Validator** - Auto-detect format issues on startup
- ✅ **Auto Fix** - One-click fix missing fields and format errors
- ✅ **JSONC Support** - Perfect compatibility with commented config files
- ✅ **External Import** - Support Claude Code, Codex, Gemini, cc-switch
- ✅ **Backup & Restore** - Multi-version backup management, one-click restore

### Other Features
- ✅ **GitHub Version Check** - Auto-detect latest version
- ✅ **Dark/Light Theme** - Auto-switch following system
- ✅ **Global Tooltip** - Mouse hover shows parameter descriptions
- ✅ **Unified Save Logic** - Save changes directly write to file

---

## 📦 Installation

### Method 1: Download Pre-compiled Version (Recommended)

Download the executable file for your platform from [Releases](https://github.com/icysaintdx/OpenCode-Config-Manager/releases):

| Platform | File | Description |
|----------|------|-------------|
| Windows | `OpenCodeConfigManager_windows.exe` | Single file version, double-click to run |
| macOS | `OpenCode-Config-Manager-MacOS.dmg` | DMG image, drag to Applications |
| Linux | `OpenCode-Config-Manager-Linux-x64.tar.gz` | Extract and run |

### Method 2: Run from Source

```bash
# Clone repository
git clone https://github.com/icysaintdx/OpenCode-Config-Manager.git
cd OpenCode-Config-Manager

# Install dependencies
pip install PyQt5 PyQt-Fluent-Widgets

# Run
python opencode_config_manager_fluent.py
```

**System Requirements**: Python 3.8+

---

## ⚙️ Configuration

### Config File Locations

| Config File | Path |
|-------------|------|
| OpenCode | `~/.config/opencode/opencode.json` |
| Oh My OpenCode | `~/.config/opencode/oh-my-opencode.json` |
| Backup Directory | `~/.config/opencode/backups/` |

### Config Priority (High to Low)

1. **Remote Config** - Retrieved via `.well-known/opencode`
2. **Global Config** - `~/.config/opencode/opencode.json`
3. **Custom Config** - Specified by `OPENCODE_CONFIG` environment variable
4. **Project Config** - `<project>/opencode.json`
5. **.opencode Directory** - `<project>/.opencode/config.json`

### Options vs Variants

According to [OpenCode Official Documentation](https://opencode.ai/docs/models/):

- **options**: Default config parameters for the model, used in every call
- **variants**: Switchable variant configs, toggle via `variant_cycle` shortcut

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

## 📋 Version History

### Latest Release

**[v1.4.0](https://github.com/icysaintdx/OpenCode-Config-Manager/releases/tag/v1.4.0)** - 2026-01-20
- ⭐ Skill Marketplace - Built-in 20 curated Skills, browse by category + search
- 🛡️ Security Scanning - Detect 9 dangerous code patterns, security scoring system
- 🎨 UI Improvements - New marketplace button and security scan button

**[v1.3.0](https://github.com/icysaintdx/OpenCode-Config-Manager/releases/tag/v1.3.0)** - 2026-01-20
- 📦 Skills Installation - Support install Skills from GitHub and local
- 🔄 Skills Update - One-click check updates, batch update support
- 📝 Metadata Management - Auto-generate `.skill-meta.json` to record installation info

**[v1.2.0](https://github.com/icysaintdx/OpenCode-Config-Manager/releases/tag/v1.2.0)** - 2026-01-20
- 🔧 Oh My MCP Management - Visually manage 3 built-in MCP servers from Oh My OpenCode

**[v1.1.9](https://github.com/icysaintdx/OpenCode-Config-Manager/releases/tag/v1.1.9)** - 2026-01-20
- 🐛 Fixed MCP config non-compliance causing OpenCode startup failure

**[v1.1.8](https://github.com/icysaintdx/OpenCode-Config-Manager/releases/tag/v1.1.8)** - 2026-01-20
- 🐛 Fixed startup crash due to abnormal config file format

**[v1.1.7](https://github.com/icysaintdx/OpenCode-Config-Manager/releases/tag/v1.1.7)** - 2026-01-20
- 🆕 CLI Tool Export - Claude Code, Codex, Gemini config export
- 🎨 UI Optimization - Navigation menu font bold, CLI export page tab layout

**[v1.1.6](https://github.com/icysaintdx/OpenCode-Config-Manager/releases/tag/v1.1.6)** - 2026-01-19
- 🆕 Native Provider Support - Manage 12 OpenCode official AI service providers
- 🔐 AuthManager - Independent auth.json file management

**[v1.0.0](https://github.com/icysaintdx/OpenCode-Config-Manager/releases/tag/v1.0.0)** - 2026-01-14
- 🎨 Fluent Design Complete Refactor - Migrated from ttkbootstrap to PyQt5 + QFluentWidgets
- 🌓 Dark/Light Theme - Auto-switch following system

[View Full Changelog →](CHANGELOG_EN.md) | [查看中文更新日志 →](CHANGELOG.md)

---

---

## 🔗 Related Projects

- [OpenCode](https://github.com/anomalyco/opencode) - AI Coding Assistant
- [Oh My OpenCode](https://github.com/code-yeongyu/oh-my-opencode) - OpenCode Enhancement Plugin

---

## 📄 License

MIT License

---

## 🤝 Contributing

Issues and Pull Requests are welcome!

1. Fork this repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Submit Pull Request

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/icysaintdx">IcySaint</a>
</p>
