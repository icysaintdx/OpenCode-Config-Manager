# -*- coding: utf-8 -*-
"""
OpenCode 配置管理器 v0.9.0 - PyQt5 + QFluentWidgets 版本
Part 4: Provider页面和Model页面
"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QSplitter, QDialog, QDialogButtonBox
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


class ProviderDialog(Dialog):
    """服务商编辑对话框"""

    def __init__(self, parent=None, provider_name: str = "", provider_config: dict = None, presets: dict = None):
        super().__init__("编辑服务商" if provider_name else "添加服务商", "", parent)
        self.provider_name = provider_name
        self.provider_config = provider_config or {}
        self.presets = presets or {}
        self._init_ui()

    def _init_ui(self):
        # 移除默认内容
        self.textLayout.deleteLater()

        # 创建表单
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(16)

        # SDK预设选择
        preset_layout = QHBoxLayout()
        preset_label = BodyLabel("SDK预设:")
        preset_label.setMinimumWidth(100)
        self.preset_combo = ComboBox()
        self.preset_combo.addItem("自定义")
        self.preset_combo.addItems(list(self.presets.keys()))
        self.preset_combo.currentTextChanged.connect(self._on_preset_changed)
        preset_layout.addWidget(preset_label)
        preset_layout.addWidget(self.preset_combo, 1)
        form_layout.addLayout(preset_layout)

        # 名称
        name_layout = QHBoxLayout()
        name_label = BodyLabel("名称:")
        name_label.setMinimumWidth(100)
        self.name_edit = LineEdit()
        self.name_edit.setPlaceholderText("服务商名称")
        self.name_edit.setText(self.provider_name)
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit, 1)
        form_layout.addLayout(name_layout)

        # API Key
        key_layout = QHBoxLayout()
        key_label = BodyLabel("API Key:")
        key_label.setMinimumWidth(100)
        self.key_edit = LineEdit()
        self.key_edit.setPlaceholderText("API密钥或环境变量 ${ENV_VAR}")
        self.key_edit.setText(self.provider_config.get("apiKey", ""))
        key_layout.addWidget(key_label)
        key_layout.addWidget(self.key_edit, 1)
        form_layout.addLayout(key_layout)

        # Base URL
        url_layout = QHBoxLayout()
        url_label = BodyLabel("Base URL:")
        url_label.setMinimumWidth(100)
        self.url_edit = LineEdit()
        self.url_edit.setPlaceholderText("API基础URL")
        self.url_edit.setText(self.provider_config.get("baseUrl", ""))
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_edit, 1)
        form_layout.addLayout(url_layout)

        # 禁用开关
        disabled_layout = QHBoxLayout()
        disabled_label = BodyLabel("禁用:")
        disabled_label.setMinimumWidth(100)
        self.disabled_switch = SwitchButton()
        self.disabled_switch.setChecked(self.provider_config.get("disabled", False))
        disabled_layout.addWidget(disabled_label)
        disabled_layout.addWidget(self.disabled_switch)
        disabled_layout.addStretch()
        form_layout.addLayout(disabled_layout)

        self.vBoxLayout.insertWidget(0, form_widget)
        self.widget.setMinimumWidth(500)

    def _on_preset_changed(self, preset_name: str):
        """预设选择变化"""
        if preset_name in self.presets:
            preset = self.presets[preset_name]
            self.name_edit.setText(preset.get("name", ""))
            self.url_edit.setText(preset.get("base_url", ""))
            env_key = preset.get("env_key", "")
            if env_key:
                self.key_edit.setText(f"${{{env_key}}}")

    def get_data(self) -> tuple:
        """获取表单数据"""
        name = self.name_edit.text().strip()
        config = {
            "apiKey": self.key_edit.text().strip(),
            "baseUrl": self.url_edit.text().strip(),
        }
        if self.disabled_switch.isChecked():
            config["disabled"] = True
        return name, config


class ProviderPage(BasePage):
    """服务商配置页面"""

    def __init__(self, config_manager, presets: dict, parent=None):
        super().__init__("服务商配置", parent)
        self.config_manager = config_manager
        self.presets = presets
        self._init_content()
        self._load_data()

    def _init_content(self):
        self.add_title("服务商配置")
        self.add_subtitle("管理API服务商，配置API密钥和端点地址")
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

        self.detail_title = SubtitleLabel("选择服务商查看详情")
        detail_layout.addWidget(self.detail_title)

        self.detail_info = QWidget()
        info_layout = QGridLayout(self.detail_info)
        info_layout.setSpacing(8)

        info_layout.addWidget(BodyLabel("名称:"), 0, 0)
        self.info_name = BodyLabel("-")
        info_layout.addWidget(self.info_name, 0, 1)

        info_layout.addWidget(BodyLabel("API Key:"), 1, 0)
        self.info_key = BodyLabel("-")
        info_layout.addWidget(self.info_key, 1, 1)

        info_layout.addWidget(BodyLabel("Base URL:"), 2, 0)
        self.info_url = BodyLabel("-")
        self.info_url.setWordWrap(True)
        info_layout.addWidget(self.info_url, 2, 1)

        info_layout.addWidget(BodyLabel("状态:"), 3, 0)
        self.info_status = BodyLabel("-")
        info_layout.addWidget(self.info_status, 3, 1)

        info_layout.setColumnStretch(1, 1)
        detail_layout.addWidget(self.detail_info)
        detail_layout.addStretch()

        splitter.addWidget(self.detail_card)
        splitter.setSizes([300, 400])

        self.content_layout.addWidget(splitter, 1)

    def _load_data(self):
        """加载数据"""
        self.list_card.clear()
        providers = self.config_manager.get_providers()
        for name in providers.keys():
            self.list_card.add_item(name)

    def _on_select(self, name: str):
        """选择服务商"""
        provider = self.config_manager.get_provider(name)
        if provider:
            self.detail_title.setText(name)
            self.info_name.setText(name)

            api_key = provider.get("apiKey", "")
            if api_key.startswith("${"):
                self.info_key.setText(api_key)
            else:
                self.info_key.setText("*" * 8 if api_key else "-")

            self.info_url.setText(provider.get("baseUrl", "-") or "-")
            self.info_status.setText("已禁用" if provider.get("disabled") else "已启用")

    def _on_add(self):
        """添加服务商"""
        dialog = ProviderDialog(self, presets=self.presets)
        if dialog.exec():
            name, config = dialog.get_data()
            if name:
                self.config_manager.add_provider(name, config)
                self._load_data()
                self.show_success("成功", f"已添加服务商: {name}")
            else:
                self.show_error("错误", "服务商名称不能为空")

    def _on_edit(self):
        """编辑服务商"""
        name = self.list_card.current_item()
        if not name:
            self.show_warning("提示", "请先选择要编辑的服务商")
            return

        provider = self.config_manager.get_provider(name)
        dialog = ProviderDialog(self, name, provider, self.presets)
        if dialog.exec():
            new_name, config = dialog.get_data()
            if new_name:
                if new_name != name:
                    self.config_manager.delete_provider(name)
                self.config_manager.add_provider(new_name, config)
                self._load_data()
                self.show_success("成功", f"已更新服务商: {new_name}")

    def _on_delete(self):
        """删除服务商"""
        name = self.list_card.current_item()
        if not name:
            self.show_warning("提示", "请先选择要删除的服务商")
            return

        box = MessageBox("确认删除", f"确定要删除服务商 '{name}' 吗？", self)
        if box.exec():
            self.config_manager.delete_provider(name)
            self._load_data()
            self.detail_title.setText("选择服务商查看详情")
            self.show_success("成功", f"已删除服务商: {name}")


class ModelDialog(Dialog):
    """模型编辑对话框"""

    def __init__(self, parent=None, model_id: str = "", model_config: dict = None, presets: dict = None):
        super().__init__("编辑模型" if model_id else "添加模型", "", parent)
        self.model_id = model_id
        self.model_config = model_config or {}
        self.presets = presets or {}
        self._init_ui()

    def _init_ui(self):
        self.textLayout.deleteLater()

        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(12)

        # 预设选择
        preset_layout = QHBoxLayout()
        preset_label = BodyLabel("预设模型:")
        preset_label.setMinimumWidth(120)
        self.preset_combo = ComboBox()
        self.preset_combo.addItem("自定义")
        self.preset_combo.addItems(list(self.presets.keys()))
        self.preset_combo.currentTextChanged.connect(self._on_preset_changed)
        preset_layout.addWidget(preset_label)
        preset_layout.addWidget(self.preset_combo, 1)
        form_layout.addLayout(preset_layout)

        # 模型ID
        id_layout = QHBoxLayout()
        id_label = BodyLabel("模型ID:")
        id_label.setMinimumWidth(120)
        self.id_edit = LineEdit()
        self.id_edit.setPlaceholderText("模型标识符")
        self.id_edit.setText(self.model_id)
        id_layout.addWidget(id_label)
        id_layout.addWidget(self.id_edit, 1)
        form_layout.addLayout(id_layout)

        # 最大Token数
        tokens_layout = QHBoxLayout()
        tokens_label = BodyLabel("最大Token数:")
        tokens_label.setMinimumWidth(120)
        self.tokens_spin = SpinBox()
        self.tokens_spin.setRange(1, 1000000)
        self.tokens_spin.setValue(self.model_config.get("maxTokens", 8192))
        tokens_layout.addWidget(tokens_label)
        tokens_layout.addWidget(self.tokens_spin, 1)
        form_layout.addLayout(tokens_layout)

        # 上下文窗口
        context_layout = QHBoxLayout()
        context_label = BodyLabel("上下文窗口:")
        context_label.setMinimumWidth(120)
        self.context_spin = SpinBox()
        self.context_spin.setRange(1, 10000000)
        self.context_spin.setValue(self.model_config.get("contextWindow", 128000))
        context_layout.addWidget(context_label)
        context_layout.addWidget(self.context_spin, 1)
        form_layout.addLayout(context_layout)

        # 支持图像
        images_layout = QHBoxLayout()
        images_label = BodyLabel("支持图像:")
        images_label.setMinimumWidth(120)
        self.images_switch = SwitchButton()
        self.images_switch.setChecked(self.model_config.get("supportsImages", False))
        images_layout.addWidget(images_label)
        images_layout.addWidget(self.images_switch)
        images_layout.addStretch()
        form_layout.addLayout(images_layout)

        # 支持计算机使用
        computer_layout = QHBoxLayout()
        computer_label = BodyLabel("计算机使用:")
        computer_label.setMinimumWidth(120)
        self.computer_switch = SwitchButton()
        self.computer_switch.setChecked(self.model_config.get("supportsComputerUse", False))
        computer_layout.addWidget(computer_label)
        computer_layout.addWidget(self.computer_switch)
        computer_layout.addStretch()
        form_layout.addLayout(computer_layout)

        # 推理模型
        reasoning_layout = QHBoxLayout()
        reasoning_label = BodyLabel("推理模型:")
        reasoning_label.setMinimumWidth(120)
        self.reasoning_switch = SwitchButton()
        self.reasoning_switch.setChecked(self.model_config.get("reasoning", False))
        reasoning_layout.addWidget(reasoning_label)
        reasoning_layout.addWidget(self.reasoning_switch)
        reasoning_layout.addStretch()
        form_layout.addLayout(reasoning_layout)

        self.vBoxLayout.insertWidget(0, form_widget)
        self.widget.setMinimumWidth(500)

    def _on_preset_changed(self, preset_name: str):
        """预设选择变化"""
        if preset_name in self.presets:
            preset = self.presets[preset_name]
            self.id_edit.setText(preset_name)
            self.tokens_spin.setValue(preset.get("maxTokens", 8192))
            self.context_spin.setValue(preset.get("contextWindow", 128000))
            self.images_switch.setChecked(preset.get("supportsImages", False))
            self.computer_switch.setChecked(preset.get("supportsComputerUse", False))
            self.reasoning_switch.setChecked(preset.get("reasoning", False))

    def get_data(self) -> tuple:
        """获取表单数据"""
        model_id = self.id_edit.text().strip()
        config = {
            "maxTokens": self.tokens_spin.value(),
            "contextWindow": self.context_spin.value(),
            "supportsImages": self.images_switch.isChecked(),
            "supportsComputerUse": self.computer_switch.isChecked(),
        }
        if self.reasoning_switch.isChecked():
            config["reasoning"] = True
        return model_id, config


class ModelPage(BasePage):
    """模型配置页面"""

    def __init__(self, config_manager, presets: dict, parent=None):
        super().__init__("模型配置", parent)
        self.config_manager = config_manager
        self.presets = presets
        self._init_content()
        self._load_data()

    def _init_content(self):
        self.add_title("模型配置")
        self.add_subtitle("配置模型参数，包括Token限制、上下文窗口和特性支持")
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

        self.detail_title = SubtitleLabel("选择模型查看详情")
        detail_layout.addWidget(self.detail_title)

        self.detail_info = QWidget()
        info_layout = QGridLayout(self.detail_info)
        info_layout.setSpacing(8)

        info_layout.addWidget(BodyLabel("模型ID:"), 0, 0)
        self.info_id = BodyLabel("-")
        info_layout.addWidget(self.info_id, 0, 1)

        info_layout.addWidget(BodyLabel("最大Token:"), 1, 0)
        self.info_tokens = BodyLabel("-")
        info_layout.addWidget(self.info_tokens, 1, 1)

        info_layout.addWidget(BodyLabel("上下文窗口:"), 2, 0)
        self.info_context = BodyLabel("-")
        info_layout.addWidget(self.info_context, 2, 1)

        info_layout.addWidget(BodyLabel("支持图像:"), 3, 0)
        self.info_images = BodyLabel("-")
        info_layout.addWidget(self.info_images, 3, 1)

        info_layout.addWidget(BodyLabel("计算机使用:"), 4, 0)
        self.info_computer = BodyLabel("-")
        info_layout.addWidget(self.info_computer, 4, 1)

        info_layout.addWidget(BodyLabel("推理模型:"), 5, 0)
        self.info_reasoning = BodyLabel("-")
        info_layout.addWidget(self.info_reasoning, 5, 1)

        info_layout.setColumnStretch(1, 1)
        detail_layout.addWidget(self.detail_info)

        # Options配置区域
        options_label = SubtitleLabel("Options配置")
        detail_layout.addWidget(options_label)

        self.options_edit = TextEdit()
        self.options_edit.setPlaceholderText('{"temperature": 0.7, "top_p": 0.9}')
        self.options_edit.setMaximumHeight(100)
        detail_layout.addWidget(self.options_edit)

        # Variants配置区域
        variants_label = SubtitleLabel("Variants配置")
        detail_layout.addWidget(variants_label)

        self.variants_edit = TextEdit()
        self.variants_edit.setPlaceholderText('{"fast": {"maxTokens": 4096}}')
        self.variants_edit.setMaximumHeight(100)
        detail_layout.addWidget(self.variants_edit)

        # 保存按钮
        save_btn = PrimaryPushButton("保存Options/Variants")
        save_btn.clicked.connect(self._save_options_variants)
        detail_layout.addWidget(save_btn)

        detail_layout.addStretch()

        splitter.addWidget(self.detail_card)
        splitter.setSizes([300, 500])

        self.content_layout.addWidget(splitter, 1)

    def _load_data(self):
        """加载数据"""
        self.list_card.clear()
        models = self.config_manager.get_models()
        for model_id in models.keys():
            self.list_card.add_item(model_id)

    def _on_select(self, model_id: str):
        """选择模型"""
        model = self.config_manager.get_model(model_id)
        if model:
            self.detail_title.setText(model_id)
            self.info_id.setText(model_id)
            self.info_tokens.setText(str(model.get("maxTokens", "-")))
            self.info_context.setText(str(model.get("contextWindow", "-")))
            self.info_images.setText("是" if model.get("supportsImages") else "否")
            self.info_computer.setText("是" if model.get("supportsComputerUse") else "否")
            self.info_reasoning.setText("是" if model.get("reasoning") else "否")

            # 加载options和variants
            import json
            options = model.get("options", {})
            variants = model.get("variants", {})
            self.options_edit.setText(json.dumps(options, indent=2, ensure_ascii=False) if options else "")
            self.variants_edit.setText(json.dumps(variants, indent=2, ensure_ascii=False) if variants else "")

    def _on_add(self):
        """添加模型"""
        dialog = ModelDialog(self, presets=self.presets)
        if dialog.exec():
            model_id, config = dialog.get_data()
            if model_id:
                self.config_manager.add_model(model_id, config)
                self._load_data()
                self.show_success("成功", f"已添加模型: {model_id}")
            else:
                self.show_error("错误", "模型ID不能为空")

    def _on_edit(self):
        """编辑模型"""
        model_id = self.list_card.current_item()
        if not model_id:
            self.show_warning("提示", "请先选择要编辑的模型")
            return

        model = self.config_manager.get_model(model_id)
        dialog = ModelDialog(self, model_id, model, self.presets)
        if dialog.exec():
            new_id, config = dialog.get_data()
            if new_id:
                if new_id != model_id:
                    self.config_manager.delete_model(model_id)
                self.config_manager.add_model(new_id, config)
                self._load_data()
                self.show_success("成功", f"已更新模型: {new_id}")

    def _on_delete(self):
        """删除模型"""
        model_id = self.list_card.current_item()
        if not model_id:
            self.show_warning("提示", "请先选择要删除的模型")
            return

        box = MessageBox("确认删除", f"确定要删除模型 '{model_id}' 吗？", self)
        if box.exec():
            self.config_manager.delete_model(model_id)
            self._load_data()
            self.detail_title.setText("选择模型查看详情")
            self.show_success("成功", f"已删除模型: {model_id}")

    def _save_options_variants(self):
        """保存Options和Variants配置"""
        model_id = self.list_card.current_item()
        if not model_id:
            self.show_warning("提示", "请先选择模型")
            return

        import json
        model = self.config_manager.get_model(model_id)
        if not model:
            return

        try:
            options_text = self.options_edit.toPlainText().strip()
            variants_text = self.variants_edit.toPlainText().strip()

            if options_text:
                model["options"] = json.loads(options_text)
            elif "options" in model:
                del model["options"]

            if variants_text:
                model["variants"] = json.loads(variants_text)
            elif "variants" in model:
                del model["variants"]

            self.config_manager.update_model(model_id, model)
            self.show_success("成功", "Options/Variants配置已保存")
        except json.JSONDecodeError as e:
            self.show_error("JSON格式错误", str(e))
