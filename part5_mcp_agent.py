# -*- coding: utf-8 -*-
"""
OpenCode 配置管理器 v0.9.0 - PyQt5 + QFluentWidgets 版本
Part 5: MCP页面和Agent页面
"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QSplitter
)

from qfluentwidgets import (
    FluentIcon as FIF, InfoBar, InfoBarPosition, MessageBox,
    PushButton, PrimaryPushButton, TransparentPushButton,
    SubtitleLabel, BodyLabel, CaptionLabel,
    CardWidget, SimpleCardWidget,
    ComboBox, LineEdit, TextEdit, SpinBox, DoubleSpinBox,
    SwitchButton, CheckBox, RadioButton,
    ListWidget, TableWidget,
    ToolTipFilter, ToolTipPosition,
    Dialog
)

from part3_mainwindow import (
    BasePage, SettingCard, SwitchSettingCard, ComboBoxSettingCard,
    SpinBoxSettingCard, LineEditSettingCard, ButtonSettingCard,
    FormCard, ListCard
)


class MCPDialog(Dialog):
    """MCP服务器编辑对话框"""

    def __init__(self, parent=None, server_name: str = "", server_config: dict = None):
        super().__init__("编辑MCP服务器" if server_name else "添加MCP服务器", "", parent)
        self.server_name = server_name
        self.server_config = server_config or {}
        self._init_ui()

    def _init_ui(self):
        self.textLayout.deleteLater()

        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(12)

        # 名称
        name_layout = QHBoxLayout()
        name_label = BodyLabel("名称:")
        name_label.setMinimumWidth(100)
        self.name_edit = LineEdit()
        self.name_edit.setPlaceholderText("MCP服务器名称")
        self.name_edit.setText(self.server_name)
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit, 1)
        form_layout.addLayout(name_layout)

        # 类型
        type_layout = QHBoxLayout()
        type_label = BodyLabel("类型:")
        type_label.setMinimumWidth(100)
        self.type_combo = ComboBox()
        self.type_combo.addItems(["local", "remote"])
        current_type = self.server_config.get("type", "local")
        self.type_combo.setCurrentText(current_type)
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo, 1)
        form_layout.addLayout(type_layout)

        # Local配置区域
        self.local_widget = QWidget()
        local_layout = QVBoxLayout(self.local_widget)
        local_layout.setContentsMargins(0, 0, 0, 0)
        local_layout.setSpacing(12)

        # 命令
        cmd_layout = QHBoxLayout()
        cmd_label = BodyLabel("命令:")
        cmd_label.setMinimumWidth(100)
        self.cmd_edit = LineEdit()
        self.cmd_edit.setPlaceholderText("启动命令，如 npx, python")
        self.cmd_edit.setText(self.server_config.get("command", ""))
        cmd_layout.addWidget(cmd_label)
        cmd_layout.addWidget(self.cmd_edit, 1)
        local_layout.addLayout(cmd_layout)

        # 参数
        args_layout = QHBoxLayout()
        args_label = BodyLabel("参数:")
        args_label.setMinimumWidth(100)
        self.args_edit = LineEdit()
        self.args_edit.setPlaceholderText("命令参数，用逗号分隔")
        args = self.server_config.get("args", [])
        self.args_edit.setText(", ".join(args) if args else "")
        args_layout.addWidget(args_label)
        args_layout.addWidget(self.args_edit, 1)
        local_layout.addLayout(args_layout)

        form_layout.addWidget(self.local_widget)

        # Remote配置区域
        self.remote_widget = QWidget()
        remote_layout = QVBoxLayout(self.remote_widget)
        remote_layout.setContentsMargins(0, 0, 0, 0)
        remote_layout.setSpacing(12)

        # URL
        url_layout = QHBoxLayout()
        url_label = BodyLabel("URL:")
        url_label.setMinimumWidth(100)
        self.url_edit = LineEdit()
        self.url_edit.setPlaceholderText("远程服务器URL")
        self.url_edit.setText(self.server_config.get("url", ""))
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_edit, 1)
        remote_layout.addLayout(url_layout)

        form_layout.addWidget(self.remote_widget)

        # 环境变量
        env_layout = QHBoxLayout()
        env_label = BodyLabel("环境变量:")
        env_label.setMinimumWidth(100)
        self.env_edit = TextEdit()
        self.env_edit.setPlaceholderText('{"KEY": "value"}')
        self.env_edit.setMaximumHeight(80)
        import json
        env = self.server_config.get("env", {})
        self.env_edit.setText(json.dumps(env, indent=2, ensure_ascii=False) if env else "")
        env_layout.addWidget(env_label)
        env_layout.addWidget(self.env_edit, 1)
        form_layout.addLayout(env_layout)

        # 超时
        timeout_layout = QHBoxLayout()
        timeout_label = BodyLabel("超时(秒):")
        timeout_label.setMinimumWidth(100)
        self.timeout_spin = SpinBox()
        self.timeout_spin.setRange(1, 3600)
        self.timeout_spin.setValue(self.server_config.get("timeout", 60))
        timeout_layout.addWidget(timeout_label)
        timeout_layout.addWidget(self.timeout_spin, 1)
        form_layout.addLayout(timeout_layout)

        self.vBoxLayout.insertWidget(0, form_widget)
        self.widget.setMinimumWidth(500)

        # 初始化显示
        self._on_type_changed(current_type)

    def _on_type_changed(self, type_name: str):
        """类型变化"""
        self.local_widget.setVisible(type_name == "local")
        self.remote_widget.setVisible(type_name == "remote")

    def get_data(self) -> tuple:
        """获取表单数据"""
        import json
        name = self.name_edit.text().strip()
        server_type = self.type_combo.currentText()

        config = {"type": server_type}

        if server_type == "local":
            config["command"] = self.cmd_edit.text().strip()
            args_text = self.args_edit.text().strip()
            if args_text:
                config["args"] = [a.strip() for a in args_text.split(",") if a.strip()]
        else:
            config["url"] = self.url_edit.text().strip()

        env_text = self.env_edit.toPlainText().strip()
        if env_text:
            try:
                config["env"] = json.loads(env_text)
            except json.JSONDecodeError:
                pass

        timeout = self.timeout_spin.value()
        if timeout != 60:
            config["timeout"] = timeout

        return name, config


class MCPPage(BasePage):
    """MCP服务器配置页面"""

    def __init__(self, config_manager, parent=None):
        super().__init__("MCP配置", parent)
        self.config_manager = config_manager
        self._init_content()
        self._load_data()

    def _init_content(self):
        self.add_title("MCP服务器配置")
        self.add_subtitle("管理Model Context Protocol服务器，支持本地和远程类型")
        self.add_spacing(8)

        # 创建分栏布局
        splitter = QSplitter(Qt.Horizontal)

        # 左侧列表
        self.list_card = ListCard()
        self.add_btn = self.list_card.add_toolbar_button("添加", FIF.ADD)
        self.edit_btn = self.list_card.add_toolbar_button("编辑", FIF.EDIT)
        self.delete_btn = self.list_card.add_toolbar_button("删除", FIF.DELETE)
        self.list_card.add_toolbar_stretch()

        self.add_btn.clicked.connect(self._on_add)
        self.edit_btn.clicked.connect(self._on_edit)
        self.delete_btn.clicked.connect(self._on_delete)
        self.list_card.itemDoubleClicked.connect(lambda: self._on_edit())
        self.list_card.itemSelected.connect(self._on_select)

        splitter.addWidget(self.list_card)

        # 右侧详情
        self.detail_card = CardWidget()
        detail_layout = QVBoxLayout(self.detail_card)
        detail_layout.setContentsMargins(20, 20, 20, 20)
        detail_layout.setSpacing(12)

        self.detail_title = SubtitleLabel("选择MCP服务器查看详情")
        detail_layout.addWidget(self.detail_title)

        self.detail_info = QWidget()
        info_layout = QGridLayout(self.detail_info)
        info_layout.setSpacing(8)

        info_layout.addWidget(BodyLabel("名称:"), 0, 0)
        self.info_name = BodyLabel("-")
        info_layout.addWidget(self.info_name, 0, 1)

        info_layout.addWidget(BodyLabel("类型:"), 1, 0)
        self.info_type = BodyLabel("-")
        info_layout.addWidget(self.info_type, 1, 1)

        info_layout.addWidget(BodyLabel("命令/URL:"), 2, 0)
        self.info_cmd = BodyLabel("-")
        self.info_cmd.setWordWrap(True)
        info_layout.addWidget(self.info_cmd, 2, 1)

        info_layout.addWidget(BodyLabel("参数:"), 3, 0)
        self.info_args = BodyLabel("-")
        self.info_args.setWordWrap(True)
        info_layout.addWidget(self.info_args, 3, 1)

        info_layout.addWidget(BodyLabel("超时:"), 4, 0)
        self.info_timeout = BodyLabel("-")
        info_layout.addWidget(self.info_timeout, 4, 1)

        info_layout.setColumnStretch(1, 1)
        detail_layout.addWidget(self.detail_info)

        # 环境变量显示
        env_label = SubtitleLabel("环境变量")
        detail_layout.addWidget(env_label)

        self.env_display = TextEdit()
        self.env_display.setReadOnly(True)
        self.env_display.setMaximumHeight(120)
        detail_layout.addWidget(self.env_display)

        detail_layout.addStretch()

        splitter.addWidget(self.detail_card)
        splitter.setSizes([300, 400])

        self.content_layout.addWidget(splitter, 1)

    def _load_data(self):
        """加载数据"""
        self.list_card.clear()
        servers = self.config_manager.get_mcp_servers()
        for name in servers.keys():
            self.list_card.add_item(name)

    def _on_select(self, name: str):
        """选择MCP服务器"""
        server = self.config_manager.get_mcp_server(name)
        if server:
            self.detail_title.setText(name)
            self.info_name.setText(name)
            self.info_type.setText(server.get("type", "local"))

            if server.get("type") == "remote":
                self.info_cmd.setText(server.get("url", "-"))
                self.info_args.setText("-")
            else:
                self.info_cmd.setText(server.get("command", "-"))
                args = server.get("args", [])
                self.info_args.setText(", ".join(args) if args else "-")

            self.info_timeout.setText(f"{server.get('timeout', 60)}秒")

            import json
            env = server.get("env", {})
            self.env_display.setText(json.dumps(env, indent=2, ensure_ascii=False) if env else "无")

    def _on_add(self):
        """添加MCP服务器"""
        dialog = MCPDialog(self)
        if dialog.exec():
            name, config = dialog.get_data()
            if name:
                self.config_manager.add_mcp_server(name, config)
                self._load_data()
                self.show_success("成功", f"已添加MCP服务器: {name}")
            else:
                self.show_error("错误", "服务器名称不能为空")

    def _on_edit(self):
        """编辑MCP服务器"""
        name = self.list_card.current_item()
        if not name:
            self.show_warning("提示", "请先选择要编辑的MCP服务器")
            return

        server = self.config_manager.get_mcp_server(name)
        dialog = MCPDialog(self, name, server)
        if dialog.exec():
            new_name, config = dialog.get_data()
            if new_name:
                if new_name != name:
                    self.config_manager.delete_mcp_server(name)
                self.config_manager.add_mcp_server(new_name, config)
                self._load_data()
                self.show_success("成功", f"已更新MCP服务器: {new_name}")

    def _on_delete(self):
        """删除MCP服务器"""
        name = self.list_card.current_item()
        if not name:
            self.show_warning("提示", "请先选择要删除的MCP服务器")
            return

        box = MessageBox("确认删除", f"确定要删除MCP服务器 '{name}' 吗？", self)
        if box.exec():
            self.config_manager.delete_mcp_server(name)
            self._load_data()
            self.detail_title.setText("选择MCP服务器查看详情")
            self.show_success("成功", f"已删除MCP服务器: {name}")


class OpenCodeAgentPage(BasePage):
    """OpenCode Agent配置页面"""

    def __init__(self, config_manager, parent=None):
        super().__init__("OpenCode Agent", parent)
        self.config_manager = config_manager
        self._init_content()
        self._load_data()

    def _init_content(self):
        self.add_title("OpenCode Agent配置")
        self.add_subtitle("配置Agent的运行模式、温度参数和工具权限")
        self.add_spacing(8)

        # Agent模式
        mode_card = CardWidget()
        mode_layout = QVBoxLayout(mode_card)
        mode_layout.setContentsMargins(20, 16, 20, 16)
        mode_layout.setSpacing(12)

        mode_title = SubtitleLabel("运行模式")
        mode_layout.addWidget(mode_title)

        mode_row = QHBoxLayout()
        mode_row.addWidget(BodyLabel("Agent模式:"))
        self.mode_combo = ComboBox()
        self.mode_combo.addItems(["auto", "manual", "hybrid"])
        self.mode_combo.setMinimumWidth(150)
        mode_row.addWidget(self.mode_combo)
        mode_row.addStretch()
        mode_layout.addLayout(mode_row)

        self.content_layout.addWidget(mode_card)

        # 参数配置
        param_card = CardWidget()
        param_layout = QVBoxLayout(param_card)
        param_layout.setContentsMargins(20, 16, 20, 16)
        param_layout.setSpacing(12)

        param_title = SubtitleLabel("参数配置")
        param_layout.addWidget(param_title)

        # Temperature
        temp_row = QHBoxLayout()
        temp_row.addWidget(BodyLabel("Temperature:"))
        self.temp_slider = DoubleSpinBox()
        self.temp_slider.setRange(0, 2)
        self.temp_slider.setSingleStep(0.1)
        self.temp_slider.setValue(0.7)
        self.temp_slider.setMinimumWidth(120)
        temp_row.addWidget(self.temp_slider)
        temp_row.addStretch()
        param_layout.addLayout(temp_row)

        # Max Steps
        steps_row = QHBoxLayout()
        steps_row.addWidget(BodyLabel("最大步骤数:"))
        self.steps_spin = SpinBox()
        self.steps_spin.setRange(1, 1000)
        self.steps_spin.setValue(50)
        self.steps_spin.setMinimumWidth(120)
        steps_row.addWidget(self.steps_spin)
        steps_row.addStretch()
        param_layout.addLayout(steps_row)

        self.content_layout.addWidget(param_card)

        # 工具配置
        tools_card = CardWidget()
        tools_layout = QVBoxLayout(tools_card)
        tools_layout.setContentsMargins(20, 16, 20, 16)
        tools_layout.setSpacing(12)

        tools_title = SubtitleLabel("可用工具")
        tools_layout.addWidget(tools_title)

        tools_grid = QGridLayout()
        tools_grid.setSpacing(8)

        self.tool_checks = {}
        tools = ["read", "write", "edit", "bash", "glob", "grep", "ls", "web_search", "web_fetch"]
        for i, tool in enumerate(tools):
            check = CheckBox(tool)
            check.setChecked(True)
            self.tool_checks[tool] = check
            tools_grid.addWidget(check, i // 3, i % 3)

        tools_layout.addLayout(tools_grid)
        self.content_layout.addWidget(tools_card)

        # 权限配置
        perm_card = CardWidget()
        perm_layout = QVBoxLayout(perm_card)
        perm_layout.setContentsMargins(20, 16, 20, 16)
        perm_layout.setSpacing(12)

        perm_title = SubtitleLabel("权限配置")
        perm_layout.addWidget(perm_title)

        # 文件写入权限
        write_row = QHBoxLayout()
        write_row.addWidget(BodyLabel("文件写入:"))
        self.write_perm = ComboBox()
        self.write_perm.addItems(["allow", "ask", "deny"])
        self.write_perm.setMinimumWidth(120)
        write_row.addWidget(self.write_perm)
        write_row.addStretch()
        perm_layout.addLayout(write_row)

        # Bash执行权限
        bash_row = QHBoxLayout()
        bash_row.addWidget(BodyLabel("Bash执行:"))
        self.bash_perm = ComboBox()
        self.bash_perm.addItems(["allow", "ask", "deny", "allowlist"])
        self.bash_perm.setMinimumWidth(120)
        bash_row.addWidget(self.bash_perm)
        bash_row.addStretch()
        perm_layout.addLayout(bash_row)

        self.content_layout.addWidget(perm_card)

        # 保存按钮
        save_btn = PrimaryPushButton("保存配置")
        save_btn.clicked.connect(self._save_config)
        self.content_layout.addWidget(save_btn)

        self.add_stretch()

    def _load_data(self):
        """加载数据"""
        config = self.config_manager.get_config()
        agent_config = config.get("agent", {})

        self.mode_combo.setCurrentText(agent_config.get("mode", "auto"))
        self.temp_slider.setValue(agent_config.get("temperature", 0.7))
        self.steps_spin.setValue(agent_config.get("maxSteps", 50))

        tools = agent_config.get("tools", list(self.tool_checks.keys()))
        for tool, check in self.tool_checks.items():
            check.setChecked(tool in tools)

        permissions = agent_config.get("permissions", {})
        self.write_perm.setCurrentText(permissions.get("write", "ask"))
        self.bash_perm.setCurrentText(permissions.get("bash", "ask"))

    def _save_config(self):
        """保存配置"""
        agent_config = {
            "mode": self.mode_combo.currentText(),
            "temperature": self.temp_slider.value(),
            "maxSteps": self.steps_spin.value(),
            "tools": [tool for tool, check in self.tool_checks.items() if check.isChecked()],
            "permissions": {
                "write": self.write_perm.currentText(),
                "bash": self.bash_perm.currentText()
            }
        }

        self.config_manager.set("agent", agent_config)
        self.show_success("成功", "Agent配置已保存")


class AgentPage(BasePage):
    """Agent配置页面 - OhMy OpenCode"""

    def __init__(self, config_manager, presets: dict, parent=None):
        super().__init__("Agent管理", parent)
        self.config_manager = config_manager
        self.presets = presets
        self._init_content()
        self._load_data()

    def _init_content(self):
        self.add_title("Agent管理")
        self.add_subtitle("管理自定义Agent，配置模型绑定和行为指令")
        self.add_spacing(8)

        # 创建分栏布局
        splitter = QSplitter(Qt.Horizontal)

        # 左侧列表
        self.list_card = ListCard()
        self.add_btn = self.list_card.add_toolbar_button("添加", FIF.ADD)
        self.preset_btn = self.list_card.add_toolbar_button("预设", FIF.LIBRARY)
        self.delete_btn = self.list_card.add_toolbar_button("删除", FIF.DELETE)
        self.list_card.add_toolbar_stretch()

        self.add_btn.clicked.connect(self._on_add)
        self.preset_btn.clicked.connect(self._on_add_preset)
        self.delete_btn.clicked.connect(self._on_delete)
        self.list_card.itemSelected.connect(self._on_select)

        splitter.addWidget(self.list_card)

        # 右侧编辑区
        self.edit_card = CardWidget()
        edit_layout = QVBoxLayout(self.edit_card)
        edit_layout.setContentsMargins(20, 20, 20, 20)
        edit_layout.setSpacing(12)

        self.edit_title = SubtitleLabel("选择Agent进行编辑")
        edit_layout.addWidget(self.edit_title)

        # 名称
        name_row = QHBoxLayout()
        name_row.addWidget(BodyLabel("名称:"))
        self.name_edit = LineEdit()
        self.name_edit.setPlaceholderText("Agent名称")
        name_row.addWidget(self.name_edit, 1)
        edit_layout.addLayout(name_row)

        # 绑定模型
        model_row = QHBoxLayout()
        model_row.addWidget(BodyLabel("绑定模型:"))
        self.model_combo = ComboBox()
        self.model_combo.setMinimumWidth(200)
        model_row.addWidget(self.model_combo, 1)
        edit_layout.addLayout(model_row)

        # 描述
        desc_row = QHBoxLayout()
        desc_row.addWidget(BodyLabel("描述:"))
        self.desc_edit = LineEdit()
        self.desc_edit.setPlaceholderText("Agent描述")
        desc_row.addWidget(self.desc_edit, 1)
        edit_layout.addLayout(desc_row)

        # 指令
        inst_label = BodyLabel("指令:")
        edit_layout.addWidget(inst_label)

        self.inst_edit = TextEdit()
        self.inst_edit.setPlaceholderText("Agent行为指令")
        self.inst_edit.setMinimumHeight(150)
        edit_layout.addWidget(self.inst_edit)

        # 保存按钮
        save_btn = PrimaryPushButton("保存Agent")
        save_btn.clicked.connect(self._save_agent)
        edit_layout.addWidget(save_btn)

        edit_layout.addStretch()

        splitter.addWidget(self.edit_card)
        splitter.setSizes([300, 500])

        self.content_layout.addWidget(splitter, 1)

    def _load_data(self):
        """加载数据"""
        self.list_card.clear()
        agents = self.config_manager.get_agents()
        for name in agents.keys():
            self.list_card.add_item(name)

        # 更新模型下拉框
        self.model_combo.clear()
        self.model_combo.addItem("")
        models = self.config_manager.get_models()
        self.model_combo.addItems(list(models.keys()))

    def _on_select(self, name: str):
        """选择Agent"""
        agent = self.config_manager.get_agent(name)
        if agent:
            self.edit_title.setText(f"编辑: {name}")
            self.name_edit.setText(agent.get("name", name))
            self.model_combo.setCurrentText(agent.get("model", ""))
            self.desc_edit.setText(agent.get("description", ""))
            self.inst_edit.setText(agent.get("instructions", ""))

    def _on_add(self):
        """添加Agent"""
        self.edit_title.setText("新建Agent")
        self.name_edit.clear()
        self.model_combo.setCurrentIndex(0)
        self.desc_edit.clear()
        self.inst_edit.clear()

    def _on_add_preset(self):
        """添加预设Agent"""
        from qfluentwidgets import RoundMenu, Action
        menu = RoundMenu(parent=self)
        for preset_name in self.presets.keys():
            action = Action(preset_name)
            action.triggered.connect(lambda checked, n=preset_name: self._apply_preset(n))
            menu.addAction(action)
        menu.exec_(self.preset_btn.mapToGlobal(self.preset_btn.rect().bottomLeft()))

    def _apply_preset(self, preset_name: str):
        """应用预设"""
        preset = self.presets.get(preset_name, {})
        self.edit_title.setText(f"新建Agent (预设: {preset_name})")
        self.name_edit.setText(preset.get("name", ""))
        self.model_combo.setCurrentText(preset.get("model", ""))
        self.desc_edit.setText(preset.get("description", ""))
        self.inst_edit.setText(preset.get("instructions", ""))

    def _on_delete(self):
        """删除Agent"""
        name = self.list_card.current_item()
        if not name:
            self.show_warning("提示", "请先选择要删除的Agent")
            return

        box = MessageBox("确认删除", f"确定要删除Agent '{name}' 吗？", self)
        if box.exec():
            self.config_manager.delete_agent(name)
            self._load_data()
            self.edit_title.setText("选择Agent进行编辑")
            self.show_success("成功", f"已删除Agent: {name}")

    def _save_agent(self):
        """保存Agent"""
        name = self.name_edit.text().strip()
        if not name:
            self.show_error("错误", "Agent名称不能为空")
            return

        config = {
            "name": name,
            "model": self.model_combo.currentText(),
            "description": self.desc_edit.text().strip(),
            "instructions": self.inst_edit.toPlainText().strip()
        }

        # 检查是否是编辑现有Agent
        current = self.list_card.current_item()
        if current and current != name:
            self.config_manager.delete_agent(current)

        self.config_manager.add_agent(name, config)
        self._load_data()
        self.show_success("成功", f"已保存Agent: {name}")
