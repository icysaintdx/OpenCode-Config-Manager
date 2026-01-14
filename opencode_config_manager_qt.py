#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenCode & Oh My OpenCode 配置管理器 v1.0.0 (PyQt5 + QFluentWidgets)
一个可视化的GUI工具，用于管理OpenCode和Oh My OpenCode的配置文件

更新日志 v1.0.0:
- 完全重写 GUI，使用 PyQt5 + QFluentWidgets
- Win11 Fluent Design 风格界面
- 深色/浅色主题一键切换
- 所有功能从 v0.7.0 迁移
"""

import sys
import json
import shutil
import webbrowser
import urllib.request
import urllib.error
import threading
import re
from pathlib import Path
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QLabel, QFrame, QSplitter, QMessageBox,
    QFileDialog, QDialog, QDialogButtonBox, QTextEdit, QScrollArea,
    QSizePolicy, QSpacerItem, QListWidget, QListWidgetItem, QTreeWidget,
    QTreeWidgetItem, QHeaderView, QAbstractItemView, QMenu, QAction
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QThread, QTimer
from PyQt5.QtGui import QIcon, QFont, QColor, QPalette

from qfluentwidgets import (
    NavigationInterface, NavigationItemPosition, NavigationWidget,
    FluentIcon, Theme, setTheme, isDarkTheme,
    PushButton, PrimaryPushButton, TransparentPushButton,
    LineEdit, TextEdit, ComboBox, CheckBox, RadioButton,
    Slider, SpinBox, SwitchButton, ToggleButton,
    CardWidget, SimpleCardWidget, ElevatedCardWidget,
    TableWidget, TreeWidget, ListWidget,
    InfoBar, InfoBarPosition, MessageBox, Dialog,
    FluentWindow, SplitFluentWindow, MSFluentWindow,
    SubtitleLabel, BodyLabel, CaptionLabel, StrongBodyLabel,
    ToolTipFilter, ToolTipPosition,
    ScrollArea, SmoothScrollArea,
    CommandBar, Action,
    Flyout, FlyoutView, FlyoutAnimationType,
    qconfig, QConfig
)
from qfluentwidgets import FluentIcon as FIF


# ==================== 版本和项目信息 ====================
APP_VERSION = "1.0.0"
GITHUB_REPO = "icysaintdx/OpenCode-Config-Manager"
GITHUB_URL = f"https://github.com/{GITHUB_REPO}"
GITHUB_RELEASES_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
AUTHOR_NAME = "IcySaint"
AUTHOR_GITHUB = "https://github.com/icysaintdx"


# ==================== 配置路径 ====================
class ConfigPaths:
    @staticmethod
    def get_config_dir():
        if sys.platform == "win32":
            return Path.home() / ".config" / "opencode"
        return Path.home() / ".config" / "opencode"

    @staticmethod
    def get_opencode_config():
        return ConfigPaths.get_config_dir() / "opencode.json"

    @staticmethod
    def get_ohmyopencode_config():
        return ConfigPaths.get_config_dir() / "oh-my-opencode.json"

    @staticmethod
    def get_backup_dir():
        return ConfigPaths.get_config_dir() / "backups"


# ==================== 配置管理器 ====================
class ConfigManager:
    @staticmethod
    def load_json(path):
        try:
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"加载配置失败: {e}")
        return None

    @staticmethod
    def save_json(path, data):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False


# ==================== 备份管理器 ====================
class BackupManager:
    def __init__(self):
        self.backup_dir = ConfigPaths.get_backup_dir()
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def backup(self, config_path, tag="auto"):
        if not config_path.exists():
            return None
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{config_path.stem}_{timestamp}_{tag}.json"
        backup_path = self.backup_dir / backup_name
        shutil.copy2(config_path, backup_path)
        return backup_path

    def list_backups(self):
        return sorted(self.backup_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)

    def restore(self, backup_path, target_path):
        shutil.copy2(backup_path, target_path)

    def delete_backup(self, backup_path):
        backup_path.unlink()


# ==================== 版本检查器 ====================
class VersionChecker(QThread):
    version_checked = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.latest_version = None
        self.release_url = None

    def run(self):
        try:
            req = urllib.request.Request(
                GITHUB_RELEASES_API,
                headers={"User-Agent": "OpenCode-Config-Manager"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                tag_name = data.get("tag_name", "")
                version_match = re.search(r"v?(\d+\.\d+\.\d+)", tag_name)
                if version_match:
                    self.latest_version = version_match.group(1)
                    self.release_url = data.get("html_url", GITHUB_URL)
                    self.version_checked.emit(self.latest_version, self.release_url)
        except Exception as e:
            print(f"版本检查失败: {e}")

    @staticmethod
    def compare_versions(current, latest):
        try:
            current_parts = [int(x) for x in current.split(".")]
            latest_parts = [int(x) for x in latest.split(".")]
            return latest_parts > current_parts
        except:
            return False


# ==================== 预设配置 ====================
PRESET_MODEL_CONFIGS = {
    "Claude 系列": {
        "sdk": "@ai-sdk/anthropic",
        "models": {
            "claude-opus-4-5-20251101": {"name": "Claude Opus 4.5"},
            "claude-sonnet-4-5-20250929": {"name": "Claude Sonnet 4.5"},
            "claude-haiku-3-5-20241022": {"name": "Claude Haiku 3.5"},
        }
    },
    "GPT 系列": {
        "sdk": "@ai-sdk/openai",
        "models": {
            "gpt-5": {"name": "GPT-5"},
            "gpt-4o": {"name": "GPT-4o"},
            "o1-preview": {"name": "o1-preview"},
        }
    },
    "Gemini 系列": {
        "sdk": "@ai-sdk/google",
        "models": {
            "gemini-2.0-flash": {"name": "Gemini 2.0 Flash"},
            "gemini-1.5-pro": {"name": "Gemini 1.5 Pro"},
        }
    },
}

SDK_OPTIONS = [
    "@ai-sdk/anthropic",
    "@ai-sdk/openai",
    "@ai-sdk/google",
    "@ai-sdk/azure",
    "@ai-sdk/mistral",
    "@ai-sdk/cohere",
]

PRESET_AGENTS = {
    "oracle": {"description": "架构设计、代码审查专家", "temperature": 0.3},
    "librarian": {"description": "多仓库分析、文档查找专家", "temperature": 0.2},
    "explore": {"description": "快速代码库探索专家", "temperature": 0.1},
    "code-reviewer": {"description": "代码质量审查专家", "temperature": 0.2},
}


# ==================== Provider 页面 ====================
class ProviderPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.current_provider = None
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # 左侧列表
        left_card = CardWidget(self)
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(16, 16, 16, 16)

        # 标题和按钮
        header = QHBoxLayout()
        header.addWidget(SubtitleLabel("Provider 列表"))
        header.addStretch()
        
        self.add_btn = PrimaryPushButton("+ 添加")
        self.add_btn.clicked.connect(self.add_provider)
        header.addWidget(self.add_btn)
        
        self.del_btn = PushButton("删除")
        self.del_btn.setProperty("danger", True)
        self.del_btn.clicked.connect(self.delete_provider)
        header.addWidget(self.del_btn)
        
        left_layout.addLayout(header)

        # 列表
        self.provider_list = ListWidget()
        self.provider_list.itemClicked.connect(self.on_provider_selected)
        left_layout.addWidget(self.provider_list)

        layout.addWidget(left_card, 1)

        # 右侧详情
        right_card = CardWidget(sel
