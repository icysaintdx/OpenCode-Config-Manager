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
</p>

<p align="center">
  <a href="#-核心亮点">核心亮点</a> •
  <a href="#-功能特性">功能特性</a> •
  <a href="#-安装使用">安装使用</a> •
  <a href="#-配置说明">配置说明</a> •
  <a href="#-更新日志">更新日志</a>
</p>

---

## ✨ 核心亮点

> **告别手写 JSON，一键配置 AI 编程助手！**

- 🎨 **Fluent Design 风格** - 微软设计语言，现代化卡片布局，深浅色主题自动切换
- 🚀 **零门槛上手** - 可视化操作，无需记忆 JSON 结构，小白也能轻松配置
- 🔧 **一站式管理** - Provider、Model、MCP、Agent、权限，全部搞定
- 🛡️ **智能配置验证** - 启动时自动检测配置问题，一键修复格式错误
- 📦 **跨平台支持** - Windows / macOS / Linux 三平台原生支持
- 🔄 **外部导入** - 一键导入 Claude Code、Codex、Gemini 等配置

---

## 🎯 v1.0.9 最新版本

### 🆕 新功能
- **配置文件冲突检测** - 启动时自动检测 `.json` 和 `.jsonc` 冲突，用户选择保留哪个
- **配置格式验证器** - 启动时自动检测并修复配置问题
- **JSONC 注释支持** - 完美兼容带注释的配置文件
- **自定义路径** - 支持切换到项目级配置或任意配置文件

### 🐛 修复
- Category 和 Agent 描述丢失问题（因 `.jsonc` 优先级导致）
- 版本检查线程安全问题
- MCP 服务器 type 字段缺失

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
- ✅ 预设常用 MCP 服务器（Context7、Sentry 等）

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
- ✅ **备份恢复** - 多版本备份管理，一键恢复

### 其他特性
- ✅ **GitHub 版本检查** - 自动检测最新版本
- ✅ **深浅色主题** - 跟随系统自动切换
- ✅ **全局 Tooltip** - 鼠标悬停显示参数说明
- ✅ **统一保存逻辑** - 保存修改直接写入文件

---

## 📦 安装使用

### 方式一：下载预编译版本（推荐）

从 [Releases](https://github.com/icysaintdx/OpenCode-Config-Manager/releases) 下载对应平台的可执行文件：

| 平台 | 文件 | 说明 |
|------|------|------|
| Windows | `OpenCodeConfigManager_windows.exe` | 单文件版，双击运行 |
| macOS | `OpenCode-Config-Manager-MacOS.dmg` | DMG 镜像，拖入应用程序 |
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

### 配置优先级（从高到低）

1. **远程配置** - 通过 `.well-known/opencode` 获取
2. **全局配置** - `~/.config/opencode/opencode.json`
3. **自定义配置** - `OPENCODE_CONFIG` 环境变量指定
4. **项目配置** - `<项目>/opencode.json`
5. **.opencode 目录** - `<项目>/.opencode/config.json`

### Options vs Variants

根据 [OpenCode 官方文档](https://opencode.ai/docs/models/)：

- **options**: 模型的默认配置参数，每次调用都会使用
- **variants**: 可切换的变体配置，通过 `variant_cycle` 快捷键切换

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

## 📋 更新日志

详见 [CHANGELOG.md](CHANGELOG.md)

### v1.0.9 (最新)
- 🆕 配置文件冲突检测（.json vs .jsonc）
- 🐛 修复 Category 和 Agent 描述丢失问题

### v1.0.8
- 🐛 修复版本检查线程安全问题
- 🐛 修复 PyInstaller 打包资源路径问题

### v1.0.7
- 🆕 配置格式验证器和自动修复功能
- 🐛 防御性类型检查，修复配置异常崩溃

[查看完整更新日志 →](CHANGELOG.md)

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
