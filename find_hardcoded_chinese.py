#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查找 opencode_config_manager_fluent.py 中的硬编码中文"""

import re
import json

# 读取文件
with open("opencode_config_manager_fluent.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# 中文模式
chinese_pattern = re.compile(r"[\u4e00-\u9fa5]+")

# 分类统计
categories = {
    "InfoBar": [],
    "MessageBox": [],
    "Dialog": [],
    "Label": [],
    "Button": [],
    "Placeholder": [],
    "Tooltip": [],
    "Docstring": [],
    "Comment": [],
    "Other": [],
}

in_docstring = False
docstring_marker = None

for i, line in enumerate(lines, 1):
    stripped = line.strip()

    # 跳过空行
    if not stripped:
        continue

    # 检测 docstring
    if stripped.startswith('"""') or stripped.startswith("'''"):
        marker = '"""' if stripped.startswith('"""') else "'''"
        if in_docstring and marker == docstring_marker:
            in_docstring = False
            docstring_marker = None
        elif not in_docstring:
            in_docstring = True
            docstring_marker = marker

    # 跳过已使用 tr() 的行
    if "tr(" in line:
        continue

    # 查找中文
    matches = chinese_pattern.findall(line)
    if not matches:
        continue

    chinese_text = "".join(matches)

    # 分类
    if in_docstring or stripped.startswith("#"):
        if in_docstring:
            categories["Docstring"].append((i, chinese_text, line.strip()[:80]))
        else:
            categories["Comment"].append((i, chinese_text, line.strip()[:80]))
    elif "InfoBar" in line:
        categories["InfoBar"].append((i, chinese_text, line.strip()[:80]))
    elif "MessageBox" in line or "FluentMessageBox" in line:
        categories["MessageBox"].append((i, chinese_text, line.strip()[:80]))
    elif "Dialog" in line:
        categories["Dialog"].append((i, chinese_text, line.strip()[:80]))
    elif "Label" in line or "setText" in line:
        categories["Label"].append((i, chinese_text, line.strip()[:80]))
    elif "Button" in line:
        categories["Button"].append((i, chinese_text, line.strip()[:80]))
    elif "setPlaceholder" in line:
        categories["Placeholder"].append((i, chinese_text, line.strip()[:80]))
    elif "setToolTip" in line:
        categories["Tooltip"].append((i, chinese_text, line.strip()[:80]))
    else:
        categories["Other"].append((i, chinese_text, line.strip()[:80]))

# 输出统计
print("=" * 80)
print("硬编码中文字符串统计报告")
print("=" * 80)
print()

total = sum(len(v) for v in categories.values())
print(f"总计: {total} 处硬编码中文")
print()

for category, items in categories.items():
    if items:
        print(f"{category}: {len(items)} 处")

print()
print("=" * 80)
print("详细列表（每类显示前 10 个）")
print("=" * 80)

for category, items in categories.items():
    if not items:
        continue

    print(f"\n### {category} ({len(items)} 处) ###\n")
    for i, (line_num, chinese, context) in enumerate(items[:10]):
        print(f"  行 {line_num:5d}: {chinese}")
        print(f"           {context}")
        print()

    if len(items) > 10:
        print(f"  ... 还有 {len(items) - 10} 处\n")

# 保存完整数据
with open("hardcoded_chinese_report.json", "w", encoding="utf-8") as f:
    json.dump(
        {k: [(ln, ch, ctx) for ln, ch, ctx in v] for k, v in categories.items()},
        f,
        ensure_ascii=False,
        indent=2,
    )

print("\n完整数据已保存到 hardcoded_chinese_report.json")
