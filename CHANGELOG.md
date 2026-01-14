# 更新日志

所有版本的更新记录。

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
- **侧边栏导航**：FluentWindow 原生导航栏，图标 + 文字

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
- 列表组件列宽优化，信息展示更清晰
- Tooltip 提示系统完整保留
- 配置保存逻辑优化

### 📁 文件变更
- 新增：`opencode_config_manager_fluent_v1.0.0.py` (Fluent 版本主程序)
- 新增：`assets/logo1.png` (首页 Logo)
- 新增：`assets/logo.png`, `assets/logo.ico` (品牌资源)
- 保留：`opencode_config_manager_v0.7.0.py` (ttkbootstrap 版本，兼容旧系统)

---

## [v0.7.0] - 2025-01-09
**版本代号**: 主题系统增强版

### 🆕 新增功能
- 集成 ttkbootstrap 现代化 UI 框架
- 支持 10 种内置主题（深色/浅色各 5 种）
  - 深色：Darkly、Superhero、Cyborg、Vapor、Solar
  - 浅色：Cosmo、Flatly、Litera、Minty、Pulse
- 实时主题切换，无需重启应用

---

## [v0.6.3 - v0.6.5] - 2025-01-08
**版本代号**: 版本检查增强版

### 🆕 新增功能
- GitHub 版本检查和更新提示
- 优化主题配色（Fluent Design 风格）
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
- 外部导入（Claude Code、Codex、Gemini）

---

## 版本命名规范

- **主版本号 (Major)**：重大架构变更、不兼容的 API 修改
- **次版本号 (Minor)**：新增功能、向后兼容的功能迭代
- **补丁版本号 (Patch)**：Bug 修复、小优化
