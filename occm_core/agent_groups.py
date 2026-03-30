from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from .i18n import tr


class AgentGroupManager:
    """Agent分组管理器

    管理OpenCode和Oh My OpenCode的Agent分组配置，支持：
    - 创建、编辑、删除自定义分组
    - 快速应用预设或自定义分组
    - 导入/导出分组配置
    - 使用统计追踪
    """

    # 预设模板定义
    PRESETS = [
        {
            "id": "preset-minimal",
            "name": "最小化配置",
            "name_en": "Minimal",
            "description": "仅启用核心Agent，适合简单任务",
            "description_en": "Core agents only, for simple tasks",
            "icon": "⚡",
            "agents": {
                "opencode": [{"agent_id": "build", "enabled": True, "config": {}}],
                "oh_my_opencode": [{"agent_id": "sisyphus-junior", "enabled": True}],
            },
        },
        {
            "id": "preset-standard",
            "name": "标准配置",
            "name_en": "Standard",
            "description": "平衡的Agent组合，适合大多数任务",
            "description_en": "Balanced agent combination for most tasks",
            "icon": "⚙️",
            "agents": {
                "opencode": [
                    {"agent_id": "build", "enabled": True, "config": {}},
                    {"agent_id": "plan", "enabled": True, "config": {}},
                ],
                "oh_my_opencode": [
                    {"agent_id": "prometheus", "enabled": True},
                    {"agent_id": "sisyphus-junior", "enabled": True},
                    {"agent_id": "oracle", "enabled": True},
                ],
            },
        },
        {
            "id": "preset-full",
            "name": "常用配置",
            "name_en": "Common",
            "description": "常用Agent组合，适合大多数复杂项目",
            "description_en": "Common agent combination for most complex projects",
            "icon": "🚀",
            "agents": {
                "opencode": [
                    {"agent_id": "build", "enabled": True, "config": {}},
                    {"agent_id": "plan", "enabled": True, "config": {}},
                    {"agent_id": "explore", "enabled": True, "config": {}},
                    {"agent_id": "code-reviewer", "enabled": True, "config": {}},
                ],
                "oh_my_opencode": [
                    {"agent_id": "prometheus", "enabled": True},
                    {"agent_id": "sisyphus-junior", "enabled": True},
                    {"agent_id": "oracle", "enabled": True},
                    {"agent_id": "librarian", "enabled": True},
                    {"agent_id": "explore", "enabled": True},
                ],
            },
        },
        {
            "id": "preset-complete",
            "name": "完整配置",
            "name_en": "Complete",
            "description": "启用所有Agent，最大化功能",
            "description_en": "All agents enabled, maximum functionality",
            "icon": "💎",
            "agents": {
                "opencode": [
                    {"agent_id": "build", "enabled": True, "config": {}},
                    {"agent_id": "plan", "enabled": True, "config": {}},
                    {"agent_id": "explore", "enabled": True, "config": {}},
                    {"agent_id": "code-reviewer", "enabled": True, "config": {}},
                    {"agent_id": "oracle", "enabled": True, "config": {}},
                    {"agent_id": "librarian", "enabled": True, "config": {}},
                    {"agent_id": "prometheus", "enabled": True, "config": {}},
                ],
                "oh_my_opencode": [
                    {"agent_id": "prometheus", "enabled": True},
                    {"agent_id": "sisyphus-junior", "enabled": True},
                    {"agent_id": "oracle", "enabled": True},
                    {"agent_id": "librarian", "enabled": True},
                    {"agent_id": "explore", "enabled": True},
                    {"agent_id": "atlas", "enabled": True},
                    {"agent_id": "metis", "enabled": True},
                ],
            },
        },
        {
            "id": "preset-frontend",
            "name": "前端开发",
            "name_en": "Frontend",
            "description": "针对前端UI/UX开发优化",
            "description_en": "Optimized for frontend UI/UX development",
            "icon": "🎨",
            "agents": {
                "opencode": [
                    {"agent_id": "build", "enabled": True, "config": {}},
                    {"agent_id": "plan", "enabled": True, "config": {}},
                ],
                "oh_my_opencode": [
                    {"agent_id": "prometheus", "enabled": True},
                    {"agent_id": "sisyphus-junior", "enabled": True},
                ],
            },
        },
        {
            "id": "preset-backend",
            "name": "后端开发",
            "name_en": "Backend",
            "description": "针对后端API/数据库开发优化",
            "description_en": "Optimized for backend API/database development",
            "icon": "🔧",
            "agents": {
                "opencode": [
                    {"agent_id": "build", "enabled": True, "config": {}},
                    {"agent_id": "plan", "enabled": True, "config": {}},
                    {"agent_id": "explore", "enabled": True, "config": {}},
                ],
                "oh_my_opencode": [
                    {"agent_id": "prometheus", "enabled": True},
                    {"agent_id": "sisyphus-junior", "enabled": True},
                    {"agent_id": "oracle", "enabled": True},
                ],
            },
        },
    ]

    def __init__(self, config_dir: Path):
        """初始化分组管理器

        Args:
            config_dir: 配置文件目录 (~/.config/opencode)
        """
        self.config_dir = config_dir
        self.groups_file = config_dir / "agent-groups.json"
        self.backup_dir = config_dir / "backups"
        self.groups_data = {}
        self.load_groups()

    # ========== 数据加载/保存 ==========

    def load_groups(self) -> None:
        """从文件加载分组配置"""
        if not self.groups_file.exists():
            # 初始化默认配置
            self.groups_data = {
                "version": "1.0.0",
                "groups": [],
                "settings": {
                    "auto_backup": True,
                    "show_usage_stats": True,
                    "default_group_id": None,
                },
            }
            self.save_groups()
            return

        try:
            with open(self.groups_file, "r", encoding="utf-8") as f:
                self.groups_data = json.load(f)

            # 确保必要的字段存在
            if "groups" not in self.groups_data:
                self.groups_data["groups"] = []
            if "settings" not in self.groups_data:
                self.groups_data["settings"] = {
                    "auto_backup": True,
                    "show_usage_stats": True,
                    "default_group_id": None,
                }
        except Exception as e:
            print(tr("agent_groups.load_failed", error=str(e)))
            self.groups_data = {
                "version": "1.0.0",
                "groups": [],
                "settings": {
                    "auto_backup": True,
                    "show_usage_stats": True,
                    "default_group_id": None,
                },
            }

    def save_groups(self) -> None:
        """保存分组配置到文件"""
        try:
            # 确保目录存在
            self.config_dir.mkdir(parents=True, exist_ok=True)

            # 保存前备份
            if self.groups_data.get("settings", {}).get("auto_backup", True):
                if self.groups_file.exists():
                    self.backup_groups()

            # 保存配置
            with open(self.groups_file, "w", encoding="utf-8") as f:
                json.dump(self.groups_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(tr("agent_groups.save_failed", error=str(e)))
            raise

    def backup_groups(self) -> Optional[Path]:
        """备份当前分组配置

        Returns:
            Path: 备份文件路径，失败返回None
        """
        try:
            # 确保备份目录存在
            self.backup_dir.mkdir(parents=True, exist_ok=True)

            # 生成备份文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"agent-groups-backup-{timestamp}.json"

            # 复制当前配置
            if self.groups_file.exists():
                import shutil

                shutil.copy2(self.groups_file, backup_file)

                # 清理旧备份（保留最近10个）
                self._cleanup_old_backups()

                return backup_file
        except Exception as e:
            print(tr("agent_groups.backup_failed", error=str(e)))
            return None

    def _cleanup_old_backups(self, keep_count: int = 10) -> None:
        """清理旧备份文件

        Args:
            keep_count: 保留的备份数量
        """
        try:
            # 获取所有备份文件
            backup_files = sorted(
                self.backup_dir.glob("agent-groups-backup-*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )

            # 删除多余的备份
            for backup_file in backup_files[keep_count:]:
                backup_file.unlink()
        except Exception as e:
            print(tr("agent_groups.cleanup_failed", error=str(e)))

    # ========== 分组CRUD操作 ==========

    def create_group(
        self, name: str, description: str, agents: Dict, icon: str = "📁"
    ) -> str:
        """创建新分组

        Args:
            name: 分组名称
            description: 分组描述
            agents: Agent配置字典
            icon: 分组图标

        Returns:
            str: 分组ID (UUID)
        """
        import uuid

        group_id = f"group-{uuid.uuid4().hex[:8]}"
        now = datetime.now().isoformat()

        group = {
            "id": group_id,
            "name": name,
            "description": description,
            "type": "custom",
            "icon": icon,
            "created_at": now,
            "updated_at": now,
            "agents": agents,
            "statistics": {"usage_count": 0, "last_used": None},
        }

        self.groups_data["groups"].append(group)
        self.save_groups()

        return group_id

    def update_group(self, group_id: str, **kwargs) -> bool:
        """更新分组配置

        Args:
            group_id: 分组ID
            **kwargs: 要更新的字段

        Returns:
            bool: 是否成功
        """
        group = self.get_group(group_id)
        if not group:
            return False

        # 更新字段
        for key, value in kwargs.items():
            if key in ["name", "description", "icon", "agents"]:
                group[key] = value

        # 更新时间戳
        group["updated_at"] = datetime.now().isoformat()

        self.save_groups()
        return True

    def delete_group(self, group_id: str) -> bool:
        """删除分组

        Args:
            group_id: 分组ID

        Returns:
            bool: 是否成功
        """
        groups = self.groups_data["groups"]
        original_len = len(groups)

        self.groups_data["groups"] = [g for g in groups if g["id"] != group_id]

        if len(self.groups_data["groups"]) < original_len:
            self.save_groups()
            return True

        return False

    def get_group(self, group_id: str) -> Optional[Dict]:
        """获取分组配置

        Args:
            group_id: 分组ID

        Returns:
            Optional[Dict]: 分组配置，不存在返回None
        """
        for group in self.groups_data["groups"]:
            if group["id"] == group_id:
                return group
        return None

    def list_groups(self, include_presets: bool = False) -> List[Dict]:
        """列出所有分组

        Args:
            include_presets: 是否包含预设模板

        Returns:
            List[Dict]: 分组列表
        """
        groups = self.groups_data["groups"].copy()

        if include_presets:
            # 添加预设模板（标记为preset类型）
            for preset in self.PRESETS:
                preset_copy = self._localize_preset(preset)
                preset_copy["type"] = "preset"
                groups.append(preset_copy)
        return groups

    # ========== 分组应用 ==========

    def apply_group(
        self, group_id: str, opencode_config: Dict, omo_config: Dict
    ) -> Tuple[Dict, Dict]:
        """应用分组配置到OpenCode和Oh My OpenCode

        Args:
            group_id: 分组ID
            opencode_config: 当前OpenCode配置
            omo_config: 当前Oh My OpenCode配置

        Returns:
            Tuple[Dict, Dict]: 更新后的(opencode_config, omo_config)
        """
        # 获取分组配置（支持预设模板）
        group = self.get_group(group_id)
        if not group:
            # 尝试从预设模板中查找
            for preset in self.PRESETS:
                if preset["id"] == group_id:
                    group = preset
                    break

        if not group:
            return opencode_config, omo_config

        # 1. 更新OpenCode Agent配置
        if "agent" not in opencode_config:
            opencode_config["agent"] = {}

        # 获取所有OpenCode Agent ID
        all_opencode_agents = set()
        for agent_cfg in group["agents"].get("opencode", []):
            all_opencode_agents.add(agent_cfg["agent_id"])

        # 应用分组配置
        for agent_cfg in group["agents"].get("opencode", []):
            agent_id = agent_cfg["agent_id"]
            if agent_cfg["enabled"]:
                # 启用Agent并应用配置
                if agent_id not in opencode_config["agent"]:
                    opencode_config["agent"][agent_id] = {}

                # 合并配置
                config = agent_cfg.get("config", {})
                opencode_config["agent"][agent_id].update(config)

                # 确保disable字段为False或不存在
                if "disable" in opencode_config["agent"][agent_id]:
                    opencode_config["agent"][agent_id]["disable"] = False
            else:
                # 禁用Agent
                if agent_id in opencode_config["agent"]:
                    opencode_config["agent"][agent_id]["disable"] = True

        # 2. 更新Oh My OpenCode Agent配置
        if "agents" not in omo_config:
            omo_config["agents"] = {}

        # 获取所有Oh My OpenCode Agent ID
        all_omo_agents = set()
        for agent_cfg in group["agents"].get("oh_my_opencode", []):
            all_omo_agents.add(agent_cfg["agent_id"])

        # 应用分组配置
        for agent_cfg in group["agents"].get("oh_my_opencode", []):
            agent_id = agent_cfg["agent_id"]
            if agent_cfg["enabled"]:
                # 启用Agent并应用配置
                omo_config["agents"][agent_id] = {
                    "provider": agent_cfg.get("provider", ""),
                    "model": agent_cfg.get("model", ""),
                }
            else:
                # 禁用Agent（从配置中移除）
                if agent_id in omo_config["agents"]:
                    del omo_config["agents"][agent_id]

        # 3. 更新使用统计（仅对自定义分组）
        if group.get("type") == "custom":
            self.update_usage_stats(group_id)

        return opencode_config, omo_config

    def get_current_group_match(
        self, opencode_config: Dict, omo_config: Dict
    ) -> Optional[str]:
        """检测当前配置是否匹配某个分组

        Args:
            opencode_config: 当前OpenCode配置
            omo_config: 当前Oh My OpenCode配置

        Returns:
            Optional[str]: 匹配的分组ID，无匹配返回None
        """
        # 获取当前启用的Agent
        current_opencode_agents = set()
        for agent_id, config in opencode_config.get("agent", {}).items():
            if not config.get("disable", False):
                current_opencode_agents.add(agent_id)

        current_omo_agents = set(omo_config.get("agents", {}).keys())

        # 检查所有分组（包括预设）
        all_groups = self.list_groups(include_presets=True)

        for group in all_groups:
            # 获取分组中启用的Agent
            group_opencode_agents = set()
            for agent_cfg in group["agents"].get("opencode", []):
                if agent_cfg["enabled"]:
                    group_opencode_agents.add(agent_cfg["agent_id"])

            group_omo_agents = set()
            for agent_cfg in group["agents"].get("oh_my_opencode", []):
                if agent_cfg["enabled"]:
                    group_omo_agents.add(agent_cfg["agent_id"])

            # 检查是否匹配
            if (
                current_opencode_agents == group_opencode_agents
                and current_omo_agents == group_omo_agents
            ):
                return group["id"]

        return None

    # ========== 预设模板 ==========

    # Mapping from preset id to locale key prefix
    _PRESET_LOCALE_MAP = {
        "preset-minimal": "preset_minimal",
        "preset-standard": "preset_standard",
        "preset-full": "preset_common",
        "preset-complete": "preset_complete",
        "preset-frontend": "preset_frontend",
        "preset-backend": "preset_backend",
    }

    @staticmethod
    def _localize_preset(preset: Dict) -> Dict:
        """Return a copy of the preset with localized name/description."""
        p = preset.copy()
        key = AgentGroupManager._PRESET_LOCALE_MAP.get(preset["id"])
        if key:
            localized_name = tr(f"agent_groups.{key}")
            if localized_name != f"agent_groups.{key}":
                p["name"] = localized_name
            localized_desc = tr(f"agent_groups.{key}_desc")
            if localized_desc != f"agent_groups.{key}_desc":
                p["description"] = localized_desc
        return p

    def get_presets(self) -> List[Dict]:
        """获取所有预设模板

        Returns:
            List[Dict]: 预设模板列表
        """
        return [self._localize_preset(p) for p in self.PRESETS]

    def create_from_preset(
        self, preset_id: str, name: str, description: Optional[str] = None
    ) -> Optional[str]:
        """从预设模板创建分组

        Args:
            preset_id: 预设模板ID
            name: 新分组名称
            description: 新分组描述（可选）

        Returns:
            Optional[str]: 新分组ID，失败返回None
        """
        # 查找预设模板
        preset = None
        for p in self.PRESETS:
            if p["id"] == preset_id:
                preset = p
                break

        if not preset:
            return None

        # 使用预设的描述（如果未提供）
        if description is None:
            description = preset["description"]

        # 创建新分组
        return self.create_group(
            name=name,
            description=description,
            agents=preset["agents"],
            icon=preset["icon"],
        )

    # ========== 导入/导出 ==========

    def export_group(self, group_id: str, file_path: Path) -> bool:
        """导出分组到文件

        Args:
            group_id: 分组ID
            file_path: 导出文件路径

        Returns:
            bool: 是否成功
        """
        group = self.get_group(group_id)
        if not group:
            return False

        try:
            # 创建导出数据
            export_data = {
                "version": "1.0.0",
                "exported_at": datetime.now().isoformat(),
                "group": group,
            }

            # 写入文件
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            print(tr("agent_groups.export_failed", error=str(e)))
            return False

    def import_group(self, file_path: Path, overwrite: bool = False) -> Optional[str]:
        """从文件导入分组

        Args:
            file_path: 导入文件路径
            overwrite: 是否覆盖同名分组

        Returns:
            Optional[str]: 导入的分组ID，失败返回None
        """
        try:
            # 读取文件
            with open(file_path, "r", encoding="utf-8") as f:
                import_data = json.load(f)

            # 验证格式
            if "group" not in import_data:
                print(tr("agent_groups.import_format_error"))
                return None

            group = import_data["group"]

            # 检查同名分组
            existing_group = None
            for g in self.groups_data["groups"]:
                if g["name"] == group["name"]:
                    existing_group = g
                    break

            if existing_group and not overwrite:
                print(tr("agent_groups.import_exists", name=group['name']))
                return None

            if existing_group and overwrite:
                # 覆盖现有分组
                group_id = existing_group["id"]
                self.update_group(
                    group_id,
                    description=group["description"],
                    icon=group.get("icon", "📁"),
                    agents=group["agents"],
                )
                return group_id
            else:
                # 创建新分组
                return self.create_group(
                    name=group["name"],
                    description=group["description"],
                    agents=group["agents"],
                    icon=group.get("icon", "📁"),
                )
        except Exception as e:
            print(tr("agent_groups.import_failed", error=str(e)))
            return None

    # ========== 统计信息 ==========

    def update_usage_stats(self, group_id: str) -> None:
        """更新分组使用统计

        Args:
            group_id: 分组ID
        """
        group = self.get_group(group_id)
        if not group:
            return

        if "statistics" not in group:
            group["statistics"] = {"usage_count": 0, "last_used": None}

        group["statistics"]["usage_count"] = (
            group["statistics"].get("usage_count", 0) + 1
        )
        group["statistics"]["last_used"] = datetime.now().isoformat()

        self.save_groups()

    def get_usage_stats(self, group_id: str) -> Dict:
        """获取分组使用统计

        Args:
            group_id: 分组ID

        Returns:
            Dict: 统计信息
        """
        group = self.get_group(group_id)
        if not group:
            return {"usage_count": 0, "last_used": None}

        return group.get("statistics", {"usage_count": 0, "last_used": None})
