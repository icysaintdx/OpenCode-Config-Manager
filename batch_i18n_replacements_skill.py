#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量国际化替换脚本 - SkillPage 剩余部分
"""

from pathlib import Path

# 读取主文件
main_file = Path("opencode_config_manager_fluent.py")
with open(main_file, "r", encoding="utf-8") as f:
    content = f.read()

# SkillPage 替换列表
replacements = [
    ('"已发现的 Skill"', 'tr("skill.discovered_skills")'),
    (
        '"扫描 OpenCode 和 Claude 兼容路径发现的所有 Skill"',
        'tr("skill.scan_description")',
    ),
    ('"Skill 市场"', 'tr("skill.skill_market")'),
    ('"安装 Skill"', 'tr("skill.install_skill")'),
    ('"检查更新"', 'tr("skill.check_updates")'),
    ('"Skill 详情"', 'tr("skill.skill_details")'),
    ('"未选择 Skill"', 'tr("skill.no_skill_selected")'),
    ('"请从左侧列表选择一个 Skill 查看详情"', 'tr("skill.select_skill_hint")'),
    ('"Skill 名称:"', 'tr("skill.skill_name") + ":"'),
    ('"描述:"', 'tr("skill.description") + ":"'),
    ('"许可证:"', 'tr("skill.license") + ":"'),
    ('"兼容性:"', 'tr("skill.compatibility") + ":"'),
    ('"路径:"', 'tr("skill.path") + ":"'),
    ('"内容预览:"', 'tr("skill.content_preview") + ":"'),
    ('"编辑 Skill"', 'tr("skill.edit_skill")'),
    ('"删除 Skill"', 'tr("skill.delete_skill")'),
    ('"打开目录"', 'tr("skill.open_directory")'),
    ('"安全扫描"', 'tr("skill.scan_security")'),
    ('"创建新 Skill"', 'tr("skill.create_new_skill")'),
    ('"保存位置:"', 'tr("skill.save_location") + ":"'),
    ('"Skill 内容:"', 'tr("skill.skill_content") + ":"'),
    ('"保存 Skill"', 'tr("skill.save_skill")'),
    ('"权限配置"', 'tr("skill.permission_config")'),
    ('"全局权限"', 'tr("skill.global_permission")'),
    ('"模式"', 'tr("skill.pattern")'),
    ('"权限"', 'tr("skill.permission")'),
    ('"添加权限"', 'tr("skill.add_permission")'),
    ('"成功", "Skill 已保存"', 'tr("common.success"), tr("skill.skill_saved")'),
    ('"成功", "Skill 已删除"', 'tr("common.success"), tr("skill.skill_deleted")'),
]

# 执行替换
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
