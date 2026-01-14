# -*- coding: utf-8 -*-
"""
OpenCode 配置管理器 v0.9.0 - PyQt5 + QFluentWidgets 版本
Part 8: Compaction页面和Import页面
"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QSplitter, QFileDialog
)

from qfluentwidgets import (
    FluentIcon as FIF, InfoBar, InfoBarPosition, MessageBox,
    PushButton, PrimaryPushButton, TransparentPushButton,
    SubtitleLabel, BodyLabel, CaptionLabel,
    CardWidget, SimpleCardWidget,
    ComboBox, LineEdit, TextEdit, SpinBox,
    SwitchButton, CheckBox, RadioButton,
    ListWidget, TableWidget,
    ProgressBar,
    ToolTipFilter, ToolTipPosition,
    Dialog
)

from part3_mainwindow import (
    BasePage, SettingCard, SwitchSettingCard, ComboBoxSettingCard,
    SpinBoxSettingCard, LineEditSettingCard, ButtonSettingCard,
    FormCard, ListCard
)


class CompactionPage(BasePage):
    """上下文压缩配置页面"""

    def __init__(self, config_manager, parent=None):
        super().__init__("压缩配置", parent)
        self.config_manager = config_manager
        self._init_content()
        self._load_data()

    def _init_content(self):
        self.add_title("上下文压缩配置")
        self.add_subtitle("配置自动压缩功能，优化长对话的上下文管理")
        self.add_spacing(8)

        # 启用压缩
        enable_card = CardWidget()
        enable_layout = QHBoxLayout(enable_card)
        enable_layout.setContentsMargins(20, 16, 20, 16)

        enable_text = QVBoxLayout()
        enable_title = BodyLabel("启用自动压缩")
        enable_title.setFont(QFont("Microsoft YaHei UI", 11))
        enable_text.addWidget(enable_title)

        enable_desc = CaptionLabel("当上下文超过阈值时自动压缩历史消息")
        enable_desc.setStyleSheet("color: gray;")
        enable_text.addWidget(enable_desc)

        enable_layout.addLayout(enable_text)
        enable_layout.addStretch()

        self.enable_switch = SwitchButton()
        self.enable_switch.checkedChanged.connect(self._on_enable_changed)
        enable_layout.addWidget(self.enable_switch)

        self.content_layout.addWidget(enable_card)

        # 压缩参数
        self.param_card = CardWidget()
        param_layout = QVBoxLayout(self.param_card)
        param_layout.setContentsMargins(20, 16, 20, 16)
        param_layout.setSpacing(16)

        param_title = SubtitleLabel("压缩参数")
        param_layout.addWidget(param_title)

        # 压缩阈值
        threshold_row = QHBoxLayout()
        threshold_row.addWidget(BodyLabel("压缩阈值 (Token数):"))
        self.threshold_spin = SpinBox()
        self.threshold_spin.setRange(10000, 1000000)
        self.threshold_spin.setSingleStep(10000)
        self.threshold_spin.setValue(100000)
        self.threshold_spin.setMinimumWidth(150)
        threshold_row.addWidget(self.threshold_spin)
        threshold_row.addStretch()
        param_layout.addLayout(threshold_row)

        threshold_desc = CaptionLabel("当上下文Token数超过此值时触发压缩")
        threshold_desc.setStyleSheet("color: gray;")
        param_layout.addWidget(threshold_desc)

        # 修剪旧输出
        trim_row = QHBoxLayout()
        trim_text = QVBoxLayout()
        trim_title = BodyLabel("修剪旧输出")
        trim_text.addWidget(trim_title)
        trim_desc = CaptionLabel("移除较早的输出内容以节省空间")
        trim_desc.setStyleSheet("color: gray;")
        trim_text.addWidget(trim_desc)
        trim_row.addLayout(trim_text)
        trim_row.addStretch()

        self.trim_switch = SwitchButton()
        trim_row.addWidget(self.trim_switch)
        param_layout.addLayout(trim_row)

        self.content_layout.addWidget(self.param_card)

        # 压缩策略
        strategy_card = CardWidget()
        strategy_layout = QVBoxLayout(strategy_card)
        strategy_layout.setContentsMargins(20, 16, 20, 16)
        strategy_layout.setSpacing(12)

        strategy_title = SubtitleLabel("压缩策略")
        strategy_layout.addWidget(strategy_title)

        strategy_row = QHBoxLayout()
        strategy_row.addWidget(BodyLabel("策略:"))
        self.strategy_combo = ComboBox()
        self.strategy_combo.addItems(["summarize", "truncate", "sliding_window"])
        self.strategy_combo.setMinimumWidth(150)
        strategy_row.addWidget(self.strategy_combo)
        strategy_row.addStretch()
        strategy_layout.addLayout(strategy_row)

        strategies_desc = {
            "summarize": "总结 - 将历史消息总结为摘要",
            "truncate": "截断 - 直接移除最早的消息",
            "sliding_window": "滑动窗口 - 保留最近N条消息"
        }

        for strategy, desc in strategies_desc.items():
            desc_label = CaptionLabel(f"• {desc}")
            desc_label.setStyleSheet("color: gray;")
            strategy_layout.addWidget(desc_label)

        self.content_layout.addWidget(strategy_card)

        # 保存按钮
        save_btn = PrimaryPushButton("保存压缩配置")
        save_btn.clicked.connect(self._save_config)
        self.content_layout.addWidget(save_btn)

        self.add_stretch()

    def _load_data(self):
        """加载数据"""
        compaction = self.config_manager.get_compaction()
        self.enable_switch.setChecked(compaction.get("enabled", False))
        self.threshold_spin.setValue(compaction.get("threshold", 100000))
        self.trim_switch.setChecked(compaction.get("trimOldOutput", False))

        strategy = compaction.get("strategy", "summarize")
        self.strategy_combo.setCurrentText(strategy)

        self._on_enable_changed(self.enable_switch.isChecked())

    def _on_enable_changed(self, enabled: bool):
        """启用状态变化"""
        self.param_card.setEnabled(enabled)

    def _save_config(self):
        """保存配置"""
        compaction = {
            "enabled": self.enable_switch.isChecked(),
            "threshold": self.threshold_spin.value(),
            "trimOldOutput": self.trim_switch.isChecked(),
            "strategy": self.strategy_combo.currentText()
        }
        self.config_manager.set_compaction(compaction)
        self.show_success("成功", "压缩配置已保存")


class ImportPage(BasePage):
    """导入配置页面"""

    def __init__(self, config_manager, import_service, backup_manager, parent=None):
        super().__init__("导入配置", parent)
        self.config_manager = config_manager
        self.import_service = import_service
        self.backup_manager = backup_manager
        self._init_content()
        self._detect_configs()

    def _init_content(self):
        self.add_title("导入配置")
        self.add_subtitle("检测并导入外部配置文件，支持合并或覆盖模式")
        self.add_spacing(8)

        # 检测到的配置
        detect_card = CardWidget()
        detect_layout = QVBoxLayout(detect_card)
        detect_layout.setContentsMargins(20, 16, 20, 16)
        detect_layout.setSpacing(12)

        detect_header = QHBoxLayout()
        detect_title = SubtitleLabel("检测到的配置文件")
        detect_header.addWidget(detect_title)
        detect_header.addStretch()

        refresh_btn = PushButton("刷新")
        refresh_btn.setIcon(FIF.SYNC)
        refresh_btn.clicked.connect(self._detect_configs)
        detect_header.addWidget(refresh_btn)

        detect_layout.addLayout(detect_header)

        self.config_list = ListWidget()
        self.config_list.setMaximumHeight(150)
        self.config_list.itemClicked.connect(self._on_config_selected)
        detect_layout.addWidget(self.config_list)

        self.content_layout.addWidget(detect_card)

        # 预览区域
        preview_card = CardWidget()
        preview_layout = QVBoxLayout(preview_card)
        preview_layout.setContentsMargins(20, 16, 20, 16)
        preview_layout.setSpacing(12)

        preview_title = SubtitleLabel("配置预览")
        preview_layout.addWidget(preview_title)

        # 预览信息
        self.preview_info = QWidget()
        preview_info_layout = QGridLayout(self.preview_info)
        preview_info_layout.setSpacing(8)

        preview_info_layout.addWidget(BodyLabel("路径:"), 0, 0)
        self.preview_path = BodyLabel("-")
        self.preview_path.setWordWrap(True)
        preview_info_layout.addWidget(self.preview_path, 0, 1)

        preview_info_layout.addWidget(BodyLabel("大小:"), 1, 0)
        self.preview_size = BodyLabel("-")
        preview_info_layout.addWidget(self.preview_size, 1, 1)

        preview_info_layout.addWidget(BodyLabel("修改时间:"), 2, 0)
        self.preview_modified = BodyLabel("-")
        preview_info_layout.addWidget(self.preview_modified, 2, 1)

        preview_info_layout.addWidget(BodyLabel("服务商:"), 3, 0)
        self.preview_providers = BodyLabel("-")
        preview_info_layout.addWidget(self.preview_providers, 3, 1)

        preview_info_layout.addWidget(BodyLabel("模型:"), 4, 0)
        self.preview_models = BodyLabel("-")
        preview_info_layout.addWidget(self.preview_models, 4, 1)

        preview_info_layout.addWidget(BodyLabel("MCP服务器:"), 5, 0)
        self.preview_mcp = BodyLabel("-")
        preview_info_layout.addWidget(self.preview_mcp, 5, 1)

        preview_info_layout.setColumnStretch(1, 1)
        preview_layout.addWidget(self.preview_info)

        self.content_layout.addWidget(preview_card)

        # 导入选项
        import_card = CardWidget()
        import_layout = QVBoxLayout(import_card)
        import_layout.setContentsMargins(20, 16, 20, 16)
        import_layout.setSpacing(12)

        import_title = SubtitleLabel("导入选项")
        import_layout.addWidget(import_title)

        # 导入模式
        mode_row = QHBoxLayout()
        mode_row.addWidget(BodyLabel("导入模式:"))
        self.merge_radio = RadioButton("合并 (保留现有配置)")
        self.merge_radio.setChecked(True)
        mode_row.addWidget(self.merge_radio)
        self.replace_radio = RadioButton("覆盖 (替换现有配置)")
        mode_row.addWidget(self.replace_radio)
        mode_row.addStretch()
        import_layout.addLayout(mode_row)

        # 备份选项
        backup_row = QHBoxLayout()
        self.backup_check = CheckBox("导入前自动备份当前配置")
        self.backup_check.setChecked(True)
        backup_row.addWidget(self.backup_check)
        backup_row.addStretch()
        import_layout.addLayout(backup_row)

        # 按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        browse_btn = PushButton("浏览文件...")
        browse_btn.clicked.connect(self._browse_file)
        btn_row.addWidget(browse_btn)

        self.import_btn = PrimaryPushButton("导入配置")
        self.import_btn.clicked.connect(self._import_config)
        self.import_btn.setEnabled(False)
        btn_row.addWidget(self.import_btn)

        import_layout.addLayout(btn_row)
        self.content_layout.addWidget(import_card)

        # 导出配置
        export_card = CardWidget()
        export_layout = QVBoxLayout(export_card)
        export_layout.setContentsMargins(20, 16, 20, 16)
        export_layout.setSpacing(12)

        export_title = SubtitleLabel("导出配置")
        export_layout.addWidget(export_title)

        export_desc = CaptionLabel("将当前配置导出为JSON文件，方便备份或迁移")
        export_desc.setStyleSheet("color: gray;")
        export_layout.addWidget(export_desc)

        export_btn = PushButton("导出配置...")
        export_btn.clicked.connect(self._export_config)
        export_layout.addWidget(export_btn, alignment=Qt.AlignLeft)

        self.content_layout.addWidget(export_card)

        self.add_stretch()

        # 存储检测到的配置
        self._detected_configs = []
        self._selected_config = None

    def _detect_configs(self):
        """检测外部配置"""
        self.config_list.clear()
        self._detected_configs = self.import_service.detect_external_configs()

        for config in self._detected_configs:
            self.config_list.addItem(f"{config['name']} - {config['path']}")

        if not self._detected_configs:
            self.config_list.addItem("未检测到外部配置文件")

    def _on_config_selected(self, item):
        """选择配置"""
        index = self.config_list.currentRow()
        if index >= 0 and index < len(self._detected_configs):
            self._selected_config = self._detected_configs[index]
            self._update_preview()
            self.import_btn.setEnabled(True)
        else:
            self._selected_config = None
            self.import_btn.setEnabled(False)

    def _update_preview(self):
        """更新预览"""
        if not self._selected_config:
            return

        self.preview_path.setText(self._selected_config.get("path", "-"))
        self.preview_size.setText(f"{self._selected_config.get('size', 0)} 字节")
        self.preview_modified.setText(self._selected_config.get("modified", "-"))

        preview = self.import_service.preview_import(self._selected_config)
        self.preview_providers.setText(", ".join(preview.get("providers", [])) or "无")
        self.preview_models.setText(", ".join(preview.get("models", [])) or "无")
        self.preview_mcp.setText(", ".join(preview.get("mcpServers", [])) or "无")

    def _browse_file(self):
        """浏览文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择配置文件", "", "JSON文件 (*.json);;所有文件 (*)"
        )
        if file_path:
            try:
                import json
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                import os
                from datetime import datetime
                stat = os.stat(file_path)

                self._selected_config = {
                    "path": file_path,
                    "name": "手动选择",
                    "data": data,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                }
                self._update_preview()
                self.import_btn.setEnabled(True)
            except Exception as e:
                self.show_error("错误", f"无法读取文件: {e}")

    def _import_config(self):
        """导入配置"""
        if not self._selected_config:
            self.show_warning("提示", "请先选择要导入的配置")
            return

        # 备份
        if self.backup_check.isChecked():
            self.backup_manager.create_backup("导入前自动备份")

        # 导入
        merge = self.merge_radio.isChecked()
        if self.import_service.import_config(self._selected_config, merge):
            self.config_manager.load()  # 重新加载配置
            self.show_success("成功", "配置已导入")
        else:
            self.show_error("错误", "导入配置失败")

    def _export_config(self):
        """导出配置"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出配置", "opencode_config.json", "JSON文件 (*.json)"
        )
        if file_path:
            if self.import_service.export_config(file_path):
                self.show_success("成功", f"配置已导出到: {file_path}")
            else:
                self.show_error("错误", "导出配置失败")
