## v1.1.0 (2026-01-15)

### 版本代号: 模态与更新提示增强版

### 新增功能

- **模型 Modalities 配置**
  - 模型编辑对话框新增输入/输出模态设置
  - 输入模态支持：text、image、audio、video
  - 输出模态支持：text、image、audio
  - 编辑时自动加载已有配置，保存时写入 `modalities` 字段

- **更新提示增强**
  - 提示条不再自动消失，需手动关闭
  - 点击提示条可直接打开 GitHub 发布页面
  - 浅色模式使用琥珀色背景，深色模式使用蓝色背景
  - 定时检查间隔改为 1 分钟

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
