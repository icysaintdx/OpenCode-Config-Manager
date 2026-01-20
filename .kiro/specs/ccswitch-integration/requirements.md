# Requirements Document

## Introduction

本功能将 CC-Switch 的核心配置同步逻辑融合到 OpenCode Config Manager 中 实现从 OpenCode 配置导出到 Claude Code、Codex CLI、Gemini CLI 的配置写入能力。

用户可以从 OpenCode 中已配置的 Provider 和 Model 信息中选择性提取 转换成各 CLI 工具所需的格式 然后直接写入到对应的配置文件中。

## Glossary

- **OpenCode_Config**: OpenCode 的配置文件 `opencode.json` 包含 Provider 和 Model 配置
- **Claude_Code**: Anthropic 的 Claude Code CLI 工具
  - 配置目录: `~/.claude/`
  - 主配置文件: `~/.claude/settings.json` (包含 env 字段存储环境变量）
  - MCP 配置文件: `~/.claude.json` (包含 mcpServers 字段）
- **Codex_CLI**: OpenAI 的 Codex CLI 工具
  - 配置目录: `~/.codex/`
  - 认证文件: `~/.codex/auth.json` (包含 OPENAI_API_KEY）
  - 配置文件: `~/.codex/config.toml` (TOML 格式 包含 model_provider、model、base_url 等）
- **Gemini_CLI**: Google 的 Gemini CLI 工具
  - 配置目录: `~/.gemini/`
  - 环境变量文件: `~/.gemini/.env` (包含 GOOGLE_GEMINI_BASE_URL、GEMINI_API_KEY、GEMINI_MODEL）
  - 设置文件: `~/.gemini/settings.json` (包含 security.auth.selectedType 和 mcpServers）
- **Live_Config**: 各 CLI 工具实际读取的配置文件 (运行时配置）
- **Provider_Sync**: 将 OpenCode Provider 配置转换并写入到目标 CLI 工具的过程
- **Config_Manager**: OpenCode Config Manager 应用程序
- **CLI_Export_Module**: 新增的 CLI 工具导出功能模块

## Requirements

### Requirement 1: 导出目标选择界面

**User Story:** As a user, I want to select which CLI tools to export my OpenCode provider configuration to, so that I can use the same API endpoints across different AI coding assistants.

#### Acceptance Criteria

1. THE Config_Manager SHALL provide an "导出到 CLI 工具" section in the Provider management page
2. WHEN the user views a Provider, THE Config_Manager SHALL display export options for Claude Code, Codex CLI, and Gemini CLI
3. THE Config_Manager SHALL show the installation status of each CLI tool (已安装/未安装)
4. WHEN a CLI tool is not installed, THE Config_Manager SHALL disable the export option and show a tooltip explaining the requirement

### Requirement 2: Claude Code 配置导出

**User Story:** As a user, I want to export my OpenCode provider configuration to Claude Code, so that I can use my API endpoint with Claude Code CLI.

#### Acceptance Criteria

1. WHEN the user exports to Claude Code, THE Config_Manager SHALL generate a valid Claude Code settings configuration
2. THE Config_Manager SHALL write the configuration to `~/.claude/settings.json`
3. THE Config_Manager SHALL set the following environment variables in the configuration:
   - ANTHROPIC_BASE_URL: 从 OpenCode Provider 的 baseURL 转换
   - ANTHROPIC_AUTH_TOKEN: 从 OpenCode Provider 的 apiKey 转换
   - ANTHROPIC_MODEL: 从 OpenCode 的默认模型配置转换
4. THE Config_Manager SHALL preserve existing Claude Code configuration fields that are not related to the provider
5. IF the user has configured custom models, THEN THE Config_Manager SHALL map them to ANTHROPIC_DEFAULT_HAIKU_MODEL, ANTHROPIC_DEFAULT_SONNET_MODEL, ANTHROPIC_DEFAULT_OPUS_MODEL

### Requirement 3: Codex CLI 配置导出

**User Story:** As a user, I want to export my OpenCode provider configuration to Codex CLI, so that I can use my API endpoint with OpenAI Codex CLI.

#### Acceptance Criteria

1. WHEN the user exports to Codex CLI, THE Config_Manager SHALL generate valid Codex auth.json and config.toml files
2. THE Config_Manager SHALL write authentication to `~/.codex/auth.json` with OPENAI_API_KEY
3. THE Config_Manager SHALL write configuration to `~/.codex/config.toml` with:
   - model_provider: 设置为 "newapi" 或适当的提供商类型
   - model: 从 OpenCode 的默认模型配置转换
   - base_url: 从 OpenCode Provider 的 baseURL 转换 (确保以 /v1 结尾）
4. THE Config_Manager SHALL preserve existing Codex configuration fields that are not related to the provider (如 MCP 配置)

### Requirement 4: Gemini CLI 配置导出

**User Story:** As a user, I want to export my OpenCode provider configuration to Gemini CLI, so that I can use my API endpoint with Google Gemini CLI.

#### Acceptance Criteria

1. WHEN the user exports to Gemini CLI, THE Config_Manager SHALL generate valid Gemini .env and settings.json files
2. THE Config_Manager SHALL write environment variables to `~/.gemini/.env` with:
   - GOOGLE_GEMINI_BASE_URL: 从 OpenCode Provider 的 baseURL 转换
   - GEMINI_API_KEY: 从 OpenCode Provider 的 apiKey 转换
   - GEMINI_MODEL: 从 OpenCode 的默认模型配置转换
3. THE Config_Manager SHALL update `~/.gemini/settings.json` 中的 security.auth.selectedType 为 "gemini-api-key" (使用 API Key 模式）
4. THE Config_Manager SHALL preserve existing Gemini settings.json fields (如 mcpServers、其他 security 设置)
5. THE Config_Manager SHALL set appropriate file permissions (600) on the .env file for security on Unix systems

### Requirement 5: 配置备份与恢复

**User Story:** As a user, I want my existing CLI configurations to be backed up before export, so that I can restore them if needed.

#### Acceptance Criteria

1. WHEN exporting configuration, THE Config_Manager SHALL create a backup of existing configuration files
2. THE Config_Manager SHALL store backups in `~/.cc-switch-backup/` or similar directory with timestamp
3. THE Config_Manager SHALL provide a "恢复备份" option to restore previous configurations
4. THE Config_Manager SHALL keep the last 5 backups for each CLI tool

### Requirement 6: 批量导出功能

**User Story:** As a user, I want to export my provider configuration to multiple CLI tools at once, so that I can quickly set up all my AI coding assistants.

#### Acceptance Criteria

1. THE Config_Manager SHALL provide a "一键导出到所有已安装的 CLI 工具" button
2. WHEN batch exporting, THE Config_Manager SHALL show a progress indicator for each CLI tool
3. WHEN batch export completes, THE Config_Manager SHALL display a summary of successful and failed exports
4. IF any export fails, THEN THE Config_Manager SHALL continue with remaining exports and report all errors at the end

### Requirement 7: 配置验证

**User Story:** As a user, I want to verify that my exported configuration works correctly, so that I can ensure the CLI tools will function properly.

#### Acceptance Criteria

1. THE Config_Manager SHALL provide a "验证配置" button after export
2. WHEN validating, THE Config_Manager SHALL check if the configuration files exist and are valid JSON/TOML
3. THE Config_Manager SHALL attempt to parse the configuration and verify required fields are present
4. IF validation fails, THEN THE Config_Manager SHALL display specific error messages indicating what is wrong

### Requirement 8: CLI 工具检测

**User Story:** As a user, I want the application to automatically detect which CLI tools are installed, so that I know which export options are available.

#### Acceptance Criteria

1. THE Config_Manager SHALL detect Claude Code installation by checking for `~/.claude/` directory or `claude` command
2. THE Config_Manager SHALL detect Codex CLI installation by checking for `~/.codex/` directory or `codex` command
3. THE Config_Manager SHALL detect Gemini CLI installation by checking for `~/.gemini/` directory or `gemini` command
4. THE Config_Manager SHALL refresh detection status when the export page is opened
5. THE Config_Manager SHALL provide a "刷新检测" button to manually re-detect installations

### Requirement 9: 模型映射配置

**User Story:** As a user, I want to configure how OpenCode models map to CLI tool models, so that I can use the correct model names for each tool.

#### Acceptance Criteria

1. THE Config_Manager SHALL provide a model mapping configuration interface
2. THE Config_Manager SHALL allow users to specify which OpenCode model maps to which CLI tool model
3. THE Config_Manager SHALL provide default mappings for common models (如 gpt-4o → gpt-4o, claude-3-5-sonnet → claude-sonnet-4-20250514)
4. THE Config_Manager SHALL save model mappings persistently

### Requirement 10: 跨平台路径支持

**User Story:** As a user on different operating systems, I want the export paths to be correctly resolved, so that the application works on Windows, macOS, and Linux.

#### Acceptance Criteria

1. THE Config_Manager SHALL resolve CLI tool paths correctly on all platforms:
   - Claude Code: `~/.claude/` on all platforms
   - Codex CLI: `~/.codex/` on all platforms
   - Gemini CLI: `~/.gemini/` on all platforms
2. THE Config_Manager SHALL create parent directories if they do not exist when exporting
3. THE Config_Manager SHALL handle path separators correctly for each operating system
4. THE Config_Manager SHALL set appropriate file permissions on Unix systems (600 for sensitive files)

### Requirement 11: 功能模块位置与入口

**User Story:** As a user, I want to access the CLI export feature from a logical location in the application, so that I can easily find and use it.

#### Acceptance Criteria

1. THE Config_Manager SHALL add a new "CLI 工具导出" tab/page in the main navigation
2. THE Config_Manager SHALL also provide quick export buttons in the Provider detail view
3. THE Config_Manager SHALL display the export module with clear sections for each CLI tool
4. THE Config_Manager SHALL show the current OpenCode configuration summary at the top of the export page

### Requirement 12: Provider 和 Model 选择

**User Story:** As a user, I want to select which Provider and Model to export, so that I can choose the appropriate configuration for each CLI tool.

#### Acceptance Criteria

1. THE Config_Manager SHALL display a list of all configured OpenCode Providers
2. THE Config_Manager SHALL allow users to select one Provider for export
3. WHEN a Provider is selected, THE Config_Manager SHALL validate that the Provider has complete configuration (baseURL, apiKey)
4. IF the Provider configuration is incomplete, THEN THE Config_Manager SHALL display a warning and prevent export until fixed
5. THE Config_Manager SHALL display available Models for the selected Provider
6. THE Config_Manager SHALL allow users to select a default Model for each CLI tool
7. THE Config_Manager SHALL remember the last selected Provider and Model for convenience

### Requirement 15: Provider 配置完整性检查

**User Story:** As a user, I want the system to verify my Provider configuration is complete before export, so that I don't export invalid configurations.

#### Acceptance Criteria

1. WHEN a Provider is selected for export, THE Config_Manager SHALL check for required fields:
   - baseURL: 必须存在且非空
   - apiKey: 必须存在且非空
2. IF baseURL is missing or empty, THEN THE Config_Manager SHALL display "缺少 API 地址 (baseURL)"
3. IF apiKey is missing or empty, THEN THE Config_Manager SHALL display "缺少 API 密钥 (apiKey)"
4. THE Config_Manager SHALL also check Model configuration completeness:
   - 至少有一个可用的 Model
   - 选中的 Model 必须有有效的 model ID
5. THE Config_Manager SHALL provide a "修复配置" button to navigate to Provider edit page

### Requirement 13: 配置预览

**User Story:** As a user, I want to preview the generated configuration before exporting, so that I can verify the content is correct.

#### Acceptance Criteria

1. WHEN a Provider is selected, THE Config_Manager SHALL generate and display a preview of the configuration for each CLI tool
2. THE Config_Manager SHALL show the preview in the appropriate format (JSON for Claude, TOML for Codex, .env for Gemini)
3. THE Config_Manager SHALL highlight the key fields (API Key, Base URL, Model) in the preview
4. THE Config_Manager SHALL allow users to edit the preview before exporting (advanced mode)

### Requirement 14: 原子写入与错误恢复

**User Story:** As a user, I want the export operation to be safe and recoverable, so that my existing configurations are not corrupted if something goes wrong.

#### Acceptance Criteria

1. THE Config_Manager SHALL use atomic write operations (write to temp file, then rename)
2. IF the export fails midway, THEN THE Config_Manager SHALL restore the original configuration
3. THE Config_Manager SHALL validate the generated configuration before writing
4. THE Config_Manager SHALL display clear error messages if validation or writing fails

</content>
</invoke>