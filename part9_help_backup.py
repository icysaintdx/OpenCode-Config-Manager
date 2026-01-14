# -*- coding: utf-8 -*-
"""
OpenCode 配置管理器 v0.9.0 - PyQt5 + QFluentWidgets 版本
Part 9: Help页面和备份恢复功能
"""

from PyQt5.QtCore import Qt, pyqtSignal, QUrl
from PyQt5.QtGui import QFont, QDesktopServices
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QSplitter
)

from qfluentwidgets import (
    FluentIcon as FIF, InfoBar, InfoBarPosition, MessageBox,
    PushButton, PrimaryPushButton, TransparentPushButton,
    SubtitleLabel, BodyLabel, CaptionLabel, TitleLabel,
    CardWidget, SimpleCardWidget,
    ComboBox, LineEdit, TextEdit, SpinBox,
    SwitchButton, CheckBox, RadioButton,
    ListWidget, TableWidget,
    HyperlinkButton,
    ToolTipFilter, ToolTipPosition,
    Dialog
)

from part3_mainwindow import (
    BasePage, SettingCard, SwitchSettingCard, ComboBoxSettingCard,
    SpinBoxSettingCard, LineEditSettingCard, ButtonSettingCard,
    FormCard, ListCard
)


class HelpPage(BasePage):
    """帮助页面"""

    def __init__(self, version: str, parent=None):
        super().__init__("帮助", parent)
        self.version = version
        self._init_content()

    def _init_content(self):
        self.add_title("帮助与关于")
        self.add_subtitle("配置优先级说明、使用指南和版本信息")
        self.add_spacing(8)

        # 配置优先级
        priority_card = CardWidget()
        priority_layout = QVBoxLayout(priority_card)
        priority_layout.setContentsMargins(20, 16, 20, 16)
        priority_layout.setSpacing(12)

        priority_title = SubtitleLabel("配置优先级")
        priority_layout.addWidget(priority_title)

        priority_desc = CaptionLabel("OpenCode配置文件的加载优先级（从高到低）")
        priority_desc.setStyleSheet("color: gray;")
        priority_layout.addWidget(priority_desc)

        priorities = [
            ("1. 项目级配置", ".opencode/opencode.json", "当前项目目录下的配置"),
            ("2. 用户级配置", "~/.opencode/opencode.json", "用户主目录下的配置"),
            ("3. 环境变量", "OPENCODE_*", "以OPENCODE_开头的环境变量"),
            ("4. 默认配置", "内置默认值", "程序内置的默认配置"),
        ]

        for level, path, desc in priorities:
            row = QHBoxLayout()
            level_label = BodyLabel(level)
            level_label.setMinimumWidth(120)
            row.addWidget(level_label)

            path_label = CaptionLabel(path)
            path_label.setMinimumWidth(200)
            path_label.setStyleSheet("color: #0078d4;")
            row.addWidget(path_label)

            desc_label = CaptionLabel(desc)
            desc_label.setStyleSheet("color: gray;")
            row.addWidget(desc_label)

            row.addStretch()
            priority_layout.addLayout(row)

        self.content_layout.addWidget(priority_card)

        # 使用说明
        guide_card = CardWidget()
        guide_layout = QVBoxLayout(guide_card)
        guide_layout.setContentsMargins(20, 16, 20, 16)
        guide_layout.setSpacing(12)

        guide_title = SubtitleLabel("使用说明")
        guide_layout.addWidget(guide_title)

        guides = [
            ("服务商配置", "添加API服务商，配置API密钥和端点地址。支持OpenAI、Anthropic等主流服务商。"),
            ("模型配置", "配置模型参数，包括Token限制、上下文窗口大小和特性支持。"),
            ("MCP服务器", "管理Model Context Protocol服务器，支持本地进程和远程SSE两种类型。"),
            ("Agent管理", "创建和管理自定义Agent，配置模型绑定和行为指令。"),
            ("权限配置", "控制文件操作、命令执行等权限，保护系统安全。"),
            ("备份恢复", "定期备份配置文件，支持多版本管理和一键恢复。"),
        ]

        for title, desc in guides:
            item_layout = QVBoxLayout()
            item_title = BodyLabel(f"• {title}")
            item_title.setFont(QFont("Microsoft YaHei UI", 10, QFont.Bold))
            item_layout.addWidget(item_title)

            item_desc = CaptionLabel(f"  {desc}")
            item_desc.setStyleSheet("color: gray;")
            item_desc.setWordWrap(True)
            item_layout.addWidget(item_desc)

            guide_layout.addLayout(item_layout)

        self.content_layout.addWidget(guide_card)

        # 快捷键
        shortcut_card = CardWidget()
        shortcut_layout = QVBoxLayout(shortcut_card)
        shortcut_layout.setContentsMargins(20, 16, 20, 16)
        shortcut_layout.setSpacing(12)

        shortcut_title = SubtitleLabel("快捷键")
        shortcut_layout.addWidget(shortcut_title)

        shortcuts = [
            ("Ctrl+S", "保存当前配置"),
            ("Ctrl+Z", "撤销操作"),
            ("Ctrl+Shift+S", "另存为"),
            ("F5", "刷新配置"),
            ("F1", "打开帮助"),
        ]

        shortcut_grid = QGridLayout()
        shortcut_grid.setSpacing(8)

        for i, (key, desc) in enumerate(shortcuts):
            key_label = BodyLabel(key)
            key_label.setStyleSheet("background: #f0f0f0; padding: 4px 8px; border-radius: 4px;")
            shortcut_grid.addWidget(key_label, i, 0)

            desc_label = BodyLabel(desc)
            shortcut_grid.addWidget(desc_label, i, 1)

        shortcut_grid.setColumnStretch(1, 1)
        shortcut_layout.addLayout(shortcut_grid)

        self.content_layout.addWidget(shortcut_card)

        # 关于
        about_card = CardWidget()
        about_layout = QVBoxLayout(about_card)
        about_layout.setContentsMargins(20, 16, 20, 16)
        about_layout.setSpacing(12)

        about_title = SubtitleLabel("关于")
        about_layout.addWidget(about_title)

        version_row = QHBoxLayout()
        version_row.addWidget(BodyLabel("版本:"))
        version_label = BodyLabel(f"v{self.version}")
        version_label.setStyleSheet("color: #0078d4;")
        version_row.addWidget(version_label)
        version_row.addStretch()
        about_layout.addLayout(version_row)

        framework_row = QHBoxLayout()
        framework_row.addWidget(BodyLabel("框架:"))
        framework_label = BodyLabel("PyQt5 + QFluentWidgets")
        framework_row.addWidget(framework_label)
        framework_row.addStretch()
        about_layout.addLayout(framework_row)

        author_row = QHBoxLayout()
        author_row.addWidget(BodyLabel("作者:"))
        author_label = BodyLabel("OpenCode Team")
        author_row.addWidget(author_label)
        author_row.addStretch()
        about_layout.addLayout(author_row)

        # 链接
        links_row = QHBoxLayout()
        github_btn = HyperlinkButton("https://github.com/opencode", "GitHub")
        links_row.addWidget(github_btn)

        docs_btn = HyperlinkButton("https://opencode.dev/docs", "文档")
        links_row.addWidget(docs_btn)

        links_row.addStretch()
        about_layout.addLayout(links_row)

        self.content_layout.addWidget(about_card)

        self.add_stretch()


class BackupDialog(Dialog):
    """备份管理对话框"""

    def __init__(self, backup_manager, parent=None):
        super().__init__("备份管理", "", parent)
        self.backup_manager = backup_manager
        self._init_ui()
        self._load_backups()

    def _init_ui(self):
        self.textLayout.deleteLater()

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(16)

        # 创建备份
        create_card = CardWidget()
        create_layout = QVBoxLayout(create_card)
        create_layout.setContentsMargins(16, 12, 16, 12)
        create_layout.setSpacing(8)

        create_title = BodyLabel("创建新备份")
        create_title.setFont(QFont("Microsoft YaHei UI", 11, QFont.Bold))
        create_layout.addWidget(create_title)

        create_row = QHBoxLayout()
        self.desc_edit = LineEdit()
        self.desc_edit.setPlaceholderText("备份描述（可选）")
        create_row.addWidget(self.desc_edit, 1)

        create_btn = PrimaryPushButton("创建备份")
        create_btn.clicked.connect(self._create_backup)
        create_row.addWidget(create_btn)

        create_layout.addLayout(create_row)
        layout.addWidget(create_card)

        # 备份列表
        list_title = BodyLabel("备份列表")
        list_title.setFont(QFont("Microsoft YaHei UI", 11, QFont.Bold))
        layout.addWidget(list_title)

        self.backup_list = ListWidget()
        self.backup_list.setMinimumHeight(200)
        layout.addWidget(self.backup_list)

        # 操作按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        restore_btn = PushButton("恢复选中")
        restore_btn.clicked.connect(self._restore_backup)
        btn_row.addWidget(restore_btn)

        delete_btn = PushButton("删除选中")
        delete_btn.clicked.connect(self._delete_backup)
        btn_row.addWidget(delete_btn)

        refresh_btn = PushButton("刷新")
        refresh_btn.clicked.connect(self._load_backups)
        btn_row.addWidget(refresh_btn)

        layout.addLayout(btn_row)

        self.vBoxLayout.insertWidget(0, content)
        self.widget.setMinimumWidth(600)
        self.widget.setMinimumHeight(450)

    def _load_backups(self):
        """加载备份列表"""
        self.backup_list.clear()
        self._backups = self.backup_manager.list_backups()

        for backup in self._backups:
            desc = backup.get("description", "")
            desc_text = f" - {desc}" if desc else ""
            item_text = f"{backup['modified']} ({backup['size']} 字节){desc_text}"
            self.backup_list.addItem(item_text)

    def _create_backup(self):
        """创建备份"""
        desc = self.desc_edit.text().strip()
        result = self.backup_manager.create_backup(desc)
        if result:
            self.desc_edit.clear()
            self._load_backups()
            InfoBar.success(
                title="成功",
                content="备份已创建",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
        else:
            InfoBar.error(
                title="错误",
                content="创建备份失败",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )

    def _restore_backup(self):
        """恢复备份"""
        index = self.backup_list.currentRow()
        if index < 0 or index >= len(self._backups):
            InfoBar.warning(
                title="提示",
                content="请先选择要恢复的备份",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return

        backup = self._backups[index]
        box = MessageBox("确认恢复", f"确定要恢复备份 '{backup['modified']}' 吗？\n当前配置将被覆盖。", self)
        if box.exec():
            if self.backup_manager.restore_backup(backup["name"]):
                InfoBar.success(
                    title="成功",
                    content="备份已恢复",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
            else:
                InfoBar.error(
                    title="错误",
                    content="恢复备份失败",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )

    def _delete_backup(self):
        """删除备份"""
        index = self.backup_list.currentRow()
        if index < 0 or index >= len(self._backups):
            InfoBar.warning(
                title="提示",
                content="请先选择要删除的备份",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return

        backup = self._backups[index]
        box = MessageBox("确认删除", f"确定要删除备份 '{backup['modified']}' 吗？", self)
        if box.exec():
            if self.backup_manager.delete_backup(backup["name"]):
                self._load_backups()
                InfoBar.success(
                    title="成功",
                    content="备份已删除",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
            else:
                InfoBar.error(
                    title="错误",
                    content="删除备份失败",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )


class VersionChecker:
    """版本检查器"""

    def __init__(self, current_version: str):
        self.current_version = current_version
        self.latest_version = None
        self.update_url = "https://github.com/opencode/releases"

    def check_update(self) -> tuple:
        """检查更新，返回 (has_update, latest_version, update_url)"""
        # 这里可以实现实际的版本检查逻辑
        # 目前返回模拟数据
        return False, self.current_version, self.update_url

    def compare_versions(self, v1: str, v2: str) -> int:
        """比较版本号，返回 -1, 0, 1"""
        def parse_version(v):
            return [int(x) for x in v.replace("v", "").split(".")]

        try:
            p1 = parse_version(v1)
            p2 = parse_version(v2)

            for a, b in zip(p1, p2):
                if a < b:
                    return -1
                elif a > b:
                    return 1
            return 0
        except Exception:
            return 0
