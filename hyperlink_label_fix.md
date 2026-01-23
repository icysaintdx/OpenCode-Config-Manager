# HyperlinkLabel 修复

## 问题
打开 Skill 市场时报错:
```
TypeError: HyperlinkLabel._() takes from 2 to 3 positional arguments but 4 were given
```

## 原因
错误地使用了 `HyperlinkLabel` 的构造函数。原代码:
```python
browse_more_label = HyperlinkLabel(
    "https://skillsmp.com/", tr("skill.market_dialog.browse_more"), self.widget
)
```

`HyperlinkLabel` 的构造函数只接受 `parent` 参数,不接受 URL 和文本参数。

## 修复
使用 `setUrl()` 和 `setText()` 方法:
```python
browse_more_label = HyperlinkLabel(self.widget)
browse_more_label.setUrl("https://skillsmp.com/")
browse_more_label.setText(tr("skill.market_dialog.browse_more"))
browse_more_label.setToolTip("访问 SkillsMP.com 浏览更多社区技能")
```

## 修改的文件
- `opencode_config_manager_fluent.py` (第13466-13476行)

## 提交
```
commit 5d6498f
修复HyperlinkLabel构造函数参数错误
```

## 测试
创建了 `test_hyperlink_label.py` 用于验证修复。

## 状态
✅ 已修复并提交
