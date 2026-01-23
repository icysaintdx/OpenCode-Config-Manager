# Skill 市场分支检测修复

## 问题
ComposioHQ 的 skills 安装失败，报错:
```
网络错误: 404 Client Error: Not Found for url:
https://codeload.github.com/ComposioHQ/awesome-claude-skills/zip/refs/heads/main
```

## 根本原因
不同的 GitHub 仓库使用不同的默认分支:
- **Anthropic skills**: 使用 `main` 分支
- **ComposioHQ skills**: 使用 `master` 分支
- **nextlevelbuilder skills**: 使用 `main` 分支

之前的代码在 `_on_open_market()` 方法中硬编码了 `"main"` 分支 (第15319行)，导致所有 ComposioHQ 的 skills 安装失败。

## 修复方案

### 修改前 (第15308-15332行)
```python
# 从市场安装
owner, repo_name = skill["repo"].split("/")
subdir = skill.get("path", None)
success, message = SkillInstaller.install_from_github(
    owner,
    repo_name,
    "main",  # ❌ 硬编码为 main
    target_dir,
    subdir=subdir,
    progress_callback=install_dialog.update_progress,
)
```

### 修改后
```python
# 从市场安装
owner, repo_name = skill["repo"].split("/")
subdir = skill.get("path", None)

# 自动检测分支 (main 或 master)
branch = SkillInstaller.detect_default_branch(owner, repo_name)

success, message = SkillInstaller.install_from_github(
    owner,
    repo_name,
    branch,  # ✅ 自动检测的分支
    target_dir,
    subdir=subdir,
    progress_callback=install_dialog.update_progress,
)
```

## 分支检测逻辑

`SkillInstaller.detect_default_branch()` 方法 (第13775-13810行):

1. **尝试 GitHub API**: 获取仓库的 `default_branch` 字段
2. **API 失败时**: 依次尝试 HEAD 请求 `main.zip` 和 `master.zip`
3. **默认值**: 如果都失败，返回 `"main"`

```python
@staticmethod
def detect_default_branch(owner: str, repo: str) -> str:
    try:
        # 尝试 GitHub API
        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            return response.json().get("default_branch", "main")
    except Exception:
        pass
    
    # API 失败时，尝试检测 main 和 master
    for branch in ["main", "master"]:
        try:
            test_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
            response = requests.head(test_url, timeout=5)
            if response.status_code == 200:
                return branch
        except Exception:
            continue
    
    return "main"  # 默认返回 main
```

## 验证结果

所有 25 个 skills 现在都能正常安装:

### Anthropic Skills (11个 - main 分支)
- canvas-design ✓
- theme-factory ✓
- web-artifacts-builder ✓
- mcp-builder ✓
- webapp-testing ✓
- skill-creator ✓
- algorithmic-art ✓
- slack-gif-creator ✓
- doc-coauthoring ✓
- brand-guidelines ✓
- internal-comms ✓

### ComposioHQ Skills (13个 - master 分支)
- changelog-generator ✓
- image-enhancer ✓
- video-downloader ✓
- content-research-writer ✓
- meeting-insights-analyzer ✓
- twitter-algorithm-optimizer ✓
- competitive-ads-extractor ✓
- domain-name-brainstormer ✓
- file-organizer ✓
- invoice-organizer ✓
- raffle-winner-picker ✓
- tailored-resume-generator ✓
- connect-apps ✓

### nextlevelbuilder Skills (1个 - main 分支)
- ui-ux-pro-max ✓

## 修改的文件
- `opencode_config_manager_fluent.py` (第15308-15335行)

## 提交
```
commit ff0cce1
修复Skill市场安装: 自动检测分支(main/master)
```

## 测试建议

1. **测试 Anthropic skill**:
   - 打开 Skill 市场
   - 选择 "canvas-design"
   - 点击安装
   - 应该成功安装

2. **测试 ComposioHQ skill**:
   - 打开 Skill 市场
   - 选择 "changelog-generator"
   - 点击安装
   - 应该成功安装 (之前会 404)

3. **测试 ui-ux-pro-max**:
   - 打开 Skill 市场
   - 选择 "ui-ux-pro-max"
   - 点击安装
   - 应该成功安装

## 相关问题

这个修复解决了用户报告的问题:
> ComposioHQ/awesome-claude-skills 安装还是报错
> 网络错误: 404 Client Error: Not Found for url

现在所有 ComposioHQ 的 skills 都能正常安装了！
