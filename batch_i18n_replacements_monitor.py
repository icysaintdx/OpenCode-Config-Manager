#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量国际化替换脚本 - MonitorPage 剩余部分
"""

from pathlib import Path

# 读取主文件
main_file = Path("opencode_config_manager_fluent.py")
with open(main_file, "r", encoding="utf-8") as f:
    content = f.read()

# MonitorPage 剩余部分替换列表
replacements = [
    # 统计卡片标签
    ('FIF.ACCEPT, "可用率", "—"', 'FIF.ACCEPT, tr("monitor.availability_rate"), "—"'),
    ('FIF.CANCEL, "异常", "0"', 'FIF.CANCEL, tr("monitor.error_count"), "0"'),
    ('FIF.CHAT, "对话延迟", "—"', 'FIF.CHAT, tr("monitor.chat_latency"), "—"'),
    ('FIF.WIFI, "Ping", "—"', 'FIF.WIFI, tr("monitor.ping"), "—"'),
    ('FIF.TAG, "目标", "0"', 'FIF.TAG, tr("monitor.target_count"), "0"'),
    ('FIF.HISTORY, "最近", "—"', 'FIF.HISTORY, tr("monitor.last_checked_short"), "—"'),
    # 按钮文本
    (
        'PrimaryPushButton(FIF.SYNC, "检测", wrapper)',
        'PrimaryPushButton(FIF.SYNC, tr("monitor.check"), wrapper)',
    ),
    (
        'PushButton(FIF.PLAY, "启动", wrapper)',
        'PushButton(FIF.PLAY, tr("monitor.start"), wrapper)',
    ),
    ('"启动/停止对话延迟自动检测"', 'tr("monitor.toggle_tooltip")'),
    # 表格列标题
    ('"模型/提供商"', 'tr("monitor.model_provider")'),
    ('"可用率"', 'tr("monitor.availability_rate")'),
    ('"对话延迟"', 'tr("monitor.chat_latency")'),
    ('"Ping延迟"', 'tr("monitor.ping_latency")'),
    ('"最后检测"', 'tr("monitor.last_check")'),
    ('"历史"', 'tr("monitor.history")'),
    # 状态文本
    ('"无目标"', 'tr("monitor.no_targets")'),
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
