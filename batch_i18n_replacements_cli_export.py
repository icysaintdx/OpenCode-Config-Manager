#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量替换 CLIExportPage 中的硬编码中文字符串为 tr() 调用"""

# 替换规则：(原字符串, 翻译键, 是否需要参数)
replacements = [
    # 页面标题和描述
    (
        'super().__init__("CLI 工具导出", parent)',
        'super().__init__(tr("cli_export.title"), parent)',
        False,
    ),
    (
        '"将 OpenCode 中的 Provider 配置一键导出到 Claude Code / Codex CLI / Gemini CLI 使用"',
        'tr("cli_export.description")',
        False,
    ),
    # 按钮
    (
        'PushButton(FIF.EDIT, "修复", top_card)',
        'PushButton(FIF.EDIT, tr("cli_export.fix"), top_card)',
        False,
    ),
    (
        'refresh_btn.setToolTip("刷新检测")',
        'refresh_btn.setToolTip(tr("cli_export.refresh_detection"))',
        False,
    ),
    (
        'PrimaryPushButton(FIF.SEND, "一键导出全部", main_card)',
        'PrimaryPushButton(FIF.SEND, tr("cli_export.batch_export_all"), main_card)',
        False,
    ),
    (
        'PushButton(FIF.FOLDER, "查看备份", main_card)',
        'PushButton(FIF.FOLDER, tr("cli_export.view_backup"), main_card)',
        False,
    ),
    (
        'PushButton(FIF.HISTORY, "恢复备份", main_card)',
        'PushButton(FIF.HISTORY, tr("cli_export.restore_backup"), main_card)',
        False,
    ),
    (
        'PrimaryPushButton(FIF.SEND, "导出", preview_frame)',
        'PrimaryPushButton(FIF.SEND, tr("cli_export.export"), preview_frame)',
        False,
    ),
    (
        'HyperlinkButton("", "编辑", model_frame)',
        'HyperlinkButton("", tr("cli_export.edit"), model_frame)',
        False,
    ),
    # 配置区域
    (
        '"导出配置 (仅用于导出，不修改 OpenCode 配置)", model_frame',
        'tr("cli_export.export_config_title"), model_frame',
        False,
    ),
    (
        'self.claude_base_url_edit.setPlaceholderText("从 Provider 配置获取")',
        'self.claude_base_url_edit.setPlaceholderText(tr("cli_export.from_provider_config"))',
        False,
    ),
    (
        'self.codex_base_url_edit.setPlaceholderText("从 Provider 配置获取")',
        'self.codex_base_url_edit.setPlaceholderText(tr("cli_export.from_provider_config"))',
        False,
    ),
    (
        'self.gemini_base_url_edit.setPlaceholderText("从 Provider 配置获取")',
        'self.gemini_base_url_edit.setPlaceholderText(tr("cli_export.from_provider_config"))',
        False,
    ),
    # 模型提示
    (
        '"💡 可下拉选择或直接输入自定义模型名称，留空使用默认", model_frame',
        'tr("cli_export.model_hint_full"), model_frame',
        False,
    ),
    (
        'CaptionLabel("💡 可下拉选择或直接输入", model_frame)',
        'CaptionLabel(tr("cli_export.model_hint_simple"), model_frame)',
        False,
    ),
    # 预览标题
    (
        'StrongBodyLabel("配置预览 - settings.json", preview_frame)',
        'StrongBodyLabel(tr("cli_export.preview_title_claude"), preview_frame)',
        False,
    ),
    (
        'StrongBodyLabel("配置预览", preview_frame)',
        'StrongBodyLabel(tr("cli_export.preview_title_codex"), preview_frame)',
        False,
    ),
    # 模型标签
    (
        'CaptionLabel("模型:", model_frame)',
        'CaptionLabel(tr("cli_export.model") + ":", model_frame)',
        False,
    ),
    # 状态标签
    (
        'CaptionLabel("最近备份: 无", main_card)',
        'CaptionLabel(tr("cli_export.latest_backup_none"), main_card)',
        False,
    ),
    (
        'self.provider_combo.addItem("(无可用 Provider)")',
        'self.provider_combo.addItem(tr("cli_export.no_provider"))',
        False,
    ),
    (
        'if not provider_name or provider_name == "(无可用 Provider)":',
        'if not provider_name or provider_name == tr("cli_export.no_provider"):',
        False,
    ),
    (
        'combo.addItem("(无可用模型)", "")',
        'combo.addItem(tr("cli_export.no_model"), "")',
        False,
    ),
    (
        'self.config_status_label.setText("✓ 配置完整")',
        'self.config_status_label.setText(tr("cli_export.config_complete"))',
        False,
    ),
    # 错误和成功消息
    (
        'self.claude_preview_text.setPlainText("请先选择 Provider")',
        'self.claude_preview_text.setPlainText(tr("cli_export.select_provider_first"))',
        False,
    ),
    (
        'self.codex_auth_text.setPlainText("请先选择 Provider")',
        'self.codex_auth_text.setPlainText(tr("cli_export.select_provider_first"))',
        False,
    ),
    (
        'self.codex_config_text.setPlainText("请先选择 Provider")',
        'self.codex_config_text.setPlainText(tr("cli_export.select_provider_first"))',
        False,
    ),
    (
        'self.gemini_env_text.setPlainText("请先选择 Provider")',
        'self.gemini_env_text.setPlainText(tr("cli_export.select_provider_first"))',
        False,
    ),
    (
        'self.gemini_settings_text.setPlainText("请先选择 Provider")',
        'self.gemini_settings_text.setPlainText(tr("cli_export.select_provider_first"))',
        False,
    ),
    (
        'self.show_error("导出失败", "请先选择 Provider")',
        'self.show_error(tr("cli_export.export_failed"), tr("cli_export.select_provider_first"))',
        False,
    ),
    (
        'self.show_error("配置不完整", "\\n".join(result.errors))',
        'self.show_error(tr("cli_export.config_incomplete"), "\\n".join(result.errors))',
        False,
    ),
    (
        'self.show_error("导出失败", f"未知的 CLI 类型: {cli_type}")',
        'self.show_error(tr("cli_export.export_failed"), tr("cli_export.unknown_cli_type", cli_type=cli_type))',
        True,
    ),
    (
        'self.show_error("导出失败", export_result.error_message or "未知错误")',
        'self.show_error(tr("cli_export.export_failed"), export_result.error_message or tr("cli_export.unknown_error"))',
        False,
    ),
    (
        'self.show_warning("已恢复", "已自动恢复原配置")',
        'self.show_warning(tr("cli_export.restored"), tr("cli_export.auto_restored"))',
        False,
    ),
    (
        'self.show_warning("无可用目标", "没有检测到已安装的 CLI 工具")',
        'self.show_warning(tr("cli_export.no_available_targets"), tr("cli_export.no_cli_detected"))',
        False,
    ),
    (
        'self.show_warning("无备份", "备份目录不存在")',
        'self.show_warning(tr("cli_export.no_backup"), tr("cli_export.backup_dir_not_exist"))',
        False,
    ),
    (
        'self.show_success("恢复成功", "已恢复备份配置")',
        'self.show_success(tr("cli_export.restore_success"), tr("cli_export.backup_restored"))',
        False,
    ),
    # 带参数的消息
    (
        'self.backup_info_label.setText(f"最近备份: {time_str} ({latest.cli_type})")',
        'self.backup_info_label.setText(tr("cli_export.latest_backup", time_str=time_str, cli_type=latest.cli_type))',
        True,
    ),
    (
        'error_msg = f"生成预览失败: {e}"',
        'error_msg = tr("cli_export.preview_generation_failed", e=str(e))',
        True,
    ),
    (
        'title="保存成功", content="通用配置已更新"',
        'title=tr("cli_export.save_success"), content=tr("cli_export.common_config_updated")',
        False,
    ),
    (
        '"导出成功", f"已导出到 {cli_type.upper()}: {files_str}"',
        'tr("cli_export.export_success"), tr("cli_export.exported_to", cli_type=cli_type.upper(), files_str=files_str)',
        True,
    ),
    (
        'self.show_success("批量导出成功", f"成功导出到 {successful} 个 CLI 工具")',
        'self.show_success(tr("cli_export.batch_export_success"), tr("cli_export.exported_to_count", successful=successful))',
        True,
    ),
    ('"部分导出失败",', 'tr("cli_export.partial_export_failed"),', False),
    (
        'f"成功: {successful}, 失败: {failed}\\n"',
        'tr("cli_export.success_failed_count", successful=successful, failed=failed) + "\\n"',
        True,
    ),
]

# 读取文件
with open("opencode_config_manager_fluent.py", "r", encoding="utf-8") as f:
    content = f.read()

# 执行替换
replaced_count = 0
not_found = []
for old, new, has_params in replacements:
    if old in content:
        content = content.replace(old, new)
        replaced_count += 1
    else:
        not_found.append(old[:80])

# 保存文件
with open("opencode_config_manager_fluent.py", "w", encoding="utf-8") as f:
    f.write(content)

with open("cli_export_replacement_result.txt", "w", encoding="utf-8") as f:
    f.write(f"CLIExportPage 批量替换完成\n")
    f.write(f"成功替换: {replaced_count} 处\n")
    f.write(f"总规则数: {len(replacements)}\n")
    if not_found:
        f.write(f"\n未找到的字符串:\n")
        for item in not_found:
            f.write(f"  - {item}\n")

print(f"Completed! Replaced {replaced_count}/{len(replacements)} items")
