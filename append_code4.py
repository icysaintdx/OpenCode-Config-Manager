#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""临时脚本：追加更多页面和 MainWindow"""

content = '''

# ==================== Permission 页面 ====================
class PermissionPage(BasePage):
    """权限管理页面"""
    
    def __init__(self, main_window, parent=None):
        super().__init__("权限管理", parent)
        self.main_window = main_window
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        # 工具栏
        toolbar = QHBoxLayout()
        
        self.add_btn = PrimaryPushButton(FIF.ADD, "添加权限", self)
        self.add_btn.clicked.connect(self._on_add)
        toolbar.addWidget(self.add_btn)
        
        self.delete_btn = PushButton(FIF.DELETE, "删除", self)
        self.delete_btn.clicked.connect(self._on_delete)
        toolbar.addWidget(self.delete_btn)
        
        toolbar.addStretch()
        
        # 快捷按钮
        for tool in ["Bash", "Read", "Write", "Edit", "WebFetch"]:
            btn = PushButton(tool, self)
            btn.clicked.connect(lambda checked, t=tool: self._quick_add(t))
            toolbar.addWidget(btn)
        
        self.layout.addLayout(toolbar)
        
        # 权限列表
        self.table = TableWidget(self)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["工具名称", "权限级别"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.layout.addWidget(self.table)
    
    def _load_data(self):
        self.table.setRowCount(0)
        config = self.main_window.opencode_config or {}
        permissions = config.get("permission", {})
        
        for tool, level in permissions.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(tool))
            self.table.setItem(row, 1, QTableWidgetItem(str(level)))
    
    def _on_add(self):
        dialog = PermissionDialog(self.main_window, parent=self)
        if dialog.exec_():
            self._load_data()
            self.show_success("成功", "权限已添加")
    
    def _quick_add(self, tool: str):
        config = self.main_window.opencode_config
        if config is None:
            config = {}
            self.main_window.opencode_config = config
        
        if "permission" not in config:
            config["permission"] = {}
        
        config["permission"][tool] = "allow"
        self.main_window.save_opencode_config()
        self._load_data()
        self.show_success("成功", f'已添加 {tool} = allow')
    
    def _on_delete(self):
        row = self.table.currentRow()
        if row < 0:
            self.show_warning("提示", "请先选择一个权限")
            return
        
        tool = self.table.item(row, 0).text()
        config = self.main_window.opencode_config or {}
        if "permission" in config and tool in config["permission"]:
            del config["permission"][tool]
            self.main_window.save_opencode_config()
            self._load_data()
            self.show_success("成功", f'权限 "{tool}" 已删除')


class PermissionDialog(QDialog):
    """权限编辑对话框"""
    
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        
        self.setWindowTitle("添加权限")
        self.setMinimumWidth(400)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # 工具名称
        tool_layout = QHBoxLayout()
        tool_layout.addWidget(BodyLabel("工具名称:", self))
        self.tool_edit = LineEdit(self)
        self.tool_edit.setPlaceholderText("如: Bash, Read, mcp_*")
        tool_layout.addWidget(self.tool_edit)
        layout.addLayout(tool_layout)
        
        # 权限级别
        level_layout = QHBoxLayout()
        level_layout.addWidget(BodyLabel("权限级别:", self))
        self.level_combo = ComboBox(self)
        self.level_combo.addItems(["allow", "ask", "deny"])
        level_layout.addWidget(self.level_combo)
        layout.addLayout(level_layout)
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.cancel_btn = PushButton("取消", self)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        self.save_btn = PrimaryPushButton("保存", self)
        self.save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self.save_btn)
        
        layout.addLayout(btn_layout)
    
    def _on_save(self):
        tool = self.tool_edit.text().strip()
        if not tool:
            InfoBar.error("错误", "请输入工具名称", parent=self)
            return
        
        config = self.main_window.opencode_config
        if config is None:
            config = {}
            self.main_window.opencode_config = config
        
        if "permission" not in config:
            config["permission"] = {}
        
        config["permission"][tool] = self.level_combo.currentText()
        self.main_window.save_opencode_config()
        self.accept()


# ==================== Help 页面 ====================
class HelpPage(BasePage):
    """帮助页面"""
    
    def __init__(self, main_window, parent=None):
        super().__init__("帮助", parent)
        self.main_window = main_window
        self._setup_ui()
    
    def _setup_ui(self):
        # 关于卡片
        about_card = self.add_card("关于")
        about_layout = about_card.layout()
        
        about_layout.addWidget(TitleLabel(f"OpenCode Config Manager v{APP_VERSION}", about_card))
        about_layout.addWidget(BodyLabel("一个可视化的GUI工具，用于管理OpenCode和Oh My OpenCode的配置文件", about_card))
        about_layout.addWidget(BodyLabel(f"作者: {AUTHOR_NAME}", about_card))
        
        link_layout = QHBoxLayout()
        github_btn = PushButton(FIF.GITHUB, "GitHub", about_card)
        github_btn.clicked.connect(lambda: webbrowser.open(GITHUB_URL))
        link_layout.addWidget(github_btn)
        link_layout.addStretch()
        about_layout.addLayout(link_layout)
        
        # 配置优先级卡片
        priority_card = self.add_card("配置优先级（从高到低）")
        priority_layout = priority_card.layout()
        
        priorities = [
            "1. 远程配置 (Remote) - 通过 .well-known/opencode 获取",
            "2. 全局配置 (Global) - ~/.config/opencode/opencode.json",
            "3. 自定义配置 (Custom) - OPENCODE_CONFIG 环境变量指定",
            "4. 项目配置 (Project) - <项目>/opencode.json",
            "5. .opencode 目录 - <项目>/.opencode/config.json",
            "6. 内联配置 (Inline) - OPENCODE_CONFIG_CONTENT 环境变量",
        ]
        
        for p in priorities:
            priority_layout.addWidget(BodyLabel(p, priority_card))
        
        # 配置文件路径卡片
        paths_card = self.add_card("配置文件路径")
        paths_layout = paths_card.layout()
        
        paths_layout.addWidget(BodyLabel(f"OpenCode: {ConfigPaths.get_opencode_config()}", paths_card))
        paths_layout.addWidget(BodyLabel(f"Oh My OpenCode: {ConfigPaths.get_ohmyopencode_config()}", paths_card))
        paths_layout.addWidget(BodyLabel(f"备份目录: {ConfigPaths.get_backup_dir()}", paths_card))
        
        self.layout.addStretch()


# ==================== 主窗口 ====================
class MainWindow(FluentWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        
        # 加载配置
        self.opencode_config = ConfigManager.load_json(ConfigPaths.get_opencode_config())
        self.ohmyopencode_config = ConfigManager.load_json(ConfigPaths.get_ohmyopencode_config())
        
        if self.opencode_config is None:
            self.opencode_config = {}
        if self.ohmyopencode_config is None:
            self.ohmyopencode_config = {}
        
        # 备份管理器
        self.backup_manager = BackupManager()
        
        # 版本检查器
        self.version_checker = VersionChecker(callback=self._on_version_check)
        
        self._init_window()
        self._init_navigation()
        
        # 异步检查更新
        QTimer.singleShot(1000, self.version_checker.check_update_async)
    
    def _init_window(self):
        self.setWindowTitle(f"OpenCode Config Manager v{APP_VERSION}")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        
        # 设置主题
        setTheme(Theme.AUTO)
    
    def _init_navigation(self):
        # Provider 页面
        self.provider_page = ProviderPage(self)
        self.addSubInterface(self.provider_page, FIF.PEOPLE, "Provider")
        
        # Model 页面
        self.model_page = ModelPage(self)
        self.addSubInterface(self.model_page, FIF.ROBOT, "Model")
        
        # MCP 页面
        self.mcp_page = MCPPage(self)
        self.addSubInterface(self.mcp_page, FIF.CLOUD, "MCP")
        
        # OpenCode Agent 页面
        self.opencode_agent_page = OpenCodeAgentPage(self)
        self.addSubInterface(self.opencode_agent_page, FIF.COMMAND_PROMPT, "Agent")
        
        # Permission 页面
        self.permission_page = PermissionPage(self)
        self.addSubInterface(self.permission_page, FIF.CERTIFICATE, "Permission")
        
        # Help 页面 (底部)
        self.help_page = HelpPage(self)
        self.addSubInterface(self.help_page, FIF.HELP, "Help", NavigationItemPosition.BOTTOM)
    
    def save_opencode_config(self):
        """保存 OpenCode 配置"""
        if ConfigManager.save_json(ConfigPaths.get_opencode_config(), self.opencode_config):
            return True
        return False
    
    def save_ohmyopencode_config(self):
        """保存 Oh My OpenCode 配置"""
        if ConfigManager.save_json(ConfigPaths.get_ohmyopencode_config(), self.ohmyopencode_config):
            return True
        return False
    
    def _on_version_check(self, latest_version: str, release_url: str):
        """版本检查回调"""
        if VersionChecker.compare_versions(APP_VERSION, latest_version):
            InfoBar.info(
                title="发现新版本",
                content=f"v{latest_version} 可用，点击查看",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=10000,
                parent=self
            )


# ==================== 程序入口 ====================
def main():
    # 启用高DPI支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
    
    app = QApplication(sys.argv)
    app.setApplicationName("OpenCode Config Manager")
    app.setApplicationVersion(APP_VERSION)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
'''

with open(
    r"D:\\opcdcfg\\opencode_config_manager_fluent_v1.0.0.py", "a", encoding="utf-8"
) as f:
    f.write(content)
print("Written successfully")
