# -*- coding: utf-8 -*-
"""
OpenCode 配置管理器 v0.9.0 - PyQt5 + QFluentWidgets 版本
Part 2: 服务类
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field


class ConfigPaths:
    """配置文件路径管理"""

    def __init__(self):
        self.home = Path.home()
        self.opencode_dir = self.home / ".opencode"
        self.config_file = self.opencode_dir / "opencode.json"
        self.agents_md = self.opencode_dir / "AGENTS.md"
        self.skill_md = self.opencode_dir / "SKILL.md"
        self.backup_dir = self.opencode_dir / "backups"

    def ensure_dirs(self):
        """确保必要的目录存在"""
        self.opencode_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def config_exists(self) -> bool:
        """检查配置文件是否存在"""
        return self.config_file.exists()

    def get_external_configs(self) -> List[Dict[str, Any]]:
        """获取外部配置文件列表"""
        external_configs = []

        # 检查常见的配置文件位置
        locations = [
            (self.home / ".claude" / "claude.json", "Claude CLI"),
            (self.home / ".config" / "opencode" / "config.json", "OpenCode XDG"),
            (Path(os.environ.get("APPDATA", "")) / "opencode" / "config.json", "OpenCode AppData"),
        ]

        for path, name in locations:
            if path.exists():
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    external_configs.append({
                        "path": str(path),
                        "name": name,
                        "data": data,
                        "size": path.stat().st_size,
                        "modified": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                    })
                except Exception:
                    pass

        return external_configs


class ConfigManager:
    """配置文件管理器"""

    def __init__(self, paths: ConfigPaths):
        self.paths = paths
        self._config: Dict[str, Any] = {}
        self._dirty = False

    def load(self) -> Dict[str, Any]:
        """加载配置文件"""
        if self.paths.config_file.exists():
            try:
                with open(self.paths.config_file, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
            except Exception as e:
                print(f"加载配置失败: {e}")
                self._config = self._get_default_config()
        else:
            self._config = self._get_default_config()

        self._dirty = False
        return self._config

    def save(self) -> bool:
        """保存配置文件"""
        try:
            self.paths.ensure_dirs()
            with open(self.paths.config_file, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            self._dirty = False
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value

    def set(self, key: str, value: Any):
        """设置配置项"""
        keys = key.split(".")
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self._dirty = True

    def delete(self, key: str) -> bool:
        """删除配置项"""
        keys = key.split(".")
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                return False
            config = config[k]
        if keys[-1] in config:
            del config[keys[-1]]
            self._dirty = True
            return True
        return False

    def is_dirty(self) -> bool:
        """检查是否有未保存的更改"""
        return self._dirty

    def get_config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self._config

    def set_config(self, config: Dict[str, Any]):
        """设置完整配置"""
        self._config = config
        self._dirty = True

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "providers": {},
            "models": {},
            "mcpServers": {},
            "agents": {},
            "permissions": {
                "allow": [],
                "ask": [],
                "deny": []
            },
            "compaction": {
                "enabled": False,
                "threshold": 100000,
                "trimOldOutput": False
            }
        }

    # Provider 操作
    def get_providers(self) -> Dict[str, Any]:
        """获取所有服务商"""
        return self._config.get("providers", {})

    def get_provider(self, name: str) -> Optional[Dict[str, Any]]:
        """获取指定服务商"""
        return self._config.get("providers", {}).get(name)

    def add_provider(self, name: str, config: Dict[str, Any]):
        """添加服务商"""
        if "providers" not in self._config:
            self._config["providers"] = {}
        self._config["providers"][name] = config
        self._dirty = True

    def update_provider(self, name: str, config: Dict[str, Any]):
        """更新服务商"""
        if "providers" in self._config and name in self._config["providers"]:
            self._config["providers"][name] = config
            self._dirty = True

    def delete_provider(self, name: str) -> bool:
        """删除服务商"""
        if "providers" in self._config and name in self._config["providers"]:
            del self._config["providers"][name]
            self._dirty = True
            return True
        return False

    # Model 操作
    def get_models(self) -> Dict[str, Any]:
        """获取所有模型"""
        return self._config.get("models", {})

    def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        """获取指定模型"""
        return self._config.get("models", {}).get(model_id)

    def add_model(self, model_id: str, config: Dict[str, Any]):
        """添加模型"""
        if "models" not in self._config:
            self._config["models"] = {}
        self._config["models"][model_id] = config
        self._dirty = True

    def update_model(self, model_id: str, config: Dict[str, Any]):
        """更新模型"""
        if "models" in self._config and model_id in self._config["models"]:
            self._config["models"][model_id] = config
            self._dirty = True

    def delete_model(self, model_id: str) -> bool:
        """删除模型"""
        if "models" in self._config and model_id in self._config["models"]:
            del self._config["models"][model_id]
            self._dirty = True
            return True
        return False

    # MCP Server 操作
    def get_mcp_servers(self) -> Dict[str, Any]:
        """获取所有MCP服务器"""
        return self._config.get("mcpServers", {})

    def get_mcp_server(self, name: str) -> Optional[Dict[str, Any]]:
        """获取指定MCP服务器"""
        return self._config.get("mcpServers", {}).get(name)

    def add_mcp_server(self, name: str, config: Dict[str, Any]):
        """添加MCP服务器"""
        if "mcpServers" not in self._config:
            self._config["mcpServers"] = {}
        self._config["mcpServers"][name] = config
        self._dirty = True

    def update_mcp_server(self, name: str, config: Dict[str, Any]):
        """更新MCP服务器"""
        if "mcpServers" in self._config and name in self._config["mcpServers"]:
            self._config["mcpServers"][name] = config
            self._dirty = True

    def delete_mcp_server(self, name: str) -> bool:
        """删除MCP服务器"""
        if "mcpServers" in self._config and name in self._config["mcpServers"]:
            del self._config["mcpServers"][name]
            self._dirty = True
            return True
        return False

    # Agent 操作
    def get_agents(self) -> Dict[str, Any]:
        """获取所有Agent"""
        return self._config.get("agents", {})

    def get_agent(self, name: str) -> Optional[Dict[str, Any]]:
        """获取指定Agent"""
        return self._config.get("agents", {}).get(name)

    def add_agent(self, name: str, config: Dict[str, Any]):
        """添加Agent"""
        if "agents" not in self._config:
            self._config["agents"] = {}
        self._config["agents"][name] = config
        self._dirty = True

    def update_agent(self, name: str, config: Dict[str, Any]):
        """更新Agent"""
        if "agents" in self._config and name in self._config["agents"]:
            self._config["agents"][name] = config
            self._dirty = True

    def delete_agent(self, name: str) -> bool:
        """删除Agent"""
        if "agents" in self._config and name in self._config["agents"]:
            del self._config["agents"][name]
            self._dirty = True
            return True
        return False

    # Permission 操作
    def get_permissions(self) -> Dict[str, List[str]]:
        """获取权限配置"""
        return self._config.get("permissions", {"allow": [], "ask": [], "deny": []})

    def set_permissions(self, permissions: Dict[str, List[str]]):
        """设置权限配置"""
        self._config["permissions"] = permissions
        self._dirty = True

    # Compaction 操作
    def get_compaction(self) -> Dict[str, Any]:
        """获取压缩配置"""
        return self._config.get("compaction", {"enabled": False, "threshold": 100000, "trimOldOutput": False})

    def set_compaction(self, compaction: Dict[str, Any]):
        """设置压缩配置"""
        self._config["compaction"] = compaction
        self._dirty = True


class BackupManager:
    """备份管理器"""

    def __init__(self, paths: ConfigPaths):
        self.paths = paths
        self.max_backups = 10

    def create_backup(self, description: str = "") -> Optional[str]:
        """创建备份"""
        if not self.paths.config_file.exists():
            return None

        try:
            self.paths.ensure_dirs()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}.json"
            backup_path = self.paths.backup_dir / backup_name

            # 复制配置文件
            shutil.copy2(self.paths.config_file, backup_path)

            # 创建备份元数据
            meta_path = self.paths.backup_dir / f"backup_{timestamp}.meta"
            meta = {
                "timestamp": timestamp,
                "description": description,
                "original_size": self.paths.config_file.stat().st_size
            }
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False)

            # 清理旧备份
            self._cleanup_old_backups()

            return backup_name
        except Exception as e:
            print(f"创建备份失败: {e}")
            return None

    def restore_backup(self, backup_name: str) -> bool:
        """恢复备份"""
        backup_path = self.paths.backup_dir / backup_name
        if not backup_path.exists():
            return False

        try:
            # 先备份当前配置
            self.create_backup("自动备份（恢复前）")

            # 恢复备份
            shutil.copy2(backup_path, self.paths.config_file)
            return True
        except Exception as e:
            print(f"恢复备份失败: {e}")
            return False

    def delete_backup(self, backup_name: str) -> bool:
        """删除备份"""
        backup_path = self.paths.backup_dir / backup_name
        meta_path = self.paths.backup_dir / backup_name.replace(".json", ".meta")

        try:
            if backup_path.exists():
                backup_path.unlink()
            if meta_path.exists():
                meta_path.unlink()
            return True
        except Exception as e:
            print(f"删除备份失败: {e}")
            return False

    def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有备份"""
        backups = []
        if not self.paths.backup_dir.exists():
            return backups

        for backup_file in sorted(self.paths.backup_dir.glob("backup_*.json"), reverse=True):
            meta_file = backup_file.with_suffix(".meta")
            meta = {}
            if meta_file.exists():
                try:
                    with open(meta_file, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                except Exception:
                    pass

            backups.append({
                "name": backup_file.name,
                "path": str(backup_file),
                "size": backup_file.stat().st_size,
                "modified": datetime.fromtimestamp(backup_file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "description": meta.get("description", ""),
                "timestamp": meta.get("timestamp", "")
            })

        return backups

    def _cleanup_old_backups(self):
        """清理旧备份，保留最新的N个"""
        backups = sorted(self.paths.backup_dir.glob("backup_*.json"), reverse=True)
        for backup in backups[self.max_backups:]:
            try:
                backup.unlink()
                meta = backup.with_suffix(".meta")
                if meta.exists():
                    meta.unlink()
            except Exception:
                pass


class ModelRegistry:
    """模型注册表"""

    def __init__(self):
        self._presets = {}
        self._load_presets()

    def _load_presets(self):
        """加载预设模型配置"""
        from part1_constants import PRESET_MODEL_CONFIGS
        self._presets = PRESET_MODEL_CONFIGS.copy()

    def get_preset(self, model_id: str) -> Optional[Dict[str, Any]]:
        """获取预设模型配置"""
        return self._presets.get(model_id)

    def get_all_presets(self) -> Dict[str, Dict[str, Any]]:
        """获取所有预设模型配置"""
        return self._presets.copy()

    def get_models_for_provider(self, provider_name: str) -> List[str]:
        """获取指定服务商的模型列表"""
        from part1_constants import PRESET_SDKS
        for sdk_name, sdk_config in PRESET_SDKS.items():
            if sdk_config["name"] == provider_name:
                return sdk_config.get("models", [])
        return []


class ImportService:
    """导入服务"""

    def __init__(self, config_manager: ConfigManager, paths: ConfigPaths):
        self.config_manager = config_manager
        self.paths = paths

    def detect_external_configs(self) -> List[Dict[str, Any]]:
        """检测外部配置文件"""
        return self.paths.get_external_configs()

    def preview_import(self, external_config: Dict[str, Any]) -> Dict[str, Any]:
        """预览导入内容"""
        data = external_config.get("data", {})
        preview = {
            "providers": list(data.get("providers", {}).keys()),
            "models": list(data.get("models", {}).keys()),
            "mcpServers": list(data.get("mcpServers", {}).keys()),
            "agents": list(data.get("agents", {}).keys()),
            "has_permissions": "permissions" in data,
            "has_compaction": "compaction" in data
        }
        return preview

    def import_config(self, external_config: Dict[str, Any], merge: bool = True) -> bool:
        """导入配置"""
        try:
            data = external_config.get("data", {})

            if merge:
                # 合并模式：保留现有配置，添加新配置
                current = self.config_manager.get_config()

                for key in ["providers", "models", "mcpServers", "agents"]:
                    if key in data:
                        if key not in current:
                            current[key] = {}
                        current[key].update(data[key])

                if "permissions" in data:
                    current["permissions"] = data["permissions"]
                if "compaction" in data:
                    current["compaction"] = data["compaction"]

                self.config_manager.set_config(current)
            else:
                # 覆盖模式：完全替换
                self.config_manager.set_config(data)

            return self.config_manager.save()
        except Exception as e:
            print(f"导入配置失败: {e}")
            return False

    def export_config(self, export_path: str) -> bool:
        """导出配置"""
        try:
            config = self.config_manager.get_config()
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"导出配置失败: {e}")
            return False


class MarkdownFileManager:
    """Markdown文件管理器"""

    def __init__(self, paths: ConfigPaths):
        self.paths = paths

    def read_agents_md(self) -> str:
        """读取AGENTS.md"""
        if self.paths.agents_md.exists():
            try:
                with open(self.paths.agents_md, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                pass
        return ""

    def write_agents_md(self, content: str) -> bool:
        """写入AGENTS.md"""
        try:
            self.paths.ensure_dirs()
            with open(self.paths.agents_md, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"写入AGENTS.md失败: {e}")
            return False

    def read_skill_md(self) -> str:
        """读取SKILL.md"""
        if self.paths.skill_md.exists():
            try:
                with open(self.paths.skill_md, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                pass
        return ""

    def write_skill_md(self, content: str) -> bool:
        """写入SKILL.md"""
        try:
            self.paths.ensure_dirs()
            with open(self.paths.skill_md, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"写入SKILL.md失败: {e}")
            return False
