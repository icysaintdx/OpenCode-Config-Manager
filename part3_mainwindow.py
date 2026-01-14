# -*- coding: utf-8 -*-
"""
OpenCode 配置管理器 v0.9.0 - PyQt5 + QFluentWidgets 版本
Part 3: 主窗口架构
"""

import sys
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QLabel, QFrame, QSizePolicy, QSpacerItem
)

from qfluentwidgets import (
    FluentWindow, NavigationInterface, NavigationItemPosition,
    FluentIcon, Theme, setTheme, isDarkTheme,
    InfoBar, InfoBarPosition, MessageBox,
    PushButton, PrimaryPushButton, TransparentPushButton,
    SubtitleLabel, BodyLabel, CaptionLabel,
    CardWidget, SimpleCardWidget, ElevatedCardWidget,
    ScrollArea, SmoothScrollArea,
    ComboBox, LineEdit, TextEdit, SpinBox, DoubleSpinBox,
    SwitchButton, CheckBox, RadioButton,
    Slider, ProgressBar,
    TableWidget, ListWidget, TreeWidget,
    ToolTipFilter, ToolTipPosition,
    Action, RoundMenu,
    StateToolTip,
    setThemeColor
)
from qfluentwidgets import FluentIcon as FIF


class BasePage(ScrollArea):
    """页面基类"""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self._init_ui()

    def _init_ui(self):
        self.setObjectName(self.title.replace(" ", "_"))
        self.setWidgetResizable(True)

        # 创建内容容器
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(36, 20, 36, 20)
        self.content_layout.setSpacing(16)
        self.content_layout.setAlignment(Qt.AlignTop)

        self.setWidget(self.content_widget)

        # 设置样式
        self.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.content_widget.setStyleSheet("background: transparent;")

    def add_title(self, text: str):
        """添加标题"""
        label = SubtitleLabel(text)
        label.setFont(QFont("Microsoft YaHei UI", 18, QFont.Bold))
        self.content_layout.addWidget(label)

    def add_subtitle(self, text: str):
        """添加副标题"""
        label = BodyLabel(text)
        label.setFont(QFont("Microsoft YaHei UI", 12))
        label.setStyleSheet("color: gray;")
        self.content_layout.addWidget(label)

    def add_card(self, widget: QWidget) -> CardWidget:
        """添加卡片"""
        card = CardWidget()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.addWidget(widget)
        self.content_layout.addWidget(card)
        return card

    def add_spacing(self, height: int = 16):
        """添加间距"""
        self.content_layout.addSpacing(height)

    def add_stretch(self):
        """添加弹性空间"""
        self.content_layout.addStretch()

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

    def show_info(self, title: str, content: str):
        """显示信息提示"""
        InfoBar.info(
            title=title,
            content=content,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )


class SettingCard(CardWidget):
    """设置卡片"""

    def __init__(self, icon: FluentIcon, title: str, content: str = "", parent=None):
        super().__init__(parent)
        self.setFixedHeight(70)

        self.h_layout = QHBoxLayout(self)
        self.h_layout.setContentsMargins(16, 12, 16, 12)
        self.h_layout.setSpacing(16)

        # 图标
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(24, 24)
        if icon:
            self.icon_label.setPixmap(icon.icon().pixmap(24, 24))
        self.h_layout.addWidget(self.icon_label)

        # 文本区域
        self.text_layout = QVBoxLayout()
        self.text_layout.setSpacing(2)

        self.title_label = BodyLabel(title)
        self.title_label.setFont(QFont("Microsoft YaHei UI", 11))
        self.text_layout.addWidget(self.title_label)

        if content:
            self.content_label = CaptionLabel(content)
            self.content_label.setStyleSheet("color: gray;")
            self.text_layout.addWidget(self.content_label)

        self.h_layout.addLayout(self.text_layout)
        self.h_layout.addStretch()

    def add_widget(self, widget: QWidget):
        """添加控件到右侧"""
        self.h_layout.addWidget(widget)


class SwitchSettingCard(SettingCard):
    """开关设置卡片"""

    switched = pyqtSignal(bool)

    def __init__(self, icon: FluentIcon, title: str, content: str = "", checked: bool = False, parent=None):
        super().__init__(icon, title, content, parent)
        self.switch = SwitchButton()
        self.switch.setChecked(checked)
        self.switch.checkedChanged.connect(self.switched.emit)
        self.add_widget(self.switch)

    def is_checked(self) -> bool:
        return self.switch.isChecked()

    def set_checked(self, checked: bool):
        self.switch.setChecked(checked)


class ComboBoxSettingCard(SettingCard):
    """下拉框设置卡片"""

    currentIndexChanged = pyqtSignal(int)
    currentTextChanged = pyqtSignal(str)

    def __init__(self, icon: FluentIcon, title: str, content: str = "", items: list = None, parent=None):
        super().__init__(icon, title, content, parent)
        self.combo = ComboBox()
        self.combo.setMinimumWidth(150)
        if items:
            self.combo.addItems(items)
        self.combo.currentIndexChanged.connect(self.currentIndexChanged.emit)
        self.combo.currentTextChanged.connect(self.currentTextChanged.emit)
        self.add_widget(self.combo)

    def current_text(self) -> str:
        return self.combo.currentText()

    def current_index(self) -> int:
        return self.combo.currentIndex()

    def set_current_index(self, index: int):
        self.combo.setCurrentIndex(index)

    def set_current_text(self, text: str):
        self.combo.setCurrentText(text)

    def add_items(self, items: list):
        self.combo.addItems(items)

    def clear(self):
        self.combo.clear()


class SpinBoxSettingCard(SettingCard):
    """数字输入设置卡片"""

    valueChanged = pyqtSignal(int)

    def __init__(self, icon: FluentIcon, title: str, content: str = "",
                 min_val: int = 0, max_val: int = 100, value: int = 0, parent=None):
        super().__init__(icon, title, content, parent)
        self.spin = SpinBox()
        self.spin.setRange(min_val, max_val)
        self.spin.setValue(value)
        self.spin.setMinimumWidth(120)
        self.spin.valueChanged.connect(self.valueChanged.emit)
        self.add_widget(self.spin)

    def value(self) -> int:
        return self.spin.value()

    def set_value(self, value: int):
        self.spin.setValue(value)


class SliderSettingCard(SettingCard):
    """滑块设置卡片"""

    valueChanged = pyqtSignal(int)

    def __init__(self, icon: FluentIcon, title: str, content: str = "",
                 min_val: int = 0, max_val: int = 100, value: int = 0, parent=None):
        super().__init__(icon, title, content, parent)

        self.value_label = BodyLabel(str(value))
        self.value_label.setMinimumWidth(40)
        self.value_label.setAlignment(Qt.AlignCenter)

        self.slider = Slider(Qt.Horizontal)
        self.slider.setRange(min_val, max_val)
        self.slider.setValue(value)
        self.slider.setMinimumWidth(200)
        self.slider.valueChanged.connect(self._on_value_changed)

        self.add_widget(self.slider)
        self.add_widget(self.value_label)

    def _on_value_changed(self, value: int):
        self.value_label.setText(str(value))
        self.valueChanged.emit(value)

    def value(self) -> int:
        return self.slider.value()

    def set_value(self, value: int):
        self.slider.setValue(value)
        self.value_label.setText(str(value))


class LineEditSettingCard(SettingCard):
    """文本输入设置卡片"""

    textChanged = pyqtSignal(str)

    def __init__(self, icon: FluentIcon, title: str, content: str = "",
                 placeholder: str = "", text: str = "", parent=None):
        super().__init__(icon, title, content, parent)
        self.line_edit = LineEdit()
        self.line_edit.setPlaceholderText(placeholder)
        self.line_edit.setText(text)
        self.line_edit.setMinimumWidth(200)
        self.line_edit.textChanged.connect(self.textChanged.emit)
        self.add_widget(self.line_edit)

    def text(self) -> str:
        return self.line_edit.text()

    def set_text(self, text: str):
        self.line_edit.setText(text)


class ButtonSettingCard(SettingCard):
    """按钮设置卡片"""

    clicked = pyqtSignal()

    def __init__(self, icon: FluentIcon, title: str, content: str = "",
                 button_text: str = "操作", parent=None):
        super().__init__(icon, title, content, parent)
        self.button = PushButton(button_text)
        self.button.clicked.connect(self.clicked.emit)
        self.add_widget(self.button)


class PrimaryButtonSettingCard(SettingCard):
    """主要按钮设置卡片"""

    clicked = pyqtSignal()

    def __init__(self, icon: FluentIcon, title: str, content: str = "",
                 button_text: str = "操作", parent=None):
        super().__init__(icon, title, content, parent)
        self.button = PrimaryPushButton(button_text)
        self.button.clicked.connect(self.clicked.emit)
        self.add_widget(self.button)


class FormCard(CardWidget):
    """表单卡片"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.form_layout = QVBoxLayout(self)
        self.form_layout.setContentsMargins(20, 20, 20, 20)
        self.form_layout.setSpacing(16)

    def add_row(self, label_text: str, widget: QWidget, tooltip: str = ""):
        """添加表单行"""
        row_layout = QHBoxLayout()
        row_layout.setSpacing(12)

        label = BodyLabel(label_text)
        label.setMinimumWidth(120)
        if tooltip:
            label.setToolTip(tooltip)
            label.installEventFilter(ToolTipFilter(label, showDelay=300, position=ToolTipPosition.TOP))

        row_layout.addWidget(label)
        row_layout.addWidget(widget, 1)

        self.form_layout.addLayout(row_layout)

    def add_widget(self, widget: QWidget):
        """添加控件"""
        self.form_layout.addWidget(widget)

    def add_spacing(self, height: int = 8):
        """添加间距"""
        self.form_layout.addSpacing(height)

    def add_buttons(self, *buttons):
        """添加按钮组"""
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()
        for btn in buttons:
            btn_layout.addWidget(btn)
        self.form_layout.addLayout(btn_layout)


class ListCard(CardWidget):
    """列表卡片"""

    itemSelected = pyqtSignal(str)
    itemDoubleClicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.v_layout = QVBoxLayout(self)
        self.v_layout.setContentsMargins(0, 0, 0, 0)
        self.v_layout.setSpacing(0)

        # 工具栏
        self.toolbar = QWidget()
        self.toolbar_layout = QHBoxLayout(self.toolbar)
        self.toolbar_layout.setContentsMargins(16, 12, 16, 12)
        self.toolbar_layout.setSpacing(8)
        self.v_layout.addWidget(self.toolbar)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #e0e0e0;")
        line.setFixedHeight(1)
        self.v_layout.addWidget(line)

        # 列表
        self.list_widget = ListWidget()
        self.list_widget.itemClicked.connect(lambda item: self.itemSelected.emit(item.text()))
        self.list_widget.itemDoubleClicked.connect(lambda item: self.itemDoubleClicked.emit(item.text()))
        self.v_layout.addWidget(self.list_widget)

    def add_toolbar_button(self, text: str, icon: FluentIcon = None) -> PushButton:
        """添加工具栏按钮"""
        btn = PushButton(text)
        if icon:
            btn.setIcon(icon)
        self.toolbar_layout.addWidget(btn)
        return btn

    def add_toolbar_stretch(self):
        """添加工具栏弹性空间"""
        self.toolbar_layout.addStretch()

    def add_item(self, text: str):
        """添加列表项"""
        self.list_widget.addItem(text)

    def add_items(self, items: list):
        """添加多个列表项"""
        self.list_widget.addItems(items)

    def clear(self):
        """清空列表"""
        self.list_widget.clear()

    def current_item(self) -> str:
        """获取当前选中项"""
        item = self.list_widget.currentItem()
        return item.text() if item else ""

    def remove_current_item(self):
        """移除当前选中项"""
        row = self.list_widget.currentRow()
        if row >= 0:
            self.list_widget.takeItem(row)

    def count(self) -> int:
        """获取列表项数量"""
        return self.list_widget.count()

    def get_all_items(self) -> list:
        """获取所有列表项"""
        return [self.list_widget.item(i).text() for i in range(self.list_widget.count())]
