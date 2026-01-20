# Implementation Plan: CC-Switch Integration (CLI 工具导出)

## Overview

本实现计划将 CC-Switch 的核心配置同步逻辑集成到 OpenCode Config Manager 中 实现从 OpenCode 配置导出到 Claude Code、Codex CLI、Gemini CLI 的功能。

实现采用增量开发方式 先完成核心逻辑 再添加 UI 界面 最后完善测试和错误处理。

## Tasks

- [x] 1. 创建 CLI 导出核心模块结构
  - 在 opencode_config_manager_fluent.py 中添加 CLI 导出相关的数据类和基础结构
  - 创建 CLIToolStatus、ValidationResult、ExportResult、BatchExportResult、BackupInfo 数据类
  - 创建 CLIExportError 及其子类 (ProviderValidationError, ConfigWriteError, ConfigParseError, BackupError, RestoreError)
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. 实现 CLI 工具检测功能
  - [x] 2.1 实现 CLIConfigWriter 路径获取方法
    - 实现 get_claude_dir()、get_codex_dir()、get_gemini_dir() 静态方法
    - 支持跨平台路径解析 (Windows/macOS/Linux) 统一使用 Path.home() / ".{cli_name}/"
    - _Requirements: 10.1, 10.2, 10.3_

  - [x] 2.2 实现 CLI 工具检测逻辑
    - 在 CLIExportManager 中实现 detect_cli_tools() 方法
    - 检测配置目录是否存在 (~/.claude/, ~/.codex/, ~/.gemini/)
    - 返回 Dict[str, CLIToolStatus] 包含 installed、config_dir、has_config 信息
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [x] 3. 实现配置生成器 (CLIConfigGenerator)
  - [x] 3.1 实现 Claude 配置生成
    - 实现 generate_claude_config(provider: Dict, model: str) -> Dict 方法
    - 生成包含 env 字段的 settings.json 配置
    - 设置 ANTHROPIC_BASE_URL、ANTHROPIC_AUTH_TOKEN、ANTHROPIC_MODEL
    - 支持模型映射 (ANTHROPIC_DEFAULT_HAIKU_MODEL, ANTHROPIC_DEFAULT_SONNET_MODEL, ANTHROPIC_DEFAULT_OPUS_MODEL)
    - _Requirements: 2.1, 2.3, 2.5_

  - [x] 3.2 编写 Claude 配置生成属性测试
    - **Property 1: Claude 配置生成完整性**
    - 使用 hypothesis 生成随机 provider 配置 验证输出包含所有必需字段
    - **Validates: Requirements 2.1, 2.3**

  - [x] 3.3 实现 Codex 配置生成
    - 实现 generate_codex_auth(provider: Dict) -> Dict 方法 (生成 auth.json 内容)
    - 实现 generate_codex_config(provider: Dict, model: str) -> str 方法 (生成 config.toml 字符串)
    - 确保 base_url 以 /v1 结尾
    - 设置 model_provider、model、base_url 等字段
    - _Requirements: 3.1, 3.2, 3.3_

  - [x] 3.4 编写 Codex 配置生成属性测试
    - **Property 2: Codex 配置生成完整性**
    - 验证 auth.json 包含 OPENAI_API_KEY config.toml 是有效 TOML 格式
    - **Validates: Requirements 3.1, 3.2, 3.3**

  - [x] 3.5 实现 Gemini 配置生成
    - 实现 generate_gemini_env(provider: Dict, model: str) -> Dict[str, str] 方法 (生成 .env 内容)
    - 实现 generate_gemini_settings(auth_type: str = "gemini-api-key") -> Dict 方法 (生成 security 配置)
    - 设置 GOOGLE_GEMINI_BASE_URL、GEMINI_API_KEY、GEMINI_MODEL
    - _Requirements: 4.1, 4.2, 4.3_

  - [x] 3.6 编写 Gemini 配置生成属性测试
    - **Property 3: Gemini 配置生成完整性**
    - 验证 .env 包含所有必需环境变量 settings.json 包含 security.auth.selectedType
    - **Validates: Requirements 4.1, 4.2**

- [x] 4. 实现配置写入器 (CLIConfigWriter)
  - [x] 4.1 实现原子写入方法
    - 实现 atomic_write_json(path: Path, data: Dict) -> None 方法
    - 实现 atomic_write_text(path: Path, content: str) -> None 方法
    - 写入临时文件 (path.tmp.{timestamp}) 后验证格式 然后重命名替换原文件
    - _Requirements: 14.1_

  - [x] 4.2 实现 Claude 配置写入
    - 实现 write_claude_settings(config: Dict, merge: bool = True) -> None 方法
    - 支持与现有配置合并 (保留非 env 字段如 mcpServers)
    - 写入到 ~/.claude/settings.json
    - _Requirements: 2.2, 2.4_

  - [x] 4.3 实现 Codex 配置写入
    - 实现 write_codex_auth(auth: Dict) -> None 方法
    - 实现 write_codex_config(config_toml: str, merge: bool = True) -> None 方法
    - 支持保留现有 MCP 配置 ([mcp] 段)
    - 写入到 ~/.codex/auth.json 和 ~/.codex/config.toml
    - _Requirements: 3.2, 3.3, 3.4_

  - [x] 4.4 实现 Gemini 配置写入
    - 实现 write_gemini_env(env_map: Dict[str, str]) -> None 方法
    - 实现 write_gemini_settings(security_config: Dict, merge: bool = True) -> None 方法
    - 支持保留现有 mcpServers 配置
    - 设置 .env 文件权限 (Unix: 600) 使用 set_file_permissions() 方法
    - 写入到 ~/.gemini/.env 和 ~/.gemini/settings.json
    - _Requirements: 4.2, 4.3, 4.4, 4.5, 10.4_

  - [x] 4.5 编写配置合并属性测试
    - **Property 4: 配置合并保留性**
    - 验证导出操作后非 Provider 相关字段 (如 mcpServers) 保持不变
    - **Validates: Requirements 2.4, 3.4, 4.4**

- [x] 5. 实现备份管理器 (CLIBackupManager)
  - [x] 5.1 实现备份创建功能
    - 实现 create_backup(cli_type: str) -> Optional[Path] 方法
    - 备份到 ~/.opencode-backup/{cli_type}_{timestamp}/ 目录
    - 复制所有相关配置文件到备份目录
    - _Requirements: 5.1, 5.2_

  - [x] 5.2 实现备份恢复功能
    - 实现 restore_backup(backup_path: Path, cli_type: str) -> bool 方法
    - 实现 list_backups(cli_type: str) -> List[BackupInfo] 方法
    - 恢复时先备份当前配置
    - _Requirements: 5.3_

  - [x] 5.3 实现备份清理功能
    - 实现 cleanup_old_backups(cli_type: str) -> None 方法
    - 保留最近 MAX_BACKUPS (5) 个备份 删除旧备份
    - _Requirements: 5.4_

  - [x] 5.4 编写备份数量限制属性测试
    - **Property 5: 备份数量限制**
    - 验证多次导出后备份目录最多保留 5 个备份
    - **Validates: Requirements 5.4**

- [x] 6. 实现 Provider 验证功能
  - [x] 6.1 实现 Provider 配置验证
    - 在 CLIExportManager 中实现 validate_provider(provider: Dict) -> ValidationResult 方法
    - 检查 baseURL 和 apiKey 是否存在且非空
    - 返回 ValidationResult(valid=bool, errors=List[str], warnings=List[str])
    - _Requirements: 15.1, 15.2, 15.3, 15.4_

  - [x] 6.2 编写 Provider 验证属性测试
    - **Property 8: Provider 配置完整性检查**
    - 验证缺少 baseURL 或 apiKey 时返回失败并包含具体错误信息
    - **Validates: Requirements 15.1, 15.2, 15.3**

- [x] 7. 实现核心导出管理器 (CLIExportManager)
  - [x] 7.1 实现单个 CLI 工具导出
    - 实现 export_to_claude(provider: Dict, model: str) -> ExportResult 方法
    - 实现 export_to_codex(provider: Dict, model: str) -> ExportResult 方法
    - 实现 export_to_gemini(provider: Dict, model: str) -> ExportResult 方法
    - 集成备份、生成、写入、验证流程：备份 -> 生成配置 -> 写入 -> 验证
    - _Requirements: 2.1, 3.1, 4.1_

  - [x] 7.2 实现批量导出功能
    - 实现 batch_export(provider: Dict, models: Dict[str, str], targets: List[str]) -> BatchExportResult 方法
    - 支持部分失败继续执行 (try-except 包裹每个导出)
    - 返回 BatchExportResult(total, successful, failed, results)
    - _Requirements: 6.1, 6.4_

  - [x] 7.3 编写批量导出容错性属性测试
    - **Property 6: 批量导出容错性**
    - 验证一个 CLI 工具导出失败时其他工具继续执行
    - **Validates: Requirements 6.4**

- [x] 8. 实现配置验证功能
  - [x] 8.1 实现导出后配置验证
    - 实现 validate_exported_config(cli_type: str) -> ValidationResult 方法
    - 检查文件存在性
    - 验证 JSON/TOML 格式正确性
    - 验证必需字段存在
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

  - [x] 8.2 编写配置验证属性测试
    - **Property 7: 配置验证准确性**
    - 验证能正确识别文件存在性、格式有效性、必需字段存在性
    - **Validates: Requirements 7.2, 7.3**

- [x] 9. Checkpoint - 核心逻辑完成
  - 确保所有核心模块测试通过
  - 验证配置生成和写入逻辑正确
  - 如有问题请询问用户

- [x] 10. 实现 CLI 导出 UI 页面
  - [x] 10.1 创建 CLIExportPage 类
    - 继承 QWidget
    - 创建页面基础布局 (QVBoxLayout)
    - 添加页面标题 "CLI 工具导出"
    - _Requirements: 11.1, 11.3_

  - [x] 10.2 实现 Provider 选择区域
    - 添加 Provider 下拉选择框 (ComboBox)
    - 显示配置完整性状态 (baseURL ✓/✗, apiKey ✓/✗)
    - 添加"修复配置"按钮跳转到 Provider 编辑页面
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 15.5_

  - [x] 10.3 实现 Model 选择区域
    - 为每个 CLI 工具添加 Model 下拉框 (Claude Model, Codex Model, Gemini Model)
    - 根据选中的 Provider 更新可用 Model 列表
    - _Requirements: 12.5, 12.6_

  - [x] 10.4 实现 CLI 工具状态区域
    - 显示每个 CLI 工具的安装状态 (✓ 已安装 / ✗ 未安装)
    - 添加单独导出按钮 (未安装时禁用)
    - 添加"一键导出"按钮
    - _Requirements: 1.2, 1.3, 1.4, 6.1_

  - [x] 10.5 实现配置预览区域
    - 添加标签页切换 (Pivot: Claude/Codex/Gemini)
    - 显示生成的配置预览 (PlainTextEdit, readonly)
    - 支持语法高亮 (JSON/TOML)
    - _Requirements: 13.1, 13.2, 13.3_

  - [x] 10.6 实现备份管理区域
    - 显示最近备份信息 (时间、CLI 类型)
    - 添加"查看备份"和"恢复备份"按钮
    - _Requirements: 5.3_

- [x] 11. 实现导出操作和反馈
  - [x] 11.1 实现导出按钮点击处理
    - 执行导出流程 (验证 -> 备份 -> 生成 -> 写入 -> 验证)
    - 显示进度指示 (InfoBar)
    - _Requirements: 6.2_

  - [x] 11.2 实现导出结果显示
    - 成功时显示成功提示 (InfoBar.success)
    - 失败时显示错误详情 (FluentMessageBox)
    - 批量导出时显示汇总 (成功 N 个 失败 M 个)
    - _Requirements: 6.3, 7.4, 14.4_

  - [x] 11.3 实现错误恢复流程
    - 写入失败时自动恢复备份
    - 显示恢复状态
    - _Requirements: 14.2, 14.3_

- [x] 12. 集成到主应用
  - [x] 12.1 添加导航入口
    - 在 FluentWindow 主导航中添加"CLI 工具导出"页面
    - 使用 FIF.SEND 图标
    - _Requirements: 11.1_

  - [x] 12.2 添加 Provider 详情页快捷入口
    - 在 Provider 详情页添加"导出到 CLI"按钮
    - 点击后跳转到 CLI 导出页面并预选当前 Provider
    - _Requirements: 11.2_

  - [x] 12.3 实现页面间数据同步
    - Provider 变更时刷新导出页面 (使用信号槽机制)
    - _Requirements: 11.4_

- [x] 13. Checkpoint - UI 集成完成
  - 确保 UI 页面正常显示
  - 验证导出流程端到端工作
  - 如有问题请询问用户

- [x] 14. 完善测试和文档
  - [x] 14.1 编写配置预览一致性属性测试
    - **Property 9: 配置预览一致性**
    - 验证预览生成的配置与实际导出的配置内容完全一致
    - **Validates: Requirements 13.1, 13.2**

  - [x] 14.2 编写原子写入安全性属性测试
    - **Property 10: 原子写入安全性**
    - 验证写入过程中发生错误时原有配置文件保持不变
    - **Validates: Requirements 14.1, 14.2**

  - [x] 14.3 编写集成测试
    - 端到端导出测试 (创建测试 Provider -> 导出 -> 验证文件内容)
    - 备份恢复测试 (导出 -> 修改 -> 恢复 -> 验证)
    - 批量导出测试 (模拟部分失败场景)

- [x] 15. Final Checkpoint - 功能完成
  - 确保所有测试通过
  - 验证所有需求已实现
  - 如有问题请询问用户

## Notes

- All tasks are required for comprehensive implementation
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties using hypothesis library
- Unit tests validate specific examples and edge cases
- 现有代码中已有 BackupManager 类用于 OpenCode 配置备份 CLIBackupManager 是专门用于 CLI 工具配置的独立备份管理器
- 现有代码中已有 ConfigPaths 类包含部分 CLI 路径方法 可复用或扩展

