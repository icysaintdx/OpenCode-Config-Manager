## [v1.4.5] - 2026-01-20 21:10
**版本代号**: 依赖修复版

### 🐛 Bug 修复
- **修复 Skill 市场功能依赖缺失问题** ⭐
  - **问题**: 用户点击 Skill 市场时报错 `No module named 'requests'`
  - **原因**: `requirements.txt` 中缺少 `requests` 依赖
  - **修复**: 
    - 在 `requirements.txt` 中添加 `requests>=2.25.0`
    - 更新 `.github/workflows/build.yml` - 在 Windows/macOS/Linux 三个平台的构建步骤中添加 `requests` 依赖
  - **影响功能**:
    - Skill 市场安装功能
    - 从 GitHub 安装 Skills
    - Skill 更新检测功能

### 📝 技术说明
- `SkillInstaller.install_from_github()` 方法需要 `requests` 库下载 GitHub 仓库
- `SkillUpdater.check_updates()` 方法需要 `requests` 库调用 GitHub API

### 🔧 升级说明
如果您从 v1.4.0 或更早版本升级，请务必重新安装依赖：
```bash
pip install -r requirements.txt
```

或单独安装 requests：
```bash
pip install requests>=2.25.0
```

### 📁 文件变更
- 修改：`requirements.txt` - 添加 `requests>=2.25.0`
- 修改：`.github/workflows/build.yml` - 在三个平台的构建步骤中添加 `requests`
- 修改：`CHANGELOG.md` - 添加 v1.4.5 版本记录
- 修改：`README.md` - 更新最新版本信息

---

## [v1.4.0] - 2026-01-20 18:00
**版本代号**: Skills 市场与安全扫描版

### 🆕 新增功能 (P2)
#### **Skill 市场功能** ⭐
- **内置 Skill 市场**：
  - 20 个精选 Skills（开发工具、代码质量、测试、文档、安全、API、数据库、UI/UX、DevOps、性能优化）
  - 分类浏览：按类别筛选 Skills
  - 搜索功能：按名称、描述、标签搜索
  - 表格展示：名称、描述、分类、仓库信息
  - 一键安装：选中后直接安装到指定位置

- **市场对话框**：
  - 搜索框 + 分类下拉框
  - 表格选择 + 详情显示
  - 安装位置选择
  - 自动填充仓库地址

#### **安全扫描功能** ⭐
- **代码安全扫描**：
  - 检测 9 种危险代码模式
  - 风险等级：critical（严重）、high（高）、medium（中）、low（低）
  - 安全评分：0-100 分
  - 详细问题列表：行号、风险等级、描述、代码片段

- **扫描模式**：
  - 系统命令执行（os.system、subprocess）
  - 动态代码执行（eval、exec）
  - 文件删除（os.remove、shutil.rmtree）
  - 网络请求（requests、socket）
  - 动态导入（__import__）

- **扫描结果对话框**：
  - 安全评分 + 风险等级（颜色标识）
  - 问题表格：行号、风险等级、描述、代码
  - 风险等级颜色：安全（绿）、低风险（浅绿）、中风险（橙）、高风险（红）、严重（深红）

### 🎨 UI 改进
- **Skill 浏览页面工具栏**：
  - 新增 "Skill 市场" 按钮（主按钮，蓝色高亮）
  - 调整按钮顺序：市场 → 安装 → 更新 → 刷新

- **Skill 详情操作按钮**：
  - 新增 "安全扫描" 按钮（盾牌图标）
  - 按钮顺序：编辑 → 安全扫描 → 删除 → 打开目录

### 📝 技术实现
- **新增类**：
  - `SkillMarket`：Skill 市场数据管理
  - `SkillMarketDialog`：市场浏览对话框
  - `SkillSecurityScanner`：安全扫描器
  - `SecurityScanDialog`：扫描结果对话框

- **核心方法**：
  - `SkillMarket.get_all_skills()`：获取所有市场 Skills
  - `SkillMarket.search_skills()`：搜索 Skills
  - `SkillMarket.get_by_category()`：按分类获取
  - `SkillSecurityScanner.scan_skill()`：扫描 Skill 安全风险
  - `SkillPage._on_open_market()`：打开市场
  - `SkillPage._on_scan_skill()`：扫描 Skill

### 🔧 功能特性
- ✅ 内置 20 个精选 Skills
- ✅ 分类 + 搜索功能
- ✅ 一键安装市场 Skills
- ✅ 9 种危险模式检测
- ✅ 安全评分系统
- ✅ 详细扫描报告
- ✅ 风险等级可视化

### 📚 使用说明
1. **浏览 Skill 市场**：
   - 点击 "Skill 市场" 按钮
   - 浏览或搜索 Skills
   - 选择 Skill 后点击 "安装选中"
   - 选择安装位置并确认

2. **安全扫描**：
   - 选择一个已安装的 Skill
   - 点击 "安全扫描" 按钮
   - 查看安全评分和问题列表
   - 根据风险等级决定是否使用

### 📁 文件变更
- 修改：`opencode_config_manager_fluent.py` - 新增 Skill 市场和安全扫描功能
- 修改：`CHANGELOG.md` - 添加 v1.4.0 版本记录
- 修改：`README.md` - 更新功能说明
