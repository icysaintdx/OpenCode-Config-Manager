#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""处理所有剩余的未翻译字符串"""

import json

# 读取文件
with open("opencode_config_manager_fluent.py", "r", encoding="utf-8") as f:
    content = f.read()

# 定义替换规则
replacements = [
    # 更新提示
    (
        '"发现新版本",\n                f"v{latest_version} 可用，点击查看"',
        'tr("dialog.new_version_found"),\n                tr("dialog.new_version_available", version=latest_version)',
    ),
    # 权限删除确认
    (
        'FluentMessageBox("确认删除", f\'确定要删除权限 "{pattern}" 吗？\', self)',
        'FluentMessageBox(tr("common.confirm_delete_title"), tr("dialog.confirm_delete_permission", pattern=pattern), self)',
    ),
]

# 新增翻译键
new_translations_zh = {
    "dialog": {
        "new_version_found": "发现新版本",
        "new_version_available": "v{version} 可用，点击查看",
        "confirm_delete_permission": '确定要删除权限 "{pattern}" 吗？',
    }
}

new_translations_en = {
    "dialog": {
        "new_version_found": "New Version Found",
        "new_version_available": "v{version} available, click to view",
        "confirm_delete_permission": 'Are you sure you want to delete permission "{pattern}"?',
    }
}

# 执行替换
replaced_count = 0
not_found = []

for old, new in replacements:
    if old in content:
        content = content.replace(old, new)
        replaced_count += 1
    else:
        not_found.append(old[:100])

# 保存文件
with open("opencode_config_manager_fluent.py", "w", encoding="utf-8") as f:
    f.write(content)

# 更新语言文件
with open("locales/zh_CN.json", "r", encoding="utf-8") as f:
    zh_data = json.load(f)

with open("locales/en_US.json", "r", encoding="utf-8") as f:
    en_data = json.load(f)

# 合并新翻译
if "dialog" not in zh_data:
    zh_data["dialog"] = {}
if "dialog" not in en_data:
    en_data["dialog"] = {}

zh_data["dialog"].update(new_translations_zh["dialog"])
en_data["dialog"].update(new_translations_en["dialog"])

# 保存语言文件
with open("locales/zh_CN.json", "w", encoding="utf-8") as f:
    json.dump(zh_data, f, ensure_ascii=False, indent=2)

with open("locales/en_US.json", "w", encoding="utf-8") as f:
    json.dump(en_data, f, ensure_ascii=False, indent=2)

print(f"\n完成！成功替换 {replaced_count}/{len(replacements)} 处")
print(f"新增翻译键: {len(new_translations_zh['dialog'])} 个")

if not_found:
    print(f"\n未找到的字符串:")
    for item in not_found:
        print(f"  - {item}")
