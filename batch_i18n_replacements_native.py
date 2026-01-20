#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量国际化替换脚本 - NativeProviderPage
"""

from pathlib import Path

# 读取主文件
main_file = Path("opencode_config_manager_fluent.py")
with open(main_file, "r", encoding="utf-8") as f:
    content = f.read()

# NativeProviderPage 替换列表
replacements = [
    (
        'super().__init__("原生 Provider", parent)',
        'super().__init__(tr("native_provider.title"), parent)',
    ),
    ('"配置 Provider"', 'tr("native_provider.config_provider")'),
    ('"测试连接"', 'tr("native_provider.test_connection")'),
    ('"删除配置"', 'tr("native_provider.delete_config")'),
    (
        '["Provider", "SDK", "状态", "环境变量"]',
        '[tr("native_provider.provider"), tr("native_provider.sdk"), tr("native_provider.status"), tr("native_provider.env_vars")]',
    ),
    ('"已配置"', 'tr("native_provider.configured")'),
    ('"未配置"', 'tr("native_provider.not_configured")'),
    (
        '"成功", "Provider 配置已保存"',
        'tr("common.success"), tr("native_provider.config_saved")',
    ),
    (
        '"成功", "Provider 配置已删除"',
        'tr("common.success"), tr("native_provider.config_deleted")',
    ),
    (
        '"成功", "连接测试成功"',
        'tr("common.success"), tr("native_provider.test_success")',
    ),
    ('"错误", "连接测试失败"', 'tr("common.error"), tr("native_provider.test_failed")'),
    (
        '"提示", "请先选择一个 Provider"',
        'tr("common.warning"), tr("native_provider.select_provider_first")',
    ),
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
