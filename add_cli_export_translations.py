#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""为 CLIExportPage 添加剩余的翻译键"""

import json

# 需要添加的翻译键
new_translations_zh = {
    "cli_export": {
        # 页面基础
        "title": "CLI 工具导出",
        "description": "将 OpenCode 中的 Provider 配置一键导出到 Claude Code / Codex CLI / Gemini CLI 使用",
        # 按钮和操作
        "fix": "修复",
        "refresh_detection": "刷新检测",
        "batch_export_all": "一键导出全部",
        "view_backup": "查看备份",
        "restore_backup": "恢复备份",
        "export": "导出",
        "edit": "编辑",
        # 标签页
        "tab_claude_code": "Claude Code",
        "tab_codex": "Codex CLI",
        "tab_gemini": "Gemini CLI",
        # 配置区域
        "export_config_title": "导出配置 (仅用于导出，不修改 OpenCode 配置)",
        "base_url": "Base URL",
        "from_provider_config": "从 Provider 配置获取",
        "main_model": "主模型",
        "model": "模型",
        "model_hint_full": "💡 可下拉选择或直接输入自定义模型名称，留空使用默认",
        "model_hint_simple": "💡 可下拉选择或直接输入",
        # 预览区域
        "preview_title_claude": "配置预览 - settings.json",
        "preview_title_codex": "配置预览",
        "preview_title_gemini": "配置预览",
        "format_json": "格式化 JSON",
        # 通用配置
        "write_common_config": "写入通用配置",
        # 状态和提示
        "no_provider": "(无可用 Provider)",
        "no_model": "(无可用模型)",
        "config_complete": "✓ 配置完整",
        "latest_backup_none": "最近备份: 无",
        "latest_backup": "最近备份: {time_str} ({cli_type})",
        "select_provider_first": "请先选择 Provider",
        # 错误和成功消息
        "export_failed": "导出失败",
        "export_success": "导出成功",
        "config_incomplete": "配置不完整",
        "unknown_cli_type": "未知的 CLI 类型: {cli_type}",
        "exported_to": "已导出到 {cli_type}: {files_str}",
        "unknown_error": "未知错误",
        "restored": "已恢复",
        "auto_restored": "已自动恢复原配置",
        "no_available_targets": "无可用目标",
        "no_cli_detected": "没有检测到已安装的 CLI 工具",
        "batch_export_success": "批量导出成功",
        "exported_to_count": "成功导出到 {successful} 个 CLI 工具",
        "partial_export_failed": "部分导出失败",
        "success_failed_count": "成功: {successful}, 失败: {failed}",
        "no_backup": "无备份",
        "backup_dir_not_exist": "备份目录不存在",
        "restore_success": "恢复成功",
        "backup_restored": "已恢复备份配置",
        "preview_generation_failed": "生成预览失败: {e}",
        "common_config_updated": "通用配置已更新",
        "save_success": "保存成功",
    }
}

new_translations_en = {
    "cli_export": {
        # Page basics
        "title": "CLI Export",
        "description": "Export OpenCode Provider configuration to Claude Code / Codex CLI / Gemini CLI with one click",
        # Buttons and actions
        "fix": "Fix",
        "refresh_detection": "Refresh Detection",
        "batch_export_all": "Export All",
        "view_backup": "View Backup",
        "restore_backup": "Restore Backup",
        "export": "Export",
        "edit": "Edit",
        # Tabs
        "tab_claude_code": "Claude Code",
        "tab_codex": "Codex CLI",
        "tab_gemini": "Gemini CLI",
        # Configuration area
        "export_config_title": "Export Configuration (for export only, does not modify OpenCode config)",
        "base_url": "Base URL",
        "from_provider_config": "Get from Provider config",
        "main_model": "Main Model",
        "model": "Model",
        "model_hint_full": "💡 Select from dropdown or enter custom model name, leave empty for default",
        "model_hint_simple": "💡 Select from dropdown or enter directly",
        # Preview area
        "preview_title_claude": "Configuration Preview - settings.json",
        "preview_title_codex": "Configuration Preview",
        "preview_title_gemini": "Configuration Preview",
        "format_json": "Format JSON",
        # Common configuration
        "write_common_config": "Write Common Config",
        # Status and hints
        "no_provider": "(No Provider Available)",
        "no_model": "(No Model Available)",
        "config_complete": "✓ Configuration Complete",
        "latest_backup_none": "Latest Backup: None",
        "latest_backup": "Latest Backup: {time_str} ({cli_type})",
        "select_provider_first": "Please select a Provider first",
        # Error and success messages
        "export_failed": "Export Failed",
        "export_success": "Export Successful",
        "config_incomplete": "Configuration Incomplete",
        "unknown_cli_type": "Unknown CLI type: {cli_type}",
        "exported_to": "Exported to {cli_type}: {files_str}",
        "unknown_error": "Unknown Error",
        "restored": "Restored",
        "auto_restored": "Original configuration automatically restored",
        "no_available_targets": "No Available Targets",
        "no_cli_detected": "No installed CLI tools detected",
        "batch_export_success": "Batch Export Successful",
        "exported_to_count": "Successfully exported to {successful} CLI tools",
        "partial_export_failed": "Partial Export Failed",
        "success_failed_count": "Success: {successful}, Failed: {failed}",
        "no_backup": "No Backup",
        "backup_dir_not_exist": "Backup directory does not exist",
        "restore_success": "Restore Successful",
        "backup_restored": "Backup configuration restored",
        "preview_generation_failed": "Preview generation failed: {e}",
        "common_config_updated": "Common configuration updated",
        "save_success": "Save Successful",
    }
}

# 读取现有的语言文件
with open("locales/zh_CN.json", "r", encoding="utf-8") as f:
    zh_data = json.load(f)

with open("locales/en_US.json", "r", encoding="utf-8") as f:
    en_data = json.load(f)

# 添加新的翻译键
zh_data.update(new_translations_zh)
en_data.update(new_translations_en)

# 保存更新后的语言文件
with open("locales/zh_CN.json", "w", encoding="utf-8") as f:
    json.dump(zh_data, f, ensure_ascii=False, indent=2)

with open("locales/en_US.json", "w", encoding="utf-8") as f:
    json.dump(en_data, f, ensure_ascii=False, indent=2)

with open("translation_add_result.txt", "w", encoding="utf-8") as f:
    f.write("翻译键已添加到语言文件\n")
    f.write(f"- zh_CN.json: 新增 {len(new_translations_zh['cli_export'])} 个键\n")
    f.write(f"- en_US.json: 新增 {len(new_translations_en['cli_export'])} 个键\n")

print("Translation keys added successfully")
