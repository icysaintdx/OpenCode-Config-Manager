from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple


class ConfigPaths:
    """
    配置文件路径管理 - 跨平台支持 (Windows/Linux/macOS)

    默认路径：
    - Windows: C:/Users/<user>/.config/opencode/
    - Linux: /home/<user>/.config/opencode/
    - macOS: /Users/<user>/.config/opencode/

    支持 .json 和 .jsonc 扩展名，支持自定义路径
    """

    # 自定义路径持久化文件
    _CUSTOM_PATHS_FILE = ".occm_custom_paths.json"

    # 自定义路径存储（None 表示使用默认路径）
    _custom_opencode_path: Optional[Path] = None
    _custom_ohmyopencode_path: Optional[Path] = None
    _custom_backup_path: Optional[Path] = None
    _custom_import_paths: Optional[Dict[str, Path]] = None

    @staticmethod
    def get_user_home() -> Path:
        """获取用户主目录（跨平台）"""
        return Path.home()

    @staticmethod
    def get_platform() -> str:
        """获取当前平台: windows, linux, macos"""
        import platform

        system = platform.system().lower()
        if system == "darwin":
            return "macos"
        return system

    @classmethod
    def get_config_base_dir(cls) -> Path:
        """
        获取配置文件基础目录（跨平台）

        所有平台统一使用 ~/.config/opencode/
        """
        return cls.get_user_home() / ".config" / "opencode"

    @classmethod
    def _get_config_path(cls, base_dir: Path, base_name: str) -> Path:
        """获取配置文件路径，优先检测 .jsonc，其次 .json"""
        jsonc_path = base_dir / f"{base_name}.jsonc"
        json_path = base_dir / f"{base_name}.json"

        # 优先返回存在的 .jsonc 文件
        if jsonc_path.exists():
            return jsonc_path
        # 其次返回存在的 .json 文件
        if json_path.exists():
            return json_path
        # 都不存在时，默认返回 .json 路径（用于创建新文件）
        return json_path

    @classmethod
    def check_config_conflict(cls, base_name: str) -> Optional[Tuple[Path, Path]]:
        """
        检查是否同时存在 .json 和 .jsonc 配置文件

        Args:
            base_name: 配置文件基础名称（如 "opencode" 或 "oh-my-opencode"）

        Returns:
            如果存在冲突，返回 (json_path, jsonc_path)；否则返回 None
        """
        base_dir = cls.get_config_base_dir()
        jsonc_path = base_dir / f"{base_name}.jsonc"
        json_path = base_dir / f"{base_name}.json"

        if jsonc_path.exists() and json_path.exists():
            return (json_path, jsonc_path)
        return None

    @classmethod
    def get_config_file_info(cls, path: Path) -> Dict:
        """获取配置文件信息（大小、修改时间）"""
        import os

        if not path.exists():
            return {"exists": False}

        stat = os.stat(path)
        return {
            "exists": True,
            "size": stat.st_size,
            "size_str": f"{stat.st_size:,} 字节",
            "mtime": datetime.fromtimestamp(stat.st_mtime),
            "mtime_str": datetime.fromtimestamp(stat.st_mtime).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        }

    @classmethod
    def get_opencode_config(cls) -> Path:
        """获取 OpenCode 配置路径（优先使用自定义路径）"""
        if cls._custom_opencode_path is not None:
            return cls._custom_opencode_path
        return cls._get_config_path(cls.get_config_base_dir(), "opencode")

    @classmethod
    def set_opencode_config(cls, path: Optional[Path]) -> None:
        """设置自定义 OpenCode 配置路径"""
        cls._custom_opencode_path = path
        cls._persist_custom_paths()

    @classmethod
    def get_ohmyopencode_config(cls) -> Path:
        """获取 Oh My OpenCode 配置路径（优先使用自定义路径）"""
        if cls._custom_ohmyopencode_path is not None:
            return cls._custom_ohmyopencode_path
        return cls._get_config_path(cls.get_config_base_dir(), "oh-my-opencode")

    @classmethod
    def set_ohmyopencode_config(cls, path: Optional[Path]) -> None:
        """设置自定义 Oh My OpenCode 配置路径"""
        cls._custom_ohmyopencode_path = path
        cls._persist_custom_paths()

    @classmethod
    def _get_settings_path(cls) -> Path:
        """持久化文件路径"""
        return cls.get_config_base_dir() / cls._CUSTOM_PATHS_FILE

    @classmethod
    def _persist_custom_paths(cls) -> None:
        """将自定义路径持久化到磁盘"""
        import json
        data = {}
        if cls._custom_opencode_path is not None:
            data["custom_opencode_path"] = str(cls._custom_opencode_path)
        if cls._custom_ohmyopencode_path is not None:
            data["custom_ohmyopencode_path"] = str(cls._custom_ohmyopencode_path)
        if cls._custom_backup_path is not None:
            data["custom_backup_dir"] = str(cls._custom_backup_path)
        settings_path = cls._get_settings_path()
        try:
            settings_path.parent.mkdir(parents=True, exist_ok=True)
            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[OCCM] Failed to persist custom paths: {e}")

    @classmethod
    def _load_custom_paths(cls) -> None:
        """从磁盘恢复自定义路径"""
        import json
        settings_path = cls._get_settings_path()
        if not settings_path.exists():
            return
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("custom_opencode_path"):
                cls._custom_opencode_path = Path(data["custom_opencode_path"])
            if data.get("custom_ohmyopencode_path"):
                cls._custom_ohmyopencode_path = Path(data["custom_ohmyopencode_path"])
            if data.get("custom_backup_dir"):
                cls._custom_backup_dir = Path(data["custom_backup_dir"])
        except Exception as e:
            print(f"[OCCM] Failed to load custom paths: {e}")

    @classmethod
    def is_custom_path(cls, config_type: str) -> bool:
        """检查是否使用自定义路径"""
        if config_type == "opencode":
            return cls._custom_opencode_path is not None
        elif config_type == "ohmyopencode":
            return cls._custom_ohmyopencode_path is not None
        elif config_type == "backup":
            return cls._custom_backup_path is not None
        return False

    @classmethod
    def reset_to_default(cls, config_type: str) -> None:
        """重置为默认路径"""
        if config_type == "opencode":
            cls._custom_opencode_path = None
        elif config_type == "ohmyopencode":
            cls._custom_ohmyopencode_path = None
        elif config_type == "backup":
            cls._custom_backup_path = None
        cls._persist_custom_paths()

    @classmethod
    def get_claude_settings(cls) -> Path:
        """获取 Claude Code 设置路径"""
        base_dir = cls.get_user_home() / ".claude"
        return cls._get_config_path(base_dir, "settings")

    @classmethod
    def get_claude_providers(cls) -> Path:
        """获取 Claude Code providers 路径"""
        base_dir = cls.get_user_home() / ".claude"
        return cls._get_config_path(base_dir, "providers")

    @classmethod
    def get_backup_dir(cls) -> Path:
        """获取备份目录（优先使用自定义路径）"""
        if cls._custom_backup_path is not None:
            return cls._custom_backup_path
        return cls.get_config_base_dir() / "backups"

    @classmethod
    def set_backup_dir(cls, path: Optional[Path]) -> None:
        """设置自定义备份目录"""
        cls._custom_backup_path = path
        cls._persist_custom_paths()

    @classmethod
    def get_import_path(cls, source_type: str) -> Optional[Path]:
        """获取自定义导入路径"""
        if cls._custom_import_paths is None:
            return None
        return cls._custom_import_paths.get(source_type)

    @classmethod
    def set_import_path(cls, source_type: str, path: Optional[Path]) -> None:
        """设置自定义导入路径"""
        if cls._custom_import_paths is None:
            cls._custom_import_paths = {}
        if path is None:
            cls._custom_import_paths.pop(source_type, None)
            return
        cls._custom_import_paths[source_type] = path
