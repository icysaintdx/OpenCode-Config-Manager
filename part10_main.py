# -*- coding: utf-8 -*-
"""
OpenCode 配置管理器 v0.9.0 - PyQt5 + QFluentWidgets 版本
Part 10: 主窗口和应用入口
"""

import sys
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout

from qfluentwidgets import (
    FluentWindow, NavigationInterface, NavigationItemPosition,
    FluentIcon as FIF, Theme, setTheme, isDarkTheme,
    InfoBar, InfoBarPosition, MessageBox,
    PushButton, PrimaryPushButton,
    SubtitleLabel, BodyLabel,
    setThemeColor, NavigationAvatarWidget,
    SplashScreen
)

from part1_constants import (
    VERSION, APP_NAME, APP_TITLE,
    PRESET_SDKS, PRESET_MODEL_CONFIGS, PRESET_AGENTS, CATEGORY_PRESETS
)
from part2_services import (
    ConfigPaths, ConfigManager, BackupManager,
    ModelRegistry, ImportService, MarkdownFileManager
)
from part3_mainwindow import BasePage
from part4_provider_model import ProviderPage, ModelPage
from part5_mcp_agent import MCPPage, OpenCodeAgentPage, AgentPage
from part6_category_permission import CategoryPage, PermissionPage
from part7_skill_rules import SkillPage, RulesPage
from part8_compaction_import import CompactionPage, ImportPage
from part9_help_backup import HelpPage, BackupDialog, VersionChecker


class MainWindow(FluentWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self._init_services()
        self._init_window()
        self._init_navigation()
        self._init_pages()
        self._load_config()

    def _init_services(self):
        """初始化服务"""
        self.paths = ConfigPaths()
        self.paths.ensure_dirs()

        self.config_manager = ConfigManager(self.paths)
        self.backup_manager = BackupManager(self.paths)
        self.model_registry = ModelRegistry()
        self.import_service = ImportService(self.config_manager, self.paths)
        self.md_manager = MarkdownFileManager(self.paths)
        self.version_checker = VersionChecker(VERSION)

    def _init_window(self):
        """初始化窗口"""
        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        # 设置主题色
        setThemeColor("#0078d4")

        # 居中显示
        desktop = QApplication.desktop()
        screen_rect = desktop.availableGeometry(self)
        self.move(
            (screen_rect.width() - self.width()) // 2,
            (screen_rect.height() - self.height()) // 2
        )

    def _init_navigation(self):
        """初始化导航"""
        # 设置导航栏
        self.navigationInterface.setExpandWidth(240)
        self.navigationInterface.setMinimumExpandWidth(200)

        # 添加头像/Logo
        self.navigationInterface.addWidget(
            routeKey="avatar",
            widget=NavigationAvatarWidget("OC", "OpenCode"),
            onClick=lambda: None,
            position=NavigationItemPosition.TOP
        )

    def _init_pages(self):
        """初始化页面"""
        # 服务商配置
        self.provider_page = ProviderPage(self.config_manager, PRESET_SDKS)
        self.addSubInterface(self.provider_page, FIF.CLOUD, "服务商")

        # 模型配置
        self.model_page = ModelPage(self.config_manager, PRESET_MODEL_CONFIGS)
        self.addSubInterface(self.model_page, FIF.ROBOT, "模型")

        # MCP配置
        self.mcp_page = MCPPage(self.config_manager)
        self.addSubInterface(self.mcp_page, FIF.CONNECT, "MCP服务器")

        # OpenCode Agent配置
        self.opencode_agent_page = OpenCodeAgentPage(self.config_manager)
        self.addSubInterface(self.opencode_agent_page, FIF.COMMAND_PROMPT, "OpenCode Agent")

        # Agent管理
        self.agent_page = AgentPage(self.config_manager, PRESET_AGENTS)
        self.addSubInterface(self.agent_page, FIF.PEOPLE, "Agent管理")

        # 分类配置
        self.category_page = CategoryPage(self.config_manager, CATEGORY_PRESETS)
        self.addSubInterface(self.category_page, FIF.TAG, "分类配置")

        # 权限配置
        self.permission_page = PermissionPage(self.config_manager)
        self.addSubInterface(self.permission_page, FIF.CERTIFICATE, "权限配置")

        # 技能配置
        self.skill_page = SkillPage(self.config_manager, self.md_manager)
        self.addSubInterface(self.skill_page, FIF.DEVELOPER_TOOLS, "技能配置")

        # 规则配置
        self.rules_page = RulesPage(self.config_manager, self.md_manager)
        self.addSubInterface(self.rules_page, FIF.BOOK_SHELF, "规则配置")

        # 压缩配置
        self.compaction_page = CompactionPage(self.config_manager)
        self.addSubInterface(self.compaction_page, FIF.ZIP_FOLDER, "压缩配置")

        # 导入配置
        self.import_page = ImportPage(self.config_manager, self.import_service, self.backup_manager)
        self.addSubInterface(self.import_page, FIF.DOWNLOAD, "导入导出")

        # 分隔线
        self.navigationInterface.addSeparator(NavigationItemPosition.BOTTOM)

        # 备份管理（底部）
        self.navigationInterface.addItem(
            routeKey="backup",
            icon=FIF.HISTORY,
            text="备份管理",
            onClick=self._show_backup_dialog,
            position=NavigationItemPosition.BOTTOM
        )

        # 主题切换（底部）
        self.navigationInterface.addItem(
            routeKey="theme",
            icon=FIF.CONSTRACT,
            text="切换主题",
            onClick=self._toggle_theme,
            position=NavigationItemPosition.BOTTOM
        )

        # 保存配置（底部）
        self.navigationInterface.addItem(
            routeKey="save",
            icon=FIF.SAVE,
            text="保存配置",
            onClick=self._save_config,
            position=NavigationItemPosition.BOTTOM
        )

        # 帮助页面（底部）
        self.help_page = HelpPage(VERSION)
        self.addSubInterface(
            self.help_page, FIF.HELP, "帮助",
            position=NavigationItemPosition.BOTTOM
        )

    def _load_config(self):
        """加载配置"""
        self.config_manager.load()

        # 检查更新
        QTimer.singleShot(2000, self._check_update)

    def _save_config(self):
        """保存配置"""
        if self.config_manager.save():
            InfoBar.success(
                title="保存成功",
                content="配置已保存到 " + str(self.paths.config_file),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
        else:
            InfoBar.error(
                title="保存失败",
                content="无法保存配置文件",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )

    def _toggle_theme(self):
        """切换主题"""
        if isDarkTheme():
            setTheme(Theme.LIGHT)
        else:
            setTheme(Theme.DARK)

    def _show_backup_dialog(self):
        """显示备份管理对话框"""
        dialog = BackupDialog(self.backup_manager, self)
        dialog.exec()
        # 如果恢复了备份，重新加载配置
        self.config_manager.load()

    def _check_update(self):
        """检查更新"""
        has_update, latest_version, update_url = self.version_checker.check_update()
        if has_update:
            InfoBar.info(
                title="发现新版本",
                content=f"新版本 v{latest_version} 可用",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=10000,
                parent=self
            )

    def closeEvent(self, event):
        """关闭事件"""
        if self.config_manager.is_dirty():
            box = MessageBox(
                "未保存的更改",
                "配置已修改但未保存，是否保存后退出？",
                self
            )
            box.yesButton.setText("保存并退出")
            box.cancelButton.setText("不保存")

            if box.exec():
                self.config_manager.save()

        event.accept()


def main():
    """主函数"""
    # 启用高DPI支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(VERSION)

    # 设置字体
    font = QFont("Microsoft YaHei UI", 9)
    app.setFont(font)

    # 创建主窗口
    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
