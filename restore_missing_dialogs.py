#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""恢复被删除的 ModelSelectDialog 和 ProviderDialog 类"""

# 读取当前文件
with open("opencode_config_manager_fluent.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# 读取备份的类
with open("model_select_dialog_backup.txt", "r", encoding="utf-8") as f:
    model_select_lines = f.readlines()

with open("provider_dialog_backup.txt", "r", encoding="utf-8") as f:
    provider_dialog_lines = f.readlines()

# 找到 ModelPresetCustomDialog 类的结束位置（NativeProviderDialog 类的开始位置）
native_provider_dialog_line = None
for i, line in enumerate(lines):
    if line.startswith("class NativeProviderDialog(QDialog):"):
        native_provider_dialog_line = i
        break

if native_provider_dialog_line is None:
    print("错误：找不到 NativeProviderDialog 类")
    exit(1)

print(f"找到 NativeProviderDialog 在第 {native_provider_dialog_line + 1} 行")

# 在 NativeProviderDialog 之前插入两个类
new_lines = lines[:native_provider_dialog_line]
new_lines.extend(model_select_lines)
new_lines.append("\n\n")
new_lines.extend(provider_dialog_lines)
new_lines.append("\n\n")
new_lines.extend(lines[native_provider_dialog_line:])

# 保存文件
with open("opencode_config_manager_fluent.py", "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print(f"成功恢复 ModelSelectDialog 和 ProviderDialog 类")
print(f"插入位置：第 {native_provider_dialog_line + 1} 行之前")
print(f"ModelSelectDialog: {len(model_select_lines)} 行")
print(f"ProviderDialog: {len(provider_dialog_lines)} 行")
