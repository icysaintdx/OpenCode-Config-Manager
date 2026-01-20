# Skill 市场功能使用说明

## 问题描述

如果您在使用 Skill 市场功能时遇到以下错误：

```
安装失败: No module named 'requests'
```

这是因为缺少 `requests` 依赖库。

## 解决方案

### 方法一：重新安装所有依赖（推荐）

在项目根目录运行以下命令：

```bash
pip install -r requirements.txt
```

### 方法二：单独安装 requests

```bash
pip install requests>=2.25.0
```

### 方法三：使用国内镜像加速安装

如果下载速度较慢，可以使用清华镜像源：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 验证安装

运行依赖检查脚本验证所有依赖是否正确安装：

```bash
python test_dependencies.py
```

如果看到以下输出，说明所有依赖已正确安装：

```
[OK] PyQt5 已安装
[OK] PyQt-Fluent-Widgets 已安装
[OK] requests 已安装

==================================================
所有 3 个依赖已正确安装
```

## 受影响的功能

以下功能需要 `requests` 库：

1. **Skill 市场** - 浏览和安装市场中的 Skills
2. **从 GitHub 安装 Skills** - 从 GitHub 仓库下载并安装 Skills
3. **Skill 更新检测** - 检查已安装 Skills 的更新

## 技术说明

- `requests` 库用于：
  - 下载 GitHub 仓库的 ZIP 文件
  - 调用 GitHub API 获取最新 commit 信息
  - 检查 Skills 的更新状态

## 版本历史

- **v1.4.1** (2026-01-20) - 修复依赖缺失问题，在 `requirements.txt` 中添加 `requests>=2.25.0`
- **v1.4.0** (2026-01-20) - 新增 Skill 市场功能
- **v1.3.0** (2026-01-20) - 新增 Skills 安装与更新功能

## 联系支持

如果问题仍未解决，请：

1. 查看 [GitHub Issues](https://github.com/icysaintdx/OpenCode-Config-Manager/issues)
2. 提交新的 Issue 并附上错误信息
3. 联系作者：[@icysaintdx](https://github.com/icysaintdx)
