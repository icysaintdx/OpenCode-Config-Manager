#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全面查找所有未翻译的中文字符串"""

import re

# 读取文件
with open("opencode_config_manager_fluent.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# 查找中文字符串的模式
chinese_pattern = re.compile(r'["\']([^"\']*[\u4e00-\u9fa5]+[^"\']*)["\']')

found_strings = []

for i, line in enumerate(lines):
    line_num = i + 1

    # 跳过已经使用 tr() 的行
    if "tr(" in line:
        continue

    # 跳过注释和 docstring
    stripped = line.strip()
    if stripped.startswith("#"):
        continue

    # 查找中文字符串
    matches = chinese_pattern.findall(line)
    for match in matches:
        # 跳过一些特殊情况
        if match in ["utf-8", "zh_CN", "en_US"]:
            continue
        found_strings.append((line_num, match, line.strip()))

# 输出结果到文件
with open("all_remaining_chinese.txt", "w", encoding="utf-8") as out:
    out.write(f"找到 {len(found_strings)} 个未翻译的中文字符串:\n\n")

    # 按类别分组
    categories = {"按钮": [], "标题": [], "标签": [], "提示": [], "其他": []}

    for line_num, text, full_line in found_strings:
        # 简单分类
        if any(
            word in text
            for word in ["取消", "保存", "确定", "添加", "删除", "编辑", "测试", "配置"]
        ):
            categories["按钮"].append((line_num, text, full_line))
        elif any(word in text for word in ["标题", "名称", "描述"]):
            categories["标题"].append((line_num, text, full_line))
        elif any(word in text for word in ["状态", "环境变量", "已选", "全部", "系列"]):
            categories["标签"].append((line_num, text, full_line))
        elif any(word in text for word in ["提示", "警告", "错误", "成功"]):
            categories["提示"].append((line_num, text, full_line))
        else:
            categories["其他"].append((line_num, text, full_line))

    for category, items in categories.items():
        if items:
            out.write(f"\n### {category} ({len(items)} 个) ###\n\n")
            for line_num, text, full_line in items[:50]:  # 每类最多显示50个
                out.write(f"行 {line_num}: {text}\n")
                out.write(f"  {full_line}\n\n")

print(f"完成！找到 {len(found_strings)} 个未翻译的中文字符串")
print(f"结果已保存到 all_remaining_chinese.txt")

# 统计
print(f"\n分类统计:")
for category, items in categories.items():
    if items:
        print(f"  {category}: {len(items)} 个")
