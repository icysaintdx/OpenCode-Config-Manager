# Changelog

All version update records.

<p align="center">
  <a href="CHANGELOG.md">中文</a> | English
</p>

---

## [v1.8.0] - 2026-02-17
**Version Codename**: Web Edition & Issue Fixes

### 🆕 New Features
#### **OCCM Web Edition** ⭐⭐⭐
- **Full Web Interface**: Built on NiceGUI framework, manage configurations via browser
  - All 17 pages integrated: Provider, Model, MCP, Agent, Permission, Skill, Plugin, etc.
  - Global CSS design system (glassmorphism style) with unified occm-* classes
  - Sidebar grouped navigation with icons, full i18n internationalization
  - Provider + Model merged into collapsible page
  - Permission/Category/Rules switched to inline editing, Monitor tables merged
  - Remote configuration management
- **Custom Config Path**:
  - `--config-dir` CLI argument support
  - `OPENCODE_CONFIG_DIR` environment variable support
  - Auto-open browser on startup (disable with `--no-browser`)
- **Cross-Platform Builds**:
  - Windows exe / macOS zip / Linux tar.gz
  - Unified release with desktop builds in same GitHub Release

### 🐛 Bug Fixes
- **Provider Save `_on_models_fetched` Crash Fix** (Issue #1)
  - Added `hasattr` guard to prevent crash when ProviderPage lacks the method
- **Web Scroll Jank Fix**
  - Removed `backdrop-filter: blur()`, `scroll-behavior: smooth`
  - Simplified transitions to background/color only
- **Multiple Web Fixes**
  - Fixed `ui.select value=''` causing 500 error
  - Fixed Provider page reading npm/sdk and options.apiKey fields
  - Fixed OMO Agent page provider dropdown event
  - Fixed duplicate empty CLIConfigGenerator class causing cli-export 500 error
  - Fixed NiceGUI multiprocessing reload startup issue

### 📦 Build & CI
- Merged Web builds into build.yml for unified release
- macOS Web build changed to compress onedir directory
- Removed standalone build_web.yml; desktop + web 6-platform artifacts in single release

### 📁 File Changes
- Added: `occm_web/` full web directory (17 pages + layout + CSS + i18n)
- Added: `occm_web_launcher.py` (PyInstaller entry point)
- Added: `requirements_web.txt`
- Updated: `opencode_config_manager_fluent.py` (Issue #1 fix + version bump)
- Updated: `.github/workflows/build.yml` (unified build pipeline)

---

## [v1.7.2] - 2026-02-08
**Version Codename**: Stability Fix Release

### 🐛 Bug Fixes
- **Apply Full Configuration Crash Fix**
  - Fixed exception caused by unsupported `ComboBox.insertSeparator` usage
  - Replaced with a disabled separator item and ignored separator selection in group logic
- **Skill Marketplace Install Failure Fix**
  - Added hidden imports for `requests` and dependencies in packaging configs
  - Fixed packaged-app install error: `No module named 'requests'`
- **MCP Dialog Height/Resize Fix**
  - Fixed dialog not shrinking back after collapsing extra fields
  - Added proper vertical resize support to prevent unusable oversized dialogs
- **GLM/Native Provider Balance Query Crash Fix**
  - Added capability checks for providers that do not support balance query APIs
  - Show warning message instead of crashing when query is unsupported
- **Global Exception Handling Hardening**
  - Added cross-platform global exception handlers for main and worker threads
  - Log unhandled exceptions instead of hard-exiting the app

### 🎨 Improvements
- Persisted theme preference and restored it on startup
- Normalized model `limit` cleanup logic to avoid writing invalid empty objects

### 📁 File Changes
- Updated: `opencode_config_manager_fluent.py`
- Updated: `.github/workflows/build.yml`
- Updated: `OCCM_Dynamic_Lang.spec`

---

## [v1.7.1] - 2026-01-28
**Version Codename**: Agent Group Management

### 🆕 New Features
#### **Agent Group Management System** ⭐⭐⭐
- **Complete Agent Group Management**:
  - Create and manage agent groups (OpenCode + Oh My OpenCode agents combination)
  - One-click apply preset groups to Agent configuration pages
  - Support custom group creation, editing, and deletion
  - Group configuration saved to `~/.config/opencode/agent-groups.json`
- **6 Preset Group Templates**:
  - **Minimal**: 1 OpenCode agent + 1 OMO agent
  - **Standard**: 2 OpenCode agents + 2 OMO agents
  - **Common**: 4 OpenCode agents + 5 OMO agents
  - **Complete**: 7 OpenCode agents + 7 OMO agents
  - **Frontend**: 3 OpenCode agents + 4 OMO agents
  - **Backend**: 4 OpenCode agents + 3 OMO agents
- **Pivot Tab UI**:
  - Use Pivot component to switch between OpenCode and Oh My OpenCode agents
  - Clear tab separator line
  - Fixed 40px height tab bar
- **Dynamic Agent List**:
  - Dynamically load agent list from actual config files
  - No longer use hard-coded agent lists
  - Support custom agent display
- **Agent Count Display**:
  - Display selected/total agent count (e.g., "OpenCode: 4/7  Oh My OpenCode: 5/7")
  - Tooltip shows all selected agent names
  - Real-time count updates
- **Flexible Agent Selection**:
  - Removed mandatory agent restrictions (previously build/sisyphus-junior were required)
  - All agents can be freely selected
  - Support creating empty groups

### 🐛 Bug Fixes
#### **Dialog Layout Optimization** ⭐
- **Problem**: Agent group edit dialog layout unreasonable, insufficient table display space
- **Fix**:
  - Reduced dialog padding and spacing (20px→15px, 15px→10px)
  - Reduced description box height (60px→50px)
  - Removed scroll container for basic info area
  - Table uses stretch factor=1 to occupy remaining space
  - Saved ~25-30px vertical space for table display
- **Files**: `opencode_config_manager_fluent.py` (modified layout code)

#### **OMO Description Display Fix** ⭐
- **Problem**: Oh My OpenCode agents show blank when description is empty
- **Fix**:
  - Added fallback to PRESET_AGENTS dictionary
  - Use preset description when config lacks description
  - Ensure all OMO agents have readable descriptions
- **Files**: `opencode_config_manager_fluent.py` (modified description loading logic)

#### **Dialog Inheritance Fix**
- **Problem**: AgentGroupDialog and AgentGroupEditDialog inherit from MessageBoxBase causing layout issues
- **Fix**: Changed to inherit from QDialog, use standard dialog layout
- **Files**: `opencode_config_manager_fluent.py` (modified class inheritance)

#### **OMO Table Simplification**
- **Optimization**: Removed provider and model columns, only keep enabled, agent_id, description columns
- **Reason**: OMO agents' provider/model info managed in OMO config page, no need to display in groups
- **Files**: `opencode_config_manager_fluent.py` (modified table column definition)

#### **Translation File JSON Syntax Error**
- **Problem**: JSON syntax error in zh_CN.json
- **Fix**: Fixed JSON format error, ensure file can be parsed normally
- **Files**: `locales/zh_CN.json`

### 🎨 UI Optimization
#### **Pivot Tab Style Optimization** ⭐
- **Optimization**: 
  - Fixed Pivot component height to 40px
  - Added horizontal separator line (1px gray line)
  - Improved tab visual distinction
- **Files**: `opencode_config_manager_fluent.py` (added style code)

#### **Agent Config Page Integration**
- **Added**: Added group selector to OpenCode Agent and Oh My Agent config pages
- **Features**: 
  - Dropdown select saved groups
  - One-click apply group configuration
  - Real-time update agent enable status
- **Files**: `opencode_config_manager_fluent.py` (added AgentGroupWidget)

### 📚 Technical Implementation
- **New Classes**:
  - `AgentGroupManager`: Group CRUD manager
  - `AgentGroupDialog`: Group selection dialog
  - `AgentGroupEditDialog`: Group edit dialog
  - `AgentGroupWidget`: Group selector component
- **Core Methods**:
  - `AgentGroupManager.load_groups()`: Load all groups
  - `AgentGroupManager.save_group()`: Save group
  - `AgentGroupManager.delete_group()`: Delete group
  - `AgentGroupManager.get_preset_groups()`: Get preset groups
- **Config File**: `~/.config/opencode/agent-groups.json`

### 📁 File Changes
- Updated: `opencode_config_manager_fluent.py` (added Agent group management feature)
- Updated: `locales/zh_CN.json` (added group-related translations)
- Updated: `locales/en_US.json` (added group-related translations)

---

## [v1.7.0] - 2026-01-28
**Version Codename**: Provider Configuration Standardization

### 🆕 New Features
#### **Provider Configuration Standardization** ⭐⭐⭐
- **auth.json Format Fix**:
  - Fixed AuthManager auth.json format to comply with OpenCode official standard
  - Official format: `{"provider": {"type": "api", "key": "xxx"}}`
  - Old format: `{"provider": {"apiKey": "xxx"}}` ❌
  - Added `type` field, fixed field name `apiKey` → `key`
- **Provider Naming Fixes**:
  - Zhipu AI: `zhipu` → `zhipuai` + `zhipuai-coding-plan` (two separate providers)
  - GitHub Copilot: `copilot` → `github-copilot`
  - Google Vertex AI: `vertexai` → `google-vertex`
  - Moonshot AI: `kimi` → `moonshot`
- **Added Z.AI Provider Support**:
  - Added `zai` Provider (regular version)
  - Added `zai-coding-plan` Provider (Coding Plan version)
  - API endpoints: `https://api.z.ai/api/paas/v4` and `https://api.z.ai/api/coding/paas/v4`
- **Added auth.json Path Display on Home Page**:
  - Display auth.json file path
  - Support view and copy buttons
- **Updated Environment Variable Detector**:
  - Updated environment variable mappings for all renamed providers
  - Support environment variable detection for new providers

### 📊 Statistics
- **Fixed Providers**: 7 (zhipu, copilot, vertexai, kimi + 3 new additions)
- **New Providers**: 4 (zhipuai, zai, zai-coding-plan, zhipuai-coding-plan)
- **Total Providers Supported**: 23 (12 international + 11 Chinese)

### 📝 Technical Documentation
- Added 5 technical documents:
  - `Provider配置验证结果.md` - Complete verification report
  - `Provider配置修正完成报告.md` - Detailed fix report
  - `Provider修正计划.md` - Fix task list
  - `所有Provider命名验证.md` - Provider naming verification
  - `原生Provider配置调研报告.md` - Original research document

### 🔧 Technical Details
- **API Endpoint Differences**:
  - Zhipu Regular: `https://open.bigmodel.cn/api/paas/v4`
  - Zhipu Coding Plan: `https://open.bigmodel.cn/api/coding/paas/v4` (note `/coding/` path)
  - Z.AI Regular: `https://api.z.ai/api/paas/v4`
  - Z.AI Coding Plan: `https://api.z.ai/api/coding/paas/v4`
- **Unified Environment Variable**: All Zhipu and Z.AI providers use `ZHIPU_API_KEY` environment variable

---

## [v1.6.0] - 2026-01-27 02:42
**Version Codename**: Plugin Management & UI Optimization

### 🆕 New Features
#### **Plugin Management System** ⭐⭐⭐
- **Complete Plugin Management**:
  - Install plugins from GitHub URL
  - One-click uninstall installed plugins
  - Browse and search plugin marketplace
  - View plugin details, version, and author
- **Technical Implementation**:
  - GitHub API integration for plugin information
  - JSON-based plugin metadata management
  - Fuzzy search for plugin name, description, and author
- **Location**: Navigation menu → Plugin Management
- **Files**: `opencode_config_manager_fluent.py` (+593 lines)

#### **Config File Viewer** ⭐⭐
- **Visual Config Viewer**:
  - JSON syntax highlighting
  - Dark theme adaptation
  - Cross-line bracket highlighting
  - Bracket matching hints
  - One-click edit config files
- **Location**: Home page → Config file viewer area
- **Files**: `opencode_config_manager_fluent.py` (+509 lines)

#### **Auto-Detect Native Providers** ⭐
- **Environment Variable Detection**:
  - Auto-detect 12 official providers (Anthropic, OpenAI, Google, Azure, etc.)
  - One-click detection via "Detect Configured" button
  - Display detection results in table format
- **Location**: Native Provider page → "Detect Configured" button
- **Files**: `opencode_config_manager_fluent.py` (+38 lines)

### 🐛 Bug Fixes
#### **Translation Issues** ⭐
- **Problem**: Hard-coded English text in Chinese mode
- **Root Cause**: 
  - Provider page hard-coded "Provider", "SDK"
  - Native Provider page hard-coded "检测已配置"
  - Rules page hard-coded "错误", "保存失败"
- **Fix**: 
  - Replaced all hard-coded text with tr() function calls
  - Added missing translation keys to zh_CN.json and en_US.json
  - New keys: common.sdk, common.provider, native_provider.provider_name, native_provider.detect_configured, rules.save_failed
- **Files**: `opencode_config_manager_fluent.py` (221 lines modified), `locales/zh_CN.json` (+5 keys), `locales/en_US.json` (+5 keys)

#### **Plugin Page Startup Errors** ⭐
- **Problem**: Startup error "QTableWidget not imported", "SearchLineEdit not imported"
- **Root Cause**: Missing necessary PyQt5 component imports when adding Plugin page
- **Fix**: Added QTableWidget and SearchLineEdit import statements
- **Files**: `opencode_config_manager_fluent.py` (+2 lines)

#### **macOS Crash Issue** ⭐
- **Problem**: macOS system crashes on startup
- **Root Cause**: Navigation bar expanded before window display causing layout errors
- **Fix**: Adjusted navigation bar expand timing, expand after window display
- **Files**: `opencode_config_manager_fluent.py` (6 lines modified)

#### **Mac Install Script Issue**
- **Problem**: Install script cannot adapt to multiple directory structures
- **Root Cause**: Script assumes fixed directory structure
- **Fix**: Support automatic detection of multiple directory structures
- **Files**: `install_update.sh` (39 lines modified)

#### **Config Detection Issue**
- **Problem**: @ai-sdk/openai-compatible package not recognized as valid npm package
- **Root Cause**: Incomplete valid npm package list
- **Fix**: Added @ai-sdk/openai-compatible to valid npm package list
- **Files**: `opencode_config_manager_fluent.py` (+1 line)

#### **Skill Marketplace Issues** (4 fixes)
- **Problem 1**: Skill marketplace selection logic error
- **Problem 2**: Skill marketplace install display issue
- **Problem 3**: ui-ux-pro-max skill install issue
- **Problem 4**: 4 issues in Skill management
- **Fix**: Fixed selection logic, install display, specific skill install, management functions
- **Files**: `opencode_config_manager_fluent.py` (29 lines modified)

#### **Zhipu GLM Config Issue**
- **Problem**: Zhipu GLM config contains non-standard modelListUrl field
- **Root Cause**: Legacy non-standard field from early version
- **Fix**: Removed non-standard modelListUrl field, fixed Zhipu GLM config
- **Files**: `opencode_config_manager_fluent.py` (-40 lines)

#### **MiniMax Config Update**
- **Problem**: MiniMax config does not support Coding Plan endpoint
- **Fix**: Updated MiniMax config to support Coding Plan endpoint
- **Files**: `opencode_config_manager_fluent.py` (9 lines modified)

### 🎨 UI Improvements
#### **Oh My OpenCode Interface Optimization** ⭐
- **Optimization**: Use Pivot tabs to switch between Agent and Category
- **Improvements**: 
  - Adopted Pivot tab component
  - Agent and Category displayed in separate pages
  - Interface more clear and intuitive
- **Files**: `opencode_config_manager_fluent.py` (+228 lines, -75 lines)

#### **Navigation Menu Simplification** ⭐
- **Optimization**: Simplified navigation menu, merged related function pages
- **Improvements**: 
  - Reduced menu item count
  - Merged related functions
  - Improved navigation efficiency
- **Files**: `opencode_config_manager_fluent.py` (+565 lines, -39 lines)

#### **Config Viewer Optimization**
- **Optimization**: Dark theme, cross-line bracket highlighting, bracket matching, edit button
- **Improvements**: 
  - Dark theme adaptation
  - Cross-line bracket highlighting display
  - Bracket matching hints
  - One-click edit button
- **Files**: `opencode_config_manager_fluent.py` (+206 lines, -30 lines)

### 📚 Documentation Updates
- [Plugin Management Feature Completion Report](docs/feature/Plugin插件管理功能完成报告.md) ⭐
- [OpenCode Plugin System Technical Design Document](docs/technical/OpenCode插件系统技术设计文档.md) ⭐
- [Native Provider & CLI Export Feature Description](docs/technical/原生Provider与CLI导出功能说明.md) ⭐
- [Provider Page Merge Implementation Plan](docs/technical/Provider-merge-plan.md) (Incomplete)

### 🔧 Technical Implementation
- **Plugin Management System**: Complete plugin install, uninstall, marketplace functionality
- **Config File Viewer**: JSON syntax highlighting, dark theme, bracket matching
- **Native Provider Detection**: Environment variable auto-detection
- **Translation System Improvement**: Supplemented missing translation keys
- **UI Component Optimization**: Pivot tabs, navigation menu simplification

### 📁 File Changes
- Updated: `opencode_config_manager_fluent.py` (+2,390 lines, -253 lines)
- Updated: `locales/zh_CN.json` (+5 translation keys)
- Updated: `locales/en_US.json` (+5 translation keys)
- Updated: `install_update.sh` (39 lines modified)
- Added: `docs/feature/Plugin插件管理功能完成报告.md` (323 lines)
- Added: `docs/technical/OpenCode插件系统技术设计文档.md` (449 lines)
- Added: `docs/technical/原生Provider与CLI导出功能说明.md` (357 lines)
- Added: `docs/technical/Provider-merge-plan.md` (Incomplete)

---

## [v1.4.0] - 2026-01-20 18:00
**Version Codename**: Skill Marketplace & Security Scanning

### 🆕 New Features (P2)
#### **Skill Marketplace** ⭐
- **Built-in Skill Marketplace**:
  - Expanded Skill Marketplace - Added 12 curated Skills
  - Expanded from 8 to 20
  - Added 3 new categories (UI/UX, DevOps, Performance Optimization)
  - Covers frontend, backend, testing, deployment, optimization scenarios
  ---------------------------------------------------------------
  - 8 curated Skills (Dev Tools, Code Quality, Testing, Documentation, Security, API, Database)
  - Browse by category: Filter Skills by category
  - Search functionality: Search by name, description, tags
  - Table display: Name, description, category, repository info
  - One-click install: Select and install directly to specified location

- **Marketplace Dialog**:
  - Search box + category dropdown
  - Table selection + detail display
  - Installation location selection
  - Auto-fill repository address

#### **Security Scanning** ⭐
- **Code Security Scanning**:
  - Detects 9 types of dangerous code patterns
  - Risk levels: critical, high, medium, low
  - Security score: 0-100 points
  - Detailed issue list: line number, risk level, description, code snippet

- **Scan Modes**:
  - System command execution (os.system, subprocess)
  - Dynamic code execution (eval, exec)
  - File deletion (os.remove, shutil.rmtree)
  - Network requests (requests, socket)
  - Dynamic import (__import__)

- **Scan Result Dialog**:
  - Security score + risk level (color-coded)
  - Issue table: line number, risk level, description, code
  - Risk level colors: Safe (green), Low (light green), Medium (orange), High (red), Critical (dark red)

### 🎨 UI Improvements
- **Skill Browse Page Toolbar**:
  - Added "Skill Marketplace" button (primary button, blue highlight)
  - Adjusted button order: Marketplace → Install → Update → Refresh

- **Skill Detail Action Buttons**:
  - Added "Security Scan" button (shield icon)
  - Button order: Edit → Security Scan → Delete → Open Directory

### 📝 Technical Implementation
- **New Classes**:
  - `SkillMarket`: Skill marketplace data management
  - `SkillMarketDialog`: Marketplace browse dialog
  - `SkillSecurityScanner`: Security scanner
  - `SecurityScanDialog`: Scan result dialog

- **Core Methods**:
  - `SkillMarket.get_all_skills()`: Get all marketplace Skills
  - `SkillMarket.search_skills()`: Search Skills
  - `SkillMarket.get_by_category()`: Get by category
  - `SkillSecurityScanner.scan_skill()`: Scan Skill security risks
  - `SkillPage._on_open_market()`: Open marketplace
  - `SkillPage._on_scan_skill()`: Scan Skill

### 🔧 Features
- ✅ Built-in 8 curated Skills
- ✅ Category + search functionality
- ✅ One-click install marketplace Skills
- ✅ 9 dangerous pattern detection
- ✅ Security scoring system
- ✅ Detailed scan report
- ✅ Risk level visualization

### 📚 Usage Instructions
1. **Browse Skill Marketplace**:
   - Click "Skill Marketplace" button
   - Browse or search Skills
   - Select Skill and click "Install Selected"
   - Choose installation location and confirm

2. **Security Scan**:
   - Select an installed Skill
   - Click "Security Scan" button
   - View security score and issue list
   - Decide whether to use based on risk level

---

## [v1.3.0] - 2026-01-20 17:00
**Version Codename**: Skills Installation & Update

### 🆕 New Features
#### **Skills Installation** ⭐
- **Install Skills from GitHub**:
  - Support GitHub shorthand format: `user/repo` (e.g., `vercel-labs/git-release`)
  - Support full GitHub URL: `https://github.com/user/repo`
  - Auto download, extract, parse SKILL.md
  - Auto get latest commit hash for update detection
  - Install to 4 locations: OpenCode global/project, Claude global/project

- **Import Skills from Local**:
  - Support local path import: `./my-skill` or `/path/to/skill`
  - Auto copy to target directory
  - Validate SKILL.md format

- **Metadata Management**:
  - Auto generate `.skill-meta.json` file to record installation info
  - GitHub source record: owner, repo, branch, url, commit_hash, installed_at
  - Local source record: original_path, installed_at

#### **Skills Update** ⭐
- **Update Detection**:
  - One-click check updates for all installed Skills
  - Get latest commit hash via GitHub API
  - Compare local commit hash to determine if update available
  - Display update status: Has Update / Latest / Local / Check Failed

- **Batch Update**:
  - Table display all Skills update status
  - Support selective update (checkbox)
  - Select all / Deselect all quick operations
  - Display current version and latest version (commit hash first 7 chars)
  - Progress hints and result statistics

### 🎨 UI Improvements
- **Skill Browse Page Toolbar**:
  - Added "Install Skill" button (primary button, blue highlight)
  - Added "Check Updates" button
  - Optimized button layout and spacing

- **Install Dialog**:
  - Clear input hints and format instructions
  - Installation location dropdown selection
  - Real-time progress hints

- **Update Dialog**:
  - Table display all Skills update info
  - Statistics display (total, has update count)
  - Auto-check Skills with updates
  - Disable checkbox for Skills without updates

### 📝 Technical Implementation
- **New Classes**:
  - `SkillInstaller`: Skills installer, support GitHub and local install
  - `SkillUpdater`: Skills updater, check and update Skills
  - `SkillInstallDialog`: Install dialog
  - `SkillUpdateDialog`: Update dialog
  - `ProgressDialog`: Simple progress dialog

- **Core Methods**:
  - `SkillInstaller.parse_source()`: Parse install source (GitHub/local)
  - `SkillInstaller.install_from_github()`: Download and install from GitHub
  - `SkillInstaller.install_from_local()`: Import from local path
  - `SkillUpdater.check_updates()`: Check updates for all Skills
  - `SkillUpdater.update_skill()`: Update single Skill

- **Dependencies**:
  - `requests`: HTTP requests (download ZIP, call GitHub API)
  - `zipfile`: Extract GitHub repo ZIP
  - `tempfile`: Temporary directory management

### 🔧 Features
- ✅ Support multiple install source formats
- ✅ Auto metadata management
- ✅ Smart update detection
- ✅ Batch operation support
- ✅ Detailed error hints
- ✅ Real-time progress feedback
- ✅ Compatible with existing Skill management

### 📚 Usage Instructions
1. **Install Skill**:
   - Click "Install Skill" button
   - Enter GitHub shorthand (e.g., `vercel-labs/git-release`) or local path
   - Select installation location
   - Click "Install" and wait for completion

2. **Update Skills**:
   - Click "Check Updates" button
   - View update list, auto-check Skills with updates
   - Click "Update Selected" for batch update
   - View update result statistics

3. **Metadata File**:
   - Each Skill directory generates `.skill-meta.json`
   - Records installation source and version info
   - Used for update detection and management

---

## [v1.2.0] - 2026-01-20 16:00
**Version Codename**: Oh My MCP Management

### 🆕 New Features
- **Oh My MCP Management**:
  - Added "Oh My MCP" button in MCP Server page
  - Click to open dialog showing 3 built-in MCP servers from Oh My OpenCode:
    - **websearch** - Real-time web search (Exa AI)
    - **context7** - Get latest official documentation
    - **grep_app** - Ultra-fast code search (grep.app)
  - Visually manage enable/disable status for each MCP
  - Support single toggle, enable all, disable all operations
  - Save config via `disabled_mcps` field in `oh-my-opencode.json`

### 📝 Feature Description
- Oh My OpenCode enables these 3 MCP servers by default
- Users can conveniently disable unneeded servers via UI
- Status display in real-time: ✓ Enabled (green) / ✗ Disabled (red)
- Config auto-saved to Oh My OpenCode config file

---

## [v1.1.9] - 2026-01-20 15:30
**Version Codename**: MCP Config Specification Fix

### 🐛 Bug Fixes
- **Fixed MCP config non-compliance causing OpenCode startup failure**:
  - **Root Cause**: After adding MCP via software, OpenCode startup error `Invalid input mcp.@modelcontextprotocol/server-sequential-thinking`
  - **Fix 1 - MCP Key Name Standardization**: Preset MCP templates use simplified key names (e.g., `sequential-thinking`) instead of npm package names with special characters (e.g., `@modelcontextprotocol/server-sequential-thinking`), compliant with OpenCode config specification
  - **Fix 2 - Remove Non-Standard Fields**: According to OpenCode official docs, MCP config can only contain fixed standard fields:
    - Local MCP: `type`, `command`, `environment`, `enabled`, `timeout`
    - Remote MCP: `type`, `url`, `headers`, `oauth`, `enabled`, `timeout`
  - Removed writing of `description`, `tags`, `homepage`, `docs` and other non-standard fields, these fields only used for UI display, no longer written to config file

### 📝 Technical Details
- **OpenCode Config Validation Rules**: OpenCode strictly validates config files, does not accept MCP key names with special characters (`@`, `/`), nor non-standard fields
- **Fix Strategy**:
  1. Preset template key names directly used as MCP names, no longer use `name` field
  2. `_update_extra_info()` method no longer writes any non-standard fields
  3. Extra info (description, tags, etc.) only displayed in UI, does not affect config file
- **Impact Scope**: v1.1.8 and earlier versions all have this issue, v1.1.9 fully fixed

---

## [v1.1.8] - 2026-01-20 14:18
**Version Codename**: Config Loading Fault Tolerance Fix

### 🐛 Bug Fixes
- **Fixed startup crash due to abnormal config file format**:
  - Fixed `PermissionPage._load_data()` method: When `permission` field is non-dict type like string, program startup error `AttributeError: 'str' object has no attribute 'items'`
  - Fixed `MCPPage._load_data()` method: Added `mcp` field type check
  - Fixed `OpenCodeAgentPage._load_data()` method: Added `agent` field type check
  - Fixed `OhMyAgentPage._load_data()` method: Added `agents` field type check
  - Fixed `CategoryPage._load_data()` method: Added `categories` field type check
  - All fixes added `isinstance(data, dict)` type check, use empty dict when config format abnormal, avoid program crash

### 📝 Technical Details
- Root Cause: Some fields in user config file (e.g., `permission`) may become non-dict types (e.g., string `"allow"`) due to manual editing or external tool import, causing `AttributeError` when calling `.items()` method
- Fix Strategy: Add type check for dict-type fields read from config file in all `_load_data()` methods, ensure program robustness
- Impact Scope: v1.1.6 and v1.1.7 both have this issue, v1.1.8 fully fixed

---

## [v1.1.7] - 2026-01-20 02:54
**Version Codename**: CLI Export & UI Optimization

### 🆕 CLI Tool Export Features
- **Claude Code Multi-Model Config**:
  - Support 4 model fields: main model (ANTHROPIC_MODEL), Haiku, Sonnet, Opus
  - Each model can be configured independently or left empty to use default
  - When empty, config file does not include placeholder text
  
- **Codex/Gemini Dual-File Preview**:
  - Codex CLI: auth.json + config.toml dual-file tab preview
  - Gemini CLI: .env + settings.json dual-file tab preview
  - Each file displayed and edited independently

- **Base URL Temporary Modification**:
  - Each CLI tool tab displays Provider's Base URL
  - Support temporary modification for export, does not affect OpenCode original config
  - Preview config updates in real-time after modification

- **Custom Model Input**:
  - Model dropdown supports manual input of custom model names
  - Use native QComboBox for editable functionality
  - Dark theme text color optimized to white

- **Syntax Highlighting & Formatting**:
  - New ConfigSyntaxHighlighter class supports JSON/TOML/ENV formats
  - Color scheme: strings (green), numbers (orange), keywords (purple), key names (blue), comments (gray)
  - Added "Format" button to format JSON config

- **Common Config Feature**:
  - Added "Write Common Config" checkbox
  - Added "Edit Common Config" link button
  - New CommonConfigEditDialog for editing common config

- **Config Detection Animation**:
  - Display "⏳ Detecting Config..." status when switching Provider
  - Show detection result after 300ms delay

### 🎨 UI Optimizations
- **Navigation Menu Font Bold**: All navigation menu items font set to bold for improved readability
- **CLI Export Page Tab Layout**: Adopt main tab design (Claude/Codex/Gemini)
- **CLI Tool Status Display**: Fixed width 150px, height 100px, center aligned, status text bold
- **Config Preview Box Optimization**: Min height 350px, removed max height limit
- **Model Dropdown Width**: Increased from 200px to 300px

### 🔧 Monitor Page Optimization
- **Start/Stop Button Toggle**:
  - Default not start conversation delay detection
  - Changed "Stop" button to "Start" button
  - Click to toggle to "Stop", click again to toggle back to "Start"
  - Only manual click "Start" will begin auto detection

### 🐛 Bug Fixes
- **Model Empty Handling**: When selecting "(Leave empty to use default)", config preview does not include placeholder text
- **Delete Duplicate Styles**: Duplicate style definitions in Codex and Gemini tabs removed
- **External Import Feature Fix**: Fixed external config import related issues

### 📁 File Changes
- Updated: `opencode_config_manager_fluent.py`

---

## [v1.1.6] - 2026-01-19 12:00
**Version Codename**: Native Provider Support

### 🆕 New Features
- **Native Provider Support**:
  - New "Native Provider" page to manage OpenCode officially supported AI service providers
  - Support 12 native Providers: Anthropic, OpenAI, Gemini, Amazon Bedrock, Azure OpenAI, GitHub Copilot, xAI, Groq, OpenRouter, Vertex AI, DeepSeek, OpenCode Zen
  - Auth info stored in separate `auth.json` file, separated from `opencode.json`
  - Cross-platform path support: Windows (`%LOCALAPPDATA%/opencode`), Unix (`~/.local/share/opencode`)

- **AuthManager Authentication Manager**:
  - `read_auth()` / `write_auth()` - Read/write auth.json
  - `get_provider_auth()` / `set_provider_auth()` / `delete_provider_auth()` - Provider auth CRUD
  - `mask_api_key()` - API Key masking display (first and last 4 chars)

- **Environment Variable Detection & Import**:
  - `EnvVarDetector` class auto-detects system environment variables
  - Support `{env:VARIABLE_NAME}` format to reference environment variables
  - One-click import detected environment variables

- **NativeProviderPage**:
  - Table layout displays Provider list (name, SDK, status, environment variables)
  - Status color distinction: Configured (green) / Not Configured (gray)
  - Toolbar: Configure, Test Connection, Delete buttons
  - Double-click row to open config dialog

- **NativeProviderDialog Config Dialog**:
  - Dynamically generate auth fields (support text, password, file types)
  - Dynamically generate option fields (support text, select types)
  - Dark theme adaptation using SimpleCardWidget card layout
  - Environment variable import button

- **Connection Test Feature**:
  - Call Provider's models endpoint to verify credentials
  - Display success/failure status and response time

- **Config Sync & Deduplication**:
  - Display configured native Providers in Agent model selection
  - Detect duplicate native and custom Providers, prompt user to handle

- **Skill Discovery & Browse**:
  - Scan all 4 paths: OpenCode global/project, Claude global/project
  - Display discovered Skill list with source identifier (🌐 Global / 📁 Project)
  - Click to view details: name, description, license, compatibility, path, content preview
  - Support edit, delete, open directory operations

- **Complete SKILL.md Create/Edit**:
  - Support complete frontmatter: name, description, license, compatibility
  - 4 save location choices (OpenCode/Claude × global/project)
  - Name validation (1-64 chars, lowercase letters/numbers + single hyphen, compliant with official spec)
  - Description validation (1-1024 chars)

- **Permission Config Enhancement**:
  - Global permission config (permission.skill)
  - Agent-level permission override (agent.xxx.permission.skill)
  - Disable Skill tool (agent.xxx.tools.skill: false)

- **SkillDiscovery Class**:
  - `discover_all()` - Discover Skills in all paths
  - `parse_skill_file()` - Parse SKILL.md frontmatter
  - `validate_skill_name()` / `validate_description()` - Validate name and description

### 🔧 Optimizations
- **Skill Page Refactor**: Adopt 3-tab layout (Browse Skills, Create Skill, Permission Config)
- **Claude Compatible Path Support**: Full support for `.claude/skills/` path
- **DiscoveredSkill Data Class**: Unified Skill info structure

### 📁 File Changes
- Updated: `opencode_config_manager_fluent.py`
- Added: `assets/512x512.ico` (converted from PNG)

### 📋 New Data Classes
- `AuthField` - Auth field definition
- `OptionField` - Option field definition
- `NativeProviderConfig` - Native Provider config structure
- `NATIVE_PROVIDERS` - 12 native Provider definition list

---

## [v1.1.2] - 2026-01-18 18:30
**Version Codename**: UI Style Optimization

### 🎨 Style Optimizations
- **Theme Color Adjustment**: Theme color changed to `#2979FF` consistent with mainstream design style
- **Light Mode Optimization**: Background color adjusted to cream white `#F7F8FA` more soft and eye-friendly
- **Window Size Adjustment**: Default window height adjusted to 820px to display more content
- **Dialog Theme Adaptation**: Backup management and other dialogs support dark/light theme auto-switch
- **Status Color Unification**: Monitor page status colors consistent with global color scheme

### 🔧 Technical Improvements
- **UIConfig Class**: New global UI config class, unified management of fonts, colors, layout parameters
- **Font Config**: Default use JetBrains Mono monospace font, improve code readability
- **Navigation Bar Optimization**: Compact layout ensures bottom menu items fully displayed

### 📁 File Changes
- Updated: `opencode_config_manager_fluent.py`

---

## [v1.1.1] - 2026-01-17 21:49
**Version Codename**: Config Detection & Import Enhancement

### 🆕 New Features
- **Home Config Detection**: New "Config Detection" button and detail panel, support manual check OpenCode and Oh My OpenCode config and display issue list
- **List Batch Model**: Oh My Agent/Category support batch model dropdown selection, take effect immediately
- **Default Description Display**: When list description is empty, display preset description (display only, not written to config)
- **Monitor Page**: New model availability monitoring and history record display, support manual detection
- **MCP Preset Extension**: New chrome-devtools, open-web-mcp, serena and other common presets
- **MCP Additional Info**: New description/tags/homepage/docs fields, support preset auto-fill
- **MCP Resource Entry**: MCP page new awesome MCP collection entry button

### 🐛 Bug Fixes
- **External Import Path Compatibility**: Claude/Codex/cc-switch import auto fallback to `D:\opcdcfg\test\...` when default path does not exist
- **cc-switch Model ID Filter**: Ignore GUID-form model IDs to avoid polluting model list
- **Import Mapping Dialog Scroll**: ImportMappingDialog fixed height and scrollable

### 🔧 Optimizations
- **Model Batch Config**: New thinking/options/variants batch config logic
- **Model ID Parse Enhancement**: Extract model ID from multiple fields, cover more external config formats
- **Config Validation Enhancement**: Supplement null value check and new Oh My OpenCode config structure validation
- **Monitor Page Layout**: Monitor list layout compression and column width optimization

### 📁 File Changes
- Updated: `opencode_config_manager_fluent.py`

---

## [v1.1.0] - 2026-01-15 22:00
**Version Codename**: Modalities & Update Prompt Enhancement

### 🆕 New Features
- **Model Modalities Config**:
  - Model edit dialog new input/output modality settings
  - Input modalities support: text, image, audio, video
  - Output modalities support: text, image, audio
  - Auto-load existing config when editing, write to `modalities` field when saving

- **Update Prompt Enhancement**:
  - Prompt bar no longer auto-disappears, needs manual close
  - Click prompt bar to directly open GitHub release page
  - Light mode uses amber background, dark mode uses blue background
  - Timed check interval changed to 1 minute

### 📁 File Changes
- Updated: `opencode_config_manager_fluent.py`

---

## [v1.0.9] - 2026-01-15 19:00
**Version Codename**: Config Conflict Detection

### 🆕 New Features
- **Config File Conflict Detection**:
  - Auto-detect if both `.json` and `.jsonc` config files exist on startup
  - Popup shows size and modification time of both files to help user judge
  - User can choose which file to use, the other will be backed up then deleted
  - Solved issue of loading old config due to `.jsonc` higher priority

- **ConfigPaths Class Enhancement**:
  - `check_config_conflict()` - Detect config file conflict
  - `get_config_file_info()` - Get file size and modification time

### 🐛 Bug Fixes
- **Category and Agent Description Loss Issue**:
  - Root Cause: When both `.json` and `.jsonc` exist, program prioritizes loading old `.jsonc` file
  - Now prompts user to choose which config file to use

### 📁 File Changes
- Updated: `opencode_config_manager_fluent.py`

---

## [v1.0.8] - 2026-01-15 18:30
**Version Codename**: Version Check Fix

### 🐛 Bug Fixes
- **Version Check Thread Safety Issue**:
  - Fixed version check callback in sub-thread causing program freeze
  - Use `pyqtSignal` to safely notify main thread to update UI from sub-thread
  - `VersionChecker` changed to inherit `QObject` to support signal-slot mechanism

- **PyInstaller Package Resource Path Issue**:
  - New `get_resource_path()` function, correctly handle resource path after packaging
  - Fixed logo/icon image loading failure after packaging causing temp directory error
  - Compatible with development environment and PyInstaller package environment

### 🔧 Optimizations
- **APP_VERSION Sync Update**: Version number updated from 1.0.5 to 1.0.8

### 📁 File Changes
- Updated: `opencode_config_manager_fluent.py`
- Added: `OpenCodeConfigManager_v1.0.8.spec`

---

## [v1.0.7] - 2026-01-15 17:50
**Version Codename**: Config Validation Fix

### 🆕 New Features
- **Config Format Validator (ConfigValidator)**:
  - Auto-check config file format compliance with OpenCode spec on startup
  - Validate Provider required fields (npm, options, baseURL, apiKey)
  - Validate Model structure and limit field type
  - Validate MCP config (local/remote type corresponding fields)
  - Display error and warning list to help user locate issues

- **Config Auto-Fix Feature**:
  - Popup prompts user whether to fix when issues detected
  - Auto-backup original config before fix (tag: `before-fix`)
  - Auto-complete missing required fields (npm, options, models)
  - Standardize field order (npm → name → options → models)

### 🐛 Bug Fixes
- **Defensive Type Check**: Fixed `'str' object has no attribute 'get'` crash when config abnormal
  - `_load_stats()` - Check provider_data type when counting
  - `ModelRegistry.refresh()` - Check type when refreshing model list
  - `ProviderPage._load_data()` - Check type when loading Provider
  - `ModelPage._load_models()` - Check type when loading models
  - `ModelDialog._load_model_data()` - Check type when loading model data

### 🔧 Optimizations
- **SpinBox Display Optimization**: Set min width to improve display on Win10

### 📁 File Changes
- Updated: `opencode_config_manager_fluent.py`
- Added: `OpenCodeConfigManager_v1.0.7.spec`

---

## [v1.0.6] - 2026-01-15 15:00
**Version Codename**: MCP Type Fix

### 🐛 Bug Fixes
- **MCP Server type Field Missing**: Fixed issue of not writing `type` field when adding/editing MCP server
  - Local MCP now correctly writes `"type": "local"`
  - Remote MCP now correctly writes `"type": "remote"`

### 🔧 Optimizations
- **GitHub Actions Build Config Update**:
  - macOS build switched from `macos-latest` to `macos-15-intel` (Intel architecture, PyQt5 has precompiled wheel)
  - Solved PyQt5 compilation failure on ARM64 macOS

### 📁 File Changes
- Updated: `opencode_config_manager_fluent.py`
- Updated: `.github/workflows/build.yml`
- Updated: `.github/workflows/build_all.yml`
- Added: `OpenCodeConfigManager_v1.0.6.spec`

---

## [v1.0.5] - 2026-01-14 19:50
**Version Codename**: UI Optimization Enhancement

### 🆕 New Features
- **JSONC Comment Loss Warning**:
  - Auto-detect if JSONC file contains comments when saving
  - Display yellow warning InfoBar on first save prompting comments will be lost
  - Auto-create backup before saving (tag: `jsonc-auto`)
  - `has_jsonc_comments()` method precisely detects `//` and `/* */` comments

### 🐛 Bug Fixes
- **Preset Model Variants Config Fix**: Removed extra `variants` content in Claude series presets, now preset models only set thinking in `options`

### 🔧 Optimizations
- **Options Tab Layout Refactor**:
  - Use `QScrollArea` to wrap content, solve vertical space shortage
  - Key-value input changed to single-line compact layout (Key: [input] Value: [input])
  - Table header height optimized to 32px, data row height 28px
  - Button height unified to 32px
- **External Import List Column Width Adjustment**:
  - First column (Source): Fixed 180px
  - Second column (Config Path): Auto-fill remaining space
  - Third column (Status): Fixed 100px
- **Dark Theme Contrast Enhancement**:
  - Scroll area and content container set transparent background
  - Card padding optimized (8,6,8,6)

### 📁 File Changes
- Updated: `opencode_config_manager_fluent.py`
- Added: `OpenCodeConfigManager_v1.0.5.spec`

---

## [v1.0.4] - 2026-01-14 13:57
**Version Codename**: Custom Backup Directory

### 🆕 New Features
- **Manual Backup Directory Selection**:
  - Home page new backup directory browse and reset buttons
  - `ConfigPaths.set_backup_dir()` set custom backup path
  - `ConfigPaths.get_backup_dir()` support custom path priority
  - `ConfigPaths.is_custom_path("backup")` detect if using custom path

### 🔧 Optimizations
- File rename: `opencode_config_manager_fluent_v1.0.0.py` → `opencode_config_manager_fluent.py`
- Build scripts sync update file name reference

### 📁 File Changes
- Renamed: `opencode_config_manager_fluent.py` (original `opencode_config_manager_fluent_v1.0.0.py`)
- Updated: `build_windows.bat`
- Updated: `build_unix.sh`

---

## [v1.0.3] - 2026-01-14 13:00
**Version Codename**: Cross-Platform Enhancement

### 🆕 New Features
- **Cross-Platform Path Support**:
  - Windows/Linux/macOS unified use `~/.config/opencode/` directory
  - `ConfigPaths.get_platform()` get current platform
  - `ConfigPaths.get_config_base_dir()` get config base directory
- **Complete Build Scripts**:
  - `build_unix.sh`: Linux + macOS unified build script
  - `build_windows.bat`: Windows build script
  - Linux headless server auto-detect and use xvfb

### 🔧 Optimizations
- Build scripts auto-detect Python version
- Build scripts auto-install missing dependencies
- Display file size after build completion

### 📁 File Changes
- Updated: `opencode_config_manager_fluent_v1.0.0.py`
- Updated: `build_unix.sh`
- Added: `build_windows.bat`

---

## [v1.0.2] - 2026-01-14 12:30
**Version Codename**: Custom Path

### 🆕 New Features
- **Home Config Path Manual Selection**:
  - Click folder icon to select any JSON/JSONC config file
  - Support switch to project-level config or other custom config
  - Click reset button to restore default path
- **ConfigPaths Class Enhancement**:
  - `set_opencode_config()` / `set_ohmyopencode_config()` set custom path
  - `is_custom_path()` check if using custom path
  - `reset_to_default()` reset to default path
- **ConfigManager Enhancement**:
  - `is_jsonc_file()` detect if file is JSONC format

### 🔧 Optimizations
- Config path label dynamically updates
- Auto-validate JSON/JSONC format when selecting config file
- Auto-reload and update statistics after switching config

### 📁 File Changes
- Updated: `opencode_config_manager_fluent_v1.0.0.py`
- Updated: `build_unix.sh`

---

## [v1.0.1] - 2026-01-14 12:00
**Version Codename**: JSONC Support

### 🆕 New Features
- **JSONC Format Support**: Config files support JSON format with comments
  - Support `//` single-line comments
  - Support `/* */` multi-line comments
  - Auto-detect and parse JSONC files
- **Dual Extension Detection**: Auto-detect `.jsonc` and `.json` config files
  - Prioritize loading `.jsonc` files
  - Compatible with existing `.json` config

### 🔧 Optimizations
- `ConfigPaths` class refactor, support flexible config file path detection
- `ConfigManager.strip_jsonc_comments()` method: Safely remove JSONC comments
- `build_unix.sh` updated to Fluent version build script

### 📁 File Changes
- Updated: `opencode_config_manager_fluent_v1.0.0.py`
- Updated: `build_unix.sh` (Linux/macOS build script)

---

## [v1.0.0] - 2026-01-14 08:00
**Version Codename**: Fluent Design Complete Refactor

### 🎨 Major Update - UI Framework Complete Refactor
- **New UI Framework**: Migrated from ttkbootstrap to PyQt5 + QFluentWidgets
- **Fluent Design Style**: Adopt Microsoft Fluent Design language
- **Dark/Light Theme**:
  - Default follow system theme auto-switch
  - Support manual switch dark/light mode
  - Use SystemThemeListener to real-time listen system theme changes
- **Modern Card Layout**: All pages adopt SimpleCardWidget card design
- **Sidebar Navigation**: FluentWindow native navigation bar, icon + text

### 🆕 New Features
- **Home Logo Display**: Display OCCM brand logo
- **Theme Switch Button**: One-click switch dark/light at bottom of navigation bar
- **Window Icon**: Display custom icon in taskbar and title bar

### 📦 Tech Stack Changes
- **Removed Dependencies**: ttkbootstrap
- **New Dependencies**:
  - PyQt5 >= 5.15.0
  - PyQt5-Fluent-Widgets >= 1.5.0

### 🔧 Optimizations
- All dialogs unified dark theme base class (BaseDialog)
- List component column width optimization, clearer info display
- Tooltip system fully preserved
- Config save logic optimization

### 📁 File Changes
- Added: `opencode_config_manager_fluent_v1.0.0.py` (Fluent version main program)
- Added: `assets/logo1.png` (Home logo)
- Added: `assets/logo.png`, `assets/logo.ico` (Brand resources)
- Preserved: `opencode_config_manager_v0.7.0.py` (ttkbootstrap version, compatible with old systems)

---

## [v0.8.0] - 2025-01-10
**Version Codename**: Oh My OpenCode Support

### 🆕 New Features
- **Oh My OpenCode Config Support**:
  - Agent Management - Bind Provider/Model
  - Category Management - Temperature slider adjustment
  - Preset Templates - oracle, librarian, explore, etc.

---

## [v0.7.0] - 2025-01-09
**Version Codename**: Theme System Enhancement

### 🆕 New Features
- Integrated ttkbootstrap modern UI framework
- Support 10 built-in themes (5 dark/5 light)
  - Dark: Darkly, Superhero, Cyborg, Vapor, Solar
  - Light: Cosmo, Flatly, Litera, Minty, Pulse
- Real-time theme switching, no need to restart app

---

## [v0.6.3 - v0.6.5] - 2025-01-08
**Version Codename**: Version Check Enhancement

### 🆕 New Features
- GitHub version check and update prompt
- Optimized theme color scheme (Fluent Design style)
- Implemented real-time theme switching

---

## [v0.6.0 - v0.6.2] - 2025-01-07
**Version Codename**: MCP & Agent Config

### 🆕 New Features
- MCP Server Config Management
  - Local Type: Configure startup command and environment variables
  - Remote Type: Configure server URL and request headers
- OpenCode Agent Config
  - Mode Settings: primary / subagent / all
  - Parameter Config: temperature, maxSteps, hidden, disable
  - Tool Permission Config
- Skill/Rules Management
- Context Compression Config

---

## [v0.5.0] - 2025-01-05
**Version Codename**: Preset & Backup

### 🆕 New Features
- Complete model preset config
- Backup & restore feature
- External import refactor

---

## [v0.4.0] - 2025-01-03
**Version Codename**: Basic Features

### 🆕 New Features
- Provider Management
- Model Management
- Permission Management
- External Import (Claude Code, Codex, Gemini)

---

## Version Naming Convention

- **Major Version**: Major architecture changes, incompatible API modifications
- **Minor Version**: New features, backward-compatible feature iterations
- **Patch Version**: Bug fixes, minor optimizations
