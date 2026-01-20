#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量国际化替换脚本 - CategoryPage、OhMyAgentPage、RulesPage、ImportPage
"""

from pathlib import Path

# 读取主文件
main_file = Path("opencode_config_manager_fluent.py")
with open(main_file, "r", encoding="utf-8") as f:
    content = f.read()

# OhMyAgentPage 替换列表
ohmyagent_replacements = [
    (
        'super().__init__("Oh My Agent", parent)',
        'super().__init__(tr("ohmyagent.title"), parent)',
    ),
    ('"添加 Agent"', 'tr("ohmyagent.add_agent")'),
    ('"从预设添加"', 'tr("common.add_from_preset")'),
    (
        '["名称", "绑定模型", "描述"]',
        '[tr("common.name"), tr("ohmyagent.model"), tr("common.description")]',
    ),
    ('"成功", "Agent 已保存"', 'tr("common.success"), tr("ohmyagent.agent_saved")'),
    ('"成功", "Agent 已删除"', 'tr("common.success"), tr("ohmyagent.agent_deleted")'),
]

# CategoryPage 替换列表
category_replacements = [
    (
        'super().__init__("Category 管理", parent)',
        'super().__init__(tr("category.title"), parent)',
    ),
    ('"添加 Category"', 'tr("category.add_category")'),
    (
        '["名称", "Temperature", "模型列表"]',
        '[tr("common.name"), tr("category.temperature"), tr("category.models")]',
    ),
    (
        '"成功", "Category 已保存"',
        'tr("common.success"), tr("category.category_saved")',
    ),
    (
        '"成功", "Category 已删除"',
        'tr("common.success"), tr("category.category_deleted")',
    ),
]

# RulesPage 替换列表
rules_replacements = [
    (
        'super().__init__("Rules 管理", parent)',
        'super().__init__(tr("rules.title"), parent)',
    ),
    ('"Instructions"', 'tr("rules.instructions")'),
    ('"AGENTS.md"', 'tr("rules.agents_md")'),
    ('"保存 Instructions"', 'tr("rules.save_instructions")'),
    ('"保存 AGENTS.md"', 'tr("rules.save_agents_md")'),
    ('"加载模板"', 'tr("rules.load_template")'),
    (
        '"成功", "Instructions 已保存"',
        'tr("common.success"), tr("rules.instructions_saved")',
    ),
    ('"成功", "AGENTS.md 已保存"', 'tr("common.success"), tr("rules.agents_md_saved")'),
]

# ImportPage 替换列表
import_replacements = [
    (
        'super().__init__("外部导入", parent)',
        'super().__init__(tr("import.title"), parent)',
    ),
    ('"检测配置"', 'tr("import.detect_configs")'),
    ('"导入选中"', 'tr("import.import_selected")'),
    (
        '["来源", "配置路径", "状态"]',
        '[tr("import.source"), tr("import.config_path"), tr("import.status")]',
    ),
    ('"已检测"', 'tr("import.detected")'),
    ('"未检测"', 'tr("import.not_detected")'),
    ('"成功", "导入成功"', 'tr("common.success"), tr("import.import_success")'),
    ('"错误", "导入失败"', 'tr("common.error"), tr("import.import_failed")'),
]

# 执行替换
replacements = (
    ohmyagent_replacements
    + category_replacements
    + rules_replacements
    + import_replacements
)
replaced_count = 0

for old_text, new_text in replacements:
    if old_text in content:
        content = content.replace(old_text, new_text)
        replaced_count += 1

# 保存文件
with open(main_file, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Total replacements: {replaced_count}")
print("File updated successfully")
