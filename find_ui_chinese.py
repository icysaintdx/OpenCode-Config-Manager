#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查找真正需要翻译的用户可见中文字符串（排除 docstring）"""

import re

# 读取文件
with open("opencode_config_manager_fluent.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# 查找中文字符串的模式
chinese_pattern = re.compile(r'["\']([^"\']*[\u4e00-\u9fa5]+[^"\']*)["\']')

# 需要关注的用户可见元素
ui_keywords = [
    "PushButton",
    "PrimaryPushButton",
    "ToolButton",
    "ComboBox",
    "LineEdit",
    "TextEdit",
    "PlainTextEdit",
    "Label",
    "BodyLabel",
    "CaptionLabel",
    "StrongBodyLabel",
    "CheckBox",
    "RadioButton",
    "setPlaceholderText",
    "setToolTip",
    "setText",
    "setTitle",
    "setWindowTitle",
    "addItem",
    "setHeaderLabels",
    "setHorizontalHeaderLabels",
    "InfoBar",
    "MessageBox",
    "FluentMessageBox",
    "Pivot",
    "addTab",
]

found_strings = []

for i, line in enumerate(lines):
    line_num = i + 1

    # 跳过已经使用 tr() 的行
    if "tr(" in line:
        continue

    # 跳过注释
    stripped = line.strip()
    if stripped.startswith("#"):
        continue

    # 跳过 docstring（三引号）
    if '"""' in line or "'''" in line:
        continue

    # 只关注包含 UI 关键词的行
    has_ui_keyword = any(keyword in line for keyword in ui_keywords)

    if has_ui_keyword:
        # 查找中文字符串
        matches = chinese_pattern.findall(line)
        for match in matches:
            # 跳过一些特殊情况
            if match in ["utf-8", "zh_CN", "en_US"]:
                continue
            found_strings.append((line_num, match, line.strip()))

# 输出结果到文件
with open("ui_chinese_strings.txt", "w", encoding="utf-8") as out:
    out.write(f"找到 {len(found_strings)} 个需要翻译的UI中文字符串:\n\n")

    for line_num, text, full_line in found_strings:
        out.write(f"行 {line_num}: {text}\n")
        out.write(f"  {full_line}\n\n")

print(f"完成！找到 {len(found_strings)} 个需要翻译的UI中文字符串")
print(f"结果已保存到 ui_chinese_strings.txt")
