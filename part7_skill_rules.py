# -*- coding: utf-8 -*-
"""
OpenCode 配置管理器 v0.9.0 - PyQt5 + QFluentWidgets 版本
Part 7: Skill页面和Rules页面
"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QSplitter, QFileDialog
)

from qfluentwidgets import (
    FluentIcon as FIF, InfoBar, InfoBarPosition, MessageBox,
    PushButton, PrimaryPushButton, TransparentPushButton,
    SubtitleLabel, BodyLabel, CaptionLabel,
    CardWidget, SimpleCardWidget,
    ComboBox, LineEdit, TextEdit, SpinBox,
    SwitchButton, CheckBox, RadioButton,
    ListWidget,
    ToolTipFilter, ToolTipPosition,
    Dialog
)

from part3_mainwindow import (
    BasePage, SettingCard, SwitchSettingCard, ComboBoxSettingCard,
    SpinBoxSettingCard, LineEditSettingCard, ButtonSettingCard,
    FormCard, ListCard
)


class SkillPage(BasePage):
    """技能配置页面"""

    def __init__(self, config_manager, md_manager, parent=None):
        super().__init__("技能配置", parent)
        self.config_manager = config_manager
        self.md_manager = md_manager
        self._init_content()
        self._load_data()

    def _init_content(self):
        self.add_title("技能配置")
        self.add_subtitle("管理SKILL.md文件，配置技能权限和行为")
        self.add_spacing(8)

        # 技能权限配置
        perm_card = CardWidget()
        perm_layout = QVBoxLayout(perm_card)
        perm_layout.setContentsMargins(20, 16, 20, 16)
        perm_layout.setSpacing(12)

        perm_title = SubtitleLabel("技能权限")
        perm_layout.addWidget(perm_title)

        # 权限列表
        perm_grid = QGridLayout()
        perm_grid.setSpacing(8)

        self.skill_perms = {}
        skills = [
            ("read", "读取文件"),
            ("write", "写入文件"),
            ("edit", "编辑文件"),
            ("bash", "执行命令"),
            ("web_search", "网络搜索"),
            ("web_fetch", "获取网页"),
        ]

        for i, (skill_id, skill_name) in enumerate(skills):
            row_layout = QHBoxLayout()
            label = BodyLabel(f"{skill_name}:")
            label.setMinimumWidth(80)
            row_layout.addWidget(label)

            combo = ComboBox()
            combo.addItems(["allow", "ask", "deny"])
            combo.setMinimumWidth(100)
            self.skill_perms[skill_id] = combo
            row_layout.addWidget(combo)
            row_layout.addStretch()

            perm_grid.addLayout(row_layout, i // 2, i % 2)

        perm_layout.addLayout(perm_grid)
        self.content_layout.addWidget(perm_card)

        # SKILL.md编辑器
        editor_card = CardWidget()
        editor_layout = QVBoxLayout(editor_card)
        editor_layout.setContentsMargins(20, 16, 20, 16)
        editor_layout.setSpacing(12)

        editor_header = QHBoxLayout()
        editor_title = SubtitleLabel("SKILL.md 编辑器")
        editor_header.addWidget(editor_title)
        editor_header.addStretch()

        reload_btn = PushButton("重新加载")
        reload_btn.setIcon(FIF.SYNC)
        reload_btn.clicked.connect(self._reload_skill_md)
        editor_header.addWidget(reload_btn)

        editor_layout.addLayout(editor_header)

        # 文件路径显示
        path_row = QHBoxLayout()
        path_row.addWidget(CaptionLabel("文件路径:"))
        self.path_label = CaptionLabel("")
        self.path_label.setStyleSheet("color: gray;")
        path_row.addWidget(self.path_label, 1)
        editor_layout.addLayout(path_row)

        # 编辑器
        self.skill_editor = TextEdit()
        self.skill_editor.setPlaceholderText("# SKILL.md\n\n在此编辑技能配置...")
        self.skill_editor.setMinimumHeight(300)
        self.skill_editor.setStyleSheet("font-family: Consolas, 'Microsoft YaHei UI'; font-size: 12px;")
        editor_layout.addWidget(self.skill_editor)

        # 按钮组
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        save_btn = PrimaryPushButton("保存SKILL.md")
        save_btn.clicked.connect(self._save_skill_md)
        btn_row.addWidget(save_btn)

        editor_layout.addLayout(btn_row)
        self.content_layout.addWidget(editor_card)

        self.add_stretch()

    def _load_data(self):
        """加载数据"""
        # 加载技能权限
        config = self.config_manager.get_config()
        skill_perms = config.get("skillPermissions", {})
        for skill_id, combo in self.skill_perms.items():
            perm = skill_perms.get(skill_id, "ask")
            combo.setCurrentText(perm)

        # 加载SKILL.md
        self._reload_skill_md()

    def _reload_skill_md(self):
        """重新加载SKILL.md"""
        content = self.md_manager.read_skill_md()
        self.skill_editor.setText(content)
        self.path_label.setText(str(self.md_manager.paths.skill_md))

    def _save_skill_md(self):
        """保存SKILL.md"""
        content = self.skill_editor.toPlainText()
        if self.md_manager.write_skill_md(content):
            # 保存技能权限
            skill_perms = {skill_id: combo.currentText() for skill_id, combo in self.skill_perms.items()}
            self.config_manager.set("skillPermissions", skill_perms)
            self.show_success("成功", "SKILL.md已保存")
        else:
            self.show_error("错误", "保存SKILL.md失败")


class RulesPage(BasePage):
    """规则配置页面"""

    def __init__(self, config_manager, md_manager, parent=None):
        super().__init__("规则配置", parent)
        self.config_manager = config_manager
        self.md_manager = md_manager
        self._init_content()
        self._load_data()

    def _init_content(self):
        self.add_title("规则配置")
        self.add_subtitle("管理AGENTS.md文件，配置AI行为规则和指令")
        self.add_spacing(8)

        # Instructions配置
        inst_card = CardWidget()
        inst_layout = QVBoxLayout(inst_card)
        inst_layout.setContentsMargins(20, 16, 20, 16)
        inst_layout.setSpacing(12)

        inst_title = SubtitleLabel("全局指令 (Instructions)")
        inst_layout.addWidget(inst_title)

        inst_desc = CaptionLabel("配置全局AI行为指令，这些指令会应用到所有对话中")
        inst_desc.setStyleSheet("color: gray;")
        inst_layout.addWidget(inst_desc)

        self.instructions_edit = TextEdit()
        self.instructions_edit.setPlaceholderText("输入全局指令...")
        self.instructions_edit.setMaximumHeight(150)
        inst_layout.addWidget(self.instructions_edit)

        save_inst_btn = PushButton("保存指令")
        save_inst_btn.clicked.connect(self._save_instructions)
        inst_layout.addWidget(save_inst_btn, alignment=Qt.AlignRight)

        self.content_layout.addWidget(inst_card)

        # AGENTS.md编辑器
        editor_card = CardWidget()
        editor_layout = QVBoxLayout(editor_card)
        editor_layout.setContentsMargins(20, 16, 20, 16)
        editor_layout.setSpacing(12)

        editor_header = QHBoxLayout()
        editor_title = SubtitleLabel("AGENTS.md 编辑器")
        editor_header.addWidget(editor_title)
        editor_header.addStretch()

        reload_btn = PushButton("重新加载")
        reload_btn.setIcon(FIF.SYNC)
        reload_btn.clicked.connect(self._reload_agents_md)
        editor_header.addWidget(reload_btn)

        editor_layout.addLayout(editor_header)

        # 文件路径显示
        path_row = QHBoxLayout()
        path_row.addWidget(CaptionLabel("文件路径:"))
        self.path_label = CaptionLabel("")
        self.path_label.setStyleSheet("color: gray;")
        path_row.addWidget(self.path_label, 1)
        editor_layout.addLayout(path_row)

        # 编辑器
        self.agents_editor = TextEdit()
        self.agents_editor.setPlaceholderText("# AGENTS.md\n\n在此编辑Agent规则...")
        self.agents_editor.setMinimumHeight(300)
        self.agents_editor.setStyleSheet("font-family: Consolas, 'Microsoft YaHei UI'; font-size: 12px;")
        editor_layout.addWidget(self.agents_editor)

        # 按钮组
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        template_btn = PushButton("插入模板")
        template_btn.clicked.connect(self._insert_template)
        btn_row.addWidget(template_btn)

        save_btn = PrimaryPushButton("保存AGENTS.md")
        save_btn.clicked.connect(self._save_agents_md)
        btn_row.addWidget(save_btn)

        editor_layout.addLayout(btn_row)
        self.content_layout.addWidget(editor_card)

        self.add_stretch()

    def _load_data(self):
        """加载数据"""
        # 加载全局指令
        config = self.config_manager.get_config()
        instructions = config.get("instructions", "")
        self.instructions_edit.setText(instructions)

        # 加载AGENTS.md
        self._reload_agents_md()

    def _reload_agents_md(self):
        """重新加载AGENTS.md"""
        content = self.md_manager.read_agents_md()
        self.agents_editor.setText(content)
        self.path_label.setText(str(self.md_manager.paths.agents_md))

    def _save_instructions(self):
        """保存全局指令"""
        instructions = self.instructions_edit.toPlainText().strip()
        self.config_manager.set("instructions", instructions)
        self.show_success("成功", "全局指令已保存")

    def _save_agents_md(self):
        """保存AGENTS.md"""
        content = self.agents_editor.toPlainText()
        if self.md_manager.write_agents_md(content):
            self.show_success("成功", "AGENTS.md已保存")
        else:
            self.show_error("错误", "保存AGENTS.md失败")

    def _insert_template(self):
        """插入模板"""
        template = """# AGENTS.md

## 代码规范

- 使用简体中文编写注释
- 遵循项目既有的代码风格
- 保持代码简洁，避免过度设计

## 文档规范

- 所有文档使用Markdown格式
- 文档存放在 /docs/ 目录下
- 文件名使用中文命名

## 提交规范

- 使用语义化版本号
- Commit信息使用中文
- 每次提交前确保代码可运行

## 安全规范

- 不在代码中硬编码敏感信息
- API密钥使用环境变量
- 定期备份重要配置
"""
        current = self.agents_editor.toPlainText()
        if current.strip():
            box = MessageBox("确认", "当前内容不为空，是否追加模板？", self)
            if box.exec():
                self.agents_editor.setText(current + "\n\n" + template)
        else:
            self.agents_editor.setText(template)
