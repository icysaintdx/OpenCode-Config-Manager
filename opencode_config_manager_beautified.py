#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenCode & Oh My OpenCode 配置管理器 v0.7.1 (Beautified)
基于 ttkbootstrap 的现代化 GUI 工具

美化更新 v0.7.1:
- 全面重构 UI，移除自定义 Canvas 组件，采用 ttkbootstrap 原生控件
- 使用 Labelframe 替代 Card，布局更紧凑现代
- 优化侧边栏设计，支持深色/浅色反转风格
- 增强了间距和对齐，提升视觉呼吸感
- 完全适配 ttkbootstrap 主题系统，无需手动管理颜色代码
"""

import tkinter as tk
from tkinter import messagebox, scrolledtext
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.widgets import ToolTip
from ttkbootstrap.widgets.scrolled import ScrolledFrame
import json
from pathlib import Path
from datetime import datetime
import shutil
import webbrowser
import urllib.request
import urllib.error
import threading
import re

# ==================== 版本和项目信息 ====================
APP_VERSION = "0.7.1"
GITHUB_REPO = "icysaintdx/OpenCode-Config-Manager"
GITHUB_URL = f"https://github.com/{GITHUB_REPO}"
GITHUB_RELEASES_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
AUTHOR_NAME = "IcySaint"
AUTHOR_GITHUB = "https://github.com/icysaintdx"

FONTS = {
    "title": ("Microsoft YaHei UI", 16, "bold"),
    "subtitle": ("Microsoft YaHei UI", 12, "bold"),
    "body": ("Microsoft YaHei UI", 10),
    "small": ("Microsoft YaHei UI", 9),
    "mono": ("Consolas", 10),
}

# ==================== 预设常用模型与数据 ====================
PRESET_MODEL_CONFIGS = {
    "Claude 系列": {
        "sdk": "@ai-sdk/anthropic",
        "models": {
            "claude-opus-4-5-20251101": {
                "name": "Claude Opus 4.5", "attachment": True, "limit": {"context": 200000, "output": 32000},
                "modalities": {"input": ["text", "image"], "output": ["text"]},
                "options": {"thinking": {"type": "enabled", "budgetTokens": 16000}},
                "variants": {"high": {"thinking": {"type": "enabled", "budgetTokens": 32000}}},
                "description": "最强大的Claude模型，支持extended thinking模式"
            },
            "claude-sonnet-4-5-20250929": {
                "name": "Claude Sonnet 4.5", "attachment": True, "limit": {"context": 200000, "output": 16000},
                "modalities": {"input": ["text", "image"], "output": ["text"]},
                "options": {"thinking": {"type": "enabled", "budgetTokens": 8000}},
                "variants": {"high": {"thinking": {"type": "enabled", "budgetTokens": 16000}}},
                "description": "平衡性能与成本的Claude模型"
            },
        },
    },
    "OpenAI/Codex 系列": {
        "sdk": "@ai-sdk/openai",
        "models": {
            "gpt-5": {
                "name": "GPT-5", "attachment": True, "limit": {"context": 256000, "output": 32768},
                "modalities": {"input": ["text", "image"], "output": ["text"]},
                "options": {"reasoningEffort": "high", "textVerbosity": "low", "reasoningSummary": "auto"},
                "variants": {"high": {"reasoningEffort": "high"}},
                "description": "OpenAI最新旗舰模型"
            },
            "gpt-4o": {
                "name": "GPT-4o", "attachment": True, "limit": {"context": 128000, "output": 16384},
                "modalities": {"input": ["text", "image"], "output": ["text"]},
                "options": {}, "variants": {}, "description": "OpenAI多模态模型"
            },
        },
    },
    "Gemini 系列": {
        "sdk": "@ai-sdk/google",
        "models": {
            "gemini-3-pro": {
                "name": "Gemini 3 Pro", "attachment": True, "limit": {"context": 2097152, "output": 65536},
                "modalities": {"input": ["text", "image"], "output": ["text"]},
                "options": {"thinkingConfig": {"thinkingBudget": 8000}},
                "variants": {"high": {"thinkingConfig": {"thinkingBudget": 16000}}},
                "description": "Google最新Pro模型"
            },
        },
    },
}

PRESET_MODELS = {cat: list(data["models"].keys()) for cat, data in PRESET_MODEL_CONFIGS.items()}
PRESET_SDKS = ["@ai-sdk/anthropic", "@ai-sdk/openai", "@ai-sdk/google", "@ai-sdk/azure", "@ai-sdk/openai-compatible"]
SDK_MODEL_COMPATIBILITY = {
    "@ai-sdk/anthropic": ["Claude 系列"], "@ai-sdk/openai": ["OpenAI/Codex 系列"],
    "@ai-sdk/google": ["Gemini 系列"], "@ai-sdk/azure": ["OpenAI/Codex 系列"],
}

PRESET_AGENTS = {
    "oracle": "架构设计、代码审查、策略规划专家 - 用于复杂决策和深度分析",
    "librarian": "多仓库分析、文档查找、实现示例专家",
    "explore": "快速代码库探索和模式匹配专家",
    "frontend-ui-ux-engineer": "UI/UX 设计和前端开发专家",
    "document-writer": "技术文档写作专家",
    "code-reviewer": "代码质量审查、安全分析专家",
    "debugger": "问题诊断、Bug 修复专家",
}

PRESET_OPENCODE_AGENTS = {
    "build": {"mode": "primary", "description": "默认主Agent，拥有所有工具权限", "tools": {"write": True, "edit": True, "bash": True}},
    "plan": {"mode": "primary", "description": "规划分析Agent，限制写入权限", "permission": {"edit": "ask", "bash": "ask"}},
    "general": {"mode": "subagent", "description": "通用子Agent"},
    "code-reviewer": {"mode": "subagent", "description": "代码审查Agent，只读权限", "tools": {"write": False, "edit": False}},
}

PRESET_CATEGORIES = {
    "visual": {"temperature": 0.7, "description": "前端、UI/UX、设计相关任务"},
    "business-logic": {"temperature": 0.1, "description": "后端逻辑、架构设计"},
    "documentation": {"temperature": 0.3, "description": "文档编写、技术写作"},
    "code-analysis": {"temperature": 0.2, "description": "代码审查、重构分析"},
}

TOOLTIPS = {
    "skill_pattern": "Skill加载模式，支持通配符，例如: * 匹配所有，*.py 匹配Python文件",
    "skill_permission": "allow: 允许加载, ask: 每次询问, deny: 禁止加载",
    "skill_name": "Skill名称，只能包含小写字母、数字和连字符",
    "skill_description": "Skill的简短描述，用于说明其功能",
    "instructions_path": "额外的指令文件路径，支持通配符",
    "mcp_name": "MCP服务器名称，用于标识该服务器",
    "mcp_type": "local: 本地启动的MCP服务器, remote: 远程MCP服务器",
    "mcp_command": "启动MCP服务器的命令，JSON数组格式",
    "mcp_environment": "启动MCP服务器的环境变量，JSON对象格式",
    "mcp_url": "远程MCP服务器的URL",
    "mcp_headers": "请求远程MCP服务器时的HTTP头，JSON对象格式",
    "mcp_timeout": "MCP服务器超时时间（毫秒）",
    "agent_name": "Agent名称，用于标识该Agent",
    "agent_description": "Agent的描述，说明其用途",
    "agent_model": "Agent使用的模型，可选，不指定则使用默认模型",
    "opencode_agent_mode": "primary: 主Agent, subagent: 子Agent, all: 所有模式",
    "opencode_agent_temperature": "Agent的Temperature参数，控制输出的随机性",
    "opencode_agent_maxSteps": "Agent的最大执行步数，可选",
    "opencode_agent_tools": "Agent的工具配置，JSON对象格式",
    "opencode_agent_permission": "Agent的权限配置，JSON对象格式",
    "opencode_agent_prompt": "Agent的系统提示词",
}

# ==================== 核心服务类 ====================
class ConfigPaths:
    @staticmethod
    def get_user_home(): return Path.home()
    @classmethod
    def get_opencode_config(cls): return cls.get_user_home() / ".config" / "opencode" / "opencode.json"
    @classmethod
    def get_ohmyopencode_config(cls): return cls.get_user_home() / ".config" / "opencode" / "oh-my-opencode.json"
    @classmethod
    def get_claude_settings(cls): return cls.get_user_home() / ".claude" / "settings.json"
    @classmethod
    def get_claude_providers(cls): return cls.get_user_home() / ".claude" / "providers.json"
    @classmethod
    def get_backup_dir(cls): return cls.get_user_home() / ".config" / "opencode" / "backups"

class ConfigManager:
    @staticmethod
    def load_json(path):
        try:
            if path.exists():
                with open(path, "r", encoding="utf-8") as f: return json.load(f)
        except Exception as e: print(f"Load failed {path}: {e}")
        return None
    @staticmethod
    def save_json(path, data):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f: json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Save failed {path}: {e}")
            return False

class BackupManager:
    def __init__(self):
        self.backup_dir = ConfigPaths.get_backup_dir()
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    def backup(self, config_path, tag="auto"):
        try:
            if not config_path.exists(): return None
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"{config_path.stem}.{timestamp}.{tag}.bak"
            shutil.copy2(config_path, backup_path)
            return backup_path
        except Exception as e:
            print(f"Backup failed: {e}"); return None
    def list_backups(self, config_name=None):
        try:
            backups = []
            for f in self.backup_dir.glob("*.bak"):
                parts = f.stem.split(".")
                if len(parts) >= 3:
                    if config_name is None or parts[0] == config_name:
                        backups.append({"path": f, "name": parts[0], "timestamp": parts[1], "tag": parts[2], "display": f"{parts[0]} - {parts[1]} ({parts[2]})"})
            backups.sort(key=lambda x: x["timestamp"], reverse=True)
            return backups
        except: return []
    def restore(self, backup_path, target_path):
        try:
            if not backup_path.exists(): return False
            self.backup(target_path, tag="before_restore")
            shutil.copy2(backup_path, target_path)
            return True
        except: return False
    def delete_backup(self, backup_path):
        try:
            if backup_path.exists(): backup_path.unlink(); return True
        except: return False

class ModelRegistry:
    def __init__(self, opencode_config):
        self.config = opencode_config or {}
        self.models = {}
        self.refresh()
    def refresh(self):
        self.models = {}
        for provider_name, provider_data in self.config.get("provider", {}).items():
            for model_id in provider_data.get("models", {}).keys():
                self.models[f"{provider_name}/{model_id}"] = True
    def get_all_models(self): return list(self.models.keys())

class ImportService:
    def scan_external_configs(self):
        results = {}
        paths = {
            "Claude Settings": (ConfigPaths.get_claude_settings(), "claude"),
            "Claude Providers": (ConfigPaths.get_claude_providers(), "claude_providers"),
            "Gemini Config": (Path.home() / ".config" / "gemini" / "config.json", "gemini"),
        }
        for name, (path, type_) in paths.items():
            results[name] = {"path": str(path), "exists": path.exists(), "data": ConfigManager.load_json(path) if path.exists() else None, "type": type_}
        return results
    
    def convert_to_opencode(self, source_type, source_data):
        if not source_data: return None
        result = {"provider": {}, "permission": {}}
        if source_type == "claude" and "apiKey" in source_data:
            result["provider"]["anthropic"] = {"npm": "@ai-sdk/anthropic", "name": "Anthropic (Claude)", "options": {"apiKey": source_data["apiKey"]}, "models": {}}
        return result

class VersionChecker:
    def __init__(self, callback=None):
        self.callback = callback
        self.checking = False
    def check_update_async(self):
        if not self.checking:
            self.checking = True
            threading.Thread(target=self._check_update, daemon=True).start()
    def _check_update(self):
        try:
            req = urllib.request.Request(GITHUB_RELEASES_API, headers={"User-Agent": "OpenCode-Config-Manager"})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                version_match = re.search(r"v?(\d+\.\d+\.\d+)", data.get("tag_name", ""))
                if version_match and self.callback:
                    self.callback(version_match.group(1), data.get("html_url", ""))
        except: pass
        finally: self.checking = False
    @staticmethod
    def compare_versions(current, latest):
        try: return [int(x) for x in latest.split(".")] > [int(x) for x in current.split(".")]
        except: return False

# ==================== UI 辅助函数 ====================
def create_tooltip(widget, text):
    """创建 ttkbootstrap 风格的 ToolTip"""
    if text:
        ToolTip(widget, text=text, bootstyle="(inverse, dark)")

def pack_with_label(parent, label_text, widget, tooltip_text=None, fill=X, expand=False, pady=5):
    """辅助函数：打包一个标签和控件"""
    frame = ttk.Frame(parent)
    frame.pack(fill=fill, expand=expand, pady=pady)
    
    lbl = ttk.Label(frame, text=label_text, bootstyle="secondary")
    lbl.pack(side=LEFT, padx=(0, 10))
    if tooltip_text:
        create_tooltip(lbl, tooltip_text)
        
    widget.pack(side=LEFT, fill=fill, expand=True)
    return frame

# ==================== Provider 管理选项卡 ====================
class ProviderTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.current_provider_name = None
        self.setup_ui()

    def setup_ui(self):
        paned = ttk.Panedwindow(self, orient=HORIZONTAL)
        paned.pack(fill=BOTH, expand=True, padx=5, pady=5)

        left_frame = ttk.Labelframe(paned, text="Provider 列表", padding=10)
        paned.add(left_frame, weight=1)

        toolbar = ttk.Frame(left_frame)
        toolbar.pack(fill=X, pady=(0, 10))
        ttk.Button(toolbar, text="➕ 添加", command=self.add_provider, bootstyle="primary").pack(side=LEFT, padx=2)
        ttk.Button(toolbar, text="🗑 删除", command=self.delete_provider, bootstyle="danger").pack(side=LEFT, padx=2)

        columns = ("name", "display", "sdk", "models")
        self.tree = ttk.Treeview(left_frame, columns=columns, show="headings", bootstyle="primary")
        for col, width in zip(columns, [80, 120, 150, 60]):
            self.tree.column(col, width=width)
            self.tree.heading(col, text=col.title())
        
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar = ttk.Scrollbar(left_frame, orient=VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        right_frame = ttk.Labelframe(paned, text="Provider 详情", padding=15)
        paned.add(right_frame, weight=2)

        form = ttk.Frame(right_frame)
        form.pack(fill=BOTH, expand=True)

        self.name_var = tk.StringVar()
        f1 = ttk.Frame(form); f1.pack(fill=X, pady=5)
        ttk.Label(f1, text="ID (唯一标识)", width=15).pack(side=LEFT)
        ttk.Entry(f1, textvariable=self.name_var).pack(side=LEFT, fill=X, expand=True)

        self.display_var = tk.StringVar()
        f2 = ttk.Frame(form); f2.pack(fill=X, pady=5)
        ttk.Label(f2, text="显示名称", width=15).pack(side=LEFT)
        ttk.Entry(f2, textvariable=self.display_var).pack(side=LEFT, fill=X, expand=True)

        self.sdk_var = tk.StringVar()
        f3 = ttk.Frame(form); f3.pack(fill=X, pady=5)
        ttk.Label(f3, text="SDK", width=15).pack(side=LEFT)
        cb = ttk.Combobox(f3, textvariable=self.sdk_var, values=PRESET_SDKS)
        cb.pack(side=LEFT, fill=X, expand=True)
        cb.bind("<<ComboboxSelected>>", self.on_sdk_change)
        
        self.sdk_hint_label = ttk.Label(form, text="", bootstyle="success", font=FONTS["small"])
        self.sdk_hint_label.pack(anchor=W, padx=105, pady=(0, 5))

        self.url_var = tk.StringVar()
        f4 = ttk.Frame(form); f4.pack(fill=X, pady=5)
        ttk.Label(f4, text="API 地址 (BaseURL)", width=15).pack(side=LEFT)
        ttk.Entry(f4, textvariable=self.url_var).pack(side=LEFT, fill=X, expand=True)

        self.key_var = tk.StringVar()
        f5 = ttk.Frame(form); f5.pack(fill=X, pady=5)
        ttk.Label(f5, text="API 密钥", width=15).pack(side=LEFT)
        self.key_entry = ttk.Entry(f5, textvariable=self.key_var, show="*")
        self.key_entry.pack(side=LEFT, fill=X, expand=True)
        
        self.show_key = tk.BooleanVar()
        ttk.Checkbutton(f5, text="显示", variable=self.show_key, command=self.toggle_key, bootstyle="round-toggle").pack(side=LEFT, padx=5)

        ttk.Separator(form).pack(fill=X, pady=15)
        
        btn_frame = ttk.Frame(form)
        btn_frame.pack(fill=X)
        ttk.Button(btn_frame, text="💾 保存修改", command=self.save_changes, bootstyle="success").pack(side=LEFT)
        ttk.Label(btn_frame, text=" (直接写入配置文件)", bootstyle="secondary").pack(side=LEFT, padx=5)

    def on_sdk_change(self, event=None):
        sdk = self.sdk_var.get()
        if sdk in SDK_MODEL_COMPATIBILITY:
            self.sdk_hint_label.config(text=f"推荐用于: {', '.join(SDK_MODEL_COMPATIBILITY[sdk])}")
        else:
            self.sdk_hint_label.config(text="")

    def toggle_key(self):
        self.key_entry.config(show="" if self.show_key.get() else "*")

    def refresh_list(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        for name, data in self.app.opencode_config.get("provider", {}).items():
            self.tree.insert("", END, values=(name, data.get("name", name), data.get("npm", ""), len(data.get("models", {}))))

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel: return
        name = self.tree.item(sel[0])["values"][0]
        self.current_provider_name = name
        data = self.app.opencode_config["provider"][name]
        self.name_var.set(name); self.display_var.set(data.get("name", ""))
        self.sdk_var.set(data.get("npm", "")); self.url_var.set(data.get("options", {}).get("baseURL", ""))
        self.key_var.set(data.get("options", {}).get("apiKey", "")); self.on_sdk_change()

    def add_provider(self):
        self.current_provider_name = None
        for var in [self.name_var, self.display_var, self.url_var, self.key_var]: var.set("")
        self.sdk_var.set("@ai-sdk/anthropic")
        self.tree.selection_remove(self.tree.selection())

    def delete_provider(self):
        if not self.tree.selection(): return
        name = self.tree.item(self.tree.selection()[0])["values"][0]
        if messagebox.askyesno("确认", f"删除 Provider [{name}]?"):
            del self.app.opencode_config["provider"][name]
            self.app.save_configs_silent(); self.refresh_list()

    def save_changes(self):
        name = self.name_var.get().strip()
        if not name: return messagebox.showwarning("提示", "ID不能为空")
        provs = self.app.opencode_config.setdefault("provider", {})
        if self.current_provider_name and self.current_provider_name != name and self.current_provider_name in provs:
            provs[name] = provs.pop(self.current_provider_name)
        if name not in provs: provs[name] = {"models": {}}
        provs[name].update({"npm": self.sdk_var.get(), "name": self.display_var.get(), "options": {"baseURL": self.url_var.get(), "apiKey": self.key_var.get()}})
        if self.app.save_configs_silent():
            self.refresh_list()
            messagebox.showinfo("成功", "Provider 已保存")

# ==================== Model 管理选项卡 ====================
class ModelTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.current_provider = None
        self.current_model_data = {}
        self.setup_ui()

    def setup_ui(self):
        top_bar = ttk.Frame(self, padding=10)
        top_bar.pack(fill=X)
        ttk.Label(top_bar, text="选择 Provider:").pack(side=LEFT, padx=(0, 10))
        self.provider_var = tk.StringVar()
        self.provider_combo = ttk.Combobox(top_bar, textvariable=self.provider_var, state="readonly", width=30)
        self.provider_combo.pack(side=LEFT)
        self.provider_combo.bind("<<ComboboxSelected>>", self.on_provider_change)

        paned = ttk.Panedwindow(self, orient=HORIZONTAL)
        paned.pack(fill=BOTH, expand=True, padx=5, pady=5)

        left_frame = ttk.Labelframe(paned, text="模型列表", padding=10)
        paned.add(left_frame, weight=1)
        
        toolbar = ttk.Frame(left_frame)
        toolbar.pack(fill=X, pady=(0, 10))
        ttk.Button(toolbar, text="➕ 添加", command=self.add_model, bootstyle="primary").pack(side=LEFT, padx=2)
        ttk.Button(toolbar, text="🗑 删除", command=self.delete_model, bootstyle="danger").pack(side=LEFT, padx=2)

        self.tree = ttk.Treeview(left_frame, columns=("id", "name"), show="headings", bootstyle="info")
        self.tree.heading("id", text="模型 ID"); self.tree.column("id", width=150)
        self.tree.heading("name", text="显示名称"); self.tree.column("name", width=120)
        self.tree.pack(fill=BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        right_frame = ttk.Labelframe(paned, text="模型配置", padding=10)
        paned.add(right_frame, weight=2)

        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=BOTH, expand=True)

        basic_tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(basic_tab, text="基本信息")
        
        f_preset = ttk.Frame(basic_tab); f_preset.pack(fill=X, pady=5)
        ttk.Label(f_preset, text="快速预设", width=10).pack(side=LEFT)
        self.preset_cat_var = tk.StringVar(value="自定义")
        cb_cat = ttk.Combobox(f_preset, textvariable=self.preset_cat_var, values=["自定义"] + list(PRESET_MODELS.keys()), width=15, state="readonly")
        cb_cat.pack(side=LEFT, padx=5)
        cb_cat.bind("<<ComboboxSelected>>", self.on_preset_cat)
        self.preset_model_var = tk.StringVar()
        self.cb_model = ttk.Combobox(f_preset, textvariable=self.preset_model_var, width=20, state="disabled")
        self.cb_model.pack(side=LEFT, padx=5)
        self.cb_model.bind("<<ComboboxSelected>>", self.on_preset_model)

        f_id = ttk.Frame(basic_tab); f_id.pack(fill=X, pady=5)
        ttk.Label(f_id, text="模型 ID", width=10).pack(side=LEFT)
        self.model_id_var = tk.StringVar()
        ttk.Entry(f_id, textvariable=self.model_id_var).pack(side=LEFT, fill=X, expand=True)

        f_name = ttk.Frame(basic_tab); f_name.pack(fill=X, pady=5)
        ttk.Label(f_name, text="显示名称", width=10).pack(side=LEFT)
        self.model_name_var = tk.StringVar()
        ttk.Entry(f_name, textvariable=self.model_name_var).pack(side=LEFT, fill=X, expand=True)

        f_ctx = ttk.Frame(basic_tab); f_ctx.pack(fill=X, pady=5)
        ttk.Label(f_ctx, text="上下文限制", width=10).pack(side=LEFT)
        self.context_var = tk.StringVar(value="1048576")
        ttk.Entry(f_ctx, textvariable=self.context_var, width=12).pack(side=LEFT)
        ttk.Label(f_ctx, text="最大输出", width=10).pack(side=LEFT, padx=(10, 0))
        self.output_var = tk.StringVar(value="65535")
        ttk.Entry(f_ctx, textvariable=self.output_var, width=12).pack(side=LEFT)

        self.attachment_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(basic_tab, text="支持附件 (Vision/Upload)", variable=self.attachment_var, bootstyle="round-toggle").pack(anchor=W, pady=10)

        ttk.Button(basic_tab, text="💾 保存模型", command=self.save_model, bootstyle="success").pack(anchor=W, pady=20)

        options_tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(options_tab, text="Options (默认参数)")
        
        self.options_text = scrolledtext.ScrolledText(options_tab, height=15)
        self.options_text.pack(fill=BOTH, expand=True)
        ttk.Label(options_tab, text="JSON 格式配置，例如: {'thinking': {'type': 'enabled'}}", bootstyle="secondary").pack(anchor=W)

        variants_tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(variants_tab, text="Variants (变体)")
        
        self.variants_text = scrolledtext.ScrolledText(variants_tab, height=15)
        self.variants_text.pack(fill=BOTH, expand=True)
        ttk.Label(variants_tab, text="JSON 格式配置，例如: {'high': {'reasoningEffort': 'high'}}", bootstyle="secondary").pack(anchor=W)

    def refresh_providers(self):
        provs = list(self.app.opencode_config.get("provider", {}).keys())
        self.provider_combo['values'] = provs
        if provs and not self.current_provider:
            self.provider_combo.current(0); self.on_provider_change(None)

    def on_provider_change(self, e):
        self.current_provider = self.provider_var.get()
        self.refresh_models()

    def refresh_models(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        if self.current_provider:
            models = self.app.opencode_config["provider"][self.current_provider].get("models", {})
            for mid, mdata in models.items():
                self.tree.insert("", END, values=(mid, mdata.get("name", "")))

    def on_select(self, e):
        sel = self.tree.selection()
        if not sel: return
        mid = self.tree.item(sel[0])["values"][0]
        mdata = self.app.opencode_config["provider"][self.current_provider]["models"][mid]
        self.model_id_var.set(mid); self.model_name_var.set(mdata.get("name", ""))
        self.context_var.set(mdata.get("limit", {}).get("context", 1048576))
        self.output_var.set(mdata.get("limit", {}).get("output", 65535))
        self.attachment_var.set(mdata.get("attachment", True))
        self.options_text.delete("1.0", END); self.options_text.insert("1.0", json.dumps(mdata.get("options", {}), indent=2))
        self.variants_text.delete("1.0", END); self.variants_text.insert("1.0", json.dumps(mdata.get("variants", {}), indent=2))

    def on_preset_cat(self, e):
        cat = self.preset_cat_var.get()
        if cat == "自定义": self.cb_model.config(state="disabled", values=[])
        else: self.cb_model.config(state="readonly", values=PRESET_MODELS.get(cat, [])); self.cb_model.current(0)
    
    def on_preset_model(self, e):
        mid = self.preset_model_var.get()
        cat = self.preset_cat_var.get()
        if cat in PRESET_MODEL_CONFIGS and mid in PRESET_MODEL_CONFIGS[cat]["models"]:
            cfg = PRESET_MODEL_CONFIGS[cat]["models"][mid]
            self.model_id_var.set(mid); self.model_name_var.set(cfg["name"])
            self.context_var.set(cfg["limit"]["context"]); self.output_var.set(cfg["limit"]["output"])
            self.attachment_var.set(cfg["attachment"])
            self.options_text.delete("1.0", END); self.options_text.insert("1.0", json.dumps(cfg.get("options", {}), indent=2))
            self.variants_text.delete("1.0", END); self.variants_text.insert("1.0", json.dumps(cfg.get("variants", {}), indent=2))

    def add_model(self):
        if not self.current_provider: return messagebox.showwarning("提示", "先选择Provider")
        self.model_id_var.set(""); self.model_name_var.set("")
        self.options_text.delete("1.0", END); self.options_text.insert("1.0", "{}")
        self.variants_text.delete("1.0", END); self.variants_text.insert("1.0", "{}")

    def delete_model(self):
        sel = self.tree.selection()
        if not sel: return
        mid = self.tree.item(sel[0])["values"][0]
        if messagebox.askyesno("确认", f"删除模型 {mid}?"):
            del self.app.opencode_config["provider"][self.current_provider]["models"][mid]
            self.app.save_configs_silent(); self.refresh_models()

    def save_model(self):
        if not self.current_provider: return
        mid = self.model_id_var.get()
        if not mid: return messagebox.showwarning("错误", "模型ID必填")
        try:
            opts = json.loads(self.options_text.get("1.0", END))
            vars_ = json.loads(self.variants_text.get("1.0", END))
        except: return messagebox.showerror("JSON错误", "Options或Variants格式错误")
        
        data = {
            "name": self.model_name_var.get(), "attachment": self.attachment_var.get(),
            "limit": {"context": int(self.context_var.get()), "output": int(self.output_var.get())},
            "options": opts, "variants": vars_
        }
        self.app.opencode_config["provider"][self.current_provider].setdefault("models", {})[mid] = data
        if self.app.save_configs_silent(): self.refresh_models(); messagebox.showinfo("成功", "模型已保存")

# ==================== Agent Tab (OhMy) ====================
class AgentTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.setup_ui()

    def setup_ui(self):
        paned = ttk.Panedwindow(self, orient=HORIZONTAL)
        paned.pack(fill=BOTH, expand=True, padx=5, pady=5)

        left = ttk.Labelframe(paned, text="Agent 列表", padding=10)
        paned.add(left, weight=1)
        
        tb = ttk.Frame(left); tb.pack(fill=X, pady=(0, 10))
        ttk.Button(tb, text="➕ 添加", command=self.add_agent, bootstyle="primary").pack(side=LEFT, padx=2)
        ttk.Button(tb, text="🗑 删除", command=self.delete_agent, bootstyle="danger").pack(side=LEFT, padx=2)

        self.tree = ttk.Treeview(left, columns=("name", "model"), show="headings", bootstyle="success")
        self.tree.heading("name", text="名称"); self.tree.column("name", width=100)
        self.tree.heading("model", text="绑定模型"); self.tree.column("model", width=150)
        self.tree.pack(fill=BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        right = ttk.Labelframe(paned, text="Agent 详情", padding=15)
        paned.add(right, weight=2)
        
        f1 = ttk.Frame(right); f1.pack(fill=X, pady=5)
        ttk.Label(f1, text="Agent 名称", width=12).pack(side=LEFT)
        self.name_var = tk.StringVar()
        ttk.Entry(f1, textvariable=self.name_var).pack(side=LEFT, fill=X, expand=True)

        f2 = ttk.Frame(right); f2.pack(fill=X, pady=5)
        ttk.Label(f2, text="绑定模型", width=12).pack(side=LEFT)
        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(f2, textvariable=self.model_var)
        self.model_combo.pack(side=LEFT, fill=X, expand=True)

        f3 = ttk.Frame(right); f3.pack(fill=BOTH, expand=True, pady=5)
        ttk.Label(f3, text="功能描述").pack(anchor=W)
        self.desc_text = scrolledtext.ScrolledText(f3, height=5)
        self.desc_text.pack(fill=BOTH, expand=True)

        ttk.Button(right, text="💾 保存 Agent", command=self.save_agent, bootstyle="success").pack(anchor=E, pady=10)

    def refresh_models(self):
        self.model_combo['values'] = ModelRegistry(self.app.opencode_config).get_all_models()

    def refresh_list(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for n, d in self.app.ohmyopencode_config.get("agents", {}).items():
            self.tree.insert("", END, values=(n, d.get("model", "")))

    def on_select(self, e):
        sel = self.tree.selection()
        if not sel: return
        n = self.tree.item(sel[0])["values"][0]
        d = self.app.ohmyopencode_config["agents"][n]
        self.name_var.set(n); self.model_var.set(d.get("model", ""))
        self.desc_text.delete("1.0", END); self.desc_text.insert("1.0", d.get("description", ""))

    def add_agent(self): self.name_var.set(""); self.desc_text.delete("1.0", END)
    def delete_agent(self):
        if not (sel := self.tree.selection()): return
        n = self.tree.item(sel[0])["values"][0]
        if messagebox.askyesno("删除", f"删除 {n}?"):
            del self.app.ohmyopencode_config["agents"][n]
            self.app.save_configs_silent(); self.refresh_list()
    def save_agent(self):
        n = self.name_var.get()
        if not n: return
        self.app.ohmyopencode_config.setdefault("agents", {})[n] = {
            "model": self.model_var.get(), "description": self.desc_text.get("1.0", END).strip()
        }
        if self.app.save_configs_silent(): self.refresh_list(); messagebox.showinfo("OK", "Saved")

# ==================== Category Tab ====================
class CategoryTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.setup_ui()

    def setup_ui(self):
        paned = ttk.Panedwindow(self, orient=HORIZONTAL)
        paned.pack(fill=BOTH, expand=True, padx=5, pady=5)

        left_frame = ttk.Labelframe(paned, text="Category 列表", padding=10)
        paned.add(left_frame, weight=1)
        
        toolbar = ttk.Frame(left_frame)
        toolbar.pack(fill=X, pady=(0, 10))
        ttk.Button(toolbar, text="➕ 添加", command=self.add_category, bootstyle="primary").pack(side=LEFT, padx=2)
        ttk.Button(toolbar, text="🗑 删除", command=self.delete_category, bootstyle="danger").pack(side=LEFT, padx=2)

        columns = ("name", "model", "temp", "description")
        self.tree = ttk.Treeview(left_frame, columns=columns, show="headings", bootstyle="info")
        self.tree.heading("name", text="名称")
        self.tree.heading("model", text="绑定模型")
        self.tree.heading("temp", text="Temp")
        self.tree.heading("description", text="描述")
        self.tree.column("name", width=100)
        self.tree.column("model", width=150)
        self.tree.column("temp", width=60)
        self.tree.column("description", width=150)
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar = ttk.Scrollbar(left_frame, orient=VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        right_frame = ttk.Labelframe(paned, text="Category 详情", padding=15)
        paned.add(right_frame, weight=2)
        
        form = ttk.Frame(right_frame)
        form.pack(fill=BOTH, expand=True)

        ttk.Label(form, text="预设分类", font=FONTS["small"]).grid(row=0, column=0, sticky=W, pady=(0, 4))
        self.preset_var = tk.StringVar(value="自定义")
        preset_values = ["自定义"] + list(PRESET_CATEGORIES.keys())
        self.preset_combo = ttk.Combobox(form, textvariable=self.preset_var, values=preset_values, width=26, state="readonly")
        self.preset_combo.grid(row=1, column=0, sticky=W, pady=(0, 12))
        self.preset_combo.bind("<<ComboboxSelected>>", self.on_preset_select)

        ttk.Label(form, text="名称", font=FONTS["small"]).grid(row=2, column=0, sticky=W, pady=(0, 4))
        self.name_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.name_var, width=28).grid(row=3, column=0, sticky=W, pady=(0, 12))

        ttk.Label(form, text="绑定模型", font=FONTS["small"]).grid(row=4, column=0, sticky=W, pady=(0, 4))
        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(form, textvariable=self.model_var, width=26)
        self.model_combo.grid(row=5, column=0, sticky=W, pady=(0, 12))

        ttk.Label(form, text="Temperature", font=FONTS["small"]).grid(row=6, column=0, sticky=W, pady=(0, 4))
        temp_frame = ttk.Frame(form)
        temp_frame.grid(row=7, column=0, sticky=W, pady=(0, 12))
        self.temp_var = tk.DoubleVar(value=0.7)
        self.temp_scale = ttk.Scale(temp_frame, from_=0.0, to=2.0, variable=self.temp_var, orient=tk.HORIZONTAL, length=180, command=self.on_temp_change)
        self.temp_scale.pack(side=LEFT)
        self.temp_label = ttk.Label(temp_frame, text="0.7", width=5)
        self.temp_label.pack(side=LEFT, padx=(8, 0))

        ttk.Label(form, text="描述", font=FONTS["small"]).grid(row=8, column=0, sticky=W, pady=(0, 4))
        self.desc_text = scrolledtext.ScrolledText(form, width=30, height=3)
        self.desc_text.grid(row=9, column=0, sticky=W, pady=(0, 12))

        ttk.Button(form, text="💾 保存修改", command=self.save_changes, bootstyle="success").grid(row=10, column=0, sticky=W, pady=(8, 0))

    def on_temp_change(self, value):
        self.temp_label.config(text=f"{float(value):.1f}")

    def on_preset_select(self, event):
        preset = self.preset_var.get()
        if preset != "自定义" and preset in PRESET_CATEGORIES:
            data = PRESET_CATEGORIES[preset]
            self.name_var.set(preset)
            self.temp_var.set(data["temperature"])
            self.temp_label.config(text=f"{data['temperature']:.1f}")
            self.desc_text.delete("1.0", END)
            self.desc_text.insert("1.0", data["description"])

    def refresh_models(self):
        registry = ModelRegistry(self.app.opencode_config)
        models = registry.get_all_models()
        self.model_combo.config(values=models)

    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        categories = self.app.ohmyopencode_config.get("categories", {})
        for name, data in categories.items():
            model = data.get("model", "")
            temp = data.get("temperature", 0.7)
            desc = data.get("description", "")[:20]
            self.tree.insert("", END, values=(name, model, temp, desc))

    def on_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        name = item["values"][0]
        categories = self.app.ohmyopencode_config.get("categories", {})
        if name in categories:
            data = categories[name]
            self.name_var.set(name)
            self.model_var.set(data.get("model", ""))
            temp = data.get("temperature", 0.7)
            self.temp_var.set(temp)
            self.temp_label.config(text=f"{temp:.1f}")
            self.desc_text.delete("1.0", END)
            self.desc_text.insert("1.0", data.get("description", ""))

    def add_category(self):
        self.name_var.set("")
        self.model_var.set("")
        self.temp_var.set(0.7)
        self.temp_label.config(text="0.7")
        self.desc_text.delete("1.0", END)
        self.preset_var.set("自定义")

    def delete_category(self):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        name = item["values"][0]
        if messagebox.askyesno("确认删除", f"删除 Category [{name}]?"):
            del self.app.ohmyopencode_config["categories"][name]
            self.app.save_configs_silent()
            self.refresh_list()

    def save_changes(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("提示", "名称不能为空")
            return
        categories = self.app.ohmyopencode_config.setdefault("categories", {})
        categories[name] = {
            "model": self.model_var.get(),
            "temperature": round(self.temp_var.get(), 1),
            "description": self.desc_text.get("1.0", END).strip(),
        }
        self.app.save_configs_silent()
        self.refresh_list()
        messagebox.showinfo("成功", "Category 已保存到文件")

# ==================== Permission Tab ====================
class PermissionTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.setup_ui()

    def setup_ui(self):
        paned = ttk.Panedwindow(self, orient=HORIZONTAL)
        paned.pack(fill=BOTH, expand=True, padx=5, pady=5)

        left_frame = ttk.Labelframe(paned, text="权限列表", padding=10)
        paned.add(left_frame, weight=1)
        
        toolbar = ttk.Frame(left_frame)
        toolbar.pack(fill=X, pady=(0, 10))
        ttk.Button(toolbar, text="➕ 添加", command=self.add_permission, bootstyle="primary").pack(side=LEFT, padx=2)
        ttk.Button(toolbar, text="🗑 删除", command=self.delete_permission, bootstyle="danger").pack(side=LEFT, padx=2)

        columns = ("tool", "permission")
        self.tree = ttk.Treeview(left_frame, columns=columns, show="headings", bootstyle="info")
        self.tree.heading("tool", text="工具名称")
        self.tree.heading("permission", text="权限")
        self.tree.column("tool", width=200)
        self.tree.column("permission", width=100)
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar = ttk.Scrollbar(left_frame, orient=VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        right_frame = ttk.Labelframe(paned, text="权限详情", padding=15)
        paned.add(right_frame, weight=2)
        
        form = ttk.Frame(right_frame)
        form.pack(fill=BOTH, expand=True)

        ttk.Label(form, text="工具名称", font=FONTS["small"]).grid(row=0, column=0, sticky=W, pady=(0, 4))
        self.tool_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.tool_var, width=28).grid(row=1, column=0, sticky=W, pady=(0, 12))

        ttk.Label(form, text="权限设置", font=FONTS["small"]).grid(row=2, column=0, sticky=W, pady=(0, 4))
        self.perm_var = tk.StringVar(value="ask")
        perm_frame = ttk.Frame(form)
        perm_frame.grid(row=3, column=0, sticky=W, pady=(0, 16))
        for val, txt in [("allow", "允许"), ("ask", "询问"), ("deny", "拒绝")]:
            ttk.Radiobutton(perm_frame, text=txt, variable=self.perm_var, value=val).pack(side=LEFT, padx=(0, 16))

        ttk.Label(form, text="常用工具", font=FONTS["small"]).grid(row=4, column=0, sticky=W, pady=(0, 4))
        preset_frame = ttk.Frame(form)
        preset_frame.grid(row=5, column=0, sticky=W, pady=(0, 16))
        presets = ["Bash", "Read", "Write", "Edit", "Glob", "Grep", "WebFetch", "WebSearch", "Task"]
        for i, preset in enumerate(presets):
            btn = ttk.Button(preset_frame, text=preset, width=9, command=lambda p=preset: self.tool_var.set(p))
            btn.grid(row=i // 3, column=i % 3, padx=2, pady=2)

        ttk.Button(form, text="💾 保存修改", command=self.save_changes, bootstyle="success").grid(row=6, column=0, sticky=W, pady=(8, 0))

    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        permissions = self.app.opencode_config.get("permission", {})
        for tool, perm in permissions.items():
            self.tree.insert("", END, values=(tool, perm))

    def on_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        self.tool_var.set(item["values"][0])
        self.perm_var.set(item["values"][1])

    def add_permission(self):
        self.tool_var.set("")
        self.perm_var.set("ask")

    def delete_permission(self):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        tool = item["values"][0]
        if messagebox.askyesno("确认删除", f"删除权限 [{tool}]?"):
            del self.app.opencode_config["permission"][tool]
            self.app.save_configs_silent()
            self.refresh_list()

    def save_changes(self):
        tool = self.tool_var.get().strip()
        if not tool:
            messagebox.showwarning("提示", "工具名称不能为空")
            return
        permissions = self.app.opencode_config.setdefault("permission", {})
        permissions[tool] = self.perm_var.get()
        self.app.save_configs_silent()
        self.refresh_list()
        messagebox.showinfo("成功", "权限已保存到文件")

# ==================== Import Tab ====================
class ImportTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.import_service = ImportService()
        self.setup_ui()

    def setup_ui(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)

        top_frame = ttk.Labelframe(main_frame, text="检测到的外部配置", padding=10)
        top_frame.pack(fill=BOTH, expand=True, pady=(0, 8))
        
        toolbar = ttk.Frame(top_frame)
        toolbar.pack(fill=X, pady=(0, 10))
        ttk.Button(toolbar, text="🔄 刷新检测", command=self.refresh_scan, bootstyle="primary").pack(side=LEFT)

        columns = ("source", "path", "status")
        self.tree = ttk.Treeview(top_frame, columns=columns, show="headings", bootstyle="info")
        self.tree.heading("source", text="来源")
        self.tree.heading("path", text="配置路径")
        self.tree.heading("status", text="状态")
        self.tree.column("source", width=120)
        self.tree.column("path", width=350)
        self.tree.column("status", width=80)
        self.tree.pack(fill=BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        bottom_frame = ttk.Labelframe(main_frame, text="配置预览与转换结果", padding=10)
        bottom_frame.pack(fill=BOTH, expand=True, pady=(8, 0))

        preview_label = ttk.Label(bottom_frame, text="原始配置:", font=FONTS["small"])
        preview_label.pack(anchor=W)
        self.preview_text = scrolledtext.ScrolledText(bottom_frame, height=8, font=FONTS["mono"])
        self.preview_text.pack(fill=BOTH, expand=True, pady=(4, 8))

        convert_label = ttk.Label(bottom_frame, text="转换为OpenCode格式:", font=FONTS["small"])
        convert_label.pack(anchor=W)
        self.convert_text = scrolledtext.ScrolledText(bottom_frame, height=6, font=FONTS["mono"])
        self.convert_text.pack(fill=BOTH, expand=True, pady=(4, 8))

        btn_frame = ttk.Frame(bottom_frame)
        btn_frame.pack(fill=X, pady=(8, 0))
        ttk.Button(btn_frame, text="👁️ 预览转换", command=self.preview_convert, bootstyle="secondary").pack(side=LEFT, padx=(0, 8))
        ttk.Button(btn_frame, text="📥 导入到OpenCode", command=self.import_selected, bootstyle="success").pack(side=LEFT)

    def refresh_scan(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        results = self.import_service.scan_external_configs()
        for key, info in results.items():
            status = "✓ 已检测" if info["exists"] else "✗ 未找到"
            self.tree.insert("", END, values=(key, info["path"], status))

    def on_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        source = item["values"][0]
        results = self.import_service.scan_external_configs()
        if source in results and results[source]["data"]:
            self.preview_text.delete("1.0", END)
            self.preview_text.insert("1.0", json.dumps(results[source]["data"], indent=2, ensure_ascii=False))
            self.convert_text.delete("1.0", END)

    def preview_convert(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择要转换的配置")
            return
        item = self.tree.item(selection[0])
        source = item["values"][0]
        results = self.import_service.scan_external_configs()
        if source in results and results[source]["data"]:
            source_type = results[source].get("type", "")
            converted = self.import_service.convert_to_opencode(source_type, results[source]["data"])
            if converted:
                self.convert_text.delete("1.0", END)
                self.convert_text.insert("1.0", json.dumps(converted, indent=2, ensure_ascii=False))
            else:
                messagebox.showwarning("提示", "无法转换此配置格式")

    def import_selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择要导入的配置")
            return
        item = self.tree.item(selection[0])
        source = item["values"][0]
        results = self.import_service.scan_external_configs()

        if source not in results or not results[source]["data"]:
            messagebox.showwarning("提示", "所选配置不存在或为空")
            return

        source_type = results[source].get("type", "")
        converted = self.import_service.convert_to_opencode(source_type, results[source]["data"])

        if not converted:
            messagebox.showwarning("提示", "无法转换此配置格式")
            return

        provider_count = len(converted.get("provider", {}))
        perm_count = len(converted.get("permission", {}))

        msg = f"将导入以下配置:\n• Provider: {provider_count} 个\n• 权限: {perm_count} 个\n\n是否继续?"
        if not messagebox.askyesno("确认导入", msg):
            return

        for provider_name, provider_data in converted.get("provider", {}).items():
            if provider_name in self.app.opencode_config.get("provider", {}):
                if not messagebox.askyesno("冲突", f"Provider [{provider_name}] 已存在，是否覆盖?"):
                    continue
            self.app.opencode_config.setdefault("provider", {})[provider_name] = provider_data

        for tool, perm in converted.get("permission", {}).items():
            self.app.opencode_config.setdefault("permission", {})[tool] = perm

        if self.app.save_configs_silent():
            self.app.refresh_all_tabs()
            messagebox.showinfo("成功", f"已导入 {source} 的配置")

    def refresh_list(self):
        self.refresh_scan()

# ==================== Compaction Tab ====================
class CompactionTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.setup_ui()

    def setup_ui(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)

        compaction_frame = ttk.Labelframe(main_frame, text="上下文压缩配置", padding=10)
        compaction_frame.pack(fill=X, pady=(0, 16))

        form = ttk.Frame(compaction_frame)
        form.pack(fill=X)

        ttk.Label(form, text="上下文压缩用于在会话上下文接近满时自动压缩，以节省 tokens 并保持会话连续性。", wraplength=500).pack(anchor=W, pady=(0, 16))

        auto_frame = ttk.Frame(form)
        auto_frame.pack(fill=X, pady=(0, 8))
        self.auto_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(auto_frame, text="自动压缩", variable=self.auto_var, bootstyle="round-toggle").pack(side=LEFT)
        ttk.Label(auto_frame, text="当上下文已满时自动压缩会话", font=FONTS["small"]).pack(side=LEFT, padx=(8, 0))

        prune_frame = ttk.Frame(form)
        prune_frame.pack(fill=X, pady=(0, 16))
        self.prune_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(prune_frame, text="修剪旧输出", variable=self.prune_var, bootstyle="round-toggle").pack(side=LEFT)
        ttk.Label(prune_frame, text="删除旧的工具输出以节省 tokens", font=FONTS["small"]).pack(side=LEFT, padx=(8, 0))

        ttk.Button(form, text="💾 保存设置", command=self.save_compaction, bootstyle="success").pack(anchor=W)

        preview_frame = ttk.Labelframe(main_frame, text="配置预览", padding=10)
        preview_frame.pack(fill=BOTH, expand=True)

        self.preview_text = scrolledtext.ScrolledText(preview_frame, height=8, font=FONTS["mono"])
        self.preview_text.pack(fill=BOTH, expand=True)

        self.refresh_preview()

    def refresh_list(self):
        compaction = self.app.opencode_config.get("compaction", {})
        self.auto_var.set(compaction.get("auto", True))
        self.prune_var.set(compaction.get("prune", True))
        self.refresh_preview()

    def refresh_preview(self):
        config = {"compaction": {"auto": self.auto_var.get(), "prune": self.prune_var.get()}}
        self.preview_text.config(state=NORMAL)
        self.preview_text.delete("1.0", END)
        self.preview_text.insert("1.0", json.dumps(config, indent=2, ensure_ascii=False))
        self.preview_text.config(state=DISABLED)

    def save_compaction(self):
        self.app.opencode_config["compaction"] = {
            "auto": self.auto_var.get(),
            "prune": self.prune_var.get(),
        }
        self.refresh_preview()
        self.app.save_configs_silent()
        messagebox.showinfo("成功", "上下文压缩配置已保存")

# ==================== Skill Tab ====================
class SkillTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.setup_ui()

    def setup_ui(self):
        paned = ttk.Panedwindow(self, orient=HORIZONTAL)
        paned.pack(fill=BOTH, expand=True, padx=5, pady=5)

        left_frame = ttk.Labelframe(paned, text="Skill 权限配置", padding=10)
        paned.add(left_frame, weight=1)

        ttk.Label(left_frame, text="配置Skill的加载权限。Skill是可复用的指令文件，Agent可按需加载。", wraplength=350).pack(anchor=W, pady=(0, 12))

        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=X, pady=(0, 8))
        ttk.Button(btn_frame, text="➕ 添加权限", command=self.add_permission, bootstyle="primary").pack(side=LEFT, padx=(0, 8))
        ttk.Button(btn_frame, text="🗑 删除", command=self.delete_permission, bootstyle="danger").pack(side=LEFT)

        columns = ("pattern", "permission")
        self.tree = ttk.Treeview(left_frame, columns=columns, show="headings", bootstyle="info")
        self.tree.heading("pattern", text="模式")
        self.tree.heading("permission", text="权限")
        self.tree.column("pattern", width=150)
        self.tree.column("permission", width=80)
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar = ttk.Scrollbar(left_frame, orient=VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        edit_frame = ttk.Frame(left_frame)
        edit_frame.pack(fill=X, pady=(12, 0))

        ttk.Label(edit_frame, text="模式").grid(row=0, column=0, sticky=W, pady=(0, 4))
        self.pattern_var = tk.StringVar(value="*")
        ttk.Entry(edit_frame, textvariable=self.pattern_var, width=20).grid(row=1, column=0, sticky=W, pady=(0, 8))

        ttk.Label(edit_frame, text="权限").grid(row=2, column=0, sticky=W, pady=(0, 4))
        self.perm_var = tk.StringVar(value="ask")
        perm_frame = ttk.Frame(edit_frame)
        perm_frame.grid(row=3, column=0, sticky=W, pady=(0, 8))
        for val, txt in [("allow", "允许"), ("ask", "询问"), ("deny", "拒绝")]:
            ttk.Radiobutton(perm_frame, text=txt, variable=self.perm_var, value=val).pack(side=LEFT, padx=(0, 12))

        ttk.Button(edit_frame, text="💾 保存权限", command=self.save_permission, bootstyle="success").grid(row=4, column=0, sticky=W, pady=(8, 0))

        right_frame = ttk.Labelframe(paned, text="创建 SKILL.md", padding=10)
        paned.add(right_frame, weight=2)

        form = ttk.Frame(right_frame)
        form.pack(fill=BOTH, expand=True)

        ttk.Label(form, text="Skill 名称").pack(anchor=W)
        self.skill_name_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.skill_name_var, width=30).pack(anchor=W, pady=(4, 8))

        ttk.Label(form, text="描述").pack(anchor=W)
        self.skill_desc_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.skill_desc_var, width=40).pack(anchor=W, pady=(4, 8))

        ttk.Label(form, text="Skill 内容（Markdown格式）").pack(anchor=W)
        self.skill_content_text = scrolledtext.ScrolledText(form, height=10, font=FONTS["mono"])
        self.skill_content_text.pack(fill=BOTH, expand=True, pady=(4, 8))
        self.skill_content_text.insert("1.0", """## What I do
- 描述这个Skill的功能

## When to use me
- 描述何时使用这个Skill

## Instructions
- 具体的指令内容
""")

        loc_frame = ttk.Frame(form)
        loc_frame.pack(fill=X, pady=(0, 8))
        ttk.Label(loc_frame, text="保存位置:").pack(side=LEFT)
        self.skill_location_var = tk.StringVar(value="global")
        ttk.Radiobutton(loc_frame, text="全局 (~/.config/opencode/skill/)", variable=self.skill_location_var, value="global").pack(side=LEFT, padx=(8, 0))
        ttk.Radiobutton(loc_frame, text="项目 (.opencode/skill/)", variable=self.skill_location_var, value="project").pack(side=LEFT, padx=(8, 0))

        btn_frame2 = ttk.Frame(form)
        btn_frame2.pack(fill=X)
        ttk.Button(btn_frame2, text="📝 创建 SKILL.md", command=self.create_skill, bootstyle="success").pack(side=LEFT, padx=(0, 8))
        ttk.Button(btn_frame2, text="👁️ 预览", command=self.preview_skill, bootstyle="secondary").pack(side=LEFT)

    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        permissions = self.app.opencode_config.get("permission", {}).get("skill", {})
        if isinstance(permissions, dict):
            for pattern, perm in permissions.items():
                self.tree.insert("", END, values=(pattern, perm))
        elif isinstance(permissions, str):
            self.tree.insert("", END, values=("*", permissions))

    def on_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        self.pattern_var.set(item["values"][0])
        self.perm_var.set(item["values"][1])

    def add_permission(self):
        self.pattern_var.set("")
        self.perm_var.set("ask")

    def delete_permission(self):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        pattern = item["values"][0]
        if messagebox.askyesno("确认", f"删除 Skill 权限 [{pattern}]?"):
            skill_perms = self.app.opencode_config.get("permission", {}).get("skill", {})
            if pattern in skill_perms:
                del skill_perms[pattern]
                self.app.save_configs_silent()
                self.refresh_list()

    def save_permission(self):
        pattern = self.pattern_var.get().strip()
        if not pattern:
            messagebox.showwarning("提示", "请输入模式")
            return
        perm = self.app.opencode_config.setdefault("permission", {})
        skill_perm = perm.setdefault("skill", {})
        skill_perm[pattern] = self.perm_var.get()
        self.app.save_configs_silent()
        self.refresh_list()
        messagebox.showinfo("成功", f"Skill 权限 [{pattern}] 已保存")

    def preview_skill(self):
        name = self.skill_name_var.get().strip()
        desc = self.skill_desc_var.get().strip()
        content = self.skill_content_text.get("1.0", END).strip()

        if not name or not desc:
            messagebox.showwarning("提示", "请填写Skill名称和描述")
            return

        preview = f"""---
name: {name}
description: {desc}
---

{content}
"""
        preview_win = tk.Toplevel(self)
        preview_win.title(f"预览: {name}/SKILL.md")
        preview_win.geometry("500x400")
        text = scrolledtext.ScrolledText(preview_win, font=FONTS["mono"])
        text.pack(fill=BOTH, expand=True, padx=10, pady=10)
        text.insert("1.0", preview)
        text.config(state=DISABLED)

    def create_skill(self):
        name = self.skill_name_var.get().strip()
        desc = self.skill_desc_var.get().strip()
        content = self.skill_content_text.get("1.0", END).strip()

        if not name:
            messagebox.showwarning("提示", "请输入Skill名称")
            return
        if not desc:
            messagebox.showwarning("提示", "请输入Skill描述")
            return

        if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", name):
            messagebox.showerror("错误", "Skill名称格式错误！\n要求：小写字母、数字、连字符，不能以连字符开头或结尾")
            return

        if self.skill_location_var.get() == "global":
            base_path = Path.home() / ".config" / "opencode" / "skill"
        else:
            base_path = Path.cwd() / ".opencode" / "skill"

        skill_dir = base_path / name
        skill_file = skill_dir / "SKILL.md"

        try:
            skill_dir.mkdir(parents=True, exist_ok=True)
            skill_content = f"""---
name: {name}
description: {desc}
---

{content}
"""
            with open(skill_file, "w", encoding="utf-8") as f:
                f.write(skill_content)

            messagebox.showinfo("成功", f"Skill 已创建:\n{skill_file}")
        except Exception as e:
            messagebox.showerror("错误", f"创建失败: {e}")

# ==================== Rules Tab ====================
class RulesTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.setup_ui()

    def setup_ui(self):
        paned = ttk.Panedwindow(self, orient=HORIZONTAL)
        paned.pack(fill=BOTH, expand=True, padx=5, pady=5)

        left_frame = ttk.Labelframe(paned, text="Instructions 配置", padding=10)
        paned.add(left_frame, weight=1)

        ttk.Label(left_frame, text="配置额外的指令文件，这些文件会与AGENTS.md合并加载。", wraplength=350).pack(anchor=W, pady=(0, 12))

        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=X, pady=(0, 8))
        ttk.Button(btn_frame, text="➕ 添加", command=self.add_instruction, bootstyle="primary").pack(side=LEFT, padx=(0, 8))
        ttk.Button(btn_frame, text="🗑 删除", command=self.delete_instruction, bootstyle="danger").pack(side=LEFT)

        self.instructions_listbox = tk.Listbox(left_frame, height=8, font=FONTS["body"], selectmode=tk.SINGLE)
        self.instructions_listbox.pack(fill=BOTH, expand=True, pady=(0, 8))

        add_frame = ttk.Frame(left_frame)
        add_frame.pack(fill=X, pady=(0, 8))
        ttk.Label(add_frame, text="文件路径:").pack(anchor=W)
        self.instruction_path_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.instruction_path_var, width=35).pack(anchor=W, pady=(4, 0))

        quick_frame = ttk.Frame(left_frame)
        quick_frame.pack(fill=X, pady=(0, 8))
        ttk.Label(quick_frame, text="快捷:", font=FONTS["small"]).pack(side=LEFT)
        for path in ["CONTRIBUTING.md", "docs/*.md", ".cursor/rules/*.md"]:
            ttk.Button(quick_frame, text=path, command=lambda p=path: self.instruction_path_var.set(p)).pack(side=LEFT, padx=2)

        ttk.Button(left_frame, text="💾 保存配置", command=self.save_instructions, bootstyle="success").pack(anchor=W)

        right_frame = ttk.Labelframe(paned, text="AGENTS.md 编辑", padding=10)
        paned.add(right_frame, weight=2)

        form = ttk.Frame(right_frame)
        form.pack(fill=BOTH, expand=True)

        loc_frame = ttk.Frame(form)
        loc_frame.pack(fill=X, pady=(0, 8))
        ttk.Label(loc_frame, text="编辑位置:").pack(side=LEFT)
        self.agents_location_var = tk.StringVar(value="global")
        ttk.Radiobutton(loc_frame, text="全局", variable=self.agents_location_var, value="global", command=self.load_agents_md).pack(side=LEFT, padx=(8, 0))
        ttk.Radiobutton(loc_frame, text="项目", variable=self.agents_location_var, value="project", command=self.load_agents_md).pack(side=LEFT, padx=(8, 0))

        self.agents_path_label = ttk.Label(form, text="", font=FONTS["small"])
        self.agents_path_label.pack(anchor=W, pady=(0, 8))

        self.agents_text = scrolledtext.ScrolledText(form, height=15, font=FONTS["mono"])
        self.agents_text.pack(fill=BOTH, expand=True, pady=(0, 8))

        btn_frame2 = ttk.Frame(form)
        btn_frame2.pack(fill=X)
        ttk.Button(btn_frame2, text="💾 保存 AGENTS.md", command=self.save_agents_md, bootstyle="success").pack(side=LEFT, padx=(0, 8))
        ttk.Button(btn_frame2, text="🔄 重新加载", command=self.load_agents_md, bootstyle="secondary").pack(side=LEFT, padx=(0, 8))
        ttk.Button(btn_frame2, text="📄 使用模板", command=self.use_template, bootstyle="secondary").pack(side=LEFT)

        self.load_agents_md()

    def refresh_list(self):
        self.instructions_listbox.delete(0, tk.END)
        instructions = self.app.opencode_config.get("instructions", [])
        for path in instructions:
            self.instructions_listbox.insert(tk.END, path)

    def add_instruction(self):
        path = self.instruction_path_var.get().strip()
        if not path:
            messagebox.showwarning("提示", "请输入文件路径")
            return
        instructions = self.app.opencode_config.setdefault("instructions", [])
        if path not in instructions:
            instructions.append(path)
            self.refresh_list()
            self.instruction_path_var.set("")

    def delete_instruction(self):
        selection = self.instructions_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        instructions = self.app.opencode_config.get("instructions", [])
        if idx < len(instructions):
            del instructions[idx]
            self.refresh_list()

    def save_instructions(self):
        self.app.save_configs_silent()
        messagebox.showinfo("成功", "Instructions 配置已保存")

    def get_agents_path(self):
        if self.agents_location_var.get() == "global":
            return Path.home() / ".config" / "opencode" / "AGENTS.md"
        else:
            return Path.cwd() / "AGENTS.md"

    def load_agents_md(self):
        path = self.get_agents_path()
        self.agents_path_label.config(text=f"路径: {path}")

        self.agents_text.delete("1.0", END)
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.agents_text.insert("1.0", content)
            except Exception as e:
                self.agents_text.insert("1.0", f"# 读取失败: {e}")
        else:
            self.agents_text.insert("1.0", '# AGENTS.md 文件不存在\n# 点击"使用模板"创建新文件')

    def save_agents_md(self):
        path = self.get_agents_path()
        content = self.agents_text.get("1.0", END).strip()

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("成功", f"AGENTS.md 已保存:\n{path}")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {e}")

    def use_template(self):
        template = """# Project Rules

This is a project-specific rules file for OpenCode.

## Project Structure
- `src/` - Source code
- `tests/` - Test files
- `docs/` - Documentation

## Code Standards
- Use TypeScript with strict mode enabled
- Follow existing code patterns
- Write tests for new features

## Conventions
- Use meaningful variable names
- Add comments for complex logic
- Keep functions small and focused

## External File Loading
When you encounter a file reference (e.g., @rules/general.md), use your Read tool to load it.
"""
        self.agents_text.delete("1.0", END)
        self.agents_text.insert("1.0", template)

# ==================== MCP Tab ====================
class MCPTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.current_mcp = None
        self.setup_ui()

    def setup_ui(self):
        paned = ttk.Panedwindow(self, orient=HORIZONTAL)
        paned.pack(fill=BOTH, expand=True, padx=5, pady=5)

        left_frame = ttk.Labelframe(paned, text="MCP 服务器列表", padding=10)
        paned.add(left_frame, weight=1)

        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=X, pady=(0, 8))
        ttk.Button(btn_frame, text="➕ 添加 MCP", command=self.add_mcp, bootstyle="primary").pack(side=LEFT, padx=(0, 8))
        ttk.Button(btn_frame, text="🗑 删除", command=self.delete_mcp, bootstyle="danger").pack(side=LEFT)

        columns = ("name", "type", "enabled")
        self.tree = ttk.Treeview(left_frame, columns=columns, show="headings", bootstyle="info")
        self.tree.heading("name", text="名称")
        self.tree.heading("type", text="类型")
        self.tree.heading("enabled", text="启用")
        self.tree.column("name", width=120)
        self.tree.column("type", width=80)
        self.tree.column("enabled", width=60)
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar = ttk.Scrollbar(left_frame, orient=VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        right_frame = ttk.Labelframe(paned, text="MCP 详情", padding=10)
        paned.add(right_frame, weight=2)

        form = ttk.Frame(right_frame)
        form.pack(fill=BOTH, expand=True)

        ttk.Label(form, text="MCP 名称").grid(row=0, column=0, sticky=W, pady=(0, 4))
        self.name_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.name_var, width=30).grid(row=1, column=0, sticky=W, pady=(0, 8))

        ttk.Label(form, text="类型").grid(row=2, column=0, sticky=W, pady=(0, 4))
        self.type_var = tk.StringVar(value="local")
        type_frame = ttk.Frame(form)
        type_frame.grid(row=3, column=0, sticky=W, pady=(0, 8))
        ttk.Radiobutton(type_frame, text="Local", variable=self.type_var, value="local", command=self.on_type_change).pack(side=LEFT)
        ttk.Radiobutton(type_frame, text="Remote", variable=self.type_var, value="remote", command=self.on_type_change).pack(side=LEFT, padx=(16, 0))

        self.enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(form, text="启用", variable=self.enabled_var, bootstyle="round-toggle").grid(row=4, column=0, sticky=W, pady=(0, 8))

        self.local_frame = ttk.Frame(form)
        self.local_frame.grid(row=5, column=0, sticky=W, pady=(0, 8))
        ttk.Label(self.local_frame, text="启动命令 (JSON数组)").pack(anchor=W)
        self.command_var = tk.StringVar(value='["npx", "-y", "@mcp/server"]')
        ttk.Entry(self.local_frame, textvariable=self.command_var, width=40).pack(anchor=W, pady=(4, 8))
        ttk.Label(self.local_frame, text="环境变量 (JSON)").pack(anchor=W)
        self.env_var = tk.StringVar(value="{}")
        ttk.Entry(self.local_frame, textvariable=self.env_var, width=40).pack(anchor=W, pady=(4, 0))

        self.remote_frame = ttk.Frame(form)
        self.remote_frame.grid(row=5, column=0, sticky=W, pady=(0, 8))
        ttk.Label(self.remote_frame, text="服务器 URL").pack(anchor=W)
        self.url_var = tk.StringVar()
        ttk.Entry(self.remote_frame, textvariable=self.url_var, width=40).pack(anchor=W, pady=(4, 8))
        ttk.Label(self.remote_frame, text="请求头 (JSON)").pack(anchor=W)
        self.headers_var = tk.StringVar(value="{}")
        ttk.Entry(self.remote_frame, textvariable=self.headers_var, width=40).pack(anchor=W, pady=(4, 0))
        self.remote_frame.grid_remove()

        ttk.Label(form, text="超时 (毫秒)").grid(row=6, column=0, sticky=W, pady=(0, 4))
        self.timeout_var = tk.StringVar(value="5000")
        ttk.Entry(form, textvariable=self.timeout_var, width=15).grid(row=7, column=0, sticky=W, pady=(0, 12))

        ttk.Button(form, text="💾 保存 MCP", command=self.save_mcp, bootstyle="success").grid(row=8, column=0, sticky=W)

    def on_type_change(self):
        if self.type_var.get() == "local":
            self.remote_frame.grid_remove()
            self.local_frame.grid()
        else:
            self.local_frame.grid_remove()
            self.remote_frame.grid()

    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        mcps = self.app.opencode_config.get("mcp", {})
        for name, data in mcps.items():
            mcp_type = data.get("type", "local")
            enabled = "是" if data.get("enabled", True) else "否"
            self.tree.insert("", END, values=(name, mcp_type, enabled))

    def on_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        name = item["values"][0]
        self.current_mcp = name
        mcps = self.app.opencode_config.get("mcp", {})
        if name in mcps:
            data = mcps[name]
            self.name_var.set(name)
            self.type_var.set(data.get("type", "local"))
            self.enabled_var.set(data.get("enabled", True))
            self.timeout_var.set(str(data.get("timeout", 5000)))
            if data.get("type") == "remote":
                self.url_var.set(data.get("url", ""))
                self.headers_var.set(json.dumps(data.get("headers", {}), ensure_ascii=False))
            else:
                self.command_var.set(json.dumps(data.get("command", []), ensure_ascii=False))
                self.env_var.set(json.dumps(data.get("environment", {}), ensure_ascii=False))
            self.on_type_change()

    def add_mcp(self):
        self.current_mcp = None
        self.name_var.set("")
        self.type_var.set("local")
        self.enabled_var.set(True)
        self.command_var.set('["npx", "-y", "@mcp/server"]')
        self.env_var.set("{}")
        self.url_var.set("")
        self.headers_var.set("{}")
        self.timeout_var.set("5000")
        self.on_type_change()

    def save_mcp(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("提示", "请输入 MCP 名称")
            return
        mcp_type = self.type_var.get()
        data = {"type": mcp_type, "enabled": self.enabled_var.get()}
        try:
            timeout = int(self.timeout_var.get())
            if timeout != 5000:
                data["timeout"] = timeout
        except:
            pass
        if mcp_type == "local":
            try:
                data["command"] = json.loads(self.command_var.get())
            except:
                messagebox.showerror("错误", "启动命令格式错误，需要JSON数组")
                return
            try:
                env = json.loads(self.env_var.get())
                if env:
                    data["environment"] = env
            except:
                pass
        else:
            url = self.url_var.get().strip()
            if not url:
                messagebox.showwarning("提示", "请输入服务器 URL")
                return
            data["url"] = url
            try:
                headers = json.loads(self.headers_var.get())
                if headers:
                    data["headers"] = headers
            except:
                pass
        self.app.opencode_config.setdefault("mcp", {})[name] = data
        if self.current_mcp and self.current_mcp != name:
            del self.app.opencode_config["mcp"][self.current_mcp]
        self.current_mcp = name
        self.refresh_list()
        self.app.save_configs_silent()
        messagebox.showinfo("成功", f"MCP [{name}] 已保存")

    def delete_mcp(self):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        name = item["values"][0]
        if messagebox.askyesno("确认", f"确定删除 MCP [{name}]?"):
            if name in self.app.opencode_config.get("mcp", {}):
                del self.app.opencode_config["mcp"][name]
                self.refresh_list()
                self.app.save_configs_silent()

# ==================== OpenCode Agent Tab ====================
class OpenCodeAgentTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.current_agent = None
        self.setup_ui()

    def setup_ui(self):
        paned = ttk.Panedwindow(self, orient=HORIZONTAL)
        paned.pack(fill=BOTH, expand=True, padx=5, pady=5)

        left_frame = ttk.Labelframe(paned, text="Agent 列表", padding=10)
        paned.add(left_frame, weight=1)

        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=X, pady=(0, 8))
        ttk.Button(btn_frame, text="➕ 添加 Agent", command=self.add_agent, bootstyle="primary").pack(side=LEFT, padx=(0, 8))
        ttk.Button(btn_frame, text="🗑 删除", command=self.delete_agent, bootstyle="danger").pack(side=LEFT)

        preset_frame = ttk.Frame(left_frame)
        preset_frame.pack(fill=X, pady=(0, 8))
        ttk.Label(preset_frame, text="预设:", font=FONTS["small"]).pack(side=LEFT)
        for name in list(PRESET_OPENCODE_AGENTS.keys())[:4]:
            ttk.Button(preset_frame, text=name, command=lambda n=name: self.load_preset(n)).pack(side=LEFT, padx=2)

        columns = ("name", "mode", "model")
        self.tree = ttk.Treeview(left_frame, columns=columns, show="headings", bootstyle="info")
        self.tree.heading("name", text="名称")
        self.tree.heading("mode", text="模式")
        self.tree.heading("model", text="模型")
        self.tree.column("name", width=100)
        self.tree.column("mode", width=80)
        self.tree.column("model", width=150)
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar = ttk.Scrollbar(left_frame, orient=VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        right_frame = ttk.Labelframe(paned, text="Agent 详情", padding=10)
        paned.add(right_frame, weight=2)

        canvas = tk.Canvas(right_frame, highlightthickness=0)
        scrollbar_r = ttk.Scrollbar(right_frame, orient=VERTICAL, command=canvas.yview)
        form = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=form, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar_r.set)
        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar_r.pack(side=RIGHT, fill=Y)
        form.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        ttk.Label(form, text="Agent 名称").grid(row=0, column=0, sticky=W, padx=10, pady=(10, 4))
        self.name_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.name_var, width=25).grid(row=1, column=0, sticky=W, padx=10, pady=(0, 8))

        ttk.Label(form, text="描述").grid(row=2, column=0, sticky=W, padx=10, pady=(0, 4))
        self.desc_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.desc_var, width=35).grid(row=3, column=0, sticky=W, padx=10, pady=(0, 8))

        ttk.Label(form, text="模式").grid(row=4, column=0, sticky=W, padx=10, pady=(0, 4))
        self.mode_var = tk.StringVar(value="subagent")
        mode_frame = ttk.Frame(form)
        mode_frame.grid(row=5, column=0, sticky=W, padx=10, pady=(0, 8))
        for mode in ["primary", "subagent", "all"]:
            ttk.Radiobutton(mode_frame, text=mode, variable=self.mode_var, value=mode).pack(side=LEFT, padx=(0, 12))

        ttk.Label(form, text="模型 (可选)").grid(row=6, column=0, sticky=W, padx=10, pady=(0, 4))
        self.model_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.model_var, width=30).grid(row=7, column=0, sticky=W, padx=10, pady=(0, 8))

        ttk.Label(form, text="Temperature").grid(row=8, column=0, sticky=W, padx=10, pady=(0, 4))
        temp_frame = ttk.Frame(form)
        temp_frame.grid(row=9, column=0, sticky=W, padx=10, pady=(0, 8))
        self.temp_var = tk.DoubleVar(value=0.3)
        self.temp_scale = ttk.Scale(temp_frame, from_=0, to=2, resolution=0.1, orient=tk.HORIZONTAL, variable=self.temp_var, length=150)
        self.temp_scale.pack(side=LEFT)
        self.temp_label = ttk.Label(temp_frame, text="0.3")
        self.temp_label.pack(side=LEFT, padx=(8, 0))
        self.temp_var.trace_add("write", lambda *args: self.temp_label.config(text=f"{self.temp_var.get():.1f}"))

        ttk.Label(form, text="最大步数 (可选)").grid(row=10, column=0, sticky=W, padx=10, pady=(0, 4))
        self.maxsteps_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.maxsteps_var, width=10).grid(row=11, column=0, sticky=W, padx=10, pady=(0, 8))

        self.hidden_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(form, text="隐藏 (仅subagent)", variable=self.hidden_var, bootstyle="round-toggle").grid(row=12, column=0, sticky=W, padx=10, pady=(0, 8))

        self.disable_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(form, text="禁用此Agent", variable=self.disable_var, bootstyle="round-toggle").grid(row=13, column=0, sticky=W, padx=10, pady=(0, 8))

        ttk.Label(form, text="工具配置 (JSON)").grid(row=14, column=0, sticky=W, padx=10, pady=(0, 4))
        self.tools_text = scrolledtext.ScrolledText(form, height=3, width=35, font=FONTS["mono"])
        self.tools_text.grid(row=15, column=0, sticky=W, padx=10, pady=(0, 8))
        self.tools_text.insert("1.0", '{"write": true, "edit": true, "bash": true}')

        ttk.Label(form, text="权限配置 (JSON)").grid(row=16, column=0, sticky=W, padx=10, pady=(0, 4))
        self.perm_text = scrolledtext.ScrolledText(form, height=3, width=35, font=FONTS["mono"])
        self.perm_text.grid(row=17, column=0, sticky=W, padx=10, pady=(0, 8))
        self.perm_text.insert("1.0", "{}")

        ttk.Label(form, text="系统提示词").grid(row=18, column=0, sticky=W, padx=10, pady=(0, 4))
        self.prompt_text = scrolledtext.ScrolledText(form, height=4, width=35, font=FONTS["mono"])
        self.prompt_text.grid(row=19, column=0, sticky=W, padx=10, pady=(0, 12))

        ttk.Button(form, text="💾 保存 Agent", command=self.save_agent, bootstyle="success").grid(row=20, column=0, sticky=W, padx=10, pady=(0, 20))

    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        agents = self.app.opencode_config.get("agent", {})
        for name, data in agents.items():
            mode = data.get("mode", "all")
            model = data.get("model", "-")
            self.tree.insert("", END, values=(name, mode, model))

    def on_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        name = item["values"][0]
        self.current_agent = name
        agents = self.app.opencode_config.get("agent", {})
        if name in agents:
            data = agents[name]
            self.name_var.set(name)
            self.desc_var.set(data.get("description", ""))
            self.mode_var.set(data.get("mode", "all"))
            self.model_var.set(data.get("model", ""))
            self.temp_var.set(data.get("temperature", 0.3))
            self.maxsteps_var.set(str(data.get("maxSteps", "")) if "maxSteps" in data else "")
            self.hidden_var.set(data.get("hidden", False))
            self.disable_var.set(data.get("disable", False))
            self.tools_text.delete("1.0", END)
            self.tools_text.insert("1.0", json.dumps(data.get("tools", {}), indent=2, ensure_ascii=False))
            self.perm_text.delete("1.0", END)
            self.perm_text.insert("1.0", json.dumps(data.get("permission", {}), indent=2, ensure_ascii=False))
            self.prompt_text.delete("1.0", END)
            self.prompt_text.insert("1.0", data.get("prompt", ""))

    def load_preset(self, preset_name):
        if preset_name in PRESET_OPENCODE_AGENTS:
            preset = PRESET_OPENCODE_AGENTS[preset_name]
            self.name_var.set(preset_name)
            self.desc_var.set(preset.get("description", ""))
            self.mode_var.set(preset.get("mode", "subagent"))
            self.tools_text.delete("1.0", END)
            self.tools_text.insert("1.0", json.dumps(preset.get("tools", {}), indent=2, ensure_ascii=False))
            self.perm_text.delete("1.0", END)
            self.perm_text.insert("1.0", json.dumps(preset.get("permission", {}), indent=2, ensure_ascii=False))

    def add_agent(self):
        self.current_agent = None
        self.name_var.set("")
        self.desc_var.set("")
        self.mode_var.set("subagent")
        self.model_var.set("")
        self.temp_var.set(0.3)
        self.maxsteps_var.set("")
        self.hidden_var.set(False)
        self.disable_var.set(False)
        self.tools_text.delete("1.0", END)
        self.tools_text.insert("1.0", "{}")
        self.perm_text.delete("1.0", END)
        self.perm_text.insert("1.0", "{}")
        self.prompt_text.delete("1.0", END)

    def save_agent(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("提示", "请输入 Agent 名称")
            return
        desc = self.desc_var.get().strip()
        if not desc:
            messagebox.showwarning("提示", "请输入 Agent 描述")
            return
        data = {"description": desc, "mode": self.mode_var.get()}
        model = self.model_var.get().strip()
        if model:
            data["model"] = model
        temp = self.temp_var.get()
        if temp != 0.3:
            data["temperature"] = temp
        maxsteps = self.maxsteps_var.get().strip()
        if maxsteps:
            try:
                data["maxSteps"] = int(maxsteps)
            except:
                pass
        if self.hidden_var.get():
            data["hidden"] = True
        if self.disable_var.get():
            data["disable"] = True
        try:
            tools = json.loads(self.tools_text.get("1.0", END).strip())
            if tools:
                data["tools"] = tools
        except:
            pass
        try:
            perm = json.loads(self.perm_text.get("1.0", END).strip())
            if perm:
                data["permission"] = perm
        except:
            pass
        prompt = self.prompt_text.get("1.0", END).strip()
        if prompt:
            data["prompt"] = prompt
        self.app.opencode_config.setdefault("agent", {})[name] = data
        if self.current_agent and self.current_agent != name:
            del self.app.opencode_config["agent"][self.current_agent]
        self.current_agent = name
        self.refresh_list()
        self.app.save_configs_silent()
        messagebox.showinfo("成功", f"Agent [{name}] 已保存")

    def delete_agent(self):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        name = item["values"][0]
        if messagebox.askyesno("确认", f"确定删除 Agent [{name}]?"):
            if name in self.app.opencode_config.get("agent", {}):
                del self.app.opencode_config["agent"][name]
                self.refresh_list()
                self.app.save_configs_silent()

# ==================== Help Tab ====================
class HelpTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.setup_ui()

    def setup_ui(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill=BOTH, expand=True, padx=5, pady=5)

        priority_frame = ttk.Frame(notebook)
        notebook.add(priority_frame, text="  配置优先级  ")
        priority_text = scrolledtext.ScrolledText(priority_frame, wrap=tk.WORD, font=FONTS["body"])
        priority_text.pack(fill=BOTH, expand=True, padx=20, pady=20)
        priority_content = """配置优先顺序（从高到低）

1. 远程配置
   通过 API 或远程服务器获取的配置
   优先级最高，会覆盖所有本地配置

2. 全局配置
   位置: ~/.config/opencode/opencode.json
   影响所有项目的默认配置

3. 自定义配置
   通过 --config 参数指定的配置文件
   用于特定场景的配置覆盖

4. 项目配置
   位置: <项目根目录>/opencode.json
   项目级别的配置，仅影响当前项目

5. .opencode 目录配置
   位置: <项目根目录>/.opencode/config.json
   项目内的隐藏配置目录

6. 内联配置
   通过命令行参数直接指定的配置
   优先级最低，但最灵活

配置合并规则:
- 高优先级配置会覆盖低优先级的同名配置项
- 未指定的配置项会继承低优先级的值
- Provider 和 Model 配置会进行深度合并"""
        priority_text.insert("1.0", priority_content)
        priority_text.config(state=DISABLED)

        usage_frame = ttk.Frame(notebook)
        notebook.add(usage_frame, text="  使用说明  ")
        usage_text = scrolledtext.ScrolledText(usage_frame, wrap=tk.WORD, font=FONTS["body"])
        usage_text.pack(fill=BOTH, expand=True, padx=20, pady=20)
        usage_content = """OpenCode 配置管理器 使用说明

一、Provider 管理
   添加自定义 API 提供商
   配置 API 地址和密钥
   支持多种 SDK: @ai-sdk/anthropic, @ai-sdk/openai 等

二、Model 管理
   在 Provider 下添加模型
   支持预设常用模型快速选择
   配置模型参数（上下文限制、输出限制等）

三、Agent 管理
   配置不同用途的 Agent
   绑定已配置的 Provider/Model
   支持预设 Agent 模板

四、Category 管理
   配置任务分类
   设置不同分类的 Temperature
   绑定对应的模型

五、权限管理
   配置工具的使用权限
   allow: 允许使用
   ask: 每次询问
   deny: 禁止使用

六、外部导入
   检测 Claude Code 等工具的配置
   一键导入已有配置

注意事项:
- 修改后请点击保存按钮
- 建议定期备份配置文件
- Agent/Category 的模型必须是已配置的 Provider/Model"""
        usage_text.insert("1.0", usage_content)
        usage_text.config(state=DISABLED)

        omo_frame = ttk.Frame(notebook)
        notebook.add(omo_frame, text="  Oh My OpenCode  ")
        omo_text = scrolledtext.ScrolledText(omo_frame, wrap=tk.WORD, font=FONTS["body"])
        omo_text.pack(fill=BOTH, expand=True, padx=20, pady=20)
        omo_content = """Oh My OpenCode 核心功能说明

═══════════════════════════════════════════════════════════════
🪄 魔法关键词: ultrawork (ulw)
═══════════════════════════════════════════════════════════════

只需在提示词中包含 "ultrawork" 或 "ulw"，即可激活所有高级功能：
• 并行 Agent 编排
• 后台任务执行
• 深度探索模式
• 持续执行直到完成

示例: "ulw 帮我重构这个模块" → Agent 自动分析、并行搜索、持续工作

═══════════════════════════════════════════════════════════════
🤖 内置 Agent 团队
═══════════════════════════════════════════════════════════════

• Sisyphus (主Agent): Claude Opus 4.5 - 任务编排和执行
• Oracle: GPT 5.2 - 架构设计、代码审查、策略规划
• Librarian: 文档查找、开源实现搜索、代码库分析
• Explore: 快速代码库探索和模式匹配
• Frontend UI/UX Engineer: Gemini 3 Pro - 前端开发
• Document Writer: 技术文档写作
• Multimodal Looker: 视觉内容分析（PDF、图片等）

═══════════════════════════════════════════════════════════════
🔧 LSP 工具集 (代码智能)
═══════════════════════════════════════════════════════════════

• lsp_hover: 获取符号的类型信息、文档、签名
• lsp_goto_definition: 跳转到符号定义位置
• lsp_find_references: 查找工作区中的所有引用
• lsp_document_symbols: 获取文件符号大纲
• lsp_workspace_symbols: 按名称搜索项目中的符号
• lsp_diagnostics: 构建前获取错误/警告
• lsp_servers: 列出可用的 LSP 服务器
• lsp_prepare_rename: 验证重命名操作
• lsp_rename: 跨工作区重命名符号
• lsp_code_actions: 获取可用的快速修复/重构
• lsp_code_action_resolve: 应用代码操作

═══════════════════════════════════════════════════════════════
🔍 AST 工具 (语法树搜索)
═══════════════════════════════════════════════════════════════

• ast_grep_search: AST 感知的代码模式搜索（支持 25 种语言）
• ast_grep_replace: AST 感知的代码替换

═══════════════════════════════════════════════════════════════
📚 会话管理工具
═══════════════════════════════════════════════════════════════

• session_list: 列出所有 OpenCode 会话（支持日期过滤）
• session_read: 读取特定会话的消息和历史
• session_search: 跨会话消息全文搜索
• session_info: 获取会话的元数据和统计信息

═══════════════════════════════════════════════════════════════
📁 配置加载器 (Claude Code 兼容)
═══════════════════════════════════════════════════════════════

【命令加载器】从以下目录加载 Markdown 斜杠命令:
• ~/.claude/commands/ (用户级)
• ./.claude/commands/ (项目级)
• ~/.config/opencode/command/ (OpenCode 全局)
• ./.opencode/command/ (OpenCode 项目)

【Skill 加载器】加载基于目录的 Skill (含 SKILL.md):
• ~/.claude/skills/ (用户级)
• ./.claude/skills/ (项目级)

【Agent 加载器】从 Markdown 文件加载自定义 Agent:
• ~/.claude/agents/*.md (用户级)
• ./.claude/agents/*.md (项目级)

【MCP 加载器】从 .mcp.json 加载 MCP 服务器配置:
• ~/.claude/.mcp.json (用户级)
• ./.mcp.json (项目级)
• ./.claude/.mcp.json (本地)
• 支持环境变量扩展 (${VAR} 语法)

═══════════════════════════════════════════════════════════════
⚙️ 兼容性开关
═══════════════════════════════════════════════════════════════

在 oh-my-opencode.json 中配置 claude_code 对象可禁用特定功能:

{
  "claude_code": {
    "mcp": false,      // 禁用 Claude Code MCP 加载
    "commands": false, // 禁用 Claude Code 命令加载
    "skills": false,   // 禁用 Claude Code Skill 加载
    "agents": false,   // 禁用 Claude Code Agent 加载
    "hooks": false,    // 禁用 Claude Code Hooks
    "plugins": false   // 禁用 Claude Code 插件
  }
}

注意: 这些开关仅影响 Claude Code 兼容层，不影响 OpenCode 原生功能

═══════════════════════════════════════════════════════════════
🎯 其他核心功能
═══════════════════════════════════════════════════════════════

• Todo 持续执行器: 强制 Agent 完成所有 TODO 才能停止
• 注释检查器: 防止 AI 添加过多注释，保持代码整洁
• 思考模式: 自动检测需要深度思考的场景并切换模式
• 上下文窗口监控: 70%+ 使用率时提醒 Agent 合理利用空间
• 自动压缩: Claude 模型达到 token 限制时自动压缩会话
• 会话恢复: 自动从会话错误中恢复
• 后台通知: 后台 Agent 任务完成时发送通知

═══════════════════════════════════════════════════════════════
📖 更多信息
═══════════════════════════════════════════════════════════════

GitHub: https://github.com/code-yeongyu/oh-my-opencode
Discord: https://discord.gg/PUwSMR9XNk
"""
        omo_text.insert("1.0", omo_content)
        omo_text.config(state=DISABLED)

        about_frame = ttk.Frame(notebook)
        notebook.add(about_frame, text="  关于  ")
        center_frame = ttk.Frame(about_frame)
        center_frame.pack(expand=True)

        ttk.Label(center_frame, text="OpenCode 配置管理器", font=FONTS["title"]).pack(pady=(20, 5))
        ttk.Label(center_frame, text=f"v{APP_VERSION}", font=FONTS["subtitle"]).pack(pady=(0, 20))
        ttk.Label(center_frame, text="可视化管理 OpenCode 和 Oh My OpenCode 配置文件").pack(pady=5)
        ttk.Label(center_frame, text="支持 Provider、Model、Agent、MCP、Compaction 管理").pack(pady=5)
        ttk.Label(center_frame, text="支持从 Claude Code 等工具导入配置").pack(pady=5)
        ttk.Label(center_frame, text="").pack(pady=10)

        ttk.Button(center_frame, text="🌐 GitHub", command=lambda: webbrowser.open(GITHUB_URL), bootstyle="primary").pack(pady=5)
        ttk.Label(center_frame, text=f"作者: {AUTHOR_NAME}", font=FONTS["small"]).pack(pady=(20, 5))
        ttk.Button(center_frame, text="👤 作者主页", command=lambda: webbrowser.open(AUTHOR_GITHUB), bootstyle="secondary").pack(pady=5)

# ==================== 侧边栏 ====================
class Sidebar(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bootstyle="secondary", width=200)
        self.app = app
        self.pack_propagate(False)
        self.buttons = {}
        self.active_key = None
        self.setup_ui()

    def setup_ui(self):
        head = ttk.Frame(self, bootstyle="secondary")
        head.pack(fill=X, padx=15, pady=20)
        ttk.Label(head, text="OpenCode", font=("Helvetica", 18, "bold"), bootstyle="inverse-secondary").pack(anchor=W)
        ttk.Label(head, text=f"v{APP_VERSION}", font=("Helvetica", 9), bootstyle="inverse-secondary").pack(anchor=W)

        self.create_nav_btn("provider", "📦  Provider 管理")
        self.create_nav_btn("model", "🤖  Model 管理")
        self.create_nav_btn("agent", "🕵️  Agent (OhMy)")
        ttk.Separator(self, bootstyle="secondary").pack(fill=X, pady=10, padx=10)
        self.create_nav_btn("opencode_agent", "🧩  Agent (Native)")
        self.create_nav_btn("mcp", "🔌  MCP 服务器")
        self.create_nav_btn("skill", "⚡  Skill 技能")
        self.create_nav_btn("rules", "📜  Rules 指令")
        self.create_nav_btn("compaction", "🧹  上下文压缩")
        self.create_nav_btn("permission", "🛡️  权限管理")
        ttk.Separator(self, bootstyle="secondary").pack(fill=X, pady=10, padx=10)
        self.create_nav_btn("help", "❓  帮助 & 关于")

    def create_nav_btn(self, key, text):
        btn = ttk.Button(self, text=text, bootstyle="secondary", cursor="hand2", command=lambda k=key: self.app.show_page(k))
        btn.pack(fill=X, padx=5, pady=2)
        self.buttons[key] = btn

    def set_active(self, key):
        if self.active_key:
            self.buttons[self.active_key].configure(bootstyle="secondary")
        self.active_key = key
        self.buttons[key].configure(bootstyle="primary")

# ==================== 主窗口 ====================
class MainWindow:
    def __init__(self):
        self.root = ttk.Window(title=f"OpenCode 配置管理器 v{APP_VERSION}", themename="darkly", size=(1100, 750))
        self.opencode_config = {}
        self.ohmyopencode_config = {}
        self.pages = {}
        self.backup_manager = BackupManager()
        
        self.setup_ui()
        self.load_configs()
        
        VersionChecker(self.on_update).check_update_async()

    def setup_ui(self):
        self.sidebar = Sidebar(self.root, self)
        self.sidebar.pack(side=LEFT, fill=Y)

        main = ttk.Frame(self.root)
        main.pack(side=RIGHT, fill=BOTH, expand=True)

        toolbar = ttk.Frame(main, padding=10)
        toolbar.pack(fill=X)
        
        ttk.Button(toolbar, text="🔄 刷新", command=self.load_configs, bootstyle="info-outline").pack(side=LEFT, padx=5)
        ttk.Button(toolbar, text="💾 保存全部", command=self.save_configs, bootstyle="success").pack(side=LEFT, padx=5)
        ttk.Button(toolbar, text="💾 备份", command=self.backup_configs, bootstyle="warning").pack(side=LEFT, padx=5)
        ttk.Button(toolbar, text="♻️ 恢复", command=self.show_restore_dialog, bootstyle="secondary").pack(side=LEFT, padx=5)
        
        ttk.Label(toolbar, text="🎨 主题:").pack(side=RIGHT, padx=(10, 5))
        theme_cb = ttk.Combobox(toolbar, values=self.root.style.theme_names(), state="readonly", width=10)
        theme_cb.set("darkly")
        theme_cb.pack(side=RIGHT)
        theme_cb.bind("<<ComboboxSelected>>", lambda e: self.root.style.theme_use(theme_cb.get()))

        self.update_lbl = ttk.Label(toolbar, text="", bootstyle="danger")
        self.update_lbl.pack(side=RIGHT, padx=20)

        ttk.Separator(main).pack(fill=X)

        self.content = ttk.Frame(main, padding=15)
        self.content.pack(fill=BOTH, expand=True)
        
        self.pages["provider"] = ProviderTab(self.content, self)
        self.pages["model"] = ModelTab(self.content, self)
        self.pages["agent"] = AgentTab(self.content, self)
        self.pages["category"] = CategoryTab(self.content, self)
        self.pages["permission"] = PermissionTab(self.content, self)
        self.pages["import"] = ImportTab(self.content, self)
        self.pages["compaction"] = CompactionTab(self.content, self)
        self.pages["skill"] = SkillTab(self.content, self)
        self.pages["rules"] = RulesTab(self.content, self)
        self.pages["mcp"] = MCPTab(self.content, self)
        self.pages["opencode_agent"] = OpenCodeAgentTab(self.content, self)
        self.pages["help"] = HelpTab(self.content, self)

    def show_page(self, key):
        for p in self.pages.values(): p.pack_forget()
        if key in self.pages: self.pages[key].pack(fill=BOTH, expand=True)
        self.sidebar.set_active(key)

    def load_configs(self):
        self.opencode_config = ConfigManager.load_json(ConfigPaths.get_opencode_config()) or {}
        self.ohmyopencode_config = ConfigManager.load_json(ConfigPaths.get_ohmyopencode_config()) or {}
        for p in self.pages.values(): 
            if hasattr(p, "refresh_list"): p.refresh_list()
            if hasattr(p, "refresh_models"): p.refresh_models()
            if hasattr(p, "refresh_scan"): p.refresh_scan()

    def refresh_all_tabs(self):
        self.load_configs()

    def save_configs(self):
        self.save_configs_silent()
        messagebox.showinfo("保存", "配置已保存")

    def save_configs_silent(self):
        a = ConfigManager.save_json(ConfigPaths.get_opencode_config(), self.opencode_config)
        b = ConfigManager.save_json(ConfigPaths.get_ohmyopencode_config(), self.ohmyopencode_config)
        return a and b

    def backup_configs(self):
        opencode_path = ConfigPaths.get_opencode_config()
        ohmyopencode_path = ConfigPaths.get_ohmyopencode_config()
        
        backup1 = self.backup_manager.backup(opencode_path, tag="manual")
        backup2 = self.backup_manager.backup(ohmyopencode_path, tag="manual")
        
        if backup1 or backup2:
            messagebox.showinfo("备份成功", f"备份已创建:\n{backup1}\n{backup2}")
        else:
            messagebox.showwarning("备份失败", "没有配置文件可备份")

    def show_restore_dialog(self):
        restore_win = tk.Toplevel(self.root)
        restore_win.title("恢复备份")
        restore_win.geometry("600x400")
        
        main_frame = ttk.Frame(restore_win, padding=10)
        main_frame.pack(fill=BOTH, expand=True)
        
        ttk.Label(main_frame, text="选择要恢复的备份:", font=FONTS["subtitle"]).pack(anchor=W, pady=(0, 10))
        
        columns = ("name", "timestamp", "tag")
        tree = ttk.Treeview(main_frame, columns=columns, show="headings", bootstyle="info")
        tree.heading("name", text="配置文件")
        tree.heading("timestamp", text="时间")
        tree.heading("tag", text="标签")
        tree.column("name", width=150)
        tree.column("timestamp", width=150)
        tree.column("tag", width=100)
        tree.pack(fill=BOTH, expand=True)
        
        backups = self.backup_manager.list_backups()
        for backup in backups:
            tree.insert("", END, values=(backup["name"], backup["timestamp"], backup["tag"]))
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=X, pady=(10, 0))
        
        def restore_selected():
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("提示", "请选择要恢复的备份")
                return
            item = tree.item(selection[0])
            backup_path = item["values"][0]
            
            if messagebox.askyesno("确认", f"确定要恢复备份吗？\n当前配置将被覆盖。"):
                if item["values"][0] == "opencode":
                    target_path = ConfigPaths.get_opencode_config()
                else:
                    target_path = ConfigPaths.get_ohmyopencode_config()
                
                if self.backup_manager.restore(backup_path, target_path):
                    messagebox.showinfo("成功", "备份已恢复")
                    self.load_configs()
                    restore_win.destroy()
                else:
                    messagebox.showerror("失败", "恢复备份失败")
        
        ttk.Button(btn_frame, text="♻️ 恢复选中", command=restore_selected, bootstyle="success").pack(side=LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="🗑 删除选中", command=lambda: self.delete_backup(tree, restore_win), bootstyle="danger").pack(side=LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="关闭", command=restore_win.destroy, bootstyle="secondary").pack(side=RIGHT)

    def delete_backup(self, tree, win):
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请选择要删除的备份")
            return
        item = tree.item(selection[0])
        backup_path = item["values"][0]
        
        if messagebox.askyesno("确认", f"确定要删除备份吗？"):
            if self.backup_manager.delete_backup(backup_path):
                tree.delete(selection[0])
                messagebox.showinfo("成功", "备份已删除")
            else:
                messagebox.showerror("失败", "删除备份失败")

    def on_update(self, ver, url):
        self.update_lbl.config(text=f"🔔 新版本 v{ver} 可用!")
        self.update_lbl.bind("<Button-1>", lambda e: webbrowser.open(url))

    def run(self):
        self.root.place_window_center()
        self.root.mainloop()

if __name__ == "__main__":
    MainWindow().run()
