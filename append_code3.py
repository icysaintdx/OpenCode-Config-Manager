#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""临时脚本：追加 MCP、Agent、MainWindow 等页面代码"""

content = '''

# ==================== MCP 页面 ====================
class MCPPage(BasePage):
    """MCP 服务器管理页面"""
    
    def __init__(self, main_window, parent=None):
        super().__init__("MCP 服务器", parent)
        self.main_window = main_window
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        # 工具栏
        toolbar = QHBoxLayout()
        
        self.add_local_btn = PrimaryPushButton(FIF.ADD, "添加 Local MCP", self)
        self.add_local_btn.clicked.connect(lambda: self._on_add("local"))
        toolbar.addWidget(self.add_local_btn)
        
        self.add_remote_btn = PushButton(FIF.CLOUD, "添加 Remote MCP", self)
        self.add_remote_btn.clicked.connect(lambda: self._on_add("remote"))
        toolbar.addWidget(self.add_remote_btn)
        
        self.edit_btn = PushButton(FIF.EDIT, "编辑", self)
        self.edit_btn.clicked.connect(self._on_edit)
        toolbar.addWidget(self.edit_btn)
        
        self.delete_btn = PushButton(FIF.DELETE, "删除", self)
        self.delete_btn.clicked.connect(self._on_delete)
        toolbar.addWidget(self.delete_btn)
        
        toolbar.addStretch()
        self.layout.addLayout(toolbar)
        
        # MCP 列表
        self.table = TableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["名称", "类型", "命令/URL", "启用", "超时"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.layout.addWidget(self.table)
    
    def _load_data(self):
        self.table.setRowCount(0)
        config = self.main_window.opencode_config or {}
        mcps = config.get("mcp", {})
        
        for name, data in mcps.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(name))
            
            mcp_type = "remote" if "url" in data else "local"
            self.table.setItem(row, 1, QTableWidgetItem(mcp_type))
            
            if mcp_type == "local":
                cmd = data.get("command", [])
                self.table.setItem(row, 2, QTableWidgetItem(" ".join(cmd) if isinstance(cmd, list) else str(cmd)))
            else:
                self.table.setItem(row, 2, QTableWidgetItem(data.get("url", "")))
            
            enabled = data.get("enabled", True)
            self.table.setItem(row, 3, QTableWidgetItem("✓" if enabled else "✗"))
            self.table.setItem(row, 4, QTableWidgetItem(str(data.get("timeout", 5000))))
    
    def _on_add(self, mcp_type: str):
        dialog = MCPDialog(self.main_window, mcp_type=mcp_type, parent=self)
        if dialog.exec_():
            self._load_data()
            self.show_success("成功", "MCP 服务器已添加")
    
    def _on_edit(self):
        row = self.table.currentRow()
        if row < 0:
            self.show_warning("提示", "请先选择一个 MCP 服务器")
            return
        
        name = self.table.item(row, 0).text()
        mcp_type = self.table.item(row, 1).text()
        dialog = MCPDialog(self.main_window, mcp_name=name, mcp_type=mcp_type, parent=self)
        if dialog.exec_():
            self._load_data()
            self.show_success("成功", "MCP 服务器已更新")
    
    def _on_delete(self):
        row = self.table.currentRow()
        if row < 0:
            self.show_warning("提示", "请先选择一个 MCP 服务器")
            return
        
        name = self.table.item(row, 0).text()
        w = FluentMessageBox("确认删除", f'确定要删除 MCP "{name}" 吗？', self)
        if w.exec_():
            config = self.main_window.opencode_config or {}
            if "mcp" in config and name in config["mcp"]:
                del config["mcp"][name]
                self.main_window.save_opencode_config()
                self._load_data()
                self.show_success("成功", f'MCP "{name}" 已删除')


class MCPDialog(QDialog):
    """MCP 编辑对话框"""
    
    def __init__(self, main_window, mcp_name: str = None, mcp_type: str = "local", parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.mcp_name = mcp_name
        self.mcp_type = mcp_type
        self.is_edit = mcp_name is not None
        
        self.setWindowTitle("编辑 MCP" if self.is_edit else f"添加 {mcp_type.title()} MCP")
        self.setMinimumWidth(550)
        self._setup_ui()
        
        if self.is_edit:
            self._load_mcp_data()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # MCP 名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(BodyLabel("MCP 名称:", self))
        self.name_edit = LineEdit(self)
        self.name_edit.setPlaceholderText("如: context7, filesystem")
        if self.is_edit:
            self.name_edit.setEnabled(False)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # 启用状态
        self.enabled_check = CheckBox("启用此 MCP 服务器", self)
        self.enabled_check.setChecked(True)
        layout.addWidget(self.enabled_check)
        
        if self.mcp_type == "local":
            # 启动命令
            layout.addWidget(BodyLabel("启动命令 (JSON数组):", self))
            self.command_edit = TextEdit(self)
            self.command_edit.setPlaceholderText('["npx", "-y", "@mcp/server"]')
            self.command_edit.setMaximumHeight(80)
            layout.addWidget(self.command_edit)
            
            # 环境变量
            layout.addWidget(BodyLabel("环境变量 (JSON对象):", self))
            self.env_edit = TextEdit(self)
            self.env_edit.setPlaceholderText('{"API_KEY": "xxx"}')
            self.env_edit.setMaximumHeight(80)
            layout.addWidget(self.env_edit)
        else:
            # URL
            url_layout = QHBoxLayout()
            url_layout.addWidget(BodyLabel("服务器 URL:", self))
            self.url_edit = LineEdit(self)
            self.url_edit.setPlaceholderText("https://mcp.example.com/mcp")
            url_layout.addWidget(self.url_edit)
            layout.addLayout(url_layout)
            
            # Headers
            layout.addWidget(BodyLabel("请求头 (JSON对象):", self))
            self.headers_edit = TextEdit(self)
            self.headers_edit.setPlaceholderText('{"Authorization": "Bearer xxx"}')
            self.headers_edit.setMaximumHeight(80)
            layout.addWidget(self.headers_edit)
        
        # 超时
        timeout_layout = QHBoxLayout()
        timeout_layout.addWidget(BodyLabel("超时 (ms):", self))
        self.timeout_spin = SpinBox(self)
        self.timeout_spin.setRange(1000, 300000)
        self.timeout_spin.setValue(5000)
        timeout_layout.addWidget(self.timeout_spin)
        layout.addLayout(timeout_layout)
        
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
    
    def _load_mcp_data(self):
        config = self.main_window.opencode_config or {}
        mcp = config.get("mcp", {}).get(self.mcp_name, {})
        
        self.name_edit.setText(self.mcp_name)
        self.enabled_check.setChecked(mcp.get("enabled", True))
        self.timeout_spin.setValue(mcp.get("timeout", 5000))
        
        if self.mcp_type == "local":
            cmd = mcp.get("command", [])
            if cmd:
                self.command_edit.setPlainText(json.dumps(cmd, ensure_ascii=False))
            env = mcp.get("environment", {})
            if env:
                self.env_edit.setPlainText(json.dumps(env, indent=2, ensure_ascii=False))
        else:
            self.url_edit.setText(mcp.get("url", ""))
            headers = mcp.get("headers", {})
            if headers:
                self.headers_edit.setPlainText(json.dumps(headers, indent=2, ensure_ascii=False))
    
    def _on_save(self):
        name = self.name_edit.text().strip()
        if not name:
            InfoBar.error("错误", "请输入 MCP 名称", parent=self)
            return
        
        config = self.main_window.opencode_config
        if config is None:
            config = {}
            self.main_window.opencode_config = config
        
        if "mcp" not in config:
            config["mcp"] = {}
        
        if not self.is_edit and name in config["mcp"]:
            InfoBar.error("错误", f'MCP "{name}" 已存在', parent=self)
            return
        
        mcp_data = {
            "enabled": self.enabled_check.isChecked(),
            "timeout": self.timeout_spin.value(),
        }
        
        if self.mcp_type == "local":
            cmd_text = self.command_edit.toPlainText().strip()
            if cmd_text:
                try:
                    mcp_data["command"] = json.loads(cmd_text)
                except json.JSONDecodeError as e:
                    InfoBar.error("错误", f"命令 JSON 格式错误: {e}", parent=self)
                    return
            
            env_text = self.env_edit.toPlainText().strip()
            if env_text:
                try:
                    mcp_data["environment"] = json.loads(env_text)
                except json.JSONDecodeError as e:
                    InfoBar.error("错误", f"环境变量 JSON 格式错误: {e}", parent=self)
                    return
        else:
            url = self.url_edit.text().strip()
            if not url:
                InfoBar.error("错误", "请输入服务器 URL", parent=self)
                return
            mcp_data["url"] = url
            
            headers_text = self.headers_edit.toPlainText().strip()
            if headers_text:
                try:
                    mcp_data["headers"] = json.loads(headers_text)
                except json.JSONDecodeError as e:
                    InfoBar.error("错误", f"请求头 JSON 格式错误: {e}", parent=self)
                    return
        
        config["mcp"][name] = mcp_data
        self.main_window.save_opencode_config()
        self.accept()


# ==================== OpenCode Agent 页面 ====================
class OpenCodeAgentPage(BasePage):
    """OpenCode 原生 Agent 配置页面"""
    
    def __init__(self, main_window, parent=None):
        super().__init__("OpenCode Agent", parent)
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
        self.table.setHorizontalHeaderLabels(["名称", "模式", "Temperature", "描述"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.layout.addWidget(self.table)
    
    def _load_data(self):
        self.table.setRowCount(0)
        config = self.main_window.opencode_config or {}
        agents = config.get("agent", {})
        
        for name, data in agents.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(data.get("mode", "subagent")))
            self.table.setItem(row, 2, QTableWidgetItem(str(data.get("temperature", ""))))
            self.table.setItem(row, 3, QTableWidgetItem(data.get("description", "")[:50]))
    
    def _on_add(self):
        dialog = OpenCodeAgentDialog(self.main_window, parent=self)
        if dialog.exec_():
            self._load_data()
            self.show_success("成功", "Agent 已添加")
    
    def _on_add_preset(self):
        dialog = PresetOpenCodeAgentDialog(self.main_window, parent=self)
        if dialog.exec_():
            self._load_data()
            self.show_success("成功", "预设 Agent 已添加")
    
    def _on_edit(self):
        row = self.table.currentRow()
        if row < 0:
            self.show_warning("提示", "请先选择一个 Agent")
            return
        
        name = self.table.item(row, 0).text()
        dialog = OpenCodeAgentDialog(self.main_window, agent_name=name, parent=self)
        if dialog.exec_():
            self._load_data()
            self.show_success("成功", "Agent 已更新")
    
    def _on_delete(self):
        row = self.table.currentRow()
        if row < 0:
            self.show_warning("提示", "请先选择一个 Agent")
            return
        
        name = self.table.item(row, 0).text()
        w = FluentMessageBox("确认删除", f'确定要删除 Agent "{name}" 吗？', self)
        if w.exec_():
            config = self.main_window.opencode_config or {}
            if "agent" in config and name in config["agent"]:
                del config["agent"][name]
                self.main_window.save_opencode_config()
                self._load_data()
                self.show_success("成功", f'Agent "{name}" 已删除')


class OpenCodeAgentDialog(QDialog):
    """OpenCode Agent 编辑对话框"""
    
    def __init__(self, main_window, agent_name: str = None, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.agent_name = agent_name
        self.is_edit = agent_name is not None
        
        self.setWindowTitle("编辑 Agent" if self.is_edit else "添加 Agent")
        self.setMinimumSize(550, 450)
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
        self.name_edit.setPlaceholderText("如: build, plan, explore")
        if self.is_edit:
            self.name_edit.setEnabled(False)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # 模式
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(BodyLabel("模式:", self))
        self.mode_combo = ComboBox(self)
        self.mode_combo.addItems(["primary", "subagent", "all"])
        mode_layout.addWidget(self.mode_combo)
        layout.addLayout(mode_layout)
        
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
        self.desc_edit.setMaximumHeight(60)
        layout.addWidget(self.desc_edit)
        
        # 系统提示词
        layout.addWidget(BodyLabel("系统提示词:", self))
        self.prompt_edit = TextEdit(self)
        self.prompt_edit.setMaximumHeight(80)
        layout.addWidget(self.prompt_edit)
        
        # 隐藏
        self.hidden_check = CheckBox("在 @ 自动完成中隐藏", self)
        layout.addWidget(self.hidden_check)
        
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
    
    def _load_agent_data(self):
        config = self.main_window.opencode_config or {}
        agent = config.get("agent", {}).get(self.agent_name, {})
        
        self.name_edit.setText(self.agent_name)
        
        mode = agent.get("mode", "subagent")
        self.mode_combo.setCurrentText(mode)
        
        temp = agent.get("temperature", 0.7)
        self.temp_slider.setValue(int(temp * 100))
        
        self.desc_edit.setPlainText(agent.get("description", ""))
        self.prompt_edit.setPlainText(agent.get("prompt", ""))
        self.hidden_check.setChecked(agent.get("hidden", False))
    
    def _on_save(self):
        name = self.name_edit.text().strip()
        if not name:
            InfoBar.error("错误", "请输入 Agent 名称", parent=self)
            return
        
        config = self.main_window.opencode_config
        if config is None:
            config = {}
            self.main_window.opencode_config = config
        
        if "agent" not in config:
            config["agent"] = {}
        
        if not self.is_edit and name in config["agent"]:
            InfoBar.error("错误", f'Agent "{name}" 已存在', parent=self)
            return
        
        agent_data = {
            "mode": self.mode_combo.currentText(),
            "temperature": self.temp_slider.value() / 100,
        }
        
        desc = self.desc_edit.toPlainText().strip()
        if desc:
            agent_data["description"] = desc
        
        prompt = self.prompt_edit.toPlainText().strip()
        if prompt:
            agent_data["prompt"] = prompt
        
        if self.hidden_check.isChecked():
            agent_data["hidden"] = True
        
        config["agent"][name] = agent_data
        self.main_window.save_opencode_config()
        self.accept()


class PresetOpenCodeAgentDialog(QDialog):
    """预设 OpenCode Agent 选择对话框"""
    
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        
        self.setWindowTitle("从预设添加 Agent")
        self.setMinimumSize(450, 350)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        layout.addWidget(BodyLabel("选择预设 Agent:", self))
        
        self.agent_list = ListWidget(self)
        self.agent_list.setSelectionMode(QAbstractItemView.MultiSelection)
        for name, data in PRESET_OPENCODE_AGENTS.items():
            self.agent_list.addItem(f"{name} - {data.get('description', '')[:40]}")
        layout.addWidget(self.agent_list)
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.cancel_btn = PushButton("取消", self)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        self.add_btn = PrimaryPushButton("添加选中", self)
        self.add_btn.clicked.connect(self._on_add)
        btn_layout.addWidget(self.add_btn)
        
        layout.addLayout(btn_layout)
    
    def _on_add(self):
        selected = self.agent_list.selectedItems()
        if not selected:
            InfoBar.warning("提示", "请选择至少一个 Agent", parent=self)
            return
        
        config = self.main_window.opencode_config
        if config is None:
            config = {}
            self.main_window.opencode_config = config
        
        if "agent" not in config:
            config["agent"] = {}
        
        added = 0
        for item in selected:
            name = item.text().split(" - ")[0]
            if name in PRESET_OPENCODE_AGENTS:
                preset = PRESET_OPENCODE_AGENTS[name]
                config["agent"][name] = {
                    "mode": preset.get("mode", "subagent"),
                    "description": preset.get("description", ""),
                }
                if "tools" in preset:
                    config["agent"][name]["tools"] = preset["tools"]
                if "permission" in preset:
                    config["agent"][name]["permission"] = preset["permission"]
                added += 1
        
        self.main_window.save_opencode_config()
        InfoBar.success("成功", f"已添加 {added} 个 Agent", parent=self)
        self.accept()
'''

with open(
    r"D:\\opcdcfg\\opencode_config_manager_fluent_v1.0.0.py", "a", encoding="utf-8"
) as f:
    f.write(content)
print("Written successfully")
