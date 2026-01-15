## v1.0.9 (2026-01-15)

### 版本代号: 配置冲突检测版

### 新增功能

- **配置文件冲突检测**
  - 启动时自动检测是否同时存在 `.json` 和 `.jsonc` 配置文件
  - 弹窗显示两个文件的大小和修改时间，帮助用户判断
  - 用户可选择使用哪个文件，另一个会被备份后删除
  - 解决了因 `.jsonc` 优先级更高导致加载旧配置的问题

- **ConfigPaths 类增强**
  - `check_config_conflict()` - 检测配置文件冲突
  - `get_config_file_info()` - 获取文件大小和修改时间

### Bug 修复

- **Category 和 Agent 描述丢失问题**
  - 根因：同时存在 `.json` 和 `.jsonc` 时，程序优先加载旧的 `.jsonc` 文件
  - 现在会提示用户选择要使用的配置文件

### 文件变更

- 更新：`opencode_config_manager_fluent.py`

---

## 下载

| 平台 | 文件 | 说明 |
|------|------|------|
| Windows | `OpenCodeConfigManager_windows.exe` | 单文件版，双击运行 |
| macOS | `OpenCode-Config-Manager-MacOS.dmg` | DMG 镜像，拖入应用程序 |
| Linux | `OpenCode-Config-Manager-Linux-x64.tar.gz` | 解压后运行 |

完整更新历史请查看 [CHANGELOG.md](CHANGELOG.md)
