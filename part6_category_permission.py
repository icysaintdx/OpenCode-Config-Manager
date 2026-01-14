# -*- coding: utf-8 -*-
"""
OpenCode 配置管理器 v0.9.0 - PyQt5 + QFluentWidgets 版本
Part 6: Category页面和Permission页面
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
    Slider,
    ToolTipFilter, ToolTipPosition,
    Dialog
)

from part3_mainwindow import (
    BasePage, SettingCard, SwitchSettingCard, ComboBoxSettingCard,
    SpinBoxSettingCard, SliderSettingCard, LineEditSettingCard,
    ButtonSettingCard, FormCard, ListCard
)


class CategoryPage(BasePage):
    """分类配置页面 - Temperature滑块和预设分类模板"""

    def __init__(self, config_manager, presets: dict, parent=None):
        super().__init__("分类配置", parent)
        self.config_manager = config_manager
        self.presets = presets
        self._init_content()
        self._load_data()

    def _init_content(self):
        self.add_title("分类配置")
        self.add_subtitle("为不同任务类型配置Temperature参数，优化AI输出效果")
        self.add_spacing(8)

        # 预设分类卡片
        preset_card = CardWidget()
        preset_layout = QVBoxLayout(preset_card)
        preset_layout.setContentsMargins(20, 16, 20, 16)
        preset_layout.setSpacing(16)

        preset_title = SubtitleLabel("预设分类模板")
        preset_layout.addWidget(preset_title)

        preset_desc = CaptionLabel("点击预设分类快速应用推荐的Temperature值")
        preset_desc.setStyleSheet("color: gray;")
        preset_layout.addWidget(preset_desc)

        # 预设按钮网格
        preset_grid = QGridLayout()
        preset_grid.setSpacing(12)

        self.preset_buttons = {}
        for i, (name, config) in enumerate(self.presets.items()):
            btn = PushButton(f"{name}\n({config['temperature']})")
            btn.setMinimumHeight(60)
            btn.setToolTip(config['description'])
            btn.clicked.connect(lambda checked, n=name: self._apply_preset(n))
            self.preset_buttons[name] = btn
            preset_grid.addWidget(btn, i // 4, i % 4)

        preset_layout.addLayout(preset_grid)
        self.content_layout.addWidget(preset_card)

        # 当前配置卡片
        config_card = CardWidget()
        config_layout = QVBoxLayout(config_card)
        config_layout.setContentsMargins(20, 16, 20, 16)
        config_layout.setSpacing(16)

        config_title = SubtitleLabel("当前Temperature配置")
        config_layout.addWidget(config_title)

        # Temperature滑块
        temp_row = QHBoxLayout()
        temp_row.addWidget(BodyLabel("Temperature:"))

        self.temp_slider = Slider(Qt.Horizontal)
        self.temp_slider.setRange(0, 200)  # 0.0 - 2.0
        self.temp_slider.setValue(70)  # 0.7
        self.temp_slider.setMinimumWidth(300)
        self.temp_slider.valueChanged.connect(self._on_temp_changed)
        temp_row.addWidget(self.temp_slider)

        self.temp_label = BodyLabel("0.70")
        self.temp_label.setMinimumWidth(50)
        self.temp_label.setAlignment(Qt.AlignCenter)
        temp_row.addWidget(self.temp_label)

        temp_row.addStretch()
        config_layout.addLayout(temp_row)

        # 说明文字
        temp_desc = CaptionLabel("Temperature控制输出的随机性：0=确定性输出，1=平衡，2=高创造性")
        temp_desc.setStyleSheet("color: gray;")
        config_layout.addWidget(temp_desc)

        self.content_layout.addWidget(config_card)

        # 自定义分类配置
        custom_card = CardWidget()
        custom_layout = QVBoxLayout(custom_card)
        custom_layout.setContentsMargins(20, 16, 20, 16)
        custom_layout.setSpacing(12)

        custom_title = SubtitleLabel("自定义分类")
        custom_layout.addWidget(custom_title)

        # 分类列表
        self.category_list = ListWidget()
        self.category_list.setMaximumHeight(150)
        custom_layout.addWidget(self.category_list)

        # 添加分类
        add_row = QHBoxLayout()
        self.category_name = LineEdit()
        self.category_name.setPlaceholderText("分类名称")
        add_row.addWidget(self.category_name)

        self.category_temp = DoubleSpinBox()
        self.category_temp.setRange(0, 2)
        self.category_temp.setSingleStep(0.1)
        self.category_temp.setValue(0.7)
        add_row.addWidget(self.category_temp)

        add_btn = PushButton("添加")
        add_btn.clicked.connect(self._add_category)
        add_row.addWidget(add_btn)

        del_btn = PushButton("删除")
        del_btn.clicked.connect(self._delete_category)
        add_row.addWidget(del_btn)

        custom_layout.addLayout(add_row)
        self.content_layout.addWidget(custom_card)

        # 保存按钮
        save_btn = PrimaryPushButton("保存配置")
        save_btn.clicked.connect(self._save_config)
        self.content_layout.addWidget(save_btn)

        self.add_stretch()

    def _load_data(self):
        """加载数据"""
        config = self.config_manager.get_config()
        categories = config.get("categories", {})

        # 加载默认temperature
        default_temp = config.get("defaultTemperature", 0.7)
        self.temp_slider.setValue(int(default_temp * 100))
        self.temp_label.setText(f"{default_temp:.2f}")

        # 加载自定义分类
        self.category_list.clear()
        for name, temp in categories.items():
            self.category_list.addItem(f"{name}: {temp}")

    def _on_temp_changed(self, value: int):
        """Temperature滑块变化"""
        temp = value / 100.0
        self.temp_label.setText(f"{temp:.2f}")

    def _apply_preset(self, preset_name: str):
        """应用预设"""
        preset = self.presets.get(preset_name, {})
        temp = preset.get("temperature", 0.7)
        self.temp_slider.setValue(int(temp * 100))
        self.show_info("已应用", f"已应用预设: {preset_name} (Temperature: {temp})")

    def _add_category(self):
        """添加分类"""
        name = self.category_name.text().strip()
        if not name:
            self.show_warning("提示", "请输入分类名称")
            return

        temp = self.category_temp.value()
        self.category_list.addItem(f"{name}: {temp}")
        self.category_name.clear()
        self.show_success("成功", f"已添加分类: {name}")

    def _delete_category(self):
        """删除分类"""
        row = self.category_list.currentRow()
        if row >= 0:
            self.category_list.takeItem(row)
            self.show_success("成功", "已删除分类")
        else:
            self.show_warning("提示", "请先选择要删除的分类")

    def _save_config(self):
        """保存配置"""
        # 保存默认temperature
        default_temp = self.temp_slider.value() / 100.0
        self.config_manager.set("defaultTemperature", default_temp)

        # 保存自定义分类
        categories = {}
        for i in range(self.category_list.count()):
            item_text = self.category_list.item(i).text()
            if ": " in item_text:
                name, temp = item_text.rsplit(": ", 1)
                try:
                    categories[name] = float(temp)
                except ValueError:
                    pass

        self.config_manager.set("categories", categories)
        self.show_success("成功", "分类配置已保存")


class PermissionPage(BasePage):
    """权限配置页面"""

    def __init__(self, config_manager, parent=None):
        super().__init__("权限配置", parent)
        self.config_manager = config_manager
        self._init_content()
        self._load_data()

    def _init_content(self):
        self.add_title("权限配置")
        self.add_subtitle("配置文件操作、命令执行等权限，控制AI的操作范围")
        self.add_spacing(8)

        # 权限模式说明
        mode_card = CardWidget()
        mode_layout = QVBoxLayout(mode_card)
        mode_layout.setContentsMargins(20, 16, 20, 16)
        mode_layout.setSpacing(8)

        mode_title = SubtitleLabel("权限模式说明")
        mode_layout.addWidget(mode_title)

        modes = [
            ("allow", "允许", "自动执行，无需用户确认"),
            ("ask", "询问", "每次执行前询问用户确认"),
            ("deny", "拒绝", "禁止执行此操作")
        ]

        for mode, name, desc in modes:
            row = QHBoxLayout()
            label = BodyLabel(f"• {name} ({mode}):")
            label.setMinimumWidth(120)
            row.addWidget(label)
            row.addWidget(BodyLabel(desc))
            row.addStretch()
            mode_layout.addLayout(row)

        self.content_layout.addWidget(mode_card)

        # Allow列表
        allow_card = CardWidget()
        allow_layout = QVBoxLayout(allow_card)
        allow_layout.setContentsMargins(20, 16, 20, 16)
        allow_layout.setSpacing(12)

        allow_title = SubtitleLabel("允许列表 (Allow)")
        allow_layout.addWidget(allow_title)

        self.allow_list = ListWidget()
        self.allow_list.setMaximumHeight(120)
        allow_layout.addWidget(self.allow_list)

        allow_row = QHBoxLayout()
        self.allow_input = LineEdit()
        self.allow_input.setPlaceholderText("输入操作名称或路径模式")
        allow_row.addWidget(self.allow_input, 1)

        allow_add = PushButton("添加")
        allow_add.clicked.connect(lambda: self._add_item("allow"))
        allow_row.addWidget(allow_add)

        allow_del = PushButton("删除")
        allow_del.clicked.connect(lambda: self._delete_item("allow"))
        allow_row.addWidget(allow_del)

        allow_layout.addLayout(allow_row)
        self.content_layout.addWidget(allow_card)

        # Ask列表
        ask_card = CardWidget()
        ask_layout = QVBoxLayout(ask_card)
        ask_layout.setContentsMargins(20, 16, 20, 16)
        ask_layout.setSpacing(12)

        ask_title = SubtitleLabel("询问列表 (Ask)")
        ask_layout.addWidget(ask_title)

        self.ask_list = ListWidget()
        self.ask_list.setMaximumHeight(120)
        ask_layout.addWidget(self.ask_list)

        ask_row = QHBoxLayout()
        self.ask_input = LineEdit()
        self.ask_input.setPlaceholderText("输入操作名称或路径模式")
        ask_row.addWidget(self.ask_input, 1)

        ask_add = PushButton("添加")
        ask_add.clicked.connect(lambda: self._add_item("ask"))
        ask_row.addWidget(ask_add)

        ask_del = PushButton("删除")
        ask_del.clicked.connect(lambda: self._delete_item("ask"))
        ask_row.addWidget(ask_del)

        ask_layout.addLayout(ask_row)
        self.content_layout.addWidget(ask_card)

        # Deny列表
        deny_card = CardWidget()
        deny_layout = QVBoxLayout(deny_card)
        deny_layout.setContentsMargins(20, 16, 20, 16)
        deny_layout.setSpacing(12)

        deny_title = SubtitleLabel("拒绝列表 (Deny)")
        deny_layout.addWidget(deny_title)

        self.deny_list = ListWidget()
        self.deny_list.setMaximumHeight(120)
        deny_layout.addWidget(self.deny_list)

        deny_row = QHBoxLayout()
        self.deny_input = LineEdit()
        self.deny_input.setPlaceholderText("输入操作名称或路径模式")
        deny_row.addWidget(self.deny_input, 1)

        deny_add = PushButton("添加")
        deny_add.clicked.connect(lambda: self._add_item("deny"))
        deny_row.addWidget(deny_add)

        deny_del = PushButton("删除")
        deny_del.clicked.connect(lambda: self._delete_item("deny"))
        deny_row.addWidget(deny_del)

        deny_layout.addLayout(deny_row)
        self.content_layout.addWidget(deny_card)

        # Bash命令模式
        bash_card = CardWidget()
        bash_layout = QVBoxLayout(bash_card)
        bash_layout.setContentsMargins(20, 16, 20, 16)
        bash_layout.setSpacing(12)

        bash_title = SubtitleLabel("Bash命令权限")
        bash_layout.addWidget(bash_title)

        bash_row = QHBoxLayout()
        bash_row.addWidget(BodyLabel("命令模式:"))
        self.bash_mode = ComboBox()
        self.bash_mode.addItems(["allow", "ask", "deny", "allowlist"])
        self.bash_mode.setMinimumWidth(150)
        self.bash_mode.currentTextChanged.connect(self._on_bash_mode_changed)
        bash_row.addWidget(self.bash_mode)
        bash_row.addStretch()
        bash_layout.addLayout(bash_row)

        # 白名单
        self.allowlist_widget = QWidget()
        allowlist_layout = QVBoxLayout(self.allowlist_widget)
        allowlist_layout.setContentsMargins(0, 8, 0, 0)
        allowlist_layout.setSpacing(8)

        allowlist_label = BodyLabel("命令白名单:")
        allowlist_layout.addWidget(allowlist_label)

        self.allowlist_edit = TextEdit()
        self.allowlist_edit.setPlaceholderText("每行一个命令，如:\ngit\nnpm\npython")
        self.allowlist_edit.setMaximumHeight(100)
        allowlist_layout.addWidget(self.allowlist_edit)

        bash_layout.addWidget(self.allowlist_widget)
        self.content_layout.addWidget(bash_card)

        # 保存按钮
        save_btn = PrimaryPushButton("保存权限配置")
        save_btn.clicked.connect(self._save_config)
        self.content_layout.addWidget(save_btn)

        self.add_stretch()

    def _load_data(self):
        """加载数据"""
        permissions = self.config_manager.get_permissions()

        # 加载列表
        self.allow_list.clear()
        self.allow_list.addItems(permissions.get("allow", []))

        self.ask_list.clear()
        self.ask_list.addItems(permissions.get("ask", []))

        self.deny_list.clear()
        self.deny_list.addItems(permissions.get("deny", []))

        # 加载Bash模式
        bash_config = permissions.get("bash", {})
        if isinstance(bash_config, str):
            self.bash_mode.setCurrentText(bash_config)
        elif isinstance(bash_config, dict):
            mode = bash_config.get("mode", "ask")
            self.bash_mode.setCurrentText(mode)
            allowlist = bash_config.get("allowlist", [])
            self.allowlist_edit.setText("\n".join(allowlist))

        self._on_bash_mode_changed(self.bash_mode.currentText())

    def _on_bash_mode_changed(self, mode: str):
        """Bash模式变化"""
        self.allowlist_widget.setVisible(mode == "allowlist")

    def _add_item(self, list_type: str):
        """添加项目"""
        input_map = {
            "allow": (self.allow_input, self.allow_list),
            "ask": (self.ask_input, self.ask_list),
            "deny": (self.deny_input, self.deny_list)
        }

        input_edit, list_widget = input_map[list_type]
        text = input_edit.text().strip()
        if text:
            list_widget.addItem(text)
            input_edit.clear()
        else:
            self.show_warning("提示", "请输入内容")

    def _delete_item(self, list_type: str):
        """删除项目"""
        list_map = {
            "allow": self.allow_list,
            "ask": self.ask_list,
            "deny": self.deny_list
        }

        list_widget = list_map[list_type]
        row = list_widget.currentRow()
        if row >= 0:
            list_widget.takeItem(row)
        else:
            self.show_warning("提示", "请先选择要删除的项目")

    def _save_config(self):
        """保存配置"""
        permissions = {
            "allow": [self.allow_list.item(i).text() for i in range(self.allow_list.count())],
            "ask": [self.ask_list.item(i).text() for i in range(self.ask_list.count())],
            "deny": [self.deny_list.item(i).text() for i in range(self.deny_list.count())]
        }

        # Bash配置
        bash_mode = self.bash_mode.currentText()
        if bash_mode == "allowlist":
            allowlist = [cmd.strip() for cmd in self.allowlist_edit.toPlainText().split("\n") if cmd.strip()]
            permissions["bash"] = {
                "mode": "allowlist",
                "allowlist": allowlist
            }
        else:
            permissions["bash"] = bash_mode

        self.config_manager.set_permissions(permissions)
        self.show_success("成功", "权限配置已保存")
