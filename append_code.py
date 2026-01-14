#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""临时脚本：追加代码到 opencode_config_manager_fluent_v1.0.0.py"""

content = '''

# ==================== 基础页面类 ====================
class BasePage(QWidget):
    """页面基类 - 所有页面继承此类"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName(title.replace(' ', '_').lower())
        self._init_ui(title)
    
    def _init_ui(self, title: str):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(36, 20, 36, 20)
        self.layout.setSpacing(16)
        
        # 页面标题
        self.title_label = TitleLabel(title, self)
        self.layout.addWidget(self.title_label)
    
    def add_card(self, title: str = None) -> SimpleCardWidget:
        """添加一个卡片容器"""
        card = SimpleCardWidget(self)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(12)
        
        if title:
            card_title = SubtitleLabel(title, card)
            card_layout.addWidget(card_title)
        
        self.layout.addWidget(card)
        return card
    
    def show_success(self, title: str, content: str):
        """显示成功提示"""
        InfoBar.success(
            title=title,
            content=content,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )
    
    def show_error(self, title: str, content: str):
        """显示错误提示"""
        InfoBar.error(
            title=title,
            content=content,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )
    
    def show_warning(self, title: str, content: str):
        """显示警告提示"""
        InfoBar.warning(
            title=title,
            content=content,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=4000,
            parent=self
        )


# ==================== Provider 页面 ====================
class ProviderPage(BasePage):
    """Provider 管理页面"""
    
    def __init__(self, main_window, parent=None):
        super().__init__("Provider 管理", parent)
        self.main_window = main_window
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        # 工具栏
        toolbar = QHBoxLayout()
        
        self.add_btn = PrimaryPushButton(FIF.ADD, "添加 Provider", self)
        self.add_btn.clicked.connect(self._on_add)
        toolbar.addWidget(self.add_btn)
        
        self.edit_btn = PushButton(FIF.EDIT, "编辑", self)
        self.edit_btn.clicked.connect(self._on_edit)
        toolbar.addWidget(self.edit_btn)
        
        self.delete_btn = PushButton(FIF.DELETE, "删除", self)
        self.delete_btn.clicked.connect(self._on_delete)
        toolbar.addWidget(self.delete_btn)
        
        toolbar.addStretch()
        self.layout.addLayout(toolbar)
        
        # Provider 列表
        self.table = TableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["名称", "显示名称", "SDK", "API地址", "模型数"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.layout.addWidget(self.table)
    
    def _load_data(self):
        """加载 Provider 数据"""
        self.table.setRowCount(0)
        config = self.main_window.opencode_config or {}
        providers = config.get("provider", {})
        
        for name, data in providers.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(data.get("name", "")))
            self.table.setItem(row, 2, QTableWidgetItem(data.get("npm", "")))
            self.table.setItem(row, 3, QTableWidgetItem(data.get("options", {}).get("baseURL", "")))
            self.table.setItem(row, 4, QTableWidgetItem(str(len(data.get("models", {})))))
    
    def _on_add(self):
        """添加 Provider"""
        dialog = ProviderDialog(self.main_window, parent=self)
        if dialog.exec_():
            self._load_data()
            self.show_success("成功", "Provider 已添加")
    
    def _on_edit(self):
        """编辑 Provider"""
        row = self.table.currentRow()
        if row < 0:
            self.show_warning("提示", "请先选择一个 Provider")
            return
        
        name = self.table.item(row, 0).text()
        dialog = ProviderDialog(self.main_window, provider_name=name, parent=self)
        if dialog.exec_():
            self._load_data()
            self.show_success("成功", "Provider 已更新")
    
    def _on_delete(self):
        """删除 Provider"""
        row = self.table.currentRow()
        if row < 0:
            self.show_warning("提示", "请先选择一个 Provider")
            return
        
        name = self.table.item(row, 0).text()
        w = FluentMessageBox("确认删除", f'确定要删除 Provider "{name}" 吗？\\n此操作不可恢复。', self)
        if w.exec_():
            config = self.main_window.opencode_config or {}
            if "provider" in config and name in config["provider"]:
                del config["provider"][name]
                self.main_window.save_opencode_config()
                self._load_data()
                self.show_success("成功", f'Provider "{name}" 已删除')


class ProviderDialog(QDialog):
    """Provider 编辑对话框"""
    
    def __init__(self, main_window, provider_name: str = None, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.provider_name = provider_name
        self.is_edit = provider_name is not None
        
        self.setWindowTitle("编辑 Provider" if self.is_edit else "添加 Provider")
        self.setMinimumWidth(500)
        self._setup_ui()
        
        if self.is_edit:
            self._load_provider_data()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Provider 名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(BodyLabel("Provider 名称:", self))
        self.name_edit = LineEdit(self)
        self.name_edit.setPlaceholderText("如: anthropic, openai, my-proxy")
        if self.is_edit:
            self.name_edit.setEnabled(False)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # 显示名称
        display_layout = QHBoxLayout()
        display_layout.addWidget(BodyLabel("显示名称:", self))
        self.display_edit = LineEdit(self)
        self.display_edit.setPlaceholderText("如: Anthropic (Claude)")
        display_layout.addWidget(self.display_edit)
        layout.addLayout(display_layout)
        
        # SDK 选择
        sdk_layout = QHBoxLayout()
        sdk_layout.addWidget(BodyLabel("SDK:", self))
        self.sdk_combo = ComboBox(self)
        self.sdk_combo.addItems(PRESET_SDKS)
        sdk_layout.addWidget(self.sdk_combo)
        layout.addLayout(sdk_layout)
        
        # API 地址
        url_layout = QHBoxLayout()
        url_layout.addWidget(BodyLabel("API 地址:", self))
        self.url_edit = LineEdit(self)
        self.url_edit.setPlaceholderText("留空使用默认地址")
        url_layout.addWidget(self.url_edit)
        layout.addLayout(url_layout)
        
        # API 密钥
        key_layout = QHBoxLayout()
        key_layout.addWidget(BodyLabel("API 密钥:", self))
        self.key_edit = LineEdit(self)
        self.key_edit.setPlaceholderText("支持环境变量: {env:API_KEY}")
        self.key_edit.setEchoMode(LineEdit.Password)
        key_layout.addWidget(self.key_edit)
        
        self.show_key_btn = ToolButton(FIF.VIEW, self)
        self.show_key_btn.clicked.connect(self._toggle_key_visibility)
        key_layout.addWidget(self.show_key_btn)
        layout.addLayout(key_layout)
        
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
    
    def _toggle_key_visibility(self):
        if self.key_edit.echoMode() == LineEdit.Password:
            self.key_edit.setEchoMode(LineEdit.Normal)
            self.show_key_btn.setIcon(FIF.HIDE)
        else:
            self.key_edit.setEchoMode(LineEdit.Password)
            self.show_key_btn.setIcon(FIF.VIEW)
    
    def _load_provider_data(self):
        config = self.main_window.opencode_config or {}
        provider = config.get("provider", {}).get(self.provider_name, {})
        
        self.name_edit.setText(self.provider_name)
        self.display_edit.setText(provider.get("name", ""))
        
        sdk = provider.get("npm", "")
        if sdk in PRESET_SDKS:
            self.sdk_combo.setCurrentText(sdk)
        
        options = provider.get("options", {})
        self.url_edit.setText(options.get("baseURL", ""))
        self.key_edit.setText(options.get("apiKey", ""))
    
    def _on_save(self):
        name = self.name_edit.text().strip()
        if not name:
            InfoBar.error("错误", "请输入 Provider 名称", parent=self)
            return
        
        config = self.main_window.opencode_config
        if config is None:
            config = {}
            self.main_window.opencode_config = config
        
        if "provider" not in config:
            config["provider"] = {}
        
        # 检查名称冲突
        if not self.is_edit and name in config["provider"]:
            InfoBar.error("错误", f'Provider "{name}" 已存在', parent=self)
            return
        
        # 保存数据
        provider_data = config["provider"].get(name, {"models": {}})
        provider_data["npm"] = self.sdk_combo.currentText()
        provider_data["name"] = self.display_edit.text().strip()
        provider_data["options"] = {
            "baseURL": self.url_edit.text().strip(),
            "apiKey": self.key_edit.text().strip(),
        }
        
        config["provider"][name] = provider_data
        self.main_window.save_opencode_config()
        self.accept()
'''

with open(
    r"D:\opcdcfg\opencode_config_manager_fluent_v1.0.0.py", "a", encoding="utf-8"
) as f:
    f.write(content)
print("Written successfully")
