#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量替换 SkillPage 中的硬编码文本为翻译函数调用
"""

import re

# SkillPage 中需要替换的文本映射
SKILL_PAGE_REPLACEMENTS = [
    # 浏览标签页
    (
        r'SubtitleLabel\("已发现的 Skill"',
        r'SubtitleLabel(tr("skill.discovered_skills")',
    ),
    (
        r'"扫描 OpenCode 和 Claude 兼容路径发现的所有 Skill"',
        r'tr("skill.scan_description")',
    ),
    (
        r'PrimaryPushButton\(FIF\.MARKET, "Skill 市场"',
        r'PrimaryPushButton(FIF.MARKET, tr("skill.market")',
    ),
    (
        r'PushButton\(FIF\.DOWNLOAD, "安装 Skill"',
        r'PushButton(FIF.DOWNLOAD, tr("skill.install_skill")',
    ),
    (
        r'PushButton\(FIF\.UPDATE, "检查更新"',
        r'PushButton(FIF.UPDATE, tr("common.check_update")',
    ),
    (r'PushButton\(FIF\.SYNC, "刷新"', r'PushButton(FIF.SYNC, tr("common.refresh")'),
    (r'SubtitleLabel\("Skill 详情"', r'SubtitleLabel(tr("skill.skill_details")'),
    (
        r'StrongBodyLabel\("选择一个 Skill 查看详情"',
        r'StrongBodyLabel(tr("skill.select_to_view")',
    ),
    (r'BodyLabel\("内容预览:"', r'BodyLabel(tr("skill.skill_content") + ":")'),
    (r'PushButton\(FIF\.EDIT, "编辑"', r'PushButton(FIF.EDIT, tr("common.edit")'),
    (
        r'PushButton\(FIF\.CERTIFICATE, "安全扫描"',
        r'PushButton(FIF.CERTIFICATE, tr("skill.scan_security")',
    ),
    (r'PushButton\(FIF\.DELETE, "删除"', r'PushButton(FIF.DELETE, tr("common.delete")'),
    (
        r'PushButton\(FIF\.FOLDER, "打开目录"',
        r'PushButton(FIF.FOLDER, tr("skill.open_folder")',
    ),
    # 创建标签页
    (r'SubtitleLabel\("创建新 Skill"', r'SubtitleLabel(tr("skill.create_new")'),
    (r'BodyLabel\("Skill 名称:"', r'BodyLabel(tr("skill.skill_name") + ":")'),
    (r'BodyLabel\("描述:"', r'BodyLabel(tr("common.description") + ":")'),
    (r'BodyLabel\("许可证:"', r'BodyLabel(tr("skill.skill_license") + ":")'),
    (r'BodyLabel\("兼容性:"', r'BodyLabel(tr("skill.skill_compatibility") + ":")'),
    (r'BodyLabel\("保存位置:"', r'BodyLabel(tr("skill.save_location") + ":")'),
    (r'BodyLabel\("Skill 内容:"', r'BodyLabel(tr("skill.skill_content") + ":")'),
    (r'PrimaryPushButton\("保存 Skill"', r'PrimaryPushButton(tr("skill.save_skill")'),
    # 权限配置标签页
    (
        r'SubtitleLabel\("全局 Skill 权限"',
        r'SubtitleLabel(tr("skill.global_permission")',
    ),
    (r'BodyLabel\("模式匹配:"', r'BodyLabel(tr("skill.pattern_match") + ":")'),
    (r'BodyLabel\("权限:"', r'BodyLabel(tr("skill.permission") + ":")'),
    (r'PushButton\(FIF\.ADD, "添加"', r'PushButton(FIF.ADD, tr("common.add")'),
    (r'PushButton\(FIF\.DELETE, "删除"', r'PushButton(FIF.DELETE, tr("common.delete")'),
]


def main():
    print("SkillPage 文本替换映射已准备")
    print(f"共 {len(SKILL_PAGE_REPLACEMENTS)} 个替换规则")
    for old, new in SKILL_PAGE_REPLACEMENTS:
        print(f"  {old[:50]}... -> {new[:50]}...")


if __name__ == "__main__":
    main()
