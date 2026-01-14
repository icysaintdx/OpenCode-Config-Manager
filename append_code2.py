#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""临时脚本：追加更多页面代码"""

content = '''

# ==================== Model 页面 ====================
class ModelPage(BasePage):
    """Model 管理页面"""
    
    def __init__(self, main_window, parent=None):
        super().__init__("Model 管理", parent)
        self.main_window = main_window
        self._setup_ui()
        self._load_providers()
    
    def _setup_ui(self):
        # Provider 选择
        provider_layout = QHBoxLayout()
        provider_layout.addWidget(BodyLabel("选择 Provider:", self))
        self.provider_combo = ComboBox(self)
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        provider_layout.addWidget(self.provider_combo)
        provider_layout.addStretch()
        self.layout.addLayout(provider_layout)
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        self.add_btn = PrimaryPushButton(FIF.ADD, "添加模型", self)
        self.add_btn.clicked.connect(self._on_add)
        toolbar.addWidget(self.add_btn)
        
        self.preset_btn = PushButton(FIF.LIBRARY, "从预设添加", self)
        self.preset_btn.clicked.connect(self._on_add_preset)
        toolbar.addWidget(self.preset_btn)
        
        self.edit_btn = PushButton(FIF.EDIT, "编辑", self)
        self.edit_btn.clicked.connect(self._on_edit)
        toolbar.addWidget(self.edit_btn)
        
        self.delete_btn = PushButton(FIF.DELETE, "删除", self)
        self.delete_btn.clicked.connect(self._on_delete)
        toolbar.addWidget(self.delete_btn)
        
        toolbar.addStretch()
        self.layout.addLayout(toolbar)
        
        # Model 列表
        self.table = TableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["模型ID", "显示名称", "上下文", "输出", "附件"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.layout.addWidget(self.table)
    
    def _load_providers(self):
        """加载 Provider 列表"""
        self.provider_combo.clear()
        config = self.main_window.opencode_config or {}
        providers = config.get("provider", {})
        for name in providers.keys():
            self.provider_combo.addItem(name)
    
    def _on_provider_changed(self, provider_name: str):
        """Provider 切换时刷新模型列表"""
        self._load_models(provider_name)
    
    def _load_models(self, provider_name: str):
        """加载指定 Provider 的模型列表"""
        self.table.setRowCount(0)
        if not provider_name:
            return
        
        config = self.main_window.opencode_config or {}
        provider = config.get("provider", {}).get(provider_name, {})
        models = provider.get("models", {})
        
        for model_id, data in models.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(model_id))
            self.table.setItem(row, 1, QTableWidgetItem(data.get("name", "")))
            limit = data.get("limit", {})
            self.table.setItem(row, 2, QTableWidgetItem(str(limit.get("context", ""))))
            self.table.setItem(row, 3, QTableWidgetItem(str(limit.get("output", ""))))
            self.table.setItem(row, 4, QTableWidgetItem("✓" if data.get("attachment") else ""))
    
    def _on_add(self):
        """添加模型"""
        provider = self.provider_combo.currentText()
        if not provider:
            self.show_warning("提示", "请先选择一个 Provider")
            return
        dialog = ModelDialog(self.main_window, provider, parent=self)
        if dialog.exec_():
            self._load_models(provider)
            self.show_success("成功", "模型已添加")
    
    def _on_add_preset(self):
        """从预设添加模型"""
        provider = self.provider_combo.currentText()
        if not provider:
            self.show_warning("提示", "请先选择一个 Provider")
            return
        dialog = PresetModelDialog(self.main_window, provider, parent=self)
        if dialog.exec_():
            self._load_models(provider)
            self.show_success("成功", "预设模型已添加")
    
    def _on_edit(self):
        """编辑模型"""
        provider = self.provider_combo.currentText()
        row = self.table.currentRow()
        if row < 0:
            self.show_warning("提示", "请先选择一个模型")
            return
        model_id = self.table.item(row, 0).text()
        dialog = ModelDialog(self.main_window, provider, model_id=model_id, parent=self)
        if dialog.exec_():
            self._load_models(provider)
            self.show_success("成功", "模型已更新")
    
    def _on_delete(self):
        """删除模型"""
        provider = self.provider_combo.currentText()
        row = self.table.currentRow()
        if row < 0:
            self.show_warning("提示", "请先选择一个模型")
            return
        
        model_id = self.table.item(row, 0).text()
        w = FluentMessageBox("确认删除", f'确定要删除模型 "{model_id}" 吗？', self)
        if w.exec_():
            config = self.main_window.opencode_config or {}
            if "provider" in config and provider in config["provider"]:
                models = config["provider"][provider].get("models", {})
                if model_id in models:
                    del models[model_id]
                    self.main_window.save_opencode_config()
                    self._load_models(provider)
                    self.show_success("成功", f'模型 "{model_id}" 已删除')


class ModelDialog(QDialog):
    """模型编辑对话框"""
    
    def __init__(self, main_window, provider_name: str, model_id: str = None, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.provider_name = provider_name
        self.model_id = model_id
        self.is_edit = model_id is not None
        
        self.setWindowTitle("编辑模型" if self.is_edit else "添加模型")
        self.setMinimumSize(600, 500)
        self._setup_ui()
        
        if self.is_edit:
            self._load_model_data()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # 模型ID
        id_layout = QHBoxLayout()
        id_layout.addWidget(BodyLabel("模型 ID:", self))
        self.id_edit = LineEdit(self)
        self.id_edit.setPlaceholderText("如: claude-sonnet-4-5-20250929")
        if self.is_edit:
            self.id_edit.setEnabled(False)
        id_layout.addWidget(self.id_edit)
        layout.addLayout(id_layout)
        
        # 显示名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(BodyLabel("显示名称:", self))
        self.name_edit = LineEdit(self)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # 支持附件
        self.attachment_check = CheckBox("支持附件 (图片/文档)", self)
        layout.addWidget(self.attachment_check)
        
        # 上下文窗口
        context_layout = QHBoxLayout()
        context_layout.addWidget(BodyLabel("上下文窗口:", self))
        self.context_spin = SpinBox(self)
        self.context_spin.setRange(0, 10000000)
        self.context_spin.setValue(200000)
        context_layout.addWidget(self.context_spin)
        layout.addLayout(context_layout)
        
        # 最大输出
        output_layout = QHBoxLayout()
        output_layout.addWidget(BodyLabel("最大输出:", self))
        self.output_spin = SpinBox(self)
        self.output_spin.setRange(0, 1000000)
        self.output_spin.setValue(16000)
        output_layout.addWidget(self.output_spin)
        layout.addLayout(output_layout)
        
        # Options (JSON)
        layout.addWidget(BodyLabel("Options (JSON):", self))
        self.options_edit = TextEdit(self)
        self.options_edit.setPlaceholderText('{"thinking": {"type": "enabled", "budgetTokens": 16000}}')
        self.options_edit.setMaximumHeight(100)
        layout.addWidget(self.options_edit)
        
        # Variants (JSON)
        layout.addWidget(BodyLabel("Variants (JSON):", self))
        self.variants_edit = TextEdit(self)
        self.variants_edit.setPlaceholderText('{"high": {"thinking": {"budgetTokens": 32000}}}')
        self.variants_edit.setMaximumHeight(100)
        layout.addWidget(self.variants_edit)
        
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
    
    def _load_model_data(self):
        config = self.main_window.opencode_config or {}
        provider = config.get("provider", {}).get(self.provider_name, {})
        model = provider.get("models", {}).get(self.model_id, {})
        
        self.id_edit.setText(self.model_id)
        self.name_edit.setText(model.get("name", ""))
        self.attachment_check.setChecked(model.get("attachment", False))
        
        limit = model.get("limit", {})
        self.context_spin.setValue(limit.get("context", 200000))
        self.output_spin.setValue(limit.get("output", 16000))
        
        options = model.get("options", {})
        if options:
            self.options_edit.setPlainText(json.dumps(options, indent=2, ensure_ascii=False))
        
        variants = model.get("variants", {})
        if variants:
            self.variants_edit.setPlainText(json.dumps(variants, indent=2, ensure_ascii=False))
    
    def _on_save(self):
        model_id = self.id_edit.text().strip()
        if not model_id:
            InfoBar.error("错误", "请输入模型 ID", parent=self)
            return
        
        # 解析 JSON
        options = {}
        options_text = self.options_edit.toPlainText().strip()
        if options_text:
            try:
                options = json.loads(options_text)
            except json.JSONDecodeError as e:
                InfoBar.error("错误", f"Options JSON 格式错误: {e}", parent=self)
                return
        
        variants = {}
        variants_text = self.variants_edit.toPlainText().strip()
        if variants_text:
            try:
                variants = json.loads(variants_text)
            except json.JSONDecodeError as e:
                InfoBar.error("错误", f"Variants JSON 格式错误: {e}", parent=self)
                return
        
        config = self.main_window.opencode_config
        if config is None:
            config = {}
            self.main_window.opencode_config = config
        
        if "provider" not in config:
            config["provider"] = {}
        if self.provider_name not in config["provider"]:
            config["provider"][self.provider_name] = {"models": {}}
        if "models" not in config["provider"][self.provider_name]:
            config["provider"][self.provider_name]["models"] = {}
        
        models = config["provider"][self.provider_name]["models"]
        
        # 检查名称冲突
        if not self.is_edit and model_id in models:
            InfoBar.error("错误", f'模型 "{model_id}" 已存在', parent=self)
            return
        
        # 保存数据
        model_data = {
            "name": self.name_edit.text().strip(),
            "attachment": self.attachment_check.isChecked(),
            "limit": {
                "context": self.context_spin.value(),
                "output": self.output_spin.value(),
            },
        }
        if options:
            model_data["options"] = options
        if variants:
            model_data["variants"] = variants
        
        models[model_id] = model_data
        self.main_window.save_opencode_config()
        self.accept()


class PresetModelDialog(QDialog):
    """预设模型选择对话框"""
    
    def __init__(self, main_window, provider_name: str, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.provider_name = provider_name
        
        self.setWindowTitle("从预设添加模型")
        self.setMinimumSize(500, 400)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # 模型系列选择
        series_layout = QHBoxLayout()
        series_layout.addWidget(BodyLabel("模型系列:", self))
        self.series_combo = ComboBox(self)
        self.series_combo.addItems(list(PRESET_MODEL_CONFIGS.keys()))
        self.series_combo.currentTextChanged.connect(self._on_series_changed)
        series_layout.addWidget(self.series_combo)
        layout.addLayout(series_layout)
        
        # 模型列表
        layout.addWidget(BodyLabel("选择模型:", self))
        self.model_list = ListWidget(self)
        self.model_list.setSelectionMode(QAbstractItemView.MultiSelection)
        layout.addWidget(self.model_list)
        
        # 模型描述
        self.desc_label = CaptionLabel("", self)
        self.desc_label.setWordWrap(True)
        layout.addWidget(self.desc_label)
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.cancel_btn = PushButton("取消", self)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        self.add_btn = PrimaryPushButton("添加选中模型", self)
        self.add_btn.clicked.connect(self._on_add)
        btn_layout.addWidget(self.add_btn)
        
        layout.addLayout(btn_layout)
        
        # 初始化
        self._on_series_changed(self.series_combo.currentText())
    
    def _on_series_changed(self, series: str):
        self.model_list.clear()
        if series in PRESET_MODEL_CONFIGS:
            models = PRESET_MODEL_CONFIGS[series]["models"]
            for model_id, data in models.items():
                self.model_list.addItem(f"{model_id} - {data.get('name', '')}")
    
    def _on_add(self):
        selected = self.model_list.selectedItems()
        if not selected:
            InfoBar.warning("提示", "请选择至少一个模型", parent=self)
            return
        
        series = self.series_combo.currentText()
        series_data = PRESET_MODEL_CONFIGS.get(series, {})
        models_data = series_data.get("models", {})
        
        config = self.main_window.opencode_config
        if config is None:
            config = {}
            self.main_window.opencode_config = config
        
        if "provider" not in config:
            config["provider"] = {}
        if self.provider_name not in config["provider"]:
            config["provider"][self.provider_name] = {"models": {}}
        if "models" not in config["provider"][self.provider_name]:
            config["provider"][self.provider_name]["models"] = {}
        
        models = config["provider"][self.provider_name]["models"]
        added = 0
        
        for item in selected:
            model_id = item.text().split(" - ")[0]
            if model_id in models_data:
                preset = models_data[model_id]
                models[model_id] = {
                    "name": preset.get("name", ""),
                    "attachment": preset.get("attachment", False),
                    "limit": preset.get("limit", {}),
                    "options": preset.get("options", {}),
                    "variants": preset.get("variants", {}),
                }
                added += 1
        
        self.main_window.save_opencode_config()
        InfoBar.success("成功", f"已添加 {added} 个模型", parent=self)
        self.accept()
'''

with open(
    r"D:\\opcdcfg\\opencode_config_manager_fluent_v1.0.0.py", "a", encoding="utf-8"
) as f:
    f.write(content)
print("Written successfully")
