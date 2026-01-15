# 更新日志

所有版本的更新记录。

---

## [v1.0.8] - 2026-01-15 18:30
**版本代号**: 版本检查修复版

### 🐛 Bug 修复
- **版本检查线程安全问题**：
  - 修复版本检查回调在子线程调用导致程序卡死的问题
  - 使用 `pyqtSignal` 从子线程安全地通知主线程更新 UI
  - `VersionChecker` 改为继承 `QObject`，支持信号槽机制

- **PyInstaller 打包资源路径问题**：
  - 新增 `get_resource_path()` 函数，正确处理打包后的资源路径
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
  - 验证 Provider 必需字段（npm, options, baseURL, apiKey）
  - 验证 Model 结构和 limit 字段类型
  - 验证 MCP 配置（local/remote 类型对应字段）
  - 显示错误和警告列表，帮助用户定位问题

- **配置自动修复功能**：
  - 检测到问题时弹窗提示用户是否修复
  - 修复前自动备份原配置（标签: `before-fix`）
  - 自动补全缺失的必需字段（npm, options, models）
  - 规范化字段顺序（npm → name → options → models）

### 🐛 Bug 修复
- **防御性类型检查**：修复配置异常时 `'str' object has no attribute 'get'` 崩溃
  - `_load_stats()` - 统计时检查 provider_data 类型
  - `ModelRegistry.refresh()` - 刷新模型列表时检查类型
  - `ProviderPage._load_data()` - 加载 Provider 时检查类型
  - `ModelPage._load_models()` - 加载模型时检查类型
  - `ModelDialog._load_model_data()` - 加载模型数据时检查类型

### 🔧 优化改进
- **SpinBox 显示优化**：设置最小宽度，改善 Win10 上的显示问题

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
  - macOS 构建从 `macos-latest` 切换到 `macos-15-intel`（Intel 架构，PyQt5 有预编译 wheel）
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
  - 保存前自动创建备份（标签: `jsonc-auto`）
  - `has_jsonc_comments()` 方法精确检测 `//` 和 `/* */` 注释

### 🐛 Bug 修复
- **预设模型 Variants 配置修复**：移除 Claude 系列预设中多余的 `variants` 内容，现在预设模型只在 `options` 中设置 thinking

### 🔧 优化改进
- **Options Tab 布局重构**：
  - 使用 `QScrollArea` 包裹内容，解决垂直空间不足问题
  - 键值输入改为单行紧凑布局（键: [输入框] 值: [输入框]）
  - 表头高度优化为 32px，数据行高度 28px
  - 按钮高度统一为 32px
- **外部导入列表列宽调整**：
  - 第一列（来源）：固定 180px
  - 第二列（配置路径）：自动填充剩余空间
  - 第三列（状态）：固定 100px
- **深色主题对比度增强**：
  - 滚动区域和内容容器设置透明背景
  - 卡片内边距优化（8,6,8,6）

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
- `ConfigPaths` 类重构，支持灵活的配置文件路径检测
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
