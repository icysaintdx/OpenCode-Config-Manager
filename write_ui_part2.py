# -*- coding: utf-8 -*-
code = '''

# ==================== Provider 页面 ====================
class ProviderPage(BasePage):
    """Provider 管理页面"""
    
    def __init__(self, parent=None):
        super().__init__("Provider 管理", "管理 API 提供商配置", parent)
        self.app = parent
        self.current_provider_name = None
        self.setup_ui()
    
    def setup_ui(self):
        # 主分割布局
        splitter = QSplitter(Qt.Horizontal)
        self.vBoxLayout.addWidget(splitter, 1)
        
        # 左侧：Provider 列表
        left_card = CardWidget()
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(12)
        
        # 工具栏
        toolbar = QHBoxLayout()
        self.add_btn = PrimaryPushButton(FIF.ADD, "添加")
        self.add_btn.clicked.connect(self.add_provider)
        self.delete_btn = PushButton(FIF.DELETE, "删除")
        self.delete_btn.clicked.connect(self.delete_provider)
        toolbar.addWidget(self.add_btn)
        toolbar.addWidget(self.delete_btn)
        toolbar.addStretch()
        left_layout.addLayout(toolbar)
        
        # Provider 列表
        self.provider_table = TableWidget()
        self.provider_table.setColumnCount(4)
        self.provider_table.setHorizontalHeaderLabels(["名称", "显示名", "SDK", "模型数"])
        self.provider_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.provider_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.provider_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.provider_table.itemSelectionChanged.connect(self.on_select)
        left_layout.addWidget(self.provider_table)
        
        splitter.addWidget(left_card)
        
        # 右侧：Provider 详情
        right_card = CardWidget()
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(12)
        
        # 标题
        detail_title = SubtitleLabel("Provider 详情")
        right_layout.addWidget(detail_title)
        
        # 表单
        form_layout = QGridLayout()
        form_layout.setSpacing(12)
        row = 0
        
        # 名称
        form_layout.addWidget(BodyLabel("名称:"), row, 0)
        self.name_edit = LineEdit()
        self.name_edit.setPlaceholderText("如: anthropic, openai")
        form_layout.addWidget(self.name_edit, row, 1)
        row += 1
        
        # 显示名
        form_layout.addWidget(BodyLabel("显示名:"), row, 0)
        self.display_edit = LineEdit()
        self.display_edit.setPlaceholderText("如: Anthropic (Claude)")
        form_layout.addWidget(self.display_edit, row, 1)
        row += 1
        
        # SDK
        form_layout.addWidget(BodyLabel("SDK:"), row, 0)
        self.sdk_combo = ComboBox()
        self.sdk_combo.addItems(PRESET_SDKS)
        self.sdk_combo.currentTextChanged.connect(self.on_sdk_change)
        form_layout.addWidget(self.sdk_combo, row, 1)
        row += 1
        
        # SDK 兼容性提示
        self.sdk_hint = CaptionLabel("")
        self.sdk_hint.setStyleSheet("color: #107C10;")
        form_layout.addWidget(self.sdk_hint, row, 0, 1, 2)
        row += 1
        
        # API 地址
        form_layout.addWidget(BodyLabel("API 地址:"), row, 0)
        self.url_edit = LineEdit()
        self.url_edit.setPlaceholderText("留空使用默认地址")
        form_layout.addWidget(self.url_edit, row, 1)
        row += 1
        
        # API 密钥
        form_layout.addWidget(BodyLabel("API 密钥:"), row, 0)
        key_layout = QHBoxLayout()
        self.key_edit = PasswordLineEdit()
        self.key_edit.setPlaceholderText("支持环境变量: {env:API_KEY}")
        self.show_key_btn = ToolButton(FIF.VIEW)
        self.show_key_btn.setCheckable(True)
        self.show_key_btn.clicked.connect(self.toggle_key_visibility)
        key_layout.addWidget(self.key_edit)
        key_layout.addWidget(self.show_key_btn)
        form_layout.addLayout(key_layout, row, 1)
        row += 1
        
        right_layout.addLayout(form_layout)
        right_layout.addStretch()
        
        # 保存按钮
        self.save_btn = PrimaryPushButton(FIF.SAVE, "保存修改")
        self.save_btn.clicked.connect(self.save_changes)
        right_layout.addWidget(self.save_btn)
        
        splitter.addWidget(right_card)
        splitter.setSizes([400, 500])
    
    def on_sdk_change(self, sdk: str):
        """SDK 选择变化时显示兼容性提示"""
        if sdk in SDK_MODEL_COMPATIBILITY:
            compatible = SDK_MODEL_COMPATIBILITY[sdk]
            self.sdk_hint.setText(f"适用于: {', '.join(compatible)}")
        else:
            self.sdk_hint.setText("")
    
    def toggle_key_visibility(self):
        """切换密钥显示/隐藏"""
        if self.show_key_btn.isChecked():
            self.key_edit.setEchoMode(LineEdit.Normal)
        else:
            self.key_edit.setEchoMode(LineEdit.Password)
    
    def refresh_list(self):
        """刷新 Provider 列表"""
        self.provider_table.setRowCount(0)
        if not self.app:
            return
        providers = self.app.opencode_config.get("provider", {})
        for name, data in providers.items():
            row = self.provider_table.rowCount()
            self.provider_table.insertRow(row)
            self.provider_table.setItem(row, 0, QTableWidgetItem(name))
            self.provider_table.setItem(row, 1, QTableWidgetItem(data.get("name", "")))
            self.provider_table.setItem(row, 2, QTableWidgetItem(data.get("npm", "")))
            self.provider_table.setItem(row, 3, QTableWidgetItem(str(len(data.get("models", {})))))
    
    def on_select(self):
        """选中 Provider 时加载详情"""
        rows = self.provider_table.selectedItems()
        if not rows:
            return
        row = rows[0].row()
        name = self.provider_table.item(row, 0).text()
        self.current_provider_name = name
        
        providers = self.app.opencode_config.get("provider", {})
        if name in providers:
            data = providers[name]
            self.name_edit.setText(name)
            self.display_edit.setText(data.get("name", ""))
            self.sdk_combo.setCurrentText(data.get("npm", ""))
            self.url_edit.setText(data.get("options", {}).get("baseURL", ""))
            self.key_edit.setText(data.get("options", {}).get("apiKey", ""))
            self.on_sdk_change(data.get("npm", ""))
    
    def add_provider(self):
        """添加新 Provider"""
        self.current_provider_name = None
        self.name_edit.clear()
        self.display_edit.clear()
        self.sdk_combo.setCurrentIndex(0)
        self.url_edit.clear()
        self.key_edit.clear()
        self.sdk_hint.clear()
        self.provider_table.clearSelection()
    
    def delete_provider(self):
        """删除选中的 Provider"""
        rows = self.provider_table.selectedItems()
        if not rows:
            return
        row = rows[0].row()
        name = self.provider_table.item(row, 0).text()
        
        w = MessageBox("确认删除", f"删除 Provider [{name}] 及其所有模型?", self)
        if w.exec():
            del self.app.opencode_config["provider"][name]
            self.current_provider_name = None
            self.app.save_configs_silent()
            self.refresh_list()
            InfoBar.success("成功", f"Provider [{name}] 已删除", parent=self)
    
    def save_changes(self):
        """保存修改"""
        name = self.name_edit.text().strip()
        if not name:
            InfoBar.warning("提示", "名称不能为空", parent=self)
            return
        
        providers = self.app.opencode_config.setdefault("provider", {})
        
        # 如果是编辑现有 Provider 且名称改变了
        if self.current_provider_name and self.current_provider_name != name:
            if self.current_provider_name in providers:
                old_models = providers[self.current_provider_name].get("models", {})
                del providers[self.current_provider_name]
                providers[name] = {"models": old_models}
        
        if name not in providers:
            providers[name] = {"models": {}}
        
        providers[name]["npm"] = self.sdk_combo.currentText()
        providers
