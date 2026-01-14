#!/usr/bin/env python3
# -*- coding: utf-8 -*-
content = '''

# ==================== Oh My OpenCode Agent 页面 ====================
class OhMyAgentPage(BasePage):
    """Oh My OpenCode Agent 管理页面"""
    
    def __init__(self, main_window, parent=None):
        super().__init__("Oh My Agent", parent)
        self.main_window = main_window
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        # 工具栏
        toolbar = QHBoxLayout()
        
        self.add_btn = PrimaryPushButton(FIF.ADD, "添加 Agent", self)
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
        
        # Agent 列表
        self.table = TableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["名称", "绑定模型", "Temperature", "描述"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.layout.addWidget(self.table)
    
    def _load_data(self):
        self.table.setRowCount(0)
        config = self.main_window.ohmyopencode_config or {}
        agents = config.get("agents", {})
        
        for name, data in agents.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(data.get("model", "")))
            self.table.setItem(row, 2, QTableWidgetItem(str(data.get("temperature", ""))))
            self.table.setItem(row, 3, QTableWidgetItem(data.get("description", "")[:40]))
    
    def _on_add(self):
        dialog = OhMyAgentDialog(self.main_window, parent=self)
        if dialog.exec_():
            self._load_data()
            self.show_success("成功", "Agent 已添加")
    
    def _on_add_preset(self):
        dialog = PresetOhMyAgentDialog(self.main_window, parent=self)
        if dialog.exec_():
            self._load_data()
            self.show_success("成功", "预设 Agent 已添加")
    
    def _on_edit(self):
        row = self.table.currentRow()
        if row < 0:
            self.show_warning("提示", "请先选择一个 Agent")
            return
        name = self.table.item(row, 0).text()
        dialog = OhMyAgentDialog(self.main_window, agent_name=name, parent=self)
        if dialog.exec_():
            self._load_data()
            self.show_success("成功", "Agent 已更新")
    
    def _on_delete(self):
        row = self.table.currentRow()
        if row < 0:
            self.show_warning("提示", "请先选择一个 Agent")
            return
        name = self.table.item(row, 0).text()
        w = FluentMessageBox("确认删除", f"确定要删除 Agent \\"{name}\\" 吗？", self)
        if w.exec_():
            config = self.main_window.ohmyopencode_config or {}
            if "agents" in config and name in config["agents"]:
                del config["agents"][name]
                self.main_window.save_ohmyopencode_config()
                self._load_data()
                self.show_success("成功", f"Agent \\"{name}\\" 已删除")


class OhMyAgentDialog(QDialog):
    """Oh My OpenCode Agent 编辑对话框"""
    
    def __init__(self, main_window, agent_name: str = None, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.agent_name = agent_name
        self.is_edit = agent_name is not None
        
        self.setWindowTitle("编辑 Agent" if self.is_edit else "添加 Agent")
        self.setMinimumSize(500, 400)
        self._setup_ui()
        
        if self.is_edit:
            self._load_agent_data()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Agent 名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(BodyLabel("Agent 名称:", self))
        self.name_edit = LineEdit(self)
        self.name_edit.setPlaceholderText("如: oracle, librarian")
        if self.is_edit:
            self.name_edit.setEnabled(False)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # 绑定模型
        model_layout = QHBoxLayout()
        model_layout.addWidget(BodyLabel("绑定模型:", self))
        self.model_combo = ComboBox(self)
        self._load_models()
        model_layout.addWidget(self.model_combo)
        layout.addLayout(model_layout)
        
        # Temperature
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(BodyLabel("Temperature:", self))
        self.temp_slider = Slider(Qt.Orientation.Horizontal, self)
        self.temp_slider.setRange(0, 200)
        self.temp_slider.setValue(70)
        self.temp_label = BodyLabel("0.7", self)
        self.temp_slider.valueChanged.connect(lambda v: self.temp_label.setText(f"{v/100:.1f}"))
        temp_layout.addWidget(self.temp_slider)
        temp_layout.addWidget(self.temp_label)
        layout.addLayout(temp_layout)
        
        # 描述
        layout.addWidget(BodyLabel("描述:", self))
        self.desc_edit = TextEdit(self)
        self.desc_edit.setMaximumHeight(80)
        layout.addWidget(self.desc_edit)
        
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
    
    def _load_models(self):
        registry = ModelRegistry(self.main_window.opencode_config)
        models = registry.get_all_models()
        self.model_combo.addItems(models)
    
    def _load_agent_data(self):
        config = self.main_window.ohmyopencode_config or {}
        agent = config.get("agents", {}).get(self.agent_name, {})
        self.name_edit.setText(self.agent_name)
        model = agent.get("model", "")
        if model:
            self.model_combo.setCurrentText(model)
        temp = agent.get("temperature", 0.7)
        self.temp_slider.setValue(int(temp * 100))
        self.desc_edit.setPlainText(agent.get("description", ""))
    
    def _on_save(self):
        name = self.name_edit.text().strip()
        if not name:
            InfoBar.error("错误", "请输入 Agent 名称", parent=self)
            return
        
        config = self.main_window.ohmyopencode_config
        if config is None:
            config = {}
            self.main_window.ohmyopencode_config = config
        if "agents" not in config:
            config["agents"] = {}
        if not self.is_edit and name in config["agents"]:
            InfoBar.error("错误", f"Agent \\"{name}\\" 已存在", parent=self)
            return
        
        config["agents"][name] = {
            "model": self.model_combo.currentText(),
            "temperature": self.temp_slider.value() / 100,
            "description": self.desc_edit.toPlainText().strip(),
        }
        self.main_window.save_ohmyopencode_config()
        self.accept()


class PresetOhMyAgentDialog(QDialog):
    """预设 Oh My OpenCode Agent 选择对话框"""
    
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setWindowTitle("从预设添加 Agent")
        self.setMinimumSize(500, 350)
        self._setup_ui()
    
    def _setup_ui(self):
        layout
