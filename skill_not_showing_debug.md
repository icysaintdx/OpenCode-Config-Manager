# Skill 安装后不显示问题调试指南

## 问题描述
安装 skill 后提示成功，但在"已发现的Skills"列表中看不到。

## 可能的原因

### 1. 安装位置问题
Skill 可能被安装到了不同的位置，而程序在其他位置搜索。

### 2. 目录结构问题
Skill 的目录结构可能不符合预期。

### 3. SKILL.md 解析失败
SKILL.md 文件格式可能有问题，导致解析失败。

## 调试步骤

### 步骤 1: 运行调试脚本

在项目目录下运行：
```bash
python debug_skill_discovery.py
```

这个脚本会显示：
- 当前工作目录
- 所有搜索路径及其是否存在
- 每个路径下的子目录
- 发现的所有 skills

### 步骤 2: 检查安装位置

根据你选择的安装位置，检查对应目录：

| 安装位置 | 目录路径 |
|---------|---------|
| OpenCode 全局 | `~/.config/opencode/skills/` |
| OpenCode 项目 | `<当前目录>/.opencode/skills/` |
| Claude 全局 | `~/.claude/skills/` |
| Claude 项目 | `<当前目录>/.claude/skills/` |

**Windows 路径示例**:
- `C:\Users\<用户名>\.config\opencode\skills\`
- `C:\Users\<用户名>\.claude\skills\`

### 步骤 3: 检查目录结构

进入安装目录，检查 skill 的目录结构：

```
~/.config/opencode/skills/
└── connect-apps/              # skill 目录
    ├── SKILL.md               # 必须存在
    ├── .skill-meta.json       # 安装元数据
    └── ... 其他文件
```

**关键检查点**:
- ✅ skill 目录存在
- ✅ SKILL.md 文件存在（或 SKILL.txt）
- ✅ SKILL.md 在 skill 目录的根目录下（不是子目录）

### 步骤 4: 手动验证 SKILL.md

打开 SKILL.md 文件，检查格式：

```markdown
---
name: connect-apps
description: Connect Claude to external apps like Gmail, Slack, GitHub
---

# Connect Apps

...
```

**关键检查点**:
- ✅ 文件开头有 `---` 分隔的 frontmatter
- ✅ frontmatter 中有 `name:` 字段
- ✅ frontmatter 中有 `description:` 字段
- ✅ name 格式正确（小写字母、数字、连字符）

### 步骤 5: 检查控制台输出

如果从命令行运行程序：
```bash
python opencode_config_manager_fluent.py
```

查看控制台是否有错误信息，例如：
```
解析 skill 失败 connect-apps: ...
遍历目录失败 /path/to/skills: ...
```

## 常见问题和解决方案

### 问题 1: 目录不存在

**症状**: 调试脚本显示安装目录不存在

**解决方案**:
```bash
# 手动创建目录
mkdir -p ~/.config/opencode/skills
# 或
mkdir -p ~/.claude/skills
```

### 问题 2: SKILL.md 在子目录中

**症状**: 目录结构如下
```
connect-apps/
└── connect-apps/
    └── SKILL.md
```

**解决方案**: 将 SKILL.md 移到外层目录
```bash
cd ~/.config/opencode/skills/connect-apps
mv connect-apps/* .
rmdir connect-apps
```

### 问题 3: 当前工作目录不对

**症状**: 调试脚本显示的当前工作目录不是你期望的

**解决方案**: 
- 从正确的目录启动程序
- 或选择"全局"安装位置而不是"项目"位置

### 问题 4: SKILL.md 格式错误

**症状**: 控制台显示"解析 skill 失败"

**解决方案**: 检查 SKILL.md 格式
- 确保 frontmatter 格式正确
- 确保 name 和 description 字段存在
- 确保 name 符合命名规范

### 问题 5: 权限问题

**症状**: 无法读取目录或文件

**解决方案**:
```bash
# 检查权限
ls -la ~/.config/opencode/skills/

# 修复权限
chmod -R 755 ~/.config/opencode/skills/
```

## 手动修复步骤

如果自动安装失败，可以手动安装：

### 1. 下载 skill
```bash
cd /tmp
git clone https://github.com/ComposioHQ/awesome-claude-skills.git
```

### 2. 复制到正确位置
```bash
# 创建目标目录
mkdir -p ~/.config/opencode/skills

# 复制 skill
cp -r awesome-claude-skills/connect-apps ~/.config/opencode/skills/
```

### 3. 验证结构
```bash
ls -la ~/.config/opencode/skills/connect-apps/
# 应该看到 SKILL.md 文件
```

### 4. 刷新列表
在程序中点击"刷新"按钮，或重新打开程序。

## 获取帮助

如果以上步骤都无法解决问题，请提供以下信息：

1. **调试脚本输出**:
   ```bash
   python debug_skill_discovery.py > debug_output.txt
   ```

2. **目录结构**:
   ```bash
   ls -laR ~/.config/opencode/skills/ > directory_structure.txt
   ```

3. **SKILL.md 内容**:
   ```bash
   cat ~/.config/opencode/skills/connect-apps/SKILL.md > skill_content.txt
   ```

4. **控制台错误信息** (如果有)

将这些信息发送给开发者以获取帮助。

## 相关文件

- `debug_skill_discovery.py` - 调试脚本
- `opencode_config_manager_fluent.py` - 主程序
- `skill_fixes_summary.md` - Skill 市场修复总结
