#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量国际化替换脚本 - MonitorPage 和 CLIExportPage
"""

from pathlib import Path

# 读取主文件
main_file = Path("opencode_config_manager_fluent.py")
with open(main_file, "r", encoding="utf-8") as f:
    content = f.read()

# MonitorPage 替换列表
monitor_replacements = [
    # 按钮文本
    ('"立即检测"', 'tr("monitor.check_now")'),
    ('"清空历史"', 'tr("monitor.clear_history")'),
    # 状态文本
    ('"可用"', 'tr("monitor.available")'),
    ('"不可用"', 'tr("monitor.unavailable")'),
    ('"检测中..."', 'tr("monitor.checking")'),
    ('"未检测"', 'tr("monitor.never_checked")'),
    # 消息文本
    ('"成功", "历史记录已清空"', 'tr("common.success"), tr("monitor.history_cleared")'),
]

# CLIExportPage 替换列表
cli_replacements = [
    # 标签页标题
    ('"Claude Code"', 'tr("cli_export.tab_claude_code")'),
    ('"Codex CLI"', 'tr("cli_export.tab_codex")'),
    ('"Gemini CLI"', 'tr("cli_export.tab_gemini")'),
    # 表单标签
    ('"选择 Provider:"', 'tr("cli_export.select_provider") + ":"'),
    ('"选择模型:"', 'tr("cli_export.select_model") + ":"'),
    ('"Base URL:"', 'tr("cli_export.base_url") + ":"'),
    ('"API Key:"', 'tr("cli_export.api_key") + ":"'),
    ('"主模型:"', 'tr("cli_export.main_model") + ":"'),
    ('"Haiku 模型:"', 'tr("cli_export.haiku_model") + ":"'),
    ('"Sonnet 模型:"', 'tr("cli_export.sonnet_model") + ":"'),
    ('"Opus 模型:"', 'tr("cli_export.opus_model") + ":"'),
    # 按钮文本
    ('"复制配置"', 'tr("cli_export.copy_config")'),
    ('"格式化"', 'tr("cli_export.format_json")'),
    ('"写入通用配置"', 'tr("cli_export.write_common_config")'),
    ('"编辑通用配置"', 'tr("cli_export.edit_common_config")'),
    # 占位符和提示
    ('"(留空使用默认)"', 'tr("cli_export.leave_empty")'),
    ('"⏳ 配置检测中..."', 'tr("cli_export.detecting_config")'),
    ('"✅ 已检测到配置"', 'tr("cli_export.config_detected")'),
    ('"❌ 未检测到配置"', 'tr("cli_export.config_not_detected")'),
    # 消息文本
    (
        '"成功", "配置已复制到剪贴板"',
        'tr("common.success"), tr("cli_export.config_copied")',
    ),
    ('"错误", "无效的 JSON 格式"', 'tr("common.error"), tr("cli_export.invalid_json")'),
]

# 执行替换
replacements = monitor_replacements + cli_replacements
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
