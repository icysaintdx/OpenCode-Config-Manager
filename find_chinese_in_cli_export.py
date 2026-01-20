#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查找 CLIExportPage 中的所有中文字符串"""

import re

# 读取文件
with open("opencode_config_manager_fluent.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# 找到 CLIExportPage 的范围
start_line = None
end_line = None
for i, line in enumerate(lines):
    if "class CLIExportPage" in line:
        start_line = i
    if (
        start_line
        and i > start_line
        and line.startswith("class ")
        and "CLIExportPage" not in line
    ):
        end_line = i
        break

if not end_line:
    end_line = len(lines)

print(f"CLIExportPage 范围: {start_line + 1} - {end_line + 1}")
print("=" * 80)

# 查找中文字符串
chinese_pattern = re.compile(r'["\']([^"\']*[\u4e00-\u9fa5]+[^"\']*)["\']')
found_strings = []

for i in range(start_line, end_line):
    line = lines[i]
    line_num = i + 1

    # 跳过已经使用 tr() 的行
    if "tr(" in line:
        continue

    # 查找中文字符串
    matches = chinese_pattern.findall(line)
    for match in matches:
        found_strings.append((line_num, match, line.strip()))

# 输出结果到文件
with open("cli_export_chinese_strings.txt", "w", encoding="utf-8") as out:
    out.write(f"找到 {len(found_strings)} 个未翻译的中文字符串:\n\n")
    for line_num, text, full_line in found_strings:
        out.write(f"行 {line_num}: {text}\n")
        out.write(f"  完整行: {full_line}\n\n")

print(
    f"结果已保存到 cli_export_chinese_strings.txt，共找到 {len(found_strings)} 个未翻译的中文字符串"
)
