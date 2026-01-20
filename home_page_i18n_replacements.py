#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HomePage 国际化替换脚本
将 HomePage 中的硬编码中文文本替换为 tr() 函数调用
"""

import json
from pathlib import Path

# 需要添加到语言文件的新翻译键
NEW_TRANSLATIONS_ZH = {
    "home": {
        "select_config": "选择配置文件",
        "reset_path": "重置为默认路径",
        "select_backup_dir": "选择备份目录",
        "config_stats": "配置统计",
        "validate_config": "配置检测",
        "validation_details": "配置检测详情",
        "no_validation_yet": "点击「配置检测」按钮开始检测...",
        "validation_no_issues": "✅ 未发现配置问题",
        "validation_error_label": "错误",
        "validation_warning_label": "警告",
        "validation_complete": "检测完成",
        "validation_no_issues_msg": "未发现配置问题",
        "validation_errors_warnings": "发现 {error_count} 个错误，{warning_count} 个警告",
        "validation_warnings_only": "发现 {warning_count} 个警告",
        "copy_success": "路径已复制到剪贴板",
        "select_opencode_config": "选择 OpenCode 配置文件",
        "select_ohmyopencode_config": "选择 Oh My OpenCode 配置文件",
        "json_filter": "JSON/JSONC 文件 (*.json *.jsonc);;所有文件 (*)",
        "invalid_config": "无法解析配置文件，请确保是有效的 JSON/JSONC 格式",
        "switched_to_custom": "已切换到自定义配置文件: {filename}",
        "reset_to_default": "已重置为默认配置路径",
        "select_backup_dir_title": "选择备份目录",
        "switched_to_custom_backup": "已切换到自定义备份目录: {dirname}",
        "reset_to_default_backup": "已重置为默认备份目录",
        "config_reloaded": "配置已重新加载",
        "backup_success": "配置已备份",
        "backup_failed": "备份失败",
    }
}

NEW_TRANSLATIONS_EN = {
    "home": {
        "select_config": "Select Config File",
        "reset_path": "Reset to Default Path",
        "select_backup_dir": "Select Backup Directory",
        "config_stats": "Configuration Statistics",
        "validate_config": "Validate Configuration",
        "validation_details": "Validation Details",
        "no_validation_yet": "Click 'Validate Configuration' button to start...",
        "validation_no_issues": "✅ No configuration issues found",
        "validation_error_label": "Error",
        "validation_warning_label": "Warning",
        "validation_complete": "Validation Complete",
        "validation_no_issues_msg": "No configuration issues found",
        "validation_errors_warnings": "Found {error_count} errors, {warning_count} warnings",
        "validation_warnings_only": "Found {warning_count} warnings",
        "copy_success": "Path copied to clipboard",
        "select_opencode_config": "Select OpenCode Config File",
        "select_ohmyopencode_config": "Select Oh My OpenCode Config File",
        "json_filter": "JSON/JSONC Files (*.json *.jsonc);;All Files (*)",
        "invalid_config": "Cannot parse config file, please ensure it's valid JSON/JSONC format",
        "switched_to_custom": "Switched to custom config file: {filename}",
        "reset_to_default": "Reset to default config path",
        "select_backup_dir_title": "Select Backup Directory",
        "switched_to_custom_backup": "Switched to custom backup directory: {dirname}",
        "reset_to_default_backup": "Reset to default backup directory",
        "config_reloaded": "Configuration reloaded",
        "backup_success": "Configuration backed up",
        "backup_failed": "Backup failed",
    }
}

# 需要替换的文本映射（旧文本 -> 新的 tr() 调用）
REPLACEMENTS = [
    # _format_validation_details 方法
    ('"✅ 未发现配置问题"', 'tr("home.validation_no_issues")'),
    ('"错误"', 'tr("home.validation_error_label")'),
    ('"警告"', 'tr("home.validation_warning_label")'),
    # _on_validate_config 方法
    (
        '"检测完成", "未发现配置问题"',
        'tr("home.validation_complete"), tr("home.validation_no_issues_msg")',
    ),
    (
        '"检测完成", f"发现 {len(errors)} 个错误，{len(warnings)} 个警告"',
        'tr("home.validation_complete"), tr("home.validation_errors_warnings", error_count=len(errors), warning_count=len(warnings))',
    ),
    (
        '"检测完成", f"发现 {len(warnings)} 个警告"',
        'tr("home.validation_complete"), tr("home.validation_warnings_only", warning_count=len(warnings))',
    ),
    # _copy_to_clipboard 方法
    ('"成功", "路径已复制到剪贴板"', 'tr("common.success"), tr("home.copy_success")'),
    # _browse_config 方法
    (
        'title = (\n            "选择 OpenCode 配置文件"\n            if config_type == "opencode"\n            else "选择 Oh My OpenCode 配置文件"\n        )',
        'title = (\n            tr("home.select_opencode_config")\n            if config_type == "opencode"\n            else tr("home.select_ohmyopencode_config")\n        )',
    ),
    ('"JSON/JSONC 文件 (*.json *.jsonc);;所有文件 (*)"', 'tr("home.json_filter")'),
    (
        '"错误", "无法解析配置文件，请确保是有效的 JSON/JSONC 格式"',
        'tr("common.error"), tr("home.invalid_config")',
    ),
    (
        '"成功", f"已切换到自定义配置文件: {path.name}"',
        'tr("common.success"), tr("home.switched_to_custom", filename=path.name)',
    ),
    # _reset_config_path 方法
    (
        '"成功", "已重置为默认配置路径"',
        'tr("common.success"), tr("home.reset_to_default")',
    ),
    # _browse_backup_dir 方法
    ('"选择备份目录"', 'tr("home.select_backup_dir_title")'),
    (
        '"成功", f"已切换到自定义备份目录: {path.name}"',
        'tr("common.success"), tr("home.switched_to_custom_backup", dirname=path.name)',
    ),
    # _reset_backup_dir 方法
    (
        '"成功", "已重置为默认备份目录"',
        'tr("common.success"), tr("home.reset_to_default_backup")',
    ),
    # _on_reload 方法
    ('"成功", "配置已重新加载"', 'tr("common.success"), tr("home.config_reloaded")'),
    # _on_backup 方法
    ('"成功", "配置已备份"', 'tr("common.success"), tr("home.backup_success")'),
    ('"错误", "备份失败"', 'tr("common.error"), tr("home.backup_failed")'),
]


def update_language_files():
    """更新语言文件"""
    locales_dir = Path("locales")

    # 更新中文语言文件
    zh_file = locales_dir / "zh_CN.json"
    with open(zh_file, "r", encoding="utf-8") as f:
        zh_data = json.load(f)

    # 合并新的翻译键
    if "home" not in zh_data:
        zh_data["home"] = {}
    zh_data["home"].update(NEW_TRANSLATIONS_ZH["home"])

    with open(zh_file, "w", encoding="utf-8") as f:
        json.dump(zh_data, f, indent=2, ensure_ascii=False)

    print(f"[OK] Updated {zh_file}")

    # 更新英文语言文件
    en_file = locales_dir / "en_US.json"
    with open(en_file, "r", encoding="utf-8") as f:
        en_data = json.load(f)

    # 合并新的翻译键
    if "home" not in en_data:
        en_data["home"] = {}
    en_data["home"].update(NEW_TRANSLATIONS_EN["home"])

    with open(en_file, "w", encoding="utf-8") as f:
        json.dump(en_data, f, indent=2, ensure_ascii=False)

    print(f"[OK] Updated {en_file}")


def replace_hardcoded_text():
    """替换硬编码文本"""
    main_file = Path("opencode_config_manager_fluent.py")

    with open(main_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 执行替换
    for old_text, new_text in REPLACEMENTS:
        if old_text in content:
            content = content.replace(old_text, new_text)
            print(f"[OK] Replaced: {old_text[:50]}...")
        else:
            print(f"[WARN] Not found: {old_text[:50]}...")

    with open(main_file, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"\n[OK] Updated {main_file}")


if __name__ == "__main__":
    print("=" * 60)
    print("HomePage I18N Replacement Script")
    print("=" * 60)

    print("\nStep 1: Update language files...")
    update_language_files()

    print("\nStep 2: Replace hardcoded text...")
    replace_hardcoded_text()

    print("\n" + "=" * 60)
    print("[OK] HomePage I18N replacement completed!")
    print("=" * 60)
